import Foundation

// MARK: - Code Entity Types

enum CodeEntityType: String, Codable, CaseIterable {
    case function
    case method
    case classEntity = "class"
    case module
    case import_

    var displayName: String {
        switch self {
        case .function: return "Function"
        case .method: return "Method"
        case .classEntity: return "Class"
        case .module: return "Module"
        case .import_: return "Import"
        }
    }

    var icon: String {
        switch self {
        case .function: return "function"
        case .method: return "m.square"
        case .classEntity: return "c.square"
        case .module: return "folder"
        case .import_: return "arrow.down.square"
        }
    }
}

// MARK: - Code Entity

struct CodeEntity: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let qualifiedName: String
    let entityType: String
    let filePath: String
    let lineStart: Int
    let lineEnd: Int
    let language: String
    let docstring: String?
    let sourceCode: String?
    let tags: [String]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case qualifiedName = "qualified_name"
        case entityType = "entity_type"
        case filePath = "file_path"
        case lineStart = "line_start"
        case lineEnd = "line_end"
        case language
        case docstring
        case sourceCode = "source_code"
        case tags
    }

    var entityTypeEnum: CodeEntityType? {
        CodeEntityType(rawValue: entityType)
    }

    var lineCount: Int {
        lineEnd - lineStart + 1
    }

    static func == (lhs: CodeEntity, rhs: CodeEntity) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Function Entity

struct FunctionEntity: Identifiable, Codable {
    let id: String
    let name: String
    let qualifiedName: String
    let entityType: String
    let filePath: String
    let lineStart: Int
    let lineEnd: Int
    let language: String
    let docstring: String?
    let sourceCode: String?
    let tags: [String]
    let parameters: [FunctionParameter]
    let returnType: String?
    let decorators: [String]
    let isAsync: Bool
    let isGenerator: Bool
    let isMethod: Bool
    let parentClass: String?
    let calls: [String]
    let complexity: Int

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case qualifiedName = "qualified_name"
        case entityType = "entity_type"
        case filePath = "file_path"
        case lineStart = "line_start"
        case lineEnd = "line_end"
        case language
        case docstring
        case sourceCode = "source_code"
        case tags
        case parameters
        case returnType = "return_type"
        case decorators
        case isAsync = "is_async"
        case isGenerator = "is_generator"
        case isMethod = "is_method"
        case parentClass = "parent_class"
        case calls
        case complexity
    }
}

struct FunctionParameter: Codable {
    let name: String
    let typeAnnotation: String?
    let defaultValue: String?
    let isOptional: Bool

    enum CodingKeys: String, CodingKey {
        case name
        case typeAnnotation = "type_annotation"
        case defaultValue = "default_value"
        case isOptional = "is_optional"
    }
}

// MARK: - Class Entity

struct ClassEntity: Identifiable, Codable {
    let id: String
    let name: String
    let qualifiedName: String
    let entityType: String
    let filePath: String
    let lineStart: Int
    let lineEnd: Int
    let language: String
    let docstring: String?
    let sourceCode: String?
    let tags: [String]
    let baseClasses: [String]
    let decorators: [String]
    let methods: [String]
    let properties: [ClassProperty]
    let isAbstract: Bool
    let isDataclass: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case qualifiedName = "qualified_name"
        case entityType = "entity_type"
        case filePath = "file_path"
        case lineStart = "line_start"
        case lineEnd = "line_end"
        case language
        case docstring
        case sourceCode = "source_code"
        case tags
        case baseClasses = "base_classes"
        case decorators
        case methods
        case properties
        case isAbstract = "is_abstract"
        case isDataclass = "is_dataclass"
    }
}

struct ClassProperty: Codable {
    let name: String
    let typeAnnotation: String?
    let defaultValue: String?
    let isClassVar: Bool

    enum CodingKeys: String, CodingKey {
        case name
        case typeAnnotation = "type_annotation"
        case defaultValue = "default_value"
        case isClassVar = "is_class_var"
    }
}

// MARK: - Code Entity Type Info

struct CodeEntityTypeInfo: Identifiable, Codable {
    var id: String { typeId }
    let typeId: String
    let name: String
    let description: String

    enum CodingKeys: String, CodingKey {
        case typeId = "id"
        case name
        case description
    }
}

// MARK: - Code Relationship Type Info

