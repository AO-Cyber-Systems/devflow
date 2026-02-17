import Foundation

// MARK: - Doc Type

enum DocType: String, Codable, CaseIterable {
    case api
    case architecture
    case component
    case guide
    case reference
    case tutorial
    case custom

    var displayName: String {
        switch self {
        case .api: return "API Documentation"
        case .architecture: return "Architecture"
        case .component: return "Component Docs"
        case .guide: return "Guide"
        case .reference: return "Reference"
        case .tutorial: return "Tutorial"
        case .custom: return "Custom"
        }
    }

    var icon: String {
        switch self {
        case .api: return "network"
        case .architecture: return "building.2"
        case .component: return "square.stack.3d.up"
        case .guide: return "book"
        case .reference: return "doc.text.magnifyingglass"
        case .tutorial: return "graduationcap"
        case .custom: return "doc.text"
        }
    }
}

// MARK: - Doc Format

enum DocFormat: String, Codable, CaseIterable {
    case markdown
    case json
    case yaml
    case openapi
    case asyncapi
    case plaintext

    var displayName: String {
        switch self {
        case .markdown: return "Markdown"
        case .json: return "JSON"
        case .yaml: return "YAML"
        case .openapi: return "OpenAPI"
        case .asyncapi: return "AsyncAPI"
        case .plaintext: return "Plain Text"
        }
    }

    var fileExtension: String {
        switch self {
        case .markdown: return ".md"
        case .json: return ".json"
        case .yaml: return ".yaml"
        case .openapi: return ".json"
        case .asyncapi: return ".yaml"
        case .plaintext: return ".txt"
        }
    }
}

// MARK: - Documentation

struct Documentation: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let docType: String
    let docTypeDisplay: String
    let docTypeIcon: String
    let format: String
    let formatDisplay: String
    let projectId: String?
    let description: String
    let tags: [String]
    let aiContext: String?
    let createdAt: String
    let updatedAt: String
    let sourceFile: String?
    var content: String?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case docType = "doc_type"
        case docTypeDisplay = "doc_type_display"
        case docTypeIcon = "doc_type_icon"
        case format
        case formatDisplay = "format_display"
        case projectId = "project_id"
        case description
        case tags
        case aiContext = "ai_context"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case sourceFile = "source_file"
        case content
    }

    static func == (lhs: Documentation, rhs: Documentation) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Doc Type Info

struct DocTypeInfo: Identifiable, Codable {
    var id: String { typeId }
    let typeId: String
    let name: String
    let icon: String

    enum CodingKeys: String, CodingKey {
        case typeId = "id"
        case name
        case icon
    }
}

// MARK: - Doc Format Info

struct DocFormatInfo: Identifiable, Codable {
    var id: String { formatId }
    let formatId: String
    let name: String
    let fileExtension: String

    enum CodingKeys: String, CodingKey {
        case formatId = "id"
        case name
        case fileExtension = "extension"
    }
}

// MARK: - API Responses

struct DocsListResponse: Codable {
    let docs: [Documentation]?
    let total: Int?
    let error: String?
}

struct DocDetailResponse: Codable {
    let doc: Documentation?
    let error: String?
}

struct DocCreateResponse: Codable {
    let success: Bool
    let doc: Documentation?
    let error: String?
}

struct DocUpdateResponse: Codable {
    let success: Bool
    let doc: Documentation?
    let error: String?
}

struct DocDeleteResponse: Codable {
    let success: Bool
    let message: String?
    let error: String?
}

struct DocImportResponse: Codable {
    let success: Bool
    let doc: Documentation?
    let error: String?
}

struct DocAiContextResponse: Codable {
    let context: String?
    let length: Int?
    let error: String?
}

struct DocTypesResponse: Codable {
    let types: [DocTypeInfo]?
    let error: String?
}

struct DocFormatsResponse: Codable {
    let formats: [DocFormatInfo]?
    let error: String?
}

// MARK: - Semantic Search

struct SemanticSearchResult: Identifiable, Codable {
    var id: String { docId }
    let docId: String
    let chunkIndex: Int?
    let chunkText: String
    let similarity: Double
    let title: String?
    let docType: String?
    let description: String?
    let tags: [String]?
    let relationships: [DocumentRelationship]?
    let metadata: [String: String]?

    enum CodingKeys: String, CodingKey {
        case docId = "doc_id"
        case chunkIndex = "chunk_index"
        case chunkText = "chunk_text"
        case similarity
        case title
        case docType = "doc_type"
        case description
        case tags
        case relationships
        case metadata
    }
}

struct DocumentRelationship: Codable {
    let type: String
    let direction: String
    let relatedId: String?
    let weight: Double?

