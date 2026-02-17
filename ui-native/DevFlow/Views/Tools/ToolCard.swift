import SwiftUI

struct ToolCard: View {
    let tool: BrowsableTool
    var onTap: () -> Void
    var onInstall: () -> Void

    @Environment(AppState.self) private var appState

    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: 12) {
                // Status indicator
                Image(systemName: tool.isInstalled ? "checkmark.circle.fill" : "circle")
                    .font(.title2)
                    .foregroundStyle(tool.isInstalled ? .green : .secondary)
                    .frame(width: 28)

                // Tool info
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(tool.name)
                            .font(.headline)
                        if let version = tool.version {
                            Text("v\(version)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        if tool.isInstalled, let installedVersion = tool.installedVersion {
                            Text("(installed: \(installedVersion))")
                                .font(.caption)
                                .foregroundStyle(.green)
                        }
                    }

                    Text(tool.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)

                    HStack(spacing: 8) {
                        // Source badge
                        Label(tool.source.displayName, systemImage: tool.source.icon)
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(sourceColor.opacity(0.15))
                            .foregroundStyle(sourceColor)
                            .cornerRadius(4)

                        // Category badge
                        Label(tool.categoryDisplay, systemImage: tool.categoryIcon)
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.secondary.opacity(0.15))
                            .cornerRadius(4)

                        if tool.isRuntime {
                            Label("Runtime", systemImage: "memorychip")
                                .font(.caption)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.15))
                                .foregroundStyle(.purple)
                                .cornerRadius(4)
                        }

                        if tool.isGuiApp {
                            Label("GUI", systemImage: "macwindow")
                                .font(.caption)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.15))
                                .foregroundStyle(.blue)
                                .cornerRadius(4)
                        }
                    }
                }

                Spacer()

                // Action button
                if isInstalling {
                    ProgressView()
                        .scaleEffect(0.8)
                        .frame(width: 80)
                } else if tool.isInstalled {
                    Button("Manage") {
                        onTap()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                } else {
                    Button("Install") {
                        onInstall()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
            .padding()
            .background(Color(.textBackgroundColor))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }

    private var isInstalling: Bool {
        appState.installingToolIds.contains(tool.id)
    }

    private var sourceColor: Color {
        switch tool.source {
        case .mise:
            return .orange
        case .homebrew:
            return .brown
        case .cask:
            return .blue
        }
    }
}

#Preview {
    VStack {
        ToolCard(
            tool: BrowsableTool(
                id: "mise:node",
                name: "node",
                description: "JavaScript runtime built on Chrome's V8 JavaScript engine",
                source: .mise,
                category: .languages,
                categoryDisplay: "Languages & Runtimes",
                categoryIcon: "chevron.left.forwardslash.chevron.right",
                installCommand: "mise use node@latest",
                homepage: "https://nodejs.org",
                version: "22.0.0",
                aliases: ["nodejs"],
                license: "MIT",
                isInstalled: true,
                installedVersion: "20.10.0",
                isGuiApp: false,
                isRuntime: true
            ),
            onTap: {},
            onInstall: {}
        )

        ToolCard(
            tool: BrowsableTool(
                id: "cask:docker",
                name: "Docker Desktop",
                description: "Pack, ship and run any application as a container",
                source: .cask,
                category: .containers,
                categoryDisplay: "Containers & VMs",
                categoryIcon: "shippingbox",
                installCommand: "brew install --cask docker",
                homepage: "https://docker.com",
                version: "4.26.1",
                aliases: [],
                license: nil,
                isInstalled: false,
                installedVersion: nil,
                isGuiApp: true,
                isRuntime: false
            ),
            onTap: {},
            onInstall: {}
        )
    }
    .padding()
    .environment(AppState())
}
