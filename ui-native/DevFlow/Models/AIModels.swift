import Foundation

// MARK: - AI Status

struct AIStatusResponse: Codable {
    let available: Bool
    let providers: [String: Bool]?
    let embeddings: EmbeddingStatus?
    let activeProvider: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case available, providers, embeddings
        case activeProvider = "active_provider"
        case error
    }
}

struct EmbeddingStatus: Codable {
    let activeBackend: String?
    let dimensions: Int?
    let apple: AppleEmbeddingInfo?
    let fastembed: FastEmbedInfo?

    private enum CodingKeys: String, CodingKey {
        case activeBackend = "active_backend"
        case dimensions, apple, fastembed
    }
}

struct AppleEmbeddingInfo: Codable {
    let available: Bool
    let dimensions: Int?
}

struct FastEmbedInfo: Codable {
    let available: Bool
    let dimensions: Int?
    let model: String?
}

// MARK: - Summarization

struct SummarizeResponse: Codable {
    let success: Bool
    let title: String?
    let keyPoints: [String]?
    let summary: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, title
        case keyPoints = "key_points"
        case summary, error
    }
}

struct DocumentSummary {
    let title: String?
    let keyPoints: [String]
    let summary: String

    init(from response: SummarizeResponse) {
        self.title = response.title
        self.keyPoints = response.keyPoints ?? []
        self.summary = response.summary ?? ""
    }
}

// MARK: - Entity Extraction

struct ExtractEntitiesResponse: Codable {
    let success: Bool
    let apis: [String]?
    let components: [String]?
    let concepts: [String]?
    let suggestedTags: [String]?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, apis, components, concepts
        case suggestedTags = "suggested_tags"
        case error
    }
}

struct ExtractedEntities {
    let apis: [String]
    let components: [String]
    let concepts: [String]
    let suggestedTags: [String]

    init(from response: ExtractEntitiesResponse) {
        self.apis = response.apis ?? []
        self.components = response.components ?? []
        self.concepts = response.concepts ?? []
        self.suggestedTags = response.suggestedTags ?? []
    }
}

// MARK: - Code Explanation

struct ExplainCodeResponse: Codable {
    let success: Bool
    let summary: String?
    let algorithmSteps: [String]?
    let parameters: [String: String]?
    let returns: String?
    let example: String?
    let entityId: String?
    let entityName: String?
    let language: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, summary
        case algorithmSteps = "algorithm_steps"
        case parameters, returns, example
        case entityId = "entity_id"
        case entityName = "entity_name"
        case language, error
    }
}

struct CodeExplanation {
    let summary: String
    let algorithmSteps: [String]
    let parameters: [String: String]
    let returns: String?
    let example: String?

    init(from response: ExplainCodeResponse) {
        self.summary = response.summary ?? ""
        self.algorithmSteps = response.algorithmSteps ?? []
        self.parameters = response.parameters ?? [:]
        self.returns = response.returns
        self.example = response.example
    }
}

// MARK: - Tag Generation

struct GenerateTagsResponse: Codable {
    let success: Bool
    let tags: [String]?
    let error: String?
}

// MARK: - Query Expansion

struct ExpandQueryResponse: Codable {
    let success: Bool
    let originalQuery: String?
    let expandedQuery: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case originalQuery = "original_query"
        case expandedQuery = "expanded_query"
        case error
    }
}

// MARK: - Docstring Generation

struct GenerateDocstringResponse: Codable {
    let success: Bool
    let docstring: String?
    let entityId: String?
    let entityName: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, docstring
        case entityId = "entity_id"
        case entityName = "entity_name"
        case error
    }
}

// MARK: - Improvement Suggestions

struct SuggestImprovementsResponse: Codable {
    let success: Bool
    let suggestions: [String]?
    let entityId: String?
    let entityName: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, suggestions
        case entityId = "entity_id"
        case entityName = "entity_name"
        case error
    }
}

// MARK: - Similar Code

struct SimilarCodeResult: Codable, Identifiable {
    let entityId: String
    let entityName: String
    let entityType: String
    let filePath: String
    let similarity: Double

    var id: String { entityId }

    private enum CodingKeys: String, CodingKey {
        case entityId = "entity_id"
        case entityName = "entity_name"
        case entityType = "entity_type"
        case filePath = "file_path"
        case similarity
    }
}

