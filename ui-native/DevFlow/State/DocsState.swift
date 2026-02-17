import Foundation

/// Manages dev documentation - browsing, creating, and editing.
@Observable
@MainActor
class DocsState {
    // MARK: - State

    var docs: [Documentation] = []
    var docTypes: [DocTypeInfo] = []
    var docFormats: [DocFormatInfo] = []
    var isLoading = false
    var searchQuery: String = ""
    var selectedDocType: String? = nil
    var currentProjectPath: String? = nil

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - List Actions

    func load(projectPath: String? = nil) async {
        currentProjectPath = projectPath
        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = [:]

            if let path = projectPath {
                params["project_path"] = path
            }

            if let docType = selectedDocType {
                params["doc_type"] = docType
            }

            if !searchQuery.isEmpty {
                params["search"] = searchQuery
            }

            let response: DocsListResponse = try await bridge.call("docs.list_docs", params: params)

            if let error = response.error {
                notifications.add(.error("Failed to load docs: \(error)"))
                return
            }

            docs = response.docs ?? []
        } catch {
            notifications.add(.error("Failed to load docs: \(error.localizedDescription)"))
        }
    }

    func loadDocTypes() async {
        do {
            let response: DocTypesResponse = try await bridge.call("docs.get_doc_types")
            docTypes = response.types ?? []
        } catch {
            // Ignore
        }
    }

    func loadDocFormats() async {
        do {
            let response: DocFormatsResponse = try await bridge.call("docs.get_doc_formats")
            docFormats = response.formats ?? []
        } catch {
            // Ignore
        }
    }

    // MARK: - Document Actions

    func getDoc(_ docId: String, projectPath: String? = nil) async -> Documentation? {
        do {
            var params: [String: any Sendable] = ["doc_id": docId]
            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: DocDetailResponse = try await bridge.call("docs.get_doc", params: params)
            return response.doc
        } catch {
            return nil
        }
    }

    func createDoc(
        title: String,
        content: String,
        docType: String,
        format: String,
        projectPath: String? = nil,
        description: String = "",
        tags: [String] = [],
        aiContext: String? = nil,
        autoSummarize: Bool = false,
        autoTag: Bool = false
    ) async -> Documentation? {
        do {
            var params: [String: any Sendable] = [
                "title": title,
                "content": content,
                "doc_type": docType,
                "format": format,
                "description": description,
                "tags": tags,
                "auto_summarize": autoSummarize,
                "auto_tag": autoTag,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let context = aiContext {
                params["ai_context"] = context
            }

            let response: DocCreateResponse = try await bridge.call("docs.create_doc", params: params)

            if response.success, let doc = response.doc {
                notifications.add(.success("Documentation created"))
                docs.append(doc)
                return doc
            } else if let error = response.error {
                notifications.add(.error("Failed to create doc: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to create doc: \(error.localizedDescription)"))
        }
        return nil
    }

    func updateDoc(
        docId: String,
        projectPath: String? = nil,
        title: String? = nil,
        content: String? = nil,
        docType: String? = nil,
        format: String? = nil,
        description: String? = nil,
        tags: [String]? = nil,
        aiContext: String? = nil
    ) async -> Documentation? {
        do {
            var params: [String: any Sendable] = ["doc_id": docId]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }
            if let t = title { params["title"] = t }
            if let c = content { params["content"] = c }
            if let dt = docType { params["doc_type"] = dt }
            if let f = format { params["format"] = f }
            if let d = description { params["description"] = d }
            if let tg = tags { params["tags"] = tg }
            if let ac = aiContext { params["ai_context"] = ac }

            let response: DocUpdateResponse = try await bridge.call("docs.update_doc", params: params)

            if response.success, let doc = response.doc {
                notifications.add(.success("Documentation updated"))
                if let index = docs.firstIndex(where: { $0.id == docId }) {
                    docs[index] = doc
                }
                return doc
            } else if let error = response.error {
                notifications.add(.error("Failed to update doc: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to update doc: \(error.localizedDescription)"))
        }
        return nil
    }

    func deleteDoc(_ docId: String, projectPath: String? = nil) async {
        do {
            var params: [String: any Sendable] = ["doc_id": docId]
            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: DocDeleteResponse = try await bridge.call("docs.delete_doc", params: params)

            if response.success {
                notifications.add(.success("Documentation deleted"))
                docs.removeAll { $0.id == docId }
            } else if let error = response.error {
                notifications.add(.error("Failed to delete doc: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to delete doc: \(error.localizedDescription)"))
        }
    }

    func importFromFile(
        filePath: String,
        projectPath: String? = nil,
        docType: String = "custom",
        aiContext: String? = nil,
        autoSummarize: Bool = false,
        autoTag: Bool = false
    ) async -> Documentation? {
        do {
            var params: [String: any Sendable] = [
                "file_path": filePath,
                "doc_type": docType,
                "auto_summarize": autoSummarize,
                "auto_tag": autoTag,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let context = aiContext {
                params["ai_context"] = context
            }

            let response: DocImportResponse = try await bridge.call("docs.import_from_file", params: params)

            if response.success, let doc = response.doc {
                notifications.add(.success("Documentation imported"))
                docs.append(doc)
                return doc
            } else if let error = response.error {
                notifications.add(.error("Import failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to import doc: \(error.localizedDescription)"))
        }
        return nil
    }

    func getAiContext(
        projectPath: String? = nil,
        docTypes: [String]? = nil
    ) async -> String? {
        do {
            var params: [String: any Sendable] = [:]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let types = docTypes {
                params["doc_types"] = types
            }

            let response: DocAiContextResponse = try await bridge.call("docs.get_ai_context", params: params)
            return response.context
        } catch {
            return nil
        }
    }

    // MARK: - Semantic Search

    func semanticSearch(
        query: String,
        projectPath: String? = nil,
        limit: Int = 10,
        includeRelated: Bool = true
    ) async -> [SemanticSearchResult] {
        do {
            var params: [String: any Sendable] = [
                "query": query,
                "limit": limit,
                "include_related": includeRelated,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: SemanticSearchResponse = try await bridge.call("docs.semantic_search", params: params)

            if let error = response.error {
                notifications.add(.error("Search failed: \(error)"))
                return []
            }

            return response.results ?? []
        } catch {
            notifications.add(.error("Search failed: \(error.localizedDescription)"))
            return []
        }
    }

    func getRelatedDocs(
        docId: String,
        projectPath: String? = nil,
        relationshipTypes: [String]? = nil,
        limit: Int = 20
    ) async -> [RelatedDocument] {
        do {
            var params: [String: any Sendable] = [
                "doc_id": docId,
                "limit": limit,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let types = relationshipTypes {
                params["relationship_types"] = types
            }

            let response: RelatedDocsResponse = try await bridge.call("docs.get_related_docs", params: params)
            return response.related ?? []
        } catch {
            return []
        }
    }

    func addRelationship(
        sourceDocId: String,
        targetDocId: String,
        relationshipType: String,
        projectPath: String? = nil
    ) async -> Bool {
        do {
            var params: [String: any Sendable] = [
                "source_doc_id": sourceDocId,
                "target_doc_id": targetDocId,
                "relationship_type": relationshipType,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: AddRelationshipResponse = try await bridge.call("docs.add_relationship", params: params)

            if response.success {
                notifications.add(.success("Relationship added"))
                return true
            } else if let error = response.error {
                notifications.add(.error("Failed to add relationship: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to add relationship: \(error.localizedDescription)"))
        }
        return false
    }

    func removeRelationship(
        sourceDocId: String,
        targetDocId: String,
        relationshipType: String? = nil,
        projectPath: String? = nil
    ) async -> Int {
        do {
            var params: [String: any Sendable] = [
                "source_doc_id": sourceDocId,
                "target_doc_id": targetDocId,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let type = relationshipType {
                params["relationship_type"] = type
            }

            let response: RemoveRelationshipResponse = try await bridge.call("docs.remove_relationship", params: params)

            if response.success, let removed = response.removed, removed > 0 {
                notifications.add(.success("Relationship removed"))
                return removed
            }
        } catch {
            notifications.add(.error("Failed to remove relationship: \(error.localizedDescription)"))
        }
        return 0
    }

    func getRelationshipTypes() async -> [RelationshipTypeInfo] {
        do {
            let response: RelationshipTypesResponse = try await bridge.call("docs.get_relationship_types")
            return response.types ?? []
        } catch {
            return []
        }
    }

    func getSemanticStats(projectPath: String? = nil) async -> SemanticStatsResponse? {
        do {
            var params: [String: any Sendable] = [:]
            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: SemanticStatsResponse = try await bridge.call("docs.get_semantic_stats", params: params)
            return response
        } catch {
            return nil
        }
    }

    func reindexAll(projectPath: String? = nil) async -> Bool {
        do {
            var params: [String: any Sendable] = [:]
            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            let response: ReindexResponse = try await bridge.call("docs.reindex_all", params: params)

            if response.success {
                let indexed = response.indexed ?? 0
                notifications.add(.success("Reindexed \(indexed) documents"))
                return true
            } else if let error = response.error {
                notifications.add(.error("Reindex failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Reindex failed: \(error.localizedDescription)"))
        }
        return false
    }

    // MARK: - Web Fetch

    func fetchUrl(_ url: String) async -> [FetchedPage] {
        do {
            let params: [String: any Sendable] = ["url": url]
            let response: FetchUrlResponse = try await bridge.call("docs.fetch_url", params: params)

            if let error = response.error {
                notifications.add(.error("Fetch failed: \(error)"))
                return []
            }

            return response.pages ?? []
        } catch {
            notifications.add(.error("Fetch failed: \(error.localizedDescription)"))
            return []
        }
    }

    func importFromUrl(
        url: String,
        projectPath: String? = nil,
        docType: String = "reference",
        aiContext: String? = nil,
        title: String? = nil
    ) async -> Documentation? {
        do {
            var params: [String: any Sendable] = [
                "url": url,
                "doc_type": docType,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let context = aiContext {
                params["ai_context"] = context
            }

            if let t = title {
                params["title"] = t
            }

            let response: ImportFromUrlResponse = try await bridge.call("docs.import_from_url", params: params)

            if response.success, let doc = response.doc {
                notifications.add(.success("Imported from \(url)"))
                docs.append(doc)
                return doc
            } else if let error = response.error {
                notifications.add(.error("Import failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Import failed: \(error.localizedDescription)"))
        }
        return nil
    }

    func importDocsSite(
        url: String,
        projectPath: String? = nil,
        docType: String = "reference",
        maxPages: Int = 50,
        maxDepth: Int = 3,
        pathPrefix: String? = nil,
        includePatterns: [String]? = nil,
        excludePatterns: [String]? = nil
    ) async -> ImportDocsSiteResponse? {
        do {
            var params: [String: any Sendable] = [
                "url": url,
                "doc_type": docType,
                "max_pages": maxPages,
                "max_depth": maxDepth,
            ]

            if let path = projectPath ?? currentProjectPath {
                params["project_path"] = path
            }

            if let prefix = pathPrefix {
                params["path_prefix"] = prefix
            }

            if let include = includePatterns {
                params["include_patterns"] = include
            }

            if let exclude = excludePatterns {
                params["exclude_patterns"] = exclude
            }

            let response: ImportDocsSiteResponse = try await bridge.call("docs.import_docs_site", params: params)

            if response.success {
                let imported = response.totalImported ?? 0
                notifications.add(.success("Imported \(imported) pages from \(url)"))
                // Reload docs to get the new ones
                await load(projectPath: projectPath ?? currentProjectPath)
                return response
            } else if let error = response.error {
                notifications.add(.error("Import failed: \(error)"))
            }
            return response
        } catch {
            notifications.add(.error("Import failed: \(error.localizedDescription)"))
            return nil
        }
    }
}
