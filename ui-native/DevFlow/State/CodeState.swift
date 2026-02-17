import Foundation

/// Manages code scanning, search, and analysis.
@Observable
@MainActor
class CodeState {
    // MARK: - State

    var searchResults: [CodeSearchResult] = []
    var entityTypes: [CodeEntityTypeInfo] = []
    var relationshipTypes: [CodeRelationshipTypeInfo] = []
    var supportedLanguages: [String] = []
    var isLoading = false
    var isScanning = false
    var searchQuery: String = ""
    var selectedEntityType: String? = nil
    var currentProjectPath: String? = nil
    var scanStatus: ScanStatusInfo?
    var codeStats: CodeStats?

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Scan Actions

    func scanProject(path: String, languages: [String]? = nil) async -> ScanResult? {
        currentProjectPath = path
        isScanning = true
        defer { isScanning = false }

        do {
            var params: [String: any Sendable] = ["project_path": path]

            if let langs = languages {
                params["languages"] = langs
            }

            let response: CodeScanResponse = try await bridge.call("code.scan_project", params: params)

            if response.success, let result = response.result {
                notifications.add(.success("Scanned \(result.filesScanned) files, found \(result.entityCount) entities"))

                // Automatically index after scanning
                await indexProject(path: path)
                await getScanStatus(path: path)
                return result
            } else if let error = response.error {
                notifications.add(.error("Scan failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Scan failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func indexProject(path: String) async {
        do {
            let params: [String: any Sendable] = ["project_path": path]

            struct IndexResponse: Codable {
                let success: Bool
                let result: IndexResult?
                let error: String?

                struct IndexResult: Codable {
                    let entitiesIndexed: Int
                    let chunksIndexed: Int
                    let relationshipsIndexed: Int
                    let durationMs: Double

                    enum CodingKeys: String, CodingKey {
                        case entitiesIndexed = "entities_indexed"
                        case chunksIndexed = "chunks_indexed"
                        case relationshipsIndexed = "relationships_indexed"
                        case durationMs = "duration_ms"
                    }
                }
            }

            let response: IndexResponse = try await bridge.call("code.index_project", params: params)

            if response.success, let result = response.result {
                notifications.add(.success("Indexed \(result.entitiesIndexed) entities"))
            } else if let error = response.error {
                notifications.add(.warning("Index failed: \(error)"))
            }
        } catch {
            notifications.add(.warning("Index failed: \(error.localizedDescription)"))
        }
    }

    func getScanStatus(path: String) async {
        do {
            let params: [String: any Sendable] = ["project_path": path]
            let response: ScanStatusResponse = try await bridge.call("code.get_scan_status", params: params)

            if response.success {
                scanStatus = response.status
            }
        } catch {
            // Ignore
        }
    }

    func listEntities(
        projectPath: String,
        entityTypes: [String]? = nil,
        limit: Int = 100,
        offset: Int = 0
    ) async {
        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = [
                "project_path": projectPath,
                "limit": limit,
                "offset": offset,
            ]

            if let types = entityTypes {
                params["entity_types"] = types
            }

            struct ListResponse: Codable {
                let success: Bool
                let entities: [CodeSearchResult]?
                let count: Int?
                let error: String?
            }

            let response: ListResponse = try await bridge.call("code.list_entities", params: params)

            if response.success {
                searchResults = response.entities ?? []
            } else if let error = response.error {
                notifications.add(.error("List failed: \(error)"))
                searchResults = []
            }
        } catch {
            notifications.add(.error("List failed: \(error.localizedDescription)"))
            searchResults = []
        }
    }

    func getCodeStats(path: String) async {
        do {
            let params: [String: any Sendable] = ["project_path": path]
            let response: CodeStatsResponse = try await bridge.call("code.get_code_stats", params: params)

            if response.success {
                codeStats = response.stats
            }
        } catch {
            // Ignore
        }
    }

    // MARK: - Search Actions

    func search(
        query: String,
        projectPath: String? = nil,
        entityTypes: [String]? = nil,
        limit: Int = 20
    ) async {
        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = [
                "query": query,
                "limit": limit,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let types = entityTypes {
                params["entity_types"] = types
            }

            let response: CodeSearchResponse = try await bridge.call("code.search_code", params: params)

            if response.success {
                searchResults = response.results ?? []
            } else if let error = response.error {
                notifications.add(.error("Search failed: \(error)"))
                searchResults = []
            }
        } catch {
            notifications.add(.error("Search failed: \(error.localizedDescription)"))
            searchResults = []
        }
    }

    func findFunction(
        name: String,
        projectPath: String? = nil
    ) async -> [FunctionEntity] {
        do {
            var params: [String: any Sendable] = ["name": name]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: CodeFindFunctionResponse = try await bridge.call("code.find_function", params: params)

            if response.success {
                return response.functions ?? []
            }
        } catch {
            // Ignore
        }
        return []
    }

    func findClass(
        name: String,
        projectPath: String? = nil
    ) async -> [ClassEntity] {
        do {
            var params: [String: any Sendable] = ["name": name]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: CodeFindClassResponse = try await bridge.call("code.find_class", params: params)

            if response.success {
                return response.classes ?? []
            }
        } catch {
            // Ignore
        }
        return []
    }

    // MARK: - Relationship Actions

    func getCallers(
        entityId: String,
        projectPath: String? = nil
    ) async -> [CodeEntity] {
        do {
            var params: [String: any Sendable] = ["entity_id": entityId]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: CodeCallersResponse = try await bridge.call("code.get_callers", params: params)

            if response.success {
                return response.callers ?? []
            }
        } catch {
            // Ignore
        }
        return []
    }

    func getCallees(
        entityId: String,
        projectPath: String? = nil
    ) async -> [CodeEntity] {
        do {
            var params: [String: any Sendable] = ["entity_id": entityId]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: CodeCalleesResponse = try await bridge.call("code.get_callees", params: params)

            if response.success {
                return response.callees ?? []
            }
        } catch {
            // Ignore
        }
        return []
    }

    // MARK: - Metadata Actions

    func loadEntityTypes() async {
        do {
            let response: CodeEntityTypesResponse = try await bridge.call("code.get_entity_types")
            if response.success {
                entityTypes = response.types ?? []
            }
        } catch {
            // Ignore
        }
    }

    func loadRelationshipTypes() async {
        do {
            let response: CodeRelationshipTypesResponse = try await bridge.call("code.get_relationship_types")
            if response.success {
                relationshipTypes = response.types ?? []
            }
        } catch {
            // Ignore
        }
    }

    func loadSupportedLanguages() async {
        do {
            let response: CodeSupportedLanguagesResponse = try await bridge.call("code.get_supported_languages")
            if response.success {
                supportedLanguages = response.languages ?? []
            }
        } catch {
            // Ignore
        }
    }
}
