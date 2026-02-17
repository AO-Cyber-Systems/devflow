import XCTest
@testable import DevFlow

/// Contract tests verify that Swift models can decode actual Python RPC responses.
/// Run `python tests/contracts/generate_snapshots.py` first to generate snapshots.
final class ContractTests: XCTestCase {

    let decoder = JSONDecoder()
    var snapshotsDir: URL!

    override func setUp() {
        super.setUp()
        // Find snapshots directory relative to the project
        let projectRoot = URL(fileURLWithPath: #file)
            .deletingLastPathComponent() // ContractTests
            .deletingLastPathComponent() // Tests
            .deletingLastPathComponent() // ui-native
        snapshotsDir = projectRoot
            .appendingPathComponent("tests")
            .appendingPathComponent("contracts")
            .appendingPathComponent("snapshots")
    }

    // MARK: - Helper

    func loadSnapshot(_ name: String) throws -> Data {
        let url = snapshotsDir.appendingPathComponent("\(name).json")
        return try Data(contentsOf: url)
    }

    func decodeResult<T: Decodable>(_ type: T.Type, from snapshotName: String) throws -> T {
        let data = try loadSnapshot(snapshotName)

        // Parse the RPC response wrapper
        struct RpcResponse: Decodable {
            let result: T?
            let error: RpcError?
        }

        struct RpcError: Decodable {
            let code: Int
            let message: String
        }

        let response = try decoder.decode(RpcResponse.self, from: data)

        if let error = response.error {
            throw NSError(domain: "RPC", code: error.code, userInfo: [
                NSLocalizedDescriptionKey: error.message
            ])
        }

        guard let result = response.result else {
            throw NSError(domain: "RPC", code: -1, userInfo: [
                NSLocalizedDescriptionKey: "No result in response"
            ])
        }

        return result
    }

    // MARK: - System Tests

    func testSystemPing() throws {
        struct PingResponse: Decodable {
            let pong: Bool
            let version: String
            let timestamp: Double
        }

        let result = try decodeResult(PingResponse.self, from: "system_ping")
        XCTAssertTrue(result.pong)
        XCTAssertFalse(result.version.isEmpty)
    }

    func testSystemVersion() throws {
        struct VersionResponse: Decodable {
            let devflow: String
            let python: String
            let platform: String
        }

        let result = try decodeResult(VersionResponse.self, from: "system_version")
        XCTAssertFalse(result.devflow.isEmpty)
    }

    func testSystemFullDoctor() throws {
        let result = try decodeResult(FullDoctorResponse.self, from: "system_full_doctor")
        XCTAssertFalse(result.overallStatus.isEmpty)
        XCTAssertFalse(result.tools.checks.isEmpty)
        XCTAssertFalse(result.packages.packages.isEmpty)
    }

    func testSystemPackageDoctor() throws {
        let result = try decodeResult(PackageDoctorResponse.self, from: "system_package_doctor")
        XCTAssertFalse(result.overallStatus.isEmpty)
        XCTAssertGreaterThan(result.summary.total, 0)
    }

    // MARK: - Projects Tests

    func testProjectsList() throws {
        struct ProjectsListResponse: Decodable {
            let projects: [Project]
        }

        let result = try decodeResult(ProjectsListResponse.self, from: "projects_list")
        // Projects list can be empty, just verify it decodes
        XCTAssertNotNil(result.projects)
    }

    // MARK: - Docs Tests

    func testDocsListDocs() throws {
        let result = try decodeResult(DocsListResponse.self, from: "docs_list_docs")
        // Can be empty, just verify decode works
        XCTAssertNotNil(result.docs)
    }

    func testDocsGetDocTypes() throws {
        let result = try decodeResult(DocTypesResponse.self, from: "docs_get_doc_types")
        XCTAssertNotNil(result.types)
    }

    func testDocsGetDocFormats() throws {
        let result = try decodeResult(DocFormatsResponse.self, from: "docs_get_doc_formats")
        XCTAssertNotNil(result.formats)
    }

    // MARK: - Code Tests

    func testCodeGetEntityTypes() throws {
        struct EntityTypesResponse: Decodable {
            let types: [CodeEntityTypeInfo]?
            let entityTypes: [CodeEntityTypeInfo]?

            enum CodingKeys: String, CodingKey {
                case types
                case entityTypes = "entity_types"
            }
        }

        let result = try decodeResult(EntityTypesResponse.self, from: "code_get_entity_types")
        let types = result.types ?? result.entityTypes ?? []
        XCTAssertNotNil(types)
    }

    func testCodeGetSupportedLanguages() throws {
        struct LanguagesResponse: Decodable {
            let languages: [String]
        }

        let result = try decodeResult(LanguagesResponse.self, from: "code_get_supported_languages")
        XCTAssertFalse(result.languages.isEmpty)
    }

    // MARK: - Agents Tests

    func testAgentsListAgents() throws {
        let result = try decodeResult(AgentListResponse.self, from: "agents_list_agents")
        XCTAssertNotNil(result.agents)
        XCTAssertGreaterThan(result.total, 0)
    }
}
