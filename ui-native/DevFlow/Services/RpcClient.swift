import Foundation

struct JsonRpcRequest: Encodable {
    let jsonrpc: String = "2.0"
    let id: Int
    let method: String
    let params: [String: AnyCodable]?
}

struct JsonRpcResponse<T: Decodable>: Decodable {
    let jsonrpc: String
    let id: Int
    let result: T?
    let error: JsonRpcError?
}

struct JsonRpcError: Decodable, Error, LocalizedError {
    let code: Int
    let message: String
    let data: AnyCodable?

    var errorDescription: String? {
        "\(message) (code: \(code))"
    }
}

struct AnyCodable: Codable, @unchecked Sendable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if container.decodeNil() {
            value = NSNull()
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unable to decode value")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case is NSNull:
            try container.encodeNil()
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: encoder.codingPath, debugDescription: "Unable to encode value"))
        }
    }
}

actor RpcClient {
    private var requestId = 0
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    private var inputPipe: Pipe?
    private var outputPipe: Pipe?
    private var pendingRequests: [Int: CheckedContinuation<Data, Error>] = [:]
    private var responseBuffer = Data()
    private var isReading = false

    init() {
        encoder = JSONEncoder()
        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }

    func configure(inputPipe: Pipe, outputPipe: Pipe) {
        self.inputPipe = inputPipe
        self.outputPipe = outputPipe
    }

    func startReading() {
        guard !isReading, let outputPipe = outputPipe else { return }
        isReading = true

        // Use a detached task to avoid actor isolation issues with blocking I/O
        Task.detached { [weak self] in
            guard let self = self else { return }
            await self.readLoop(from: outputPipe.fileHandleForReading)
        }
    }

    private func readLoop(from handle: FileHandle) async {
        // Read in a safe way that doesn't block the actor
        while await isReading {
            do {
                // Use readabilityHandler for async-safe reading
                let data = try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Data, Error>) in
                    // Read synchronously but wrapped in a continuation
                    DispatchQueue.global().async {
                        do {
                            let availableData = try handle.availableData
                            if availableData.isEmpty {
                                // Pipe closed
                                continuation.resume(throwing: RpcError.disconnected)
                            } else {
                                continuation.resume(returning: availableData)
                            }
                        } catch {
                            continuation.resume(throwing: error)
                        }
                    }
                }

                await appendToBuffer(data)
                await processBuffer()
            } catch {
                // Pipe closed or error - stop reading
                await stopReading()
                break
            }
        }
    }

    private func appendToBuffer(_ data: Data) {
        responseBuffer.append(data)
    }

    private func stopReading() {
        isReading = false
    }

    private func processBuffer() async {
        while let newlineIndex = responseBuffer.firstIndex(of: UInt8(ascii: "\n")) {
            let lineData = responseBuffer[..<newlineIndex]
            responseBuffer = responseBuffer[(newlineIndex + 1)...]

            guard !lineData.isEmpty else { continue }

            do {
                let response = try decoder.decode(JsonRpcResponse<AnyCodable>.self, from: Data(lineData))
                if let continuation = pendingRequests.removeValue(forKey: response.id) {
                    continuation.resume(returning: Data(lineData))
                }
            } catch {
                // Log parsing error but continue
                print("Failed to parse response: \(error)")
            }
        }
    }

    func call<T: Decodable & Sendable>(_ method: String, params: [String: any Sendable]? = nil) async throws -> T {
        guard let inputPipe = inputPipe else {
            throw RpcError.notConnected
        }

        requestId += 1
        let currentId = requestId

        let codableParams = params?.mapValues { AnyCodable($0) }
        let request = JsonRpcRequest(id: currentId, method: method, params: codableParams)

        var requestData = try encoder.encode(request)
        requestData.append(UInt8(ascii: "\n"))

        let responseData: Data = try await withCheckedThrowingContinuation { continuation in
            pendingRequests[currentId] = continuation

            do {
                try inputPipe.fileHandleForWriting.write(contentsOf: requestData)
            } catch {
                pendingRequests.removeValue(forKey: currentId)
                continuation.resume(throwing: error)
            }
        }

        let response = try decoder.decode(JsonRpcResponse<T>.self, from: responseData)

        if let error = response.error {
            throw error
        }

        guard let result = response.result else {
            throw RpcError.noResult
        }

        return result
    }

    func stop() {
        isReading = false
        for (_, continuation) in pendingRequests {
            continuation.resume(throwing: RpcError.disconnected)
        }
        pendingRequests.removeAll()
    }
}

enum RpcError: Error, LocalizedError {
    case notConnected
    case noResult
    case disconnected
    case timeout

    var errorDescription: String? {
        switch self {
        case .notConnected: return "Not connected to Python backend"
        case .noResult: return "No result in response"
        case .disconnected: return "Connection was closed"
        case .timeout: return "Request timed out"
        }
    }
}

private extension Data {
    var nilIfEmpty: Data? {
        isEmpty ? nil : self
    }
}
