import Foundation

/// Represents a command that can be executed from the Command Palette.
struct Command: Identifiable {
    let id: String
    let title: String
    let icon: String
    let shortcut: String?
    let category: CommandCategory
    let action: () async -> Void

    init(
        _ title: String,
        icon: String,
        shortcut: String? = nil,
        category: CommandCategory = .general,
        action: @escaping () async -> Void
    ) {
        self.id = title.lowercased().replacingOccurrences(of: " ", with: "-")
        self.title = title
        self.icon = icon
        self.shortcut = shortcut
        self.category = category
        self.action = action
    }
}

/// Categories for organizing commands in the palette.
enum CommandCategory: String, CaseIterable {
    case navigation = "Navigation"
    case infrastructure = "Infrastructure"
    case projects = "Projects"
    case tools = "Tools"
    case general = "General"

    var icon: String {
        switch self {
        case .navigation: return "arrow.right.circle"
        case .infrastructure: return "server.rack"
        case .projects: return "folder"
        case .tools: return "wrench.and.screwdriver"
        case .general: return "star"
        }
    }
}
