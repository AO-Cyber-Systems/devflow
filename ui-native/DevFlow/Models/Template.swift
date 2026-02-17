import Foundation

// MARK: - Template Models

struct Template: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let displayName: String
    let description: String
    let category: TemplateCategory
    let icon: String?
    let author: String?
    let version: String
    let tags: [String]
    let source: TemplateSource
    let requiredTools: [String]
    let recommendedTools: [String]
    let wizardStepCount: Int

    init(
        id: String,
        name: String,
        displayName: String,
        description: String,
        category: TemplateCategory = .other,
        icon: String? = nil,
        author: String? = nil,
        version: String = "1.0.0",
        tags: [String] = [],
        source: TemplateSource = .builtin,
        requiredTools: [String] = [],
        recommendedTools: [String] = [],
        wizardStepCount: Int = 0
    ) {
        self.id = id
        self.name = name
        self.displayName = displayName
        self.description = description
        self.category = category
        self.icon = icon
        self.author = author
        self.version = version
        self.tags = tags
        self.source = source
        self.requiredTools = requiredTools
        self.recommendedTools = recommendedTools
        self.wizardStepCount = wizardStepCount
    }

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case displayName = "display_name"
        case description
        case category
        case icon
        case author
        case version
        case tags
        case source
        case requiredTools = "required_tools"
        case recommendedTools = "recommended_tools"
        case wizardStepCount = "wizard_step_count"
    }
}

enum TemplateCategory: String, Codable, CaseIterable {
    case web
    case mobile
    case desktop
    case fullstack
    case api
    case library
    case other

    var displayName: String {
        switch self {
        case .web: return "Web"
        case .mobile: return "Mobile"
        case .desktop: return "Desktop"
        case .fullstack: return "Fullstack"
        case .api: return "API"
        case .library: return "Library"
        case .other: return "Other"
        }
    }

    var icon: String {
        switch self {
        case .web: return "globe"
        case .mobile: return "iphone"
        case .desktop: return "desktopcomputer"
        case .fullstack: return "square.stack.3d.up"
        case .api: return "server.rack"
        case .library: return "books.vertical"
        case .other: return "folder"
        }
    }
}

enum TemplateSource: String, Codable {
    case builtin
    case local
    case git

    var displayName: String {
        switch self {
        case .builtin: return "Built-in"
        case .local: return "Local"
        case .git: return "Git"
        }
    }
}

// MARK: - Wizard Models

struct WizardStep: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let description: String?
    let fields: [WizardField]

    init(
        id: String,
        title: String,
        description: String? = nil,
        fields: [WizardField] = []
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.fields = fields
    }
}

struct WizardField: Identifiable, Codable, Hashable {
    let id: String
    let type: WizardFieldType
    let label: String
    let required: Bool
    let defaultValue: String?
    let placeholder: String?
    let description: String?
    let validation: String?
    let validationMessage: String?
    let options: [WizardFieldOption]
    let showWhen: [String: String]?

    init(
        id: String,
        type: WizardFieldType = .text,
        label: String,
        required: Bool = false,
        defaultValue: String? = nil,
        placeholder: String? = nil,
        description: String? = nil,
        validation: String? = nil,
        validationMessage: String? = nil,
        options: [WizardFieldOption] = [],
        showWhen: [String: String]? = nil
    ) {
        self.id = id
        self.type = type
        self.label = label
        self.required = required
        self.defaultValue = defaultValue
        self.placeholder = placeholder
        self.description = description
        self.validation = validation
        self.validationMessage = validationMessage
        self.options = options
        self.showWhen = showWhen
    }

    enum CodingKeys: String, CodingKey {
        case id
        case type
        case label
        case required
        case defaultValue = "default"
        case placeholder
        case description
        case validation
        case validationMessage = "validation_message"
        case options
        case showWhen = "show_when"
    }
}

enum WizardFieldType: String, Codable {
    case text
    case select
    case multiselect
    case checkbox
    case directory
    case number
}

struct WizardFieldOption: Identifiable, Codable, Hashable {
    var id: String { value }
    let value: String
    let label: String
    let description: String?

    init(value: String, label: String, description: String? = nil) {
        self.value = value
        self.label = label
        self.description = description
    }
}

// MARK: - File and Hook Models

