import SwiftUI

struct ToolDetailSheet: View {
    let tool: BrowsableTool

    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState
    @Environment(\.openURL) private var openURL

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    HStack(alignment: .top, spacing: 16) {
                        Image(systemName: tool.isInstalled ? "checkmark.circle.fill" : "circle")
                            .font(.system(size: 48))
                            .foregroundStyle(tool.isInstalled ? .green : .secondary)

                        VStack(alignment: .leading, spacing: 4) {
                            Text(tool.name)
                                .font(.title)
                                .fontWeight(.bold)

                            Text(tool.description)
                                .foregroundStyle(.secondary)

                            HStack(spacing: 8) {
                                Label(tool.source.displayName, systemImage: tool.source.icon)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(sourceColor.opacity(0.15))
                                    .foregroundStyle(sourceColor)
                                    .cornerRadius(4)

                                Label(tool.categoryDisplay, systemImage: tool.categoryIcon)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color.secondary.opacity(0.15))
                                    .cornerRadius(4)
                            }
                        }

                        Spacer()
                    }

                    Divider()

                    // Details
                    VStack(alignment: .leading, spacing: 12) {
                        if let version = tool.version {
                            ToolDetailRow(label: "Latest Version", value: version)
                        }

                        if tool.isInstalled, let installedVersion = tool.installedVersion {
                            ToolDetailRow(label: "Installed Version", value: installedVersion)
                        }

                        ToolDetailRow(label: "Install Command", value: tool.installCommand, isCode: true)

                        if !tool.aliases.isEmpty {
                            ToolDetailRow(label: "Aliases", value: tool.aliases.joined(separator: ", "))
                        }

                        if let license = tool.license {
                            ToolDetailRow(label: "License", value: license)
                        }

                        if let homepage = tool.homepage, let url = URL(string: homepage) {
                            HStack {
                                Text("Homepage")
                                    .foregroundStyle(.secondary)
                                    .frame(width: 120, alignment: .leading)
                                Button(homepage) {
                                    openURL(url)
                                }
                                .buttonStyle(.link)
                            }
                        }

                        HStack {
                            Text("Tool ID")
                                .foregroundStyle(.secondary)
                                .frame(width: 120, alignment: .leading)
                            Text(tool.id)
                                .font(.system(.body, design: .monospaced))
                                .textSelection(.enabled)
                        }
                    }

                    Divider()

                    // Badges
                    HStack(spacing: 12) {
                        if tool.isRuntime {
                            Label("Version Managed Runtime", systemImage: "memorychip")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.purple.opacity(0.15))
                                .foregroundStyle(.purple)
                                .cornerRadius(4)
                        }

                        if tool.isGuiApp {
                            Label("GUI Application", systemImage: "macwindow")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.blue.opacity(0.15))
                                .foregroundStyle(.blue)
                                .cornerRadius(4)
                        }

                        if tool.isInstalled {
                            Label("Installed", systemImage: "checkmark.circle.fill")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.green.opacity(0.15))
                                .foregroundStyle(.green)
                                .cornerRadius(4)
                        }
                    }
                }
                .padding(24)
            }
            .navigationTitle("Tool Details")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    if isInstalling {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else if tool.isInstalled {
                        Button("Installed") {}
                            .disabled(true)
                    } else {
                        Button("Install") {
                            Task {
                                await appState.installBrowsableTool(tool.id)
                            }
                        }
                        .keyboardShortcut(.defaultAction)
                    }
                }
            }
        }
        .frame(minWidth: 500, minHeight: 400)
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

struct ToolDetailRow: View {
    let label: String
    let value: String
    var isCode: Bool = false

    var body: some View {
        HStack(alignment: .top) {
            Text(label)
                .foregroundStyle(.secondary)
                .frame(width: 120, alignment: .leading)

            if isCode {
                Text(value)
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(.textBackgroundColor))
                    .cornerRadius(4)
            } else {
                Text(value)
                    .textSelection(.enabled)
            }
        }
    }
}

#Preview {
    ToolDetailSheet(
        tool: BrowsableTool(
            id: "mise:node",
            name: "node",
            description: "JavaScript runtime built on Chrome's V8 JavaScript engine for building scalable network applications",
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
        )
    )
    .environment(AppState())
}
