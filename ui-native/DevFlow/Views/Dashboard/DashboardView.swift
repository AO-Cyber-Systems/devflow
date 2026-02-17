import SwiftUI

struct DashboardView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Dashboard")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        Text("Overview of your development environment")
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    Button {
                        Task { await appState.loadDashboard() }
                    } label: {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                    .accessibilityIdentifier("refreshDashboardButton")
                }

                // Infrastructure Status Cards
                VStack(alignment: .leading, spacing: 12) {
                    Text("Infrastructure")
                        .font(.headline)

                    HStack(spacing: 16) {
                        InfraStatCard(
                            title: "Network",
                            icon: "network",
                            isRunning: appState.infraStatus.networkExists,
                            isLoading: appState.isLoadingInfra
                        )
                        .accessibilityIdentifier("networkStatusCard")

                        InfraStatCard(
                            title: "Traefik",
                            icon: "arrow.triangle.branch",
                            isRunning: appState.infraStatus.traefikRunning,
                            isLoading: appState.isLoadingInfra
                        )
                        .accessibilityIdentifier("traefikStatusCard")

                        InfraStatCard(
                            title: "Certificates",
                            icon: "lock.shield",
                            isRunning: appState.infraStatus.certificatesValid,
                            isLoading: appState.isLoadingInfra
                        )
                        .accessibilityIdentifier("certsStatusCard")
                    }
                }

                // Quick Actions
                VStack(alignment: .leading, spacing: 12) {
                    Text("Quick Actions")
                        .font(.headline)

                    HStack(spacing: 12) {
                        QuickActionButton(
                            title: appState.infraStatus.allRunning ? "Stop All" : "Start All",
                            icon: appState.infraStatus.allRunning ? "stop.fill" : "play.fill",
                            color: appState.infraStatus.allRunning ? .red : .green,
                            isLoading: appState.isLoadingInfra
                        ) {
                            if appState.infraStatus.allRunning {
                                await appState.stopInfrastructure()
                            } else {
                                await appState.startInfrastructure()
                            }
                        }
                        .accessibilityIdentifier("toggleInfraButton")

                        QuickActionButton(
                            title: "Add Project",
                            icon: "plus.circle.fill",
                            color: .blue,
                            isLoading: false
                        ) {
                            appState.showAddProject = true
                        }
                        .accessibilityIdentifier("addProjectQuickButton")

                        QuickActionButton(
                            title: "Open Traefik",
                            icon: "globe",
                            color: .purple,
                            isLoading: false
                        ) {
                            if let url = URL(string: "http://localhost:\(appState.globalConfig.traefikDashboardPort)") {
                                NSWorkspace.shared.open(url)
                            }
                        }
                        .accessibilityIdentifier("openTraefikButton")
                    }
                }

                // Projects Overview
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Projects")
                            .font(.headline)
                        Spacer()
                        Text("\(appState.projects.count) total")
                            .foregroundStyle(.secondary)
                            .font(.subheadline)
                    }

                    if appState.projects.isEmpty {
                        EmptyProjectsPlaceholder()
                    } else {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 12) {
                            ForEach(appState.projects.prefix(6)) { project in
                                ProjectCard(project: project)
                            }
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("dashboardView")
    }
}

struct InfraStatCard: View {
    let title: String
    let icon: String
    let isRunning: Bool
    let isLoading: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(isRunning ? .green : .secondary)
                Text(title)
                    .fontWeight(.medium)
                Spacer()
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.7)
                }
            }

            StatusBadge(isRunning: isRunning)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct QuickActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let isLoading: Bool
    let action: () async -> Void

    var body: some View {
        Button {
            Task { await action() }
        } label: {
            VStack(spacing: 8) {
                if isLoading {
                    ProgressView()
                        .frame(width: 24, height: 24)
                } else {
                    Image(systemName: icon)
                        .font(.title2)
                }
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .frame(width: 100, height: 80)
            .background(color.opacity(0.1))
            .foregroundStyle(color)
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
        .disabled(isLoading)
    }
}

struct ProjectCard: View {
    let project: Project
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(project.name)
                    .fontWeight(.medium)
                    .lineLimit(1)
                Spacer()
                StatusBadge(isRunning: project.isRunning)
            }

            if let domain = project.domain {
                Text(domain)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            if let framework = project.framework {
                Text(framework)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .foregroundStyle(.blue)
                    .cornerRadius(4)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
        .accessibilityIdentifier("projectCard_\(project.id)")
    }
}

struct EmptyProjectsPlaceholder: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 40))
                .foregroundStyle(.secondary)
            Text("No projects yet")
                .font(.headline)
            Text("Add your first project to get started")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button("Add Project") {
                appState.showAddProject = true
            }
            .buttonStyle(.borderedProminent)
            .accessibilityIdentifier("emptyAddProjectButton")
        }
        .frame(maxWidth: .infinity)
        .padding(40)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
    }
}

#Preview {
    DashboardView()
        .environment(AppState())
        .frame(width: 900, height: 700)
}
