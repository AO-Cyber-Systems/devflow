import SwiftUI

struct AgentDetailSheet: View {
    let agent: AIAgent
    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState
    @State private var showApiKeyConfig = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    HStack(spacing: 16) {
                        Image(systemName: agent.icon)
                            .font(.system(size: 40))
                            .foregroundStyle(agent.isInstalled ? .green : .blue)
                            .frame(width: 60, height: 60)
                            .background(
                                RoundedRectangle(cornerRadius: 12)
                                    .fill(agent.isInstalled ? Color.green.opacity(0.15) : Color.blue.opacity(0.15))
                            )

                        VStack(alignment: .leading, spacing: 4) {
                            Text(agent.name)
                                .font(.title)
                                .fontWeight(.bold)

                            HStack {
                                if agent.isInstalled {
                                    Label("Installed", systemImage: "checkmark.circle.fill")
                                        .foregroundStyle(.green)
                                }
                                if agent.isConfigured {
                                    Label("Configured", systemImage: "gearshape.fill")
                                        .foregroundStyle(.blue)
                                }
                            }
                            .font(.subheadline)
                        }

                        Spacer()
                    }

                    Text(agent.description)
                        .foregroundStyle(.secondary)

                    Divider()

                    // Installation section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Installation")
                            .font(.headline)

                        HStack {
                            Label(agent.installMethodDisplay, systemImage: "shippingbox")
                            Spacer()
                            Text(agent.installCommand)
                                .font(.system(.caption, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                        .padding()
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(8)

                        if !agent.isInstalled {
                            Button {
                                Task {
                                    await appState.installAgent(agent.id)
                                }
                            } label: {
                                if appState.installingAgentIds.contains(agent.id) {
                                    ProgressView()
                                        .frame(maxWidth: .infinity)
                                } else {
                                    Text("Install \(agent.name)")
                                        .frame(maxWidth: .infinity)
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .controlSize(.large)
                            .disabled(appState.installingAgentIds.contains(agent.id))
                        }
                    }

                    Divider()

                    // Capabilities section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Capabilities")
                            .font(.headline)

                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible()),
                        ], spacing: 8) {
                            ForEach(agent.capabilitiesDisplay) { capability in
                                HStack {
                                    Image(systemName: capability.icon)
                                        .foregroundStyle(.blue)
                                    Text(capability.name)
                                        .font(.subheadline)
                                    Spacer()
                                }
                                .padding(8)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(6)
                            }
                        }
                    }

                    Divider()

                    // Providers section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Supported Providers")
                            .font(.headline)

                        ForEach(agent.supportedProvidersDisplay) { provider in
                            HStack {
                                Image(systemName: "cloud")
                                    .foregroundStyle(.purple)
                                Text(provider.name)
                                Spacer()
                            }
                            .padding(8)
                            .background(Color.purple.opacity(0.1))
                            .cornerRadius(6)
                        }
                    }

                    if agent.isInstalled && !agent.apiKeys.isEmpty {
                        Divider()

                        // API Key Configuration
                        VStack(alignment: .leading, spacing: 12) {
                            Text("API Keys")
                                .font(.headline)

                            ForEach(agent.apiKeys) { keyConfig in
                                HStack {
                                    Image(systemName: "key")
                                        .foregroundStyle(.orange)
                                    VStack(alignment: .leading) {
                                        Text(keyConfig.providerDisplay)
                                            .font(.subheadline)
                                        Text(keyConfig.envVar)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    if keyConfig.required {
                                        Text("Required")
                                            .font(.caption)
                                            .foregroundStyle(.red)
                                    }
                                }
                                .padding(8)
                                .background(Color.orange.opacity(0.1))
                                .cornerRadius(6)
                            }

                            Button("Configure API Keys") {
                                showApiKeyConfig = true
                            }
                            .buttonStyle(.bordered)
                        }
                    }

                    // Links section
                    if agent.homepage != "" || agent.docsUrl != nil || agent.githubUrl != nil {
                        Divider()

                        VStack(alignment: .leading, spacing: 12) {
                            Text("Links")
                                .font(.headline)

                            HStack(spacing: 16) {
                                if !agent.homepage.isEmpty {
                                    Link(destination: URL(string: agent.homepage)!) {
                                        Label("Homepage", systemImage: "globe")
                                    }
                                }

                                if let docsUrl = agent.docsUrl, let url = URL(string: docsUrl) {
                                    Link(destination: url) {
                                        Label("Docs", systemImage: "book")
                                    }
                                }

                                if let githubUrl = agent.githubUrl, let url = URL(string: githubUrl) {
                                    Link(destination: url) {
                                        Label("GitHub", systemImage: "chevron.left.forwardslash.chevron.right")
                                    }
                                }
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle(agent.name)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 500, minHeight: 600)
        .sheet(isPresented: $showApiKeyConfig) {
            ApiKeyConfigSheet(agent: agent)
        }
    }
}

#Preview {
    AgentDetailSheet(
        agent: AIAgent(
            id: "claude-code",
            name: "Claude Code",
            description: "Anthropic's official AI coding assistant CLI. Agentic coding with Claude directly in your terminal.",
            homepage: "https://anthropic.com",
            installMethod: .npm,
            installMethodDisplay: "npm (Node.js)",
            installCommand: "npm install -g @anthropic-ai/claude-code",
            configLocation: "~/.claude/",
            capabilities: ["code_generation", "terminal"],
            capabilitiesDisplay: [
                CapabilityDisplayInfo(capabilityId: "code_generation", name: "Code Generation", icon: "doc.text"),
                CapabilityDisplayInfo(capabilityId: "terminal", name: "Terminal Access", icon: "terminal"),
            ],
            supportedProviders: ["anthropic"],
            supportedProvidersDisplay: [
                ProviderDisplayInfo(providerId: "anthropic", name: "Anthropic (Claude)"),
            ],
            apiKeys: [
                ApiKeyConfig(provider: "anthropic", providerDisplay: "Anthropic", envVar: "ANTHROPIC_API_KEY", required: true, description: "API key from console.anthropic.com"),
            ],
            isInstalled: true,
            isConfigured: false,
            installedVersion: "1.0.0",
            icon: "brain",
            version: "1.0.0",
            aliases: [],
            docsUrl: "https://docs.anthropic.com",
            githubUrl: "https://github.com/anthropics/claude-code"
        )
    )
    .environment(AppState())
}
