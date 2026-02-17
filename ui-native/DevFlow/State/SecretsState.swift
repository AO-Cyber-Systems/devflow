import Foundation

/// Manages secrets - listing, adding, and deleting secrets.
@Observable
@MainActor
class SecretsState {
    // MARK: - State

    var secrets: [Secret] = []
    var isLoadingSecrets = false
    var showAddSecret = false

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Actions

    func load() async {
        isLoadingSecrets = true
        defer { isLoadingSecrets = false }

        // Secrets are project-specific - show empty state when no project is selected
        secrets = []
    }

    func add(key: String, value: String, provider: SecretsProvider) async {
        do {
            let _: Bool = try await bridge.call("secrets.set", params: [
                "key": key,
                "value": value,
                "provider": provider.rawValue
            ])
            notifications.add(.success("Secret '\(key)' saved"))
            await load()
        } catch {
            notifications.add(.error("Failed to save secret: \(error.localizedDescription)"))
        }
    }

    func delete(_ secret: Secret) async {
        do {
            let _: Bool = try await bridge.call("secrets.delete", params: ["key": secret.key])
            notifications.add(.success("Secret '\(secret.key)' deleted"))
            await load()
        } catch {
            notifications.add(.error("Failed to delete secret: \(error.localizedDescription)"))
        }
    }
}
