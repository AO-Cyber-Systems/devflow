import SwiftUI

struct DoctorSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Overall status
                    overallStatusSection

                    // Missing packages
                    if !appState.doctorManager.missingPackages.isEmpty {
                        missingPackagesSection
                    }

                    // Package status
                    packagesSection

                    // Tool status
                    toolsSection
                }
                .padding()
            }

            Divider()

            // Footer
            footer
        }
        .frame(width: 600, height: 500)
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            Image(systemName: statusIcon)
                .foregroundStyle(statusColor)
                .font(.title2)
            Text("System Health Check")
                .font(.headline)
            Spacer()
            if appState.doctorManager.isChecking {
                ProgressView()
                    .scaleEffect(0.7)
            }
            Button("Refresh") {
                Task { await appState.runDoctorCheck() }
            }
            .disabled(appState.doctorManager.isChecking)
        }
        .padding()
    }

    // MARK: - Overall Status

    private var overallStatusSection: some View {
        HStack(spacing: 12) {
            Image(systemName: statusIcon)
                .font(.largeTitle)
                .foregroundStyle(statusColor)

            VStack(alignment: .leading, spacing: 4) {
                Text(statusTitle)
                    .font(.headline)
                Text(statusMessage)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            if appState.doctorManager.canAutoFix {
                Button {
                    Task { await appState.installAllMissingPackages() }
                } label: {
                    Label("Fix Issues", systemImage: "wrench.and.screwdriver")
                }
                .buttonStyle(.borderedProminent)
                .disabled(appState.doctorManager.isInstalling)
            }
        }
        .padding()
        .background(statusColor.opacity(0.1))
        .cornerRadius(12)
    }

    // MARK: - Missing Packages

    private var missingPackagesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text("Missing Packages")
                    .font(.headline)
                Spacer()
                if appState.doctorManager.isInstalling {
                    ProgressView()
                        .scaleEffect(0.7)
                    Text("Installing...")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            ForEach(appState.doctorManager.missingPackages) { pkg in
                PackageRow(
                    package: pkg,
                    installStatus: appState.doctorManager.installProgress[pkg.name],
                    onInstall: {
                        Task { await appState.installPackage(pkg.name) }
                    }
                )
            }
        }
    }

    // MARK: - All Packages

    private var packagesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "shippingbox")
                Text("Python Packages")
                    .font(.headline)
                Spacer()
                if let summary = appState.doctorManager.lastCheck?.packages.summary {
                    Text("\(summary.ok)/\(summary.total) installed")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            if let packages = appState.doctorManager.lastCheck?.packages.packages {
                LazyVStack(spacing: 8) {
                    ForEach(packages.filter { $0.isOk }) { pkg in
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                            Text(pkg.name)
                            if let version = pkg.version {
                                Text("v\(version)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Text(pkg.requiredFor)
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
    }

    // MARK: - Tools

    private var toolsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "wrench.and.screwdriver")
                Text("External Tools")
                    .font(.headline)
            }

            if let tools = appState.doctorManager.lastCheck?.tools.checks {
                LazyVStack(spacing: 8) {
                    ForEach(tools) { tool in
                        HStack {
                            Image(systemName: toolStatusIcon(tool))
                                .foregroundStyle(toolStatusColor(tool))
                            Text(tool.name)
                            Spacer()
                            Text(tool.message)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
    }

    // MARK: - Footer

    private var footer: some View {
        HStack {
            if appState.doctorManager.isHealthy {
                Image(systemName: "checkmark.seal.fill")
                    .foregroundStyle(.green)
                Text("All systems operational")
                    .foregroundStyle(.secondary)
            } else if appState.doctorManager.isInstalling {
                ProgressView()
                    .scaleEffect(0.7)
                Text("Installing packages...")
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button("Close") {
                dismiss()
            }
        }
        .padding()
    }

    // MARK: - Helpers

    private var statusIcon: String {
        switch appState.doctorManager.overallStatus {
        case "healthy":
            return "checkmark.circle.fill"
        case "warning":
            return "exclamationmark.triangle.fill"
        case "error":
            return "xmark.circle.fill"
        default:
            return "questionmark.circle"
        }
    }

    private var statusColor: Color {
        switch appState.doctorManager.overallStatus {
        case "healthy":
            return .green
        case "warning":
            return .orange
        case "error":
            return .red
        default:
            return .gray
        }
    }

    private var statusTitle: String {
        switch appState.doctorManager.overallStatus {
        case "healthy":
            return "All Systems Healthy"
        case "warning":
            return "Some Optional Items Missing"
        case "error":
            return "Required Packages Missing"
        default:
            return "Status Unknown"
        }
    }

    private var statusMessage: String {
        let missing = appState.doctorManager.missingPackages.count
        if missing == 0 {
            return "All required packages are installed and working."
        } else if missing == 1 {
            return "1 package needs to be installed."
        } else {
            return "\(missing) packages need to be installed."
        }
    }

    private func toolStatusIcon(_ tool: ToolCheck) -> String {
        if tool.isOk {
            return "checkmark.circle.fill"
        } else if tool.isWarning {
            return "exclamationmark.triangle.fill"
        } else {
            return "xmark.circle.fill"
        }
    }

    private func toolStatusColor(_ tool: ToolCheck) -> Color {
        if tool.isOk {
            return .green
        } else if tool.isWarning {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - Package Row

struct PackageRow: View {
    let package: PackageCheck
    let installStatus: String?
    let onInstall: () -> Void

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundStyle(iconColor)

            VStack(alignment: .leading, spacing: 2) {
                Text(package.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(package.requiredFor)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            if let status = installStatus {
                statusView(status)
            } else {
                Button("Install") {
                    onInstall()
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.orange.opacity(0.1))
        .cornerRadius(8)
    }

    private var icon: String {
        if let status = installStatus {
            switch status {
            case "installed":
                return "checkmark.circle.fill"
            case "installing":
                return "arrow.down.circle"
            case "queued":
                return "clock.circle"
            case "failed":
                return "xmark.circle.fill"
            default:
                return "exclamationmark.triangle.fill"
            }
        }
        return "exclamationmark.triangle.fill"
    }

    private var iconColor: Color {
        if let status = installStatus {
            switch status {
            case "installed":
                return .green
            case "installing":
                return .blue
            case "queued":
                return .gray
            case "failed":
                return .red
            default:
                return .orange
            }
        }
        return .orange
    }

    @ViewBuilder
    private func statusView(_ status: String) -> some View {
        switch status {
        case "installed":
            HStack(spacing: 4) {
                Image(systemName: "checkmark")
                    .foregroundStyle(.green)
                Text("Installed")
                    .font(.caption)
                    .foregroundStyle(.green)
            }
        case "installing":
            HStack(spacing: 4) {
                ProgressView()
                    .scaleEffect(0.6)
                Text("Installing...")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        case "queued":
            HStack(spacing: 4) {
                Image(systemName: "clock")
                    .foregroundStyle(.gray)
                Text("Queued")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        case "failed":
            HStack(spacing: 4) {
                Image(systemName: "xmark")
                    .foregroundStyle(.red)
                Text("Failed")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        default:
            EmptyView()
        }
    }
}

// MARK: - Status Indicator (for sidebar/toolbar)

struct DoctorStatusIndicator: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        Button {
            appState.showDoctorSheet = true
        } label: {
            HStack(spacing: 4) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                if appState.doctorHasIssues {
                    Text(issueCount)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .buttonStyle(.plain)
        .help(helpText)
    }

    private var statusColor: Color {
        switch appState.doctorManager.overallStatus {
        case "healthy":
            return .green
        case "warning":
            return .orange
        case "error":
            return .red
        default:
            return .gray
        }
    }

    private var issueCount: String {
        let count = appState.missingPackages.count
        return count > 0 ? "\(count)" : ""
    }

    private var helpText: String {
        if appState.isDoctorHealthy {
            return "System healthy"
        } else {
            let count = appState.missingPackages.count
            return "\(count) package\(count == 1 ? "" : "s") missing"
        }
    }
}

#Preview {
    DoctorSheet()
        .environment(AppState())
}
