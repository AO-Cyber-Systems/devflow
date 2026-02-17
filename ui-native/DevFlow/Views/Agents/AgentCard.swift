import SwiftUI

struct AgentCard: View {
    let agent: AIAgent
    var onTap: () -> Void
    var onInstall: () -> Void
    var onConfigure: () -> Void

    @Environment(AppState.self) private var appState

    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: 12) {
                // Icon
                Image(systemName: agent.icon)
                    .font(.title)
                    .foregroundStyle(agent.isInstalled ? .green : .secondary)
                    .frame(width: 40, height: 40)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(agent.isInstalled ? Color.green.opacity(0.15) : Color.secondary.opacity(0.1))
                    )

                // Agent info
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(agent.name)
                            .font(.headline)

                        if agent.isInstalled {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                                .font(.caption)
                        }

                        if let version = agent.installedVersion {
                            Text("v\(version)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }

                    Text(agent.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)

                    // Capabilities row
                    HStack(spacing: 8) {
                        // Install method badge
                        Label(agent.installMethodDisplay, systemImage: installMethodIcon)
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.15))
                            .foregroundStyle(.blue)
                            .cornerRadius(4)

                        // Provider badges
                        ForEach(agent.supportedProvidersDisplay.prefix(3)) { provider in
                            Text(provider.name.split(separator: " ").first ?? "")
                                .font(.caption)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.15))
                                .foregroundStyle(.purple)
                                .cornerRadius(4)
                        }

                        if agent.supportedProvidersDisplay.count > 3 {
                            Text("+\(agent.supportedProvidersDisplay.count - 3)")
                                .font(.caption)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.secondary.opacity(0.15))
                                .foregroundStyle(.secondary)
                                .cornerRadius(4)
                        }
                    }
                }

                Spacer()

                // Action buttons
                VStack(spacing: 8) {
                    if isInstalling {
                        ProgressView()
                            .scaleEffect(0.8)
                            .frame(width: 80)
                    } else if agent.isInstalled {
                        if agent.isConfigured {
                            Label("Ready", systemImage: "checkmark.circle")
                                .font(.caption)
                                .foregroundStyle(.green)
                        } else {
                            Button("Configure") {
                                onConfigure()
                            }
                            .buttonStyle(.borderedProminent)
                            .controlSize(.small)
                        }
                    } else {
                        Button("Install") {
                            onInstall()
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.small)
                    }
                }
            }
            .padding()
            .background(Color(.textBackgroundColor))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }

    private var isInstalling: Bool {
        appState.installingAgentIds.contains(agent.id)
    }

    private var installMethodIcon: String {
        switch agent.installMethod {
        case .npm: return "shippingbox"
        case .pip: return "puzzlepiece"
        case .curl: return "arrow.down.circle"
        case .brew: return "mug"
        case .vscode: return "puzzlepiece.extension"
        case .manual: return "wrench"
        }
    }
}

#Preview {
    VStack {
        AgentCard(
            agent: AIAgent(
                id: "claude-code",
                name: "Claude Code",
                description: "Anthropic's official AI coding assistant CLI",
                homepage: "https://anthropic.com",
                installMethod: .npm,
                installMethodDisplay: "npm (Node.js)",
                installCommand: "npm install -g @anthropic-ai/claude-code",
                configLocation: "~/.claude/",
                capabilities: ["code_generation", "terminal"],
                capabilitiesDisplay: [
                    CapabilityDisplayInfo(capabilityId: "code_generation", name: "Code Generation", icon: "doc.text"),
                ],
                supportedProviders: ["anthropic"],
                supportedProvidersDisplay: [
                    ProviderDisplayInfo(providerId: "anthropic", name: "Anthropic (Claude)"),
                ],
                apiKeys: [],
                isInstalled: true,
                isConfigured: true,
                installedVersion: "1.0.0",
                icon: "brain",
                version: "1.0.0",
                aliases: [],
                docsUrl: nil,
                githubUrl: nil
            ),
            onTap: {},
            onInstall: {},
            onConfigure: {}
        )
    }
    .padding()
    .environment(AppState())
}
