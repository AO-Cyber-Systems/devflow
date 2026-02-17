import Foundation

/// Manages the setup wizard - tool detection and installation.
@Observable
@MainActor
class SetupState {
    // MARK: - State

    var setupWizardStatus: SetupWizardStatus?
    var showSetupWizard = false
    var essentialTools: [ToolStatus] = []
    var recommendedTools: [ToolStatus] = []
    var isLoadingTools = false

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Actions

    func checkStatus() async {
        do {
            setupWizardStatus = try await bridge.call("setup.get_setup_wizard_status")
            if let status = setupWizardStatus, status.needsSetup {
                showSetupWizard = true
            }
        } catch {
            // Ignore - setup might not be needed
        }
    }

    func markCompleted() async {
        do {
            let _: [String: Bool] = try await bridge.call("setup.mark_setup_completed")
            showSetupWizard = false
            setupWizardStatus = nil
        } catch {
            notifications.add(.error("Failed to complete setup: \(error.localizedDescription)"))
        }
    }

    func loadEssentialTools() async {
        isLoadingTools = true
        defer { isLoadingTools = false }

        do {
            essentialTools = try await bridge.call("setup.detect_essential_tools")
        } catch {
            notifications.add(.error("Failed to load essential tools: \(error.localizedDescription)"))
        }
    }

    func loadRecommendedTools() async {
        do {
            let response: RecommendedToolsResponse = try await bridge.call("setup.get_recommended_tools")
            recommendedTools = response.recommended
        } catch {
            // Ignore - not critical
        }
    }

    func install(_ toolId: String) async {
        // Tools that require admin privileges (sudo)
        let privilegedTools = ["docker"]

        if privilegedTools.contains(toolId) {
            await installWithPrivileges(toolId)
            return
        }

        do {
            let result: InstallResult = try await bridge.call(
                "setup.install",
                params: ["tool_id": toolId]
            )
            if result.success {
                notifications.add(.success("Installed \(toolId)"))
            } else if let error = result.errorDetails {
                notifications.add(.error("Failed to install \(toolId): \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to install \(toolId): \(error.localizedDescription)"))
        }
    }

    private func installWithPrivileges(_ toolId: String) async {
        do {
            switch toolId {
            case "docker":
                notifications.add(.info("Opening Terminal to install Docker..."))
                try await PrivilegedInstaller.installDocker()
                notifications.add(.info("Docker installation started in Terminal. Enter your password when prompted."))
            default:
                // Generic Homebrew install in Terminal
                notifications.add(.info("Opening Terminal to install \(toolId)..."))
                try await PrivilegedInstaller.installWithHomebrew(formula: toolId)
            }
        } catch PrivilegedInstaller.InstallError.cancelled {
            notifications.add(.warning("Installation cancelled"))
        } catch PrivilegedInstaller.InstallError.homebrewNotFound {
            notifications.add(.error("Homebrew not found. Please install Homebrew first: https://brew.sh"))
        } catch {
            notifications.add(.error("Failed to install \(toolId): \(error.localizedDescription)"))
        }
    }

    func installMultiple(_ toolIds: [String]) async {
        do {
            let result: BatchInstallResult = try await bridge.call(
                "setup.install_multiple",
                params: ["tool_ids": toolIds]
            )
            if result.failedCount == 0 {
                notifications.add(.success("All tools installed successfully"))
            } else {
                notifications.add(.warning("\(result.successCount) of \(result.total) tools installed"))
            }
        } catch {
            notifications.add(.error("Failed to install tools: \(error.localizedDescription)"))
        }
    }
}
