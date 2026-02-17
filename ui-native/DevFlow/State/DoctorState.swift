import Foundation

/// Manages system doctor checks and package installation.
@Observable
@MainActor
class DoctorState {
    // MARK: - State

    var isChecking = false
    var isInstalling = false
    var lastCheck: FullDoctorResponse?
    var installProgress: [String: String] = [:]  // package name -> status
    var showDoctorSheet = false

    // MARK: - Computed Properties

    var overallStatus: String {
        lastCheck?.overallStatus ?? "unknown"
    }

    var isHealthy: Bool {
        overallStatus == "healthy"
    }

    var hasIssues: Bool {
        overallStatus == "error" || overallStatus == "warning"
    }

    var canAutoFix: Bool {
        lastCheck?.canAutoFix ?? false
    }

    var missingPackages: [PackageCheck] {
        lastCheck?.packages.packages.filter { $0.isMissing } ?? []
    }

    var errorPackages: [PackageCheck] {
        lastCheck?.packages.packages.filter { $0.hasError } ?? []
    }

    var okPackages: [PackageCheck] {
        lastCheck?.packages.packages.filter { $0.isOk } ?? []
    }

    var toolChecks: [ToolCheck] {
        lastCheck?.tools.checks ?? []
    }

    var problemTools: [ToolCheck] {
        toolChecks.filter { $0.hasError || $0.isWarning }
    }

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Actions

    func runFullDoctor(includeOptional: Bool = true) async {
        isChecking = true
        defer { isChecking = false }

        do {
            let params: [String: any Sendable] = ["include_optional": includeOptional]
            let response: FullDoctorResponse = try await bridge.call("system.full_doctor", params: params)
            lastCheck = response

            // Show sheet if there are issues
            if response.overallStatus != "healthy" {
                showDoctorSheet = true
            }
        } catch {
            notifications.add(.error("Doctor check failed: \(error.localizedDescription)"))
        }
    }

    func checkPackagesOnly(includeOptional: Bool = true) async -> PackageDoctorResponse? {
        do {
            let params: [String: any Sendable] = ["include_optional": includeOptional]
            let response: PackageDoctorResponse = try await bridge.call("system.package_doctor", params: params)
            return response
        } catch {
            return nil
        }
    }

    func installPackage(_ packageName: String) async -> Bool {
        installProgress[packageName] = "installing"

        do {
            let params: [String: any Sendable] = ["package_name": packageName]
            // Use longer timeout for package installation (5 minutes)
            let response: PackageInstallResponse = try await bridge.callWithTimeout(
                "system.install_package",
                params: params,
                timeout: .seconds(300)
            )

            if response.success {
                installProgress[packageName] = "installed"
                notifications.add(.success("Installed \(packageName)"))
                return true
            } else {
                installProgress[packageName] = "failed"
                notifications.add(.error("Failed to install \(packageName): \(response.error ?? "Unknown error")"))
                return false
            }
        } catch {
            installProgress[packageName] = "failed"
            notifications.add(.error("Failed to install \(packageName): \(error.localizedDescription)"))
            return false
        }
    }

    func installAllMissing(includeOptional: Bool = false) async {
        isInstalling = true
        defer { isInstalling = false }

        // Get the list of packages to install (copy to avoid mutation during iteration)
        let packagesToInstall = missingPackages

        // Mark all as queued first
        for pkg in packagesToInstall {
            installProgress[pkg.name] = "queued"
        }

        // Yield to show queued state
        await Task.yield()

        var successCount = 0
        var failCount = 0

        // Install one at a time for real-time progress
        for pkg in packagesToInstall {
            installProgress[pkg.name] = "installing"

            // Yield to allow UI to update
            await Task.yield()

            let success = await installPackageSilently(pkg.name)

            if success {
                installProgress[pkg.name] = "installed"
                successCount += 1
            } else {
                installProgress[pkg.name] = "failed"
                failCount += 1
            }
        }

        // Summary notification
        if failCount == 0 && successCount > 0 {
            notifications.add(.success("Installed \(successCount) package\(successCount == 1 ? "" : "s")"))
        } else if failCount > 0 {
            notifications.add(.warning("Installed \(successCount), failed \(failCount)"))
        }

        // Re-run doctor check to update status
        await runFullDoctor()
    }

    /// Install a package without showing individual notifications (used for bulk install)
    private func installPackageSilently(_ packageName: String) async -> Bool {
        do {
            let params: [String: any Sendable] = ["package_name": packageName]
            let response: PackageInstallResponse = try await bridge.callWithTimeout(
                "system.install_package",
                params: params,
                timeout: .seconds(300)
            )
            return response.success
        } catch {
            return false
        }
    }

    func clearProgress() {
        installProgress.removeAll()
    }
}
