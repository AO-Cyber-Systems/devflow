import SwiftUI

struct ToolInstallRow: View {
    let tool: ToolStatus
    let onInstall: () async -> Void

    @State private var isInstalling = false

    var body: some View {
        HStack(spacing: 12) {
            // Status icon
            Image(systemName: tool.status.icon)
                .foregroundStyle(statusColor)
                .font(.title2)
                .frame(width: 24)

            // Tool info
            VStack(alignment: .leading, spacing: 2) {
                Text(tool.name)
                    .font(.headline)

                if let version = tool.version, tool.isInstalled {
                    Text("v\(version)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else if !tool.isInstalled {
                    Text("Not installed")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            // Install button or status
            if isInstalling {
                ProgressView()
                    .controlSize(.small)
            } else if !tool.isInstalled {
                Button("Install") {
                    Task {
                        isInstalling = true
                        await onInstall()
                        isInstalling = false
                    }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
            } else {
                Image(systemName: "checkmark")
                    .foregroundStyle(.green)
            }
        }
        .padding(.vertical, 8)
        .accessibilityIdentifier("toolRow_\(tool.toolId)")
    }

    private var statusColor: Color {
        switch tool.status {
        case .installed:
            return .green
        case .notInstalled:
            return .secondary
        case .outdated:
            return .orange
        case .error:
            return .red
        }
    }
}

// Alternative compact version for lists
struct ToolInstallCompactRow: View {
    let tool: ToolStatus
    let isInstalling: Bool
    let onInstall: () -> Void

    var body: some View {
        HStack {
            Label {
                Text(tool.name)
            } icon: {
                Image(systemName: tool.isInstalled ? "checkmark.circle.fill" : "circle")
                    .foregroundStyle(tool.isInstalled ? .green : .secondary)
            }

            Spacer()

            if isInstalling {
                ProgressView()
                    .controlSize(.small)
            } else if !tool.isInstalled {
                Button("Install") {
                    onInstall()
                }
                .buttonStyle(.bordered)
                .controlSize(.mini)
            } else if let version = tool.version {
                Text(version)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

// Preview
#Preview {
    VStack(spacing: 0) {
        ToolInstallRow(
            tool: ToolStatus(
                toolId: "nodejs",
                name: "Node.js",
                status: .installed,
                version: "20.10.0"
            )
        ) {
            try? await Task.sleep(for: .seconds(1))
        }
        Divider()
        ToolInstallRow(
            tool: ToolStatus(
                toolId: "docker",
                name: "Docker",
                status: .notInstalled
            )
        ) {
            try? await Task.sleep(for: .seconds(1))
        }
        Divider()
        ToolInstallRow(
            tool: ToolStatus(
                toolId: "git",
                name: "Git",
                status: .outdated,
                version: "2.39.0"
            )
        ) {
            try? await Task.sleep(for: .seconds(1))
        }
    }
    .padding()
    .frame(width: 400)
}
