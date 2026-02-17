import Foundation

// MARK: - Component Category

enum ComponentCategory: String, Codable, CaseIterable {
    case form
    case layout
    case navigation
    case feedback
    case dataDisplay = "data_display"
    case dataEntry = "data_entry"
    case overlay
    case media
    case typography
    case other

    var displayName: String {
        switch self {
        case .form: return "Form Controls"
        case .layout: return "Layout"
        case .navigation: return "Navigation"
        case .feedback: return "Feedback"
        case .dataDisplay: return "Data Display"
        case .dataEntry: return "Data Entry"
        case .overlay: return "Overlay"
        case .media: return "Media"
        case .typography: return "Typography"
        case .other: return "Other"
        }
    }

    var icon: String {
        switch self {
        case .form: return "rectangle.and.pencil.and.ellipsis"
        case .layout: return "square.grid.2x2"
        case .navigation: return "arrow.triangle.turn.up.right.diamond"
        case .feedback: return "exclamationmark.bubble"
        case .dataDisplay: return "tablecells"
        case .dataEntry: return "keyboard"
        case .overlay: return "rectangle.on.rectangle"
        case .media: return "photo.on.rectangle"
        case .typography: return "textformat"
        case .other: return "ellipsis.circle"
        }
    }
}

// MARK: - Prop Definition

struct PropDefinition: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let type: String
    let description: String
    let defaultValue: String?
    let required: Bool
    let options: [String]

    enum CodingKeys: String, CodingKey {
        case name
        case type
        case description
        case defaultValue = "default"
        case required
        case options
    }
}

// MARK: - Slot Definition

struct SlotDefinition: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let description: String
    let defaultContent: String?

    enum CodingKeys: String, CodingKey {
        case name
        case description
        case defaultContent = "default_content"
    }
}

// MARK: - Event Definition

struct EventDefinition: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let description: String
    let payloadType: String?
    let payloadDescription: String?

    enum CodingKeys: String, CodingKey {
        case name
        case description
        case payloadType = "payload_type"
        case payloadDescription = "payload_description"
    }
}

// MARK: - Component Example

struct ComponentExample: Codable, Identifiable, Hashable {
    var id: String { title }
    let title: String
    let code: String
    let description: String
    let language: String
}

// MARK: - Component Doc

struct ComponentDoc: Identifiable, Codable, Hashable {
    var id: String { name }
    let name: String
    let category: String
    let categoryDisplay: String
    let categoryIcon: String
    let description: String
    let props: [PropDefinition]
    let slots: [SlotDefinition]
    let events: [EventDefinition]
    let examples: [ComponentExample]
    let aiGuidance: String?
    let accessibility: [String]
    let tags: [String]
    let sourceFile: String?
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case name
        case category
        case categoryDisplay = "category_display"
        case categoryIcon = "category_icon"
        case description
        case props
        case slots
        case events
        case examples
        case aiGuidance = "ai_guidance"
        case accessibility
        case tags
        case sourceFile = "source_file"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    static func == (lhs: ComponentDoc, rhs: ComponentDoc) -> Bool {
        lhs.name == rhs.name
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(name)
    }
}

// MARK: - Component Category Info

struct ComponentCategoryInfo: Identifiable, Codable {
    var id: String { categoryId }
    let categoryId: String
    let name: String
    let icon: String
    let count: Int?

    enum CodingKeys: String, CodingKey {
        case categoryId = "id"
        case name
        case icon
        case count
    }
}

// MARK: - API Responses

struct ComponentsListResponse: Codable {
    let components: [ComponentDoc]?
    let total: Int?
    let error: String?
}

struct ComponentDetailResponse: Codable {
    let component: ComponentDoc?
    let error: String?
}

struct ComponentCreateResponse: Codable {
    let success: Bool
    let component: ComponentDoc?
    let error: String?
}

struct ComponentUpdateResponse: Codable {
    let success: Bool
    let component: ComponentDoc?
    let error: String?
}

struct ComponentDeleteResponse: Codable {
    let success: Bool
    let message: String?
    let error: String?
}

struct ComponentScanResponse: Codable {
    let components: [ComponentDoc]?
    let total: Int?
    let saved: Bool?
    let error: String?
}

struct ComponentAiContextResponse: Codable {
    let context: String?
    let length: Int?
    let error: String?
}

struct ComponentCategoriesResponse: Codable {
    let categories: [ComponentCategoryInfo]?
    let error: String?
}
