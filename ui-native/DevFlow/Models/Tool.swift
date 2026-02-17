import Foundation

// MARK: - Tool Models

struct Tool: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let description: String
    let category: ToolCategory
    let command: String?
    let website: String?
    let essential: Bool
    let miseManaged: Bool

    init(
        id: String,
        name: String,
        description: String,
        category: ToolCategory = .other,
        command: String? = nil,
        website: String? = nil,
        essential: Bool = false,
        miseManaged: Bool = false
    ) {
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.command = command
        self.website = website
        self.essential = essential
        self.miseManaged = miseManaged
    }

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case category
        case command
        case website
        case essential
        case miseManaged = "mise_managed"
    }
}

enum ToolCategory: String, Codable, CaseIterable {
    case core
    case runtime
    case container
    case database
    case cloud
    case editor
    case vcs
    case other

    var displayName: String {
        switch self {
        case .core: return "Core"
        case .runtime: return "Runtime"
        case .container: return "Container"
        case .database: return "Database"
        case .cloud: return "Cloud"
        case .editor: return "Editor"
        case .vcs: return "Version Control"
        case .other: return "Other"
        }
    }

    var icon: String {
        switch self {
        case .core: return "cpu"
        case .runtime: return "memorychip"
        case .container: return "shippingbox"
        case .database: return "cylinder.split.1x2"
        case .cloud: return "cloud"
        case .editor: return "chevron.left.forwardslash.chevron.right"
        case .vcs: return "arrow.triangle.branch"
        case .other: return "wrench.and.screwdriver"
        }
    }
}

// MARK: - Tool Status

struct ToolStatus: Identifiable, Codable, Hashable {
    var id: String { toolId }
    let toolId: String
    let name: String
    let status: InstallStatus
    let version: String?
    let category: String?
    let installed: Bool?
    let error: String?
    let installMethods: [String]?

    init(
        toolId: String,
        name: String,
        status: InstallStatus = .notInstalled,
        version: String? = nil,
        category: String? = nil,
        installed: Bool? = nil,
        error: String? = nil,
        installMethods: [String]? = nil
    ) {
        self.toolId = toolId
        self.name = name
        self.status = status
        self.version = version
        self.category = category
        self.installed = installed
        self.error = error
        self.installMethods = installMethods
    }

    enum CodingKeys: String, CodingKey {
        case toolId = "tool_id"
        case name
        case status
        case version
        case category
        case installed
        case error
        case installMethods = "install_methods"
    }

    // Computed property for UI display
    var isInstalled: Bool {
        if let installed = installed {
            return installed
        }
        return status == .installed
    }
}

enum InstallStatus: String, Codable {
    case installed
    case notInstalled = "not_installed"
    case outdated
    case error

    var displayName: String {
        switch self {
        case .installed: return "Installed"
        case .notInstalled: return "Not Installed"
        case .outdated: return "Outdated"
        case .error: return "Error"
        }
    }

    var color: String {
        switch self {
        case .installed: return "green"
        case .notInstalled: return "secondary"
        case .outdated: return "orange"
        case .error: return "red"
        }
    }

    var icon: String {
        switch self {
        case .installed: return "checkmark.circle.fill"
        case .notInstalled: return "circle"
        case .outdated: return "exclamationmark.circle.fill"
        case .error: return "xmark.circle.fill"
        }
    }
}

// MARK: - Install Result

struct InstallResult: Codable {
    let success: Bool
    let message: String?
    let version: String?
    let errorDetails: String?
    let requiresRestart: Bool?

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case version
        case errorDetails = "error_details"
        case requiresRestart = "requires_restart"
    }
}

struct BatchInstallResult: Codable {
    let total: Int
    let successCount: Int
    let failedCount: Int
    let results: [SingleInstallResult]

    enum CodingKeys: String, CodingKey {
        case total
        case successCount = "success_count"
        case failedCount = "failed_count"
        case results
    }
}

struct SingleInstallResult: Identifiable, Codable {
    var id: String { toolId }
    let toolId: String
    let success: Bool
    let message: String?
    let version: String?
    let errorDetails: String?
    let requiresRestart: Bool?

    enum CodingKeys: String, CodingKey {
        case toolId = "tool_id"
        case success
        case message
        case version
        case errorDetails = "error_details"
        case requiresRestart = "requires_restart"
    }
}

// MARK: - Setup Wizard Status

struct SetupWizardStatus: Codable {
    let setupCompleted: Bool
    let essentialToolsInstalled: Int
    let essentialToolsTotal: Int
    let allEssentialInstalled: Bool
    let needsSetup: Bool

    enum CodingKeys: String, CodingKey {
        case setupCompleted = "setup_completed"
        case essentialToolsInstalled = "essential_tools_installed"
        case essentialToolsTotal = "essential_tools_total"
        case allEssentialInstalled = "all_essential_installed"
        case needsSetup = "needs_setup"
    }
}

// MARK: - Platform Info

struct PlatformInfo: Codable {
    let os: String
    let distro: String?
    let architecture: String
    let isWsl: Bool
    let packageManagers: [String]
    let isMacos: Bool
    let isLinux: Bool
    let isWindows: Bool

    enum CodingKeys: String, CodingKey {
        case os
        case distro
        case architecture
        case isWsl = "is_wsl"
        case packageManagers = "package_managers"
        case isMacos = "is_macos"
        case isLinux = "is_linux"
        case isWindows = "is_windows"
    }
}

// MARK: - API Response Models

struct ToolsListResponse: Codable {
    let tools: [ToolStatus]
    let total: Int?
}

struct PrerequisitesSummary: Codable {
    let total: Int
    let installed: Int
    let notInstalled: Int
    let outdated: Int
    let byCategory: [String: CategoryCount]

    enum CodingKeys: String, CodingKey {
        case total
        case installed
        case notInstalled = "not_installed"
        case outdated
        case byCategory = "by_category"
    }
}

struct CategoryCount: Codable {
    let total: Int
    let installed: Int
}

struct RecommendedToolsResponse: Codable {
    let recommended: [ToolStatus]
    let total: Int
}
