import Foundation
import os

private let logger = Logger(subsystem: "com.devflow.app", category: "PythonBridge")

actor PythonBridge {
    private var process: Process?
    private var stdinPipe: Pipe?
    private var stdoutPipe: Pipe?
    private var stderrPipe: Pipe?
    private let rpcClient: RpcClient

    private(set) var isConnected = false
    private var healthCheckTask: Task<Void, Never>?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5

    init(rpcClient: RpcClient) {
        self.rpcClient = rpcClient
    }

    func start() async throws {
        guard !isConnected else { return }

        // Find Python executable
        let pythonPath = try await findPython()

        // Create pipes for communication
        let stdinPipe = Pipe()
        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()

        self.stdinPipe = stdinPipe
        self.stdoutPipe = stdoutPipe
        self.stderrPipe = stderrPipe

        // Create and configure the process
        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = ["-m", "bridge.main"]
        process.standardInput = stdinPipe
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        // Set working directory to devflow project
        // For development, use the parent of ui-native; for release, use bundled resources
        if let devflowPath = ProcessInfo.processInfo.environment["DEVFLOW_PATH"] {
            process.currentDirectoryURL = URL(fileURLWithPath: devflowPath)
        } else {
            // Default to ~/dev/devflow for development
            let defaultPath = NSString(string: "~/dev/devflow").expandingTildeInPath
            if FileManager.default.fileExists(atPath: defaultPath) {
                process.currentDirectoryURL = URL(fileURLWithPath: defaultPath)
            }
        }

        self.process = process

        // Start the process
        do {
            try process.run()
        } catch {
            self.process = nil
            self.stdinPipe = nil
            self.stdoutPipe = nil
            self.stderrPipe = nil
            throw BridgeError.connectionFailed(error)
        }

        // Start stderr logging
        startStderrLogging(stderrPipe)

        // Configure RPC client with the pipes
        await rpcClient.configure(inputPipe: stdinPipe, outputPipe: stdoutPipe)
        await rpcClient.startReading()

        isConnected = true
        reconnectAttempts = 0

        // Start health check
        startHealthCheck()
    }

    func stop() async {
        // Stop health check
        healthCheckTask?.cancel()
        healthCheckTask = nil

        isConnected = false
        await rpcClient.stop()

        process?.terminate()
        process = nil
        stdinPipe = nil
        stdoutPipe = nil
        stderrPipe = nil
    }

    // MARK: - Health Check

    private func startHealthCheck() {
        healthCheckTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(30))

                guard !Task.isCancelled else { break }

                do {
                    let response: [String: AnyCodable] = try await callWithTimeout("system.ping", timeout: .seconds(10))
                    if response["pong"] != nil {
                        logger.debug("Health check passed")
                    }
                } catch {
                    logger.warning("Health check failed: \(error.localizedDescription)")
                    await handleConnectionLost()
                    break
                }
            }
        }
    }

    private func handleConnectionLost() async {
        guard isConnected else { return }

        isConnected = false
        logger.warning("Connection lost, attempting to reconnect...")

        // Exponential backoff retry
        var delay: UInt64 = 1_000_000_000 // 1 second
        let maxDelay: UInt64 = 30_000_000_000 // 30 seconds

        for attempt in 1...maxReconnectAttempts {
            reconnectAttempts = attempt
            logger.info("Reconnect attempt \(attempt) of \(self.maxReconnectAttempts)")

            try? await Task.sleep(nanoseconds: delay)

            do {
                // Clean up old resources
                await rpcClient.stop()
                process?.terminate()

                // Try to reconnect
                try await start()
                logger.info("Reconnected successfully")
                return
            } catch {
                logger.warning("Reconnect attempt \(attempt) failed: \(error.localizedDescription)")
                delay = min(delay * 2, maxDelay)
            }
        }

        // Give up after max attempts
        logger.error("Failed to reconnect after \(self.maxReconnectAttempts) attempts")
    }

    // MARK: - Stderr Logging

    private func startStderrLogging(_ stderrPipe: Pipe) {
        Task.detached {
            let handle = stderrPipe.fileHandleForReading
            for try await line in handle.bytes.lines {
                logger.warning("Python stderr: \(line)")
            }
        }
    }

    // MARK: - Python Discovery

    private func findPython() async throws -> String {
        // First try to find Python using 'which' command (respects PATH including mise)
        let whichProcess = Process()
        whichProcess.executableURL = URL(fileURLWithPath: "/usr/bin/which")
        whichProcess.arguments = ["python3"]

        let pipe = Pipe()
        whichProcess.standardOutput = pipe
        whichProcess.standardError = FileHandle.nullDevice

        // Set up environment to include common paths
        var env = ProcessInfo.processInfo.environment
        let homeDir = FileManager.default.homeDirectoryForCurrentUser.path
        let additionalPaths = [
            "\(homeDir)/.local/share/mise/shims",
            "\(homeDir)/.local/bin",
            "/opt/homebrew/bin",
            "/usr/local/bin"
        ]
        if let existingPath = env["PATH"] {
            env["PATH"] = additionalPaths.joined(separator: ":") + ":" + existingPath
        }
        whichProcess.environment = env

        do {
            try whichProcess.run()
            whichProcess.waitUntilExit()

            if whichProcess.terminationStatus == 0 {
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                if let path = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                   !path.isEmpty {
                    return path
                }
            }
        } catch {
            // Fall through to static candidates
        }

        // Fallback to common Python locations
        let candidates = [
            "\(homeDir)/.local/share/mise/installs/python/3.12.12/bin/python3",
            "\(homeDir)/.local/share/mise/shims/python3",
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]

        for candidate in candidates {
            if FileManager.default.fileExists(atPath: candidate) {
                return candidate
            }
        }

        throw BridgeError.pythonNotFound
    }

    // MARK: - RPC Methods

    func call<T: Decodable & Sendable>(_ method: String, params: [String: any Sendable]? = nil) async throws -> T {
        guard isConnected else {
            throw BridgeError.notConnected
        }
        return try await rpcClient.call(method, params: params)
    }

    /// Call with timeout - returns within the specified duration or throws timeout error
    func callWithTimeout<T: Decodable & Sendable>(_ method: String, params: [String: any Sendable]? = nil, timeout: Duration = .seconds(30)) async throws -> T {
        guard isConnected else {
            throw BridgeError.notConnected
        }

        return try await withThrowingTaskGroup(of: T.self) { group in
            group.addTask {
                try await self.rpcClient.call(method, params: params)
            }

            group.addTask {
                try await Task.sleep(for: timeout)
                throw BridgeError.timeout(method)
            }

            guard let result = try await group.next() else {
                throw BridgeError.timeout(method)
            }
            group.cancelAll()
            return result
        }
    }
}

enum BridgeError: Error, LocalizedError {
    case pythonNotFound
    case notConnected
    case connectionFailed(Error)
    case timeout(String)

    var errorDescription: String? {
        switch self {
        case .pythonNotFound:
            return "Python 3 not found. Please install Python 3."
        case .notConnected:
            return "Not connected to Python backend"
        case .connectionFailed(let error):
            return "Failed to connect to Python backend: \(error.localizedDescription)"
        case .timeout(let method):
            return "Request timed out: \(method)"
        }
    }
}