struct FindSimilarCodeResponse: Codable {
    let success: Bool
    let entityId: String?
    let similar: [SimilarCodeResult]?
    let count: Int?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case entityId = "entity_id"
        case similar, count, error
    }
}

// MARK: - Embeddings

struct GetEmbeddingResponse: Codable {
    let success: Bool
    let embedding: [Double]?
    let dimensions: Int?
    let backend: String?
    let error: String?
}

struct BatchEmbeddingsResponse: Codable {
    let success: Bool
    let embeddings: [[Double]]?
    let count: Int?
    let dimensions: Int?
    let backend: String?
    let error: String?
}

struct FindSimilarResponse: Codable {
    let success: Bool
    let results: [SimilarityResult]?
    let backend: String?
    let error: String?
}

struct SimilarityResult: Codable, Identifiable {
    let index: Int
    let text: String
    let similarity: Double

    var id: Int { index }
}

// MARK: - Language Detection

struct DetectLanguageResponse: Codable {
    let success: Bool
    let language: String?
    let error: String?
}

// MARK: - Translation

struct TranslateResponse: Codable {
    let success: Bool
    let original: String?
    let translated: String?
    let sourceLang: String?
    let targetLang: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success, original, translated
        case sourceLang = "source_lang"
        case targetLang = "target_lang"
        case error
    }
}

// MARK: - Document AI

struct SummarizeDocResponse: Codable {
    let success: Bool
    let docId: String?
    let title: String?
    let keyPoints: [String]?
    let summary: String?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case docId = "doc_id"
        case title
        case keyPoints = "key_points"
        case summary, error
    }
}

struct ExtractDocEntitiesResponse: Codable {
    let success: Bool
    let docId: String?
    let apis: [String]?
    let components: [String]?
    let concepts: [String]?
    let suggestedTags: [String]?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case docId = "doc_id"
        case apis, components, concepts
        case suggestedTags = "suggested_tags"
        case error
    }
}

struct RelatedDocSuggestion: Codable, Identifiable {
    let docId: String
    let title: String
    let similarity: Double
    let source: String
    let relationships: [RelatedDocRelationship]?

    var id: String { docId }

    private enum CodingKeys: String, CodingKey {
        case docId = "doc_id"
        case title, similarity, source, relationships
    }
}

struct RelatedDocRelationship: Codable {
    let type: String
    let direction: String
    let relatedId: String

    private enum CodingKeys: String, CodingKey {
        case type, direction
        case relatedId = "related_id"
    }
}

struct SuggestRelatedDocsResponse: Codable {
    let success: Bool
    let docId: String?
    let suggestions: [RelatedDocSuggestion]?
    let total: Int?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case docId = "doc_id"
        case suggestions, total, error
    }
}

struct AutoEnhanceDocResponse: Codable {
    let success: Bool
    let doc: EnhancedDocInfo?
    let enhancements: [String]?
    let message: String?
    let error: String?
}

struct EnhancedDocInfo: Codable {
    let id: String
    let title: String
    let docType: String
    let docTypeDisplay: String?
    let format: String
    let description: String?
    let tags: [String]?
    let aiContext: String?
    let createdAt: String?
    let updatedAt: String?

    private enum CodingKeys: String, CodingKey {
        case id, title
        case docType = "doc_type"
        case docTypeDisplay = "doc_type_display"
        case format, description, tags
        case aiContext = "ai_context"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct ValidateDocQualityResponse: Codable {
    let success: Bool
    let docId: String?
    let analysis: String?
    let rawResponse: Bool?
    let error: String?

    private enum CodingKeys: String, CodingKey {
        case success
        case docId = "doc_id"
        case analysis
        case rawResponse = "raw_response"
        case error
    }
}

// MARK: - AI Provider Info

struct AIProviderStatus: Identifiable {
    let id: String
    let name: String
    let available: Bool
    let isActive: Bool

    var displayName: String {
        switch id {
        case "apple": return "Apple Intelligence"
        case "ollama": return "Ollama (Local)"
        case "claude": return "Claude (Anthropic)"
        case "openai": return "OpenAI"
        default: return name.capitalized
        }
    }

    var icon: String {
        switch id {
        case "apple": return "apple.logo"
        case "ollama": return "server.rack"
        case "claude": return "cloud"
        case "openai": return "sparkles"
        default: return "cpu"
        }
    }
}