    enum CodingKeys: String, CodingKey {
        case type
        case direction
        case relatedId = "related_id"
        case weight
    }
}

struct RelatedDocument: Identifiable, Codable {
    var id: String { docId }
    let docId: String
    let title: String
    let docType: String
    let description: String?
    let relationships: [RelationshipInfo]

    enum CodingKeys: String, CodingKey {
        case docId = "doc_id"
        case title
        case docType = "doc_type"
        case description
        case relationships
    }
}

struct RelationshipInfo: Codable {
    let type: String
    let direction: String
    let weight: Double?
}

struct RelationshipTypeInfo: Identifiable, Codable {
    var id: String { typeId }
    let typeId: String
    let name: String

    enum CodingKeys: String, CodingKey {
        case typeId = "id"
        case name
    }
}

// MARK: - Semantic Search API Responses

struct SemanticSearchResponse: Codable {
    let results: [SemanticSearchResult]?
    let total: Int?
    let query: String?
    let error: String?
}

struct RelatedDocsResponse: Codable {
    let related: [RelatedDocument]?
    let total: Int?
    let docId: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case related
        case total
        case docId = "doc_id"
        case error
    }
}

struct AddRelationshipResponse: Codable {
    let success: Bool
    let created: Bool?
    let sourceDocId: String?
    let targetDocId: String?
    let relationshipType: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case created
        case sourceDocId = "source_doc_id"
        case targetDocId = "target_doc_id"
        case relationshipType = "relationship_type"
        case error
    }
}

struct RemoveRelationshipResponse: Codable {
    let success: Bool
    let removed: Int?
    let error: String?
}

struct RelationshipTypesResponse: Codable {
    let types: [RelationshipTypeInfo]?
    let error: String?
}

struct SemanticStatsResponse: Codable {
    let enabled: Bool?
    let vectorStore: VectorStoreStats?
    let knowledgeGraph: KnowledgeGraphStats?
    let basePath: String?
    let message: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case enabled
        case vectorStore = "vector_store"
        case knowledgeGraph = "knowledge_graph"
        case basePath = "base_path"
        case message
        case error
    }
}

struct VectorStoreStats: Codable {
    let totalChunks: Int?
    let totalDocuments: Int?
    let dimensions: Int?
    let hasVecExtension: Bool?
    let dbPath: String?

    enum CodingKeys: String, CodingKey {
        case totalChunks = "total_chunks"
        case totalDocuments = "total_documents"
        case dimensions
        case hasVecExtension = "has_vec_extension"
        case dbPath = "db_path"
    }
}

struct KnowledgeGraphStats: Codable {
    let totalNodes: Int?
    let totalEdges: Int?
    let nodeTypes: [String: Int]?
    let relationshipTypes: [String: Int]?
    let dbPath: String?

    enum CodingKeys: String, CodingKey {
        case totalNodes = "total_nodes"
        case totalEdges = "total_edges"
        case nodeTypes = "node_types"
        case relationshipTypes = "relationship_types"
        case dbPath = "db_path"
    }
}

struct ReindexResponse: Codable {
    let success: Bool
    let indexed: Int?
    let failed: Int?
    let total: Int?
    let error: String?
}

// MARK: - Web Fetch

struct FetchedPage: Identifiable, Codable {
    var id: String { url }
    let url: String
    let title: String
    let content: String
    let links: [String]
    let fetchedAt: String
    let contentType: String
    let statusCode: Int

    enum CodingKeys: String, CodingKey {
        case url
        case title
        case content
        case links
        case fetchedAt = "fetched_at"
        case contentType = "content_type"
        case statusCode = "status_code"
    }
}

struct FetchUrlResponse: Codable {
    let success: Bool
    let pages: [FetchedPage]?
    let errors: [String]?
    let totalFetched: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case pages
        case errors
        case totalFetched = "total_fetched"
        case error
    }
}

struct ImportFromUrlResponse: Codable {
    let success: Bool
    let doc: Documentation?
    let sourceUrl: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case doc
        case sourceUrl = "source_url"
        case error
    }
}

struct ImportDocsSiteResponse: Codable {
    let success: Bool
    let totalFetched: Int?
    let totalImported: Int?
    let docs: [ImportedDocSummary]?
    let errors: [String]?
    let sourceUrl: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case totalFetched = "total_fetched"
        case totalImported = "total_imported"
        case docs
        case errors
        case sourceUrl = "source_url"
        case error
    }
}

struct ImportedDocSummary: Identifiable, Codable {
    let id: String
    let title: String
    let sourceUrl: String

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case sourceUrl = "source_url"
    }
}