struct CodeRelationshipTypeInfo: Identifiable, Codable {
    var id: String { typeId }
    let typeId: String
    let name: String
    let description: String

    enum CodingKeys: String, CodingKey {
        case typeId = "id"
        case name
        case description
    }
}

// MARK: - Code Search Result

struct CodeSearchResult: Identifiable, Codable, Hashable {
    var id: String { entityId }
    let entityId: String
    let name: String
    let qualifiedName: String
    let entityType: String
    let filePath: String
    let lineStart: Int
    let language: String
    let docstring: String?
    let similarity: Double?
    let snippet: String?

    enum CodingKeys: String, CodingKey {
        case entityId = "entity_id"
        case name
        case qualifiedName = "qualified_name"
        case entityType = "entity_type"
        case filePath = "file_path"
        case lineStart = "line_start"
        case language
        case docstring
        case similarity
        case snippet
    }

    static func == (lhs: CodeSearchResult, rhs: CodeSearchResult) -> Bool {
        lhs.entityId == rhs.entityId
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(entityId)
    }
}

// MARK: - Code Stats

struct CodeStats: Codable {
    let entities: EntityStats
    let relationships: RelationshipStats?

    struct EntityStats: Codable {
        let total: Int
        let byType: [String: Int]
        let byLanguage: [String: Int]

        enum CodingKeys: String, CodingKey {
            case total
            case byType = "by_type"
            case byLanguage = "by_language"
        }
    }

    struct RelationshipStats: Codable {
        let total: Int
        let byType: [String: Int]

        enum CodingKeys: String, CodingKey {
            case total
            case byType = "by_type"
        }
    }
}

// MARK: - Scan Result

struct ScanResult: Codable {
    let projectPath: String
    let entityCount: Int
    let filesScanned: Int
    let filesFailed: Int?
    let parseErrors: [String]?
    let languages: [String: Int]
    let scanTimeMs: Double
    let startedAt: String?
    let completedAt: String?

    enum CodingKeys: String, CodingKey {
        case projectPath = "project_path"
        case entityCount = "entity_count"
        case filesScanned = "files_scanned"
        case filesFailed = "files_failed"
        case parseErrors = "parse_errors"
        case languages
        case scanTimeMs = "scan_time_ms"
        case startedAt = "started_at"
        case completedAt = "completed_at"
    }
}

// MARK: - API Responses

struct CodeScanResponse: Codable {
    let success: Bool
    let result: ScanResult?
    let error: String?
}

struct CodeSearchResponse: Codable {
    let success: Bool
    let results: [CodeSearchResult]?
    let total: Int?
    let query: String?
    let error: String?
}

struct CodeFindFunctionResponse: Codable {
    let success: Bool
    let functions: [FunctionEntity]?
    let count: Int?
    let error: String?
}

struct CodeFindClassResponse: Codable {
    let success: Bool
    let classes: [ClassEntity]?
    let count: Int?
    let error: String?
}

struct CodeStatsResponse: Codable {
    let success: Bool
    let stats: CodeStats?
    let error: String?
}

struct CodeEntityTypesResponse: Codable {
    let success: Bool
    let types: [CodeEntityTypeInfo]?
    let error: String?
}

struct CodeRelationshipTypesResponse: Codable {
    let success: Bool
    let types: [CodeRelationshipTypeInfo]?
    let error: String?
}

struct CodeSupportedLanguagesResponse: Codable {
    let success: Bool
    let languages: [String]?
    let extensions: [String]?
    let error: String?
}

struct CodeCallersResponse: Codable {
    let success: Bool
    let callers: [CodeEntity]?
    let count: Int?
    let entityId: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case callers
        case count
        case entityId = "entity_id"
        case error
    }
}

struct CodeCalleesResponse: Codable {
    let success: Bool
    let callees: [CodeEntity]?
    let count: Int?
    let entityId: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case callees
        case count
        case entityId = "entity_id"
        case error
    }
}

struct ScanStatusResponse: Codable {
    let success: Bool
    let status: ScanStatusInfo?
    let error: String?
}

struct ScanStatusInfo: Codable {
    let indexed: Bool
    let entityCount: Int?
    let lastScan: String?
    let languages: [String]?

    enum CodingKeys: String, CodingKey {
        case indexed
        case entityCount = "entity_count"
        case lastScan = "last_scan"
        case languages
    }
}
