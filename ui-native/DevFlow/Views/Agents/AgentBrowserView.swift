import SwiftUI

struct AgentBrowserView: View {
    @Environment(AppState.self) private var appState
    @State private var selectedAgent: AIAgent?
    @State private var showApiKeySheet = false
    @State private var apiKeyAgent: AIAgent?

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search agents...", text: Binding(
                    get: { appState.agentSearchQuery },
                    set: { appState.agentSearchQuery = $0 }
                ))
                .textFieldStyle(.plain)
                .accessibilityIdentifier("agentSearchField")
                .onSubmit {
                    Task {
                        await appState.loadAgents()
                    }
                }

                if !appState.agentSearchQuery.isEmpty {
                    Button {
                        appState.agentSearchQuery = ""
                        Task {
                            await appState.loadAgents()
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Divider()
                    .frame(height: 20)
                    .padding(.horizontal, 8)

                Toggle("Installed Only", isOn: Binding(
                    get: { appState.showInstalledAgentsOnly },
                    set: {
                        appState.showInstalledAgentsOnly = $0
                        Task {
                            await appState.loadAgents()
                        }
                    }
                ))
                .toggleStyle(.checkbox)
                .accessibilityIdentifier("installedOnlyToggle")

                Button {
                    Task {
                        await appState.refreshAgents()
                    }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("refreshAgentsButton")
                .disabled(appState.isLoadingAgents)
            }
            .padding()

            Divider()

            // Main content
            if appState.isLoadingAgents && appState.agents.isEmpty {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Loading AI agents...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.agents.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "brain")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No AI agents found")
                        .font(.title2)
                    Text("Check your connection or try refreshing")
                        .foregroundStyle(.secondary)
                    Button("Refresh") {
                        Task {
                            await appState.refreshAgents()
                        }
                    }
                    .buttonStyle(.bordered)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(appState.agents) { agent in
                            AgentCard(agent: agent) {
                                selectedAgent = agent
                            } onInstall: {
                                Task {
                                    await appState.installAgent(agent.id)
                                }
                            } onConfigure: {
                                apiKeyAgent = agent
                                showApiKeySheet = true
                            }
                        }
                    }
                    .padding()
                }
            }
        }
        .sheet(item: $selectedAgent) { agent in
            AgentDetailSheet(agent: agent)
        }
        .sheet(isPresented: $showApiKeySheet) {
            if let agent = apiKeyAgent {
                ApiKeyConfigSheet(agent: agent)
            }
        }
        .task {
            if appState.agents.isEmpty {
                await appState.loadAgents()
            }
        }
        .accessibilityIdentifier("agentBrowserView")
    }
}

#Preview {
    AgentBrowserView()
        .environment(AppState())
        .frame(width: 800, height: 600)
}
