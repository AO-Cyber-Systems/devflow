import SwiftUI

struct ProjectsView: View {
    @Environment(AppState.self) private var appState
    @State private var searchText = ""
    @State private var selectedProject: Project?

    var filteredProjects: [Project] {
        if searchText.isEmpty {
            return appState.projects
        }
        return appState.projects.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.path.localizedCaseInsensitiveContains(searchText) ||
            ($0.domain?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }

    var body: some View {
        HSplitView {
            // Project List
            VStack(spacing: 0) {
                // Search and Add
                HStack {
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundStyle(.secondary)
                        TextField("Search projects...", text: $searchText)
                            .textFieldStyle(.plain)
                            .accessibilityIdentifier("projectSearchField")
                    }
                    .padding(8)
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(8)

                    Button {
                        appState.showAddProject = true
                    } label: {
                        Image(systemName: "plus")
                    }
                    .buttonStyle(.bordered)
                    .accessibilityIdentifier("addProjectButton")
                }
                .padding()

                Divider()

                // Project List
                if appState.isLoadingProjects && appState.projects.isEmpty {
                    VStack {
                        Spacer()
                        ProgressView("Loading projects...")
                        Spacer()
                    }
                } else if filteredProjects.isEmpty {
                    VStack(spacing: 12) {
                        Spacer()
                        Image(systemName: searchText.isEmpty ? "folder.badge.plus" : "magnifyingglass")
                            .font(.system(size: 40))
                            .foregroundStyle(.secondary)
                        Text(searchText.isEmpty ? "No projects" : "No matching projects")
                            .font(.headline)
                        if searchText.isEmpty {
                            Button("Add Project") {
                                appState.showAddProject = true
                            }
                            .accessibilityIdentifier("emptyStateAddProjectButton")
                        }
                        Spacer()
                    }
                    .frame(maxWidth: .infinity)
                } else {
                    List(selection: $selectedProject) {
                        ForEach(filteredProjects) { project in
                            ProjectListRow(project: project, isSelected: selectedProject?.id == project.id)
                                .tag(project)
                                .accessibilityIdentifier("projectRow_\(project.id)")
                        }
                    }
                    .listStyle(.sidebar)
                    .accessibilityIdentifier("projectsList")
                }
            }
            .frame(minWidth: 280, idealWidth: 320, maxWidth: 400)

            // Detail View
            if let project = selectedProject {
                ProjectDetailView(project: project)
                    .accessibilityIdentifier("projectDetailView")
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "folder")
                        .font(.system(size: 60))
                        .foregroundStyle(.secondary)
                    Text("Select a project")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(nsColor: .windowBackgroundColor))
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("projectsView")
        .task {
            await appState.loadProjects()
        }
    }
}

struct ProjectListRow: View {
    let project: Project
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 12) {
            // Status indicator
            Circle()
                .fill(project.isRunning ? Color.green : Color.secondary.opacity(0.3))
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(project.name)
                    .fontWeight(.medium)
                    .lineLimit(1)

                Text(project.path)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Spacer()

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
        .padding(.vertical, 4)
    }
}

#Preview {
    ProjectsView()
        .environment(AppState())
        .frame(width: 900, height: 600)
}
