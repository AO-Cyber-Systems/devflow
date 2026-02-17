import XCTest
@testable import DevFlow

final class RpcClientTests: XCTestCase {

    func testAnyCodableEncodesString() throws {
        let value = AnyCodable("test")
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        let json = String(data: data, encoding: .utf8)
        XCTAssertEqual(json, "\"test\"")
    }

    func testAnyCodableEncodesInt() throws {
        let value = AnyCodable(42)
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        let json = String(data: data, encoding: .utf8)
        XCTAssertEqual(json, "42")
    }

    func testAnyCodableEncodesBool() throws {
        let value = AnyCodable(true)
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        let json = String(data: data, encoding: .utf8)
        XCTAssertEqual(json, "true")
    }

    func testAnyCodableEncodesArray() throws {
        let value = AnyCodable([1, 2, 3])
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        let json = String(data: data, encoding: .utf8)
        XCTAssertEqual(json, "[1,2,3]")
    }

    func testAnyCodableEncodesDictionary() throws {
        let value = AnyCodable(["key": "value"])
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        let json = String(data: data, encoding: .utf8)
        XCTAssertEqual(json, "{\"key\":\"value\"}")
    }

    func testAnyCodableDecodesString() throws {
        let json = "\"test\""
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let value = try decoder.decode(AnyCodable.self, from: data)
        XCTAssertEqual(value.value as? String, "test")
    }

    func testAnyCodableDecodesInt() throws {
        let json = "42"
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let value = try decoder.decode(AnyCodable.self, from: data)
        XCTAssertEqual(value.value as? Int, 42)
    }

    func testJsonRpcRequestEncoding() throws {
        let request = JsonRpcRequest(id: 1, method: "test.method", params: ["key": AnyCodable("value")])
        let encoder = JSONEncoder()
        encoder.outputFormatting = .sortedKeys
        let data = try encoder.encode(request)
        let json = String(data: data, encoding: .utf8)!

        XCTAssertTrue(json.contains("\"jsonrpc\":\"2.0\""))
        XCTAssertTrue(json.contains("\"id\":1"))
        XCTAssertTrue(json.contains("\"method\":\"test.method\""))
        XCTAssertTrue(json.contains("\"params\":{\"key\":\"value\"}"))
    }

    func testJsonRpcResponseDecoding() throws {
        let json = """
        {"jsonrpc": "2.0", "id": 1, "result": {"status": "ok"}}
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()

        struct TestResult: Decodable {
            let status: String
        }

        let response = try decoder.decode(JsonRpcResponse<TestResult>.self, from: data)
        XCTAssertEqual(response.jsonrpc, "2.0")
        XCTAssertEqual(response.id, 1)
        XCTAssertEqual(response.result?.status, "ok")
        XCTAssertNil(response.error)
    }

    func testJsonRpcErrorDecoding() throws {
        let json = """
        {"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "Invalid Request"}}
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()

        let response = try decoder.decode(JsonRpcResponse<AnyCodable>.self, from: data)
        XCTAssertEqual(response.jsonrpc, "2.0")
        XCTAssertEqual(response.id, 1)
        XCTAssertNil(response.result)
        XCTAssertNotNil(response.error)
        XCTAssertEqual(response.error?.code, -32600)
        XCTAssertEqual(response.error?.message, "Invalid Request")
    }
}
