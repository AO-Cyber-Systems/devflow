import Foundation

/// Manages global configuration settings.
@Observable
@MainActor
class ConfigState {
    // MARK: - State

    var globalConfig: GlobalConfig = GlobalConfig()
    var isLoading = false

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
        isLoading = true
        defer { isLoading = false }

        do {
            globalConfig = try await bridge.call("config.get")
        } catch {
            // Use default config on error
        }
    }

    func save() async {
        do {
            let _: Bool = try await bridge.call("config.set", params: [
                "base_domain": globalConfig.baseDomain,
                "traefik_port": globalConfig.traefikPort,
                "traefik_dashboard_port": globalConfig.traefikDashboardPort,
                "dns_enabled": globalConfig.dnsEnabled,
                "secrets_provider": globalConfig.secretsProvider.rawValue
            ])
            notifications.add(.success("Configuration saved"))
        } catch {
            notifications.add(.error("Failed to save configuration: \(error.localizedDescription)"))
        }
    }
}