struct FileMapping: Codable, Hashable {
    let source: String
    let destination: String
    let template: Bool
    let recursive: Bool
    let condition: String?

    init(
        source: String,
        destination: String,
        template: Bool = false,
        recursive: Bool = false,
        condition: String? = nil
    ) {
        self.source = source
        self.destination = destination
        self.template = template
        self.recursive = recursive
        self.condition = condition
    }
}

struct TemplateHook: Codable, Hashable {
    let name: String
    let command: String
    let workingDir: String?
    let condition: String?
    let continueOnError: Bool

    init(
        name: String,
        command: String,
        workingDir: String? = nil,
        condition: String? = nil,
        continueOnError: Bool = false
    ) {
        self.name = name
        self.command = command
        self.workingDir = workingDir
        self.condition = condition
        self.continueOnError = continueOnError
    }

    enum CodingKeys: String, CodingKey {
        case name
        case command
        case workingDir = "working_dir"
        case condition
        case continueOnError = "continue_on_error"
    }
}

// MARK: - Full Template Detail

struct TemplateDetail: Codable {
    let id: String
    let name: String
    let displayName: String
    let description: String
    let category: TemplateCategory
    let icon: String?
    let author: String?
    let version: String
    let tags: [String]
    let source: TemplateSource
    let requiredTools: [String]
    let recommendedTools: [String]
    let wizardSteps: [WizardStep]
    let files: [FileMapping]
    let hooks: [TemplateHook]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case displayName = "display_name"
        case description
        case category
        case icon
        case author
        case version
        case tags
        case source
        case requiredTools = "required_tools"
        case recommendedTools = "recommended_tools"
        case wizardSteps = "wizard_steps"
        case files
        case hooks
    }
}

// MARK: - API Response Models

struct TemplateListResponse: Codable {
    let templates: [Template]
    let total: Int
}

struct TemplateDetailResponse: Codable {
    let template: TemplateDetail
}

struct WizardStepsResponse: Codable {
    let steps: [WizardStep]
    let stepCount: Int

    enum CodingKeys: String, CodingKey {
        case steps
        case stepCount = "step_count"
    }
}

struct ValidationResponse: Codable {
    let valid: Bool
    let errors: [String: [String]]?
}

struct ToolCheckResponse: Codable {
    let allRequiredInstalled: Bool
    let required: [ToolCheckItem]
    let recommended: [ToolCheckItem]

    enum CodingKeys: String, CodingKey {
        case allRequiredInstalled = "all_required_installed"
        case required
        case recommended
    }
}

struct ToolCheckItem: Identifiable, Codable, Hashable {
    var id: String { toolId }
    let toolId: String
    let name: String
    let installed: Bool
    let version: String?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case toolId = "tool_id"
        case name
        case installed
        case version
        case error
    }
}

struct CreateProjectResponse: Codable {
    let success: Bool
    let path: String?
    let filesCreated: [String]?
    let fileCount: Int?
    let hooks: [HookResult]?
    let hooksSuccess: Bool?
    let nextSteps: [String]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case path
        case filesCreated = "files_created"
        case fileCount = "file_count"
        case hooks
        case hooksSuccess = "hooks_success"
        case nextSteps = "next_steps"
        case error
    }
}

struct HookResult: Codable {
    let name: String
    let command: String
    let success: Bool
    let exitCode: Int
    let stdout: String
    let stderr: String

    enum CodingKeys: String, CodingKey {
        case name
        case command
        case success
        case exitCode = "exit_code"
        case stdout
        case stderr
    }
}

struct ImportTemplateResponse: Codable {
    let success: Bool
    let templateId: String?
    let template: Template?
    let installedPath: String?
    let existingTemplate: String?
    let errors: [String]

    enum CodingKeys: String, CodingKey {
        case success
        case templateId = "template_id"
        case template
        case installedPath = "installed_path"
        case existingTemplate = "existing_template"
        case errors
    }
}

struct CategoryInfo: Identifiable, Codable {
    var id: String { categoryId }
    let categoryId: String
    let name: String
    let count: Int

    enum CodingKeys: String, CodingKey {
        case categoryId = "id"
        case name
        case count
    }
}

struct CategoriesResponse: Codable {
    let categories: [CategoryInfo]
    let totalTemplates: Int

    enum CodingKeys: String, CodingKey {
        case categories
        case totalTemplates = "total_templates"
    }
}
