import Foundation

struct AppNotification: Identifiable {
    let id: UUID
    var message: String
    var type: NotificationType
    var timestamp: Date
    var autoDismiss: Bool

    init(
        id: UUID = UUID(),
        message: String,
        type: NotificationType = .info,
        timestamp: Date = Date(),
        autoDismiss: Bool = true
    ) {
        self.id = id
        self.message = message
        self.type = type
        self.timestamp = timestamp
        self.autoDismiss = autoDismiss
    }

    static func success(_ message: String) -> AppNotification {
        AppNotification(message: message, type: .success)
    }

    static func error(_ message: String) -> AppNotification {
        AppNotification(message: message, type: .error, autoDismiss: false)
    }

    static func warning(_ message: String) -> AppNotification {
        AppNotification(message: message, type: .warning)
    }

    static func info(_ message: String) -> AppNotification {
        AppNotification(message: message, type: .info)
    }
}

enum NotificationType {
    case success
    case error
    case warning
    case info

    var icon: String {
        switch self {
        case .success: return "checkmark.circle.fill"
        case .error: return "xmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .info: return "info.circle.fill"
        }
    }

    var color: String {
        switch self {
        case .success: return "green"
        case .error: return "red"
        case .warning: return "orange"
        case .info: return "blue"
        }
    }
}
