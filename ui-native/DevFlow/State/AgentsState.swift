import Foundation

/// Manages AI coding agents - browsing, installing, and configuring.
@Observable
@MainActor
class AgentsState {
    // MARK: - State

    var agents: [AIAgent] = []
    var isLoading = false
    var searchQuery: String = ""
    var showInstalledOnly: Bool = false
    var installingAgentIds: Set<String> = []
    var configuringAgentIds: Set<String> = []

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - List Actions

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = [:]

            if showInstalledOnly {
                params["installed_only"] = true
            }

            if !searchQuery.isEmpty {
                params["search"] = searchQuery
            }

            print("[AgentsState] Loading agents with params: \(params)")
            let response: AgentListResponse = try await bridge.call("agents.list_agents", params: params)
            print("[AgentsState] Loaded \(response.agents.count) agents, total: \(response.total)")

            if let error = response.error {
                print("[AgentsState] Error in response: \(error)")
                notifications.add(.error("Failed to load agents: \(error)"))
                return
            }

            agents = response.agents
            print("[AgentsState] Agents array now has \(agents.count) items")
        } catch {
            print("[AgentsState] Exception loading agents: \(error)")
            notifications.add(.error("Failed to load agents: \(error.localizedDescription)"))
        }
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response: AgentListResponse = try await bridge.call("agents.refresh")

            if let error = response.error {
                notifications.add(.error("Failed to refresh agents: \(error)"))
                return
            }

            agents = response.agents
        } catch {
            notifications.add(.error("Failed to refresh agents: \(error.localizedDescription)"))
        }
    }

    // MARK: - Agent Actions

    func getAgent(_ agentId: String) async -> AIAgent? {
        do {
            let response: AgentDetailResponse = try await bridge.call(
                "agents.get_agent",
                params: ["agent_id": agentId]
            )
            return response.agent
        } catch {
            return nil
        }
    }

    func install(_ agentId: String) async {
        installingAgentIds.insert(agentId)
        defer { installingAgentIds.remove(agentId) }

        do {
            let response: AgentInstallResponse = try await bridge.call(
                "agents.install",
                params: ["agent_id": agentId]
            )

            if response.success {
                notifications.add(.success(response.message ?? "Agent installed successfully"))
                // Update agent in list
                if let index = agents.firstIndex(where: { $0.id == agentId }) {
                    agents[index].isInstalled = true
                }
            } else if let error = response.error {
                notifications.add(.error("Installation failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to install agent: \(error.localizedDescription)"))
        }
    }

    func configureApiKey(_ agentId: String, provider: String, apiKey: String) async {
        configuringAgentIds.insert(agentId)
        defer { configuringAgentIds.remove(agentId) }

        do {
            let response: AgentApiKeyConfigResponse = try await bridge.call(
                "agents.configure_api_key",
                params: [
                    "agent_id": agentId,
                    "provider": provider,
                    "api_key": apiKey,
                ]
            )

            if response.success {
                notifications.add(.success(response.message ?? "API key configured"))
                // Update agent in list
                if let index = agents.firstIndex(where: { $0.id == agentId }) {
                    agents[index].isConfigured = true
                }
            } else if let error = response.error {
                notifications.add(.error("Configuration failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to configure API key: \(error.localizedDescription)"))
        }
    }

    func checkApiKeyStatus(_ agentId: String) async -> [String: Bool]? {
        do {
            let response: AgentApiKeyStatusResponse = try await bridge.call(
                "agents.check_api_key_status",
                params: ["agent_id": agentId]
            )
            return response.providers
        } catch {
            return nil
        }
    }

    func detectInstalled(_ agentIds: [String]? = nil) async {
        do {
            var params: [String: any Sendable] = [:]
            if let ids = agentIds {
                params["agent_ids"] = ids
            }

            let response: AgentInstalledCheckResponse = try await bridge.call(
                "agents.detect_installed",
                params: params
            )

            if let installed = response.installed {
                for (agentId, isInstalled) in installed {
                    if let index = agents.firstIndex(where: { $0.id == agentId }) {
                        agents[index].isInstalled = isInstalled
                    }
                }
            }
        } catch {
            // Ignore - detection is best-effort
        }
    }

    // MARK: - Computed Properties

    var installedAgents: [AIAgent] {
        agents.filter { $0.isInstalled }
    }

    var availableAgents: [AIAgent] {
        agents.filter { !$0.isInstalled }
    }
}
