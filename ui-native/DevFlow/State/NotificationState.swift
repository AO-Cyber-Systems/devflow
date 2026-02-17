import Foundation

/// Manages app notifications with auto-dismiss functionality.
@Observable
@MainActor
class NotificationState {
    // MARK: - State

    var notifications: [AppNotification] = []

    // MARK: - Actions

    func add(_ notification: AppNotification) {
        notifications.append(notification)

        if notification.autoDismiss {
            Task {
                try? await Task.sleep(for: .seconds(5))
                dismiss(notification)
            }
        }
    }

    func dismiss(_ notification: AppNotification) {
        notifications.removeAll { $0.id == notification.id }
    }

    // Convenience methods
    func success(_ message: String) {
        add(.success(message))
    }

    func error(_ message: String) {
        add(.error(message))
    }

    func warning(_ message: String) {
        add(.warning(message))
    }

    func info(_ message: String) {
        add(.info(message))
    }
}
