import Foundation

// MARK: - Tool Source

enum ToolSource: String, Codable, CaseIterable {
    case mise
    case homebrew
    case cask

    var displayName: String {
        switch self {
        case .mise: return "Mise"
        case .homebrew: return "Homebrew"
        case .cask: return "Cask"
        }
    }

    var icon: String {
        switch self {
        case .mise: return "cpu"
        case .homebrew: return "mug"
        case .cask: return "macwindow"
        }
    }
}

// MARK: - Tool Browser Category

enum ToolBrowserCategory: String, Codable, CaseIterable {
    case languages
    case databases
    case containers
    case cloud
    case vcs
    case editors
    case shell
    case build
    case security
    case networking
    case media
    case productivity
    case devops
    case applications
    case other

    var displayName: String {
        switch self {
        case .languages: return "Languages & Runtimes"
        case .databases: return "Databases"
        case .containers: return "Containers & VMs"
        case .cloud: return "Cloud & Infrastructure"
        case .vcs: return "Version Control"
        case .editors: return "Editors & IDEs"
        case .shell: return "Shell & Terminal"
        case .build: return "Build Tools"
        case .security: return "Security"
        case .networking: return "Networking"
        case .media: return "Media & Graphics"
        case .productivity: return "Productivity"
        case .devops: return "DevOps"
        case .applications: return "Applications"
        case .other: return "Other"
        }
    }

    var icon: String {
        switch self {
        case .languages: return "chevron.left.forwardslash.chevron.right"
        case .databases: return "cylinder"
        case .containers: return "shippingbox"
        case .cloud: return "cloud"
        case .vcs: return "arrow.triangle.branch"
        case .editors: return "pencil.and.outline"
        case .shell: return "terminal"
        case .build: return "hammer"
        case .security: return "lock.shield"
        case .networking: return "network"
        case .media: return "photo"
        case .productivity: return "bolt"
        case .devops: return "gearshape.2"
        case .applications: return "macwindow"
        case .other: return "ellipsis.circle"
        }
    }
}

// MARK: - Browsable Tool

struct BrowsableTool: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let description: String
    let source: ToolSource
    let category: ToolBrowserCategory
    let categoryDisplay: String
    let categoryIcon: String
    let installCommand: String
    let homepage: String?
    let version: String?
    let aliases: [String]
    let license: String?
    var isInstalled: Bool
    var installedVersion: String?
    let isGuiApp: Bool
    let isRuntime: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case source
        case category
        case categoryDisplay = "category_display"
        case categoryIcon = "category_icon"
        case installCommand = "install_command"
        case homepage
        case version
        case aliases
        case license
        case isInstalled = "is_installed"
        case installedVersion = "installed_version"
        case isGuiApp = "is_gui_app"
        case isRuntime = "is_runtime"
    }
}

// MARK: - Tool Category Info

struct ToolCategoryInfo: Identifiable, Codable {
    var id: String { categoryId }
    let categoryId: String
    let name: String
    let icon: String
    let count: Int

    enum CodingKeys: String, CodingKey {
        case categoryId = "id"
        case name
        case icon
        case count
    }
}

// MARK: - Tool Source Info

struct ToolSourceInfo: Identifiable, Codable {
    var id: String { sourceId }
    let sourceId: String
    let name: String
    let count: Int

    enum CodingKeys: String, CodingKey {
        case sourceId = "id"
        case name
        case count
    }
}

// MARK: - Tool Browser API Responses

struct ToolBrowserSearchResponse: Codable {
    let tools: [BrowsableTool]
    let total: Int
    let hasMore: Bool
    let offset: Int
    let limit: Int

    enum CodingKeys: String, CodingKey {
        case tools
        case total
        case hasMore = "has_more"
        case offset
        case limit
    }
}

struct ToolBrowserCategoriesResponse: Codable {
    let categories: [ToolCategoryInfo]
}

struct ToolBrowserSourcesResponse: Codable {
    let sources: [ToolSourceInfo]
}

struct ToolBrowserDetailResponse: Codable {
    let tool: BrowsableTool?
    let error: String?
}

struct ToolBrowserInstallResponse: Codable {
    let success: Bool
    let message: String?
    let output: String?
    let error: String?
}

struct ToolBrowserInstalledCheckResponse: Codable {
    let installed: [String: Bool]
}

struct ToolBrowserRefreshCacheResponse: Codable {
    let success: Bool
    let miseCount: Int?
    let brewCount: Int?
    let caskCount: Int?
    let total: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success
        case miseCount = "mise_count"
        case brewCount = "brew_count"
        case caskCount = "cask_count"
        case total
        case error
    }
}
