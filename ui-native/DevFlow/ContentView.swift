import SwiftUI

enum NavigationItem: String, CaseIterable, Identifiable {
    case dashboard = "Dashboard"
    case templates = "Templates"
    case tools = "Tools"
    case agents = "AI Agents"
    case documentation = "Documentation"
    case code = "Code"
    case infrastructure = "Infrastructure"
    case projects = "Projects"
    case databases = "Databases"
    case secrets = "Secrets"
    case logs = "Logs"
    case config = "Settings"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .dashboard: return "gauge.with.dots.needle.bottom.50percent"
        case .templates: return "square.grid.2x2"
        case .tools: return "wrench.and.screwdriver"
        case .agents: return "brain"
        case .documentation: return "doc.text.fill"
        case .code: return "chevron.left.forwardslash.chevron.right"
        case .infrastructure: return "server.rack"
        case .projects: return "folder.fill"
        case .databases: return "cylinder.split.1x2"
        case .secrets: return "key.fill"
        case .logs: return "list.bullet.rectangle"
        case .config: return "gearshape.fill"
        }
    }
}

struct ContentView: View {
    @Environment(AppState.self) private var appState
    @Binding var selectedItem: NavigationItem?

    init(selectedItem: Binding<NavigationItem?> = .constant(.dashboard)) {
        self._selectedItem = selectedItem
    }

    var body: some View {
        NavigationSplitView {
            List(selection: $selectedItem) {
                Section("Overview") {
                    NavigationLink(value: NavigationItem.dashboard) {
                        Label(NavigationItem.dashboard.rawValue, systemImage: NavigationItem.dashboard.icon)
                    }
                    .accessibilityIdentifier("navDashboard")

                    NavigationLink(value: NavigationItem.templates) {
                        Label(NavigationItem.templates.rawValue, systemImage: NavigationItem.templates.icon)
                    }
                    .accessibilityIdentifier("navTemplates")

                    NavigationLink(value: NavigationItem.tools) {
                        Label(NavigationItem.tools.rawValue, systemImage: NavigationItem.tools.icon)
                    }
                    .accessibilityIdentifier("navTools")

                    NavigationLink(value: NavigationItem.agents) {
                        Label(NavigationItem.agents.rawValue, systemImage: NavigationItem.agents.icon)
                    }
                    .accessibilityIdentifier("navAgents")

                    NavigationLink(value: NavigationItem.documentation) {
                        Label(NavigationItem.documentation.rawValue, systemImage: NavigationItem.documentation.icon)
                    }
                    .accessibilityIdentifier("navDocumentation")

                    NavigationLink(value: NavigationItem.code) {
                        Label(NavigationItem.code.rawValue, systemImage: NavigationItem.code.icon)
                    }
                    .accessibilityIdentifier("navCode")
                }

                Section("Manage") {
                    NavigationLink(value: NavigationItem.infrastructure) {
                        Label(NavigationItem.infrastructure.rawValue, systemImage: NavigationItem.infrastructure.icon)
                    }
                    .accessibilityIdentifier("navInfrastructure")

                    NavigationLink(value: NavigationItem.projects) {
                        Label(NavigationItem.projects.rawValue, systemImage: NavigationItem.projects.icon)
                    }
                    .accessibilityIdentifier("navProjects")

                    NavigationLink(value: NavigationItem.databases) {
                        Label(NavigationItem.databases.rawValue, systemImage: NavigationItem.databases.icon)
                    }
                    .accessibilityIdentifier("navDatabases")

                    NavigationLink(value: NavigationItem.secrets) {
                        Label(NavigationItem.secrets.rawValue, systemImage: NavigationItem.secrets.icon)
                    }
                    .accessibilityIdentifier("navSecrets")

                    NavigationLink(value: NavigationItem.logs) {
                        Label(NavigationItem.logs.rawValue, systemImage: NavigationItem.logs.icon)
                    }
                    .accessibilityIdentifier("navLogs")
                }

                Section("System") {
                    NavigationLink(value: NavigationItem.config) {
                        Label(NavigationItem.config.rawValue, systemImage: NavigationItem.config.icon)
                    }
                    .accessibilityIdentifier("navConfig")
                }
            }
            .listStyle(.sidebar)
            .navigationSplitViewColumnWidth(min: 180, ideal: 200, max: 250)
            .accessibilityIdentifier("sidebarList")
        } detail: {
            Group {
                switch selectedItem {
                case .dashboard:
                    DashboardView()
                case .templates:
                    TemplateBrowserView()
                case .tools:
                    ToolBrowserView()
                case .agents:
                    AgentBrowserView()
                case .documentation:
                    DocsView(projectPath: nil)
                case .code:
                    CodeSearchView(projectPath: nil)
                case .infrastructure:
                    InfrastructureView()
                case .projects:
                    ProjectsView()
                case .databases:
                    DatabaseView()
                case .secrets:
                    SecretsView()
                case .logs:
                    LogViewerView()
                case .config:
                    ConfigView()
                case nil:
                    Text("Select an item")
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .navigationTitle(selectedItem?.rawValue ?? "DevFlow")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                HStack(spacing: 16) {
                    DoctorStatusIndicator()
                    AIStatusIndicator()
                    ConnectionStatusView()
                }
            }
        }
        .sheet(isPresented: Binding(
            get: { appState.showAddProject },
            set: { appState.showAddProject = $0 }
        )) {
            AddProjectSheet()
        }
        .sheet(isPresented: Binding(
            get: { appState.showAddSecret },
            set: { appState.showAddSecret = $0 }
        )) {
            AddSecretSheet()
        }
        .sheet(isPresented: Binding(
            get: { appState.showAddDatabase },
            set: { appState.showAddDatabase = $0 }
        )) {
            AddDatabaseSheet()
        }
        .sheet(isPresented: Binding(
            get: { appState.showSetupWizard },
            set: { appState.showSetupWizard = $0 }
        )) {
            SetupWizardView()
        }
        .sheet(isPresented: Binding(
            get: { appState.showNewProjectWizard },
            set: { appState.showNewProjectWizard = $0 }
        )) {
            NewProjectWizardView()
        }
        .sheet(isPresented: Binding(
            get: { appState.showDoctorSheet },
            set: { appState.showDoctorSheet = $0 }
        )) {
            DoctorSheet()
        }
        .overlay(alignment: .topTrailing) {
            NotificationOverlay()
                .padding()
        }
        .task {
            // Safely initialize backend - don't crash on failure
            await appState.initialize()
            // Check if setup wizard should be shown
            await appState.checkSetupWizardStatus()
            // Check AI availability
            await appState.checkAIStatus()
        }
    }
}

struct ConnectionStatusView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(appState.isConnected ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(appState.isConnected ? "Connected" : "Disconnected")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .accessibilityIdentifier("connectionStatus")
    }
}

#Preview {
    ContentView()
        .environment(AppState())
}
