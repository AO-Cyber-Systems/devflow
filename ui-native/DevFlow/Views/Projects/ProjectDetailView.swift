import SwiftUI

struct ProjectDetailView: View {
    let project: Project
    @Environment(AppState.self) private var appState
    @State private var showDeleteConfirmation = false
    @State private var showEditSheet = false
    @State private var projectDetail: ProjectDetail?
    @State private var isLoadingDetail = false
    @State private var showServices = true
    @State private var showPorts = true
    @State private var showVolumes = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header
                ProjectHeaderView(
                    project: project,
                    detail: projectDetail,
                    onEdit: { showEditSheet = true },
                    onToggle: {
                        Task {
                            if project.isRunning {
                                await appState.stopProject(project)
                            } else {
                                await appState.startProject(project)
                            }
                        }
                    },
                    onDelete: { showDeleteConfirmation = true }
                )

                Divider()

                // Quick Actions
                QuickActionsView(project: project)

                // Services Section (if has compose file)
                if let detail = projectDetail, detail.hasComposeFile {
                    CollapsibleSection(title: "Services", count: detail.services.count, isExpanded: $showServices) {
                        ServicesGridView(services: detail.services)
                    }

                    CollapsibleSection(title: "Port Mappings", count: detail.ports.count, isExpanded: $showPorts) {
                        PortsTableView(ports: detail.ports)
                    }

                    CollapsibleSection(title: "Volumes", count: detail.volumes.count, isExpanded: $showVolumes) {
                        VolumesTableView(volumes: detail.volumes)
                    }
                } else if isLoadingDetail {
                    HStack {
                        Spacer()
                        ProgressView()
                            .controlSize(.small)
                        Text("Loading project details...")
                            .foregroundStyle(.secondary)
                        Spacer()
                    }
                    .padding()
                }

                // Project Info
                VStack(alignment: .leading, spacing: 16) {
                    SectionHeader(title: "Project Details")

                    DetailRow(label: "Path", value: project.path, monospace: true)

                    if let port = project.port {
                        DetailRow(label: "Port", value: String(port))
                    }

                    if let framework = project.framework {
                        DetailRow(label: "Framework", value: framework)
                    }

                    if let lastAccessed = project.lastAccessed {
                        DetailRow(label: "Last Accessed", value: lastAccessed)
                    }

                    if let detail = projectDetail {
                        if detail.hasComposeFile, let composePath = detail.composeFilePath {
                            DetailRow(label: "Compose File", value: composePath, monospace: true)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .task {
            await loadProjectDetail()
        }
        .refreshable {
            await loadProjectDetail()
        }
        .confirmationDialog(
            "Delete Project",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                Task {
                    await appState.removeProject(project)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to remove '\(project.name)' from DevFlow? This won't delete any files.")
        }
        .sheet(isPresented: $showEditSheet) {
            EditProjectSheet(project: project)
        }
    }

    private func openInTerminal(path: String) {
        let script = """
        tell application "Terminal"
            do script "cd '\(path)'"
            activate
        end tell
        """
        if let appleScript = NSAppleScript(source: script) {
            var error: NSDictionary?
            appleScript.executeAndReturnError(&error)
        }
    }

    private func openInEditor(path: String) {
        // Try VSCode first, fall back to default
        let vscodeURL = URL(fileURLWithPath: "/Applications/Visual Studio Code.app")
        if FileManager.default.fileExists(atPath: vscodeURL.path) {
            NSWorkspace.shared.open(
                [URL(fileURLWithPath: path)],
                withApplicationAt: vscodeURL,
                configuration: NSWorkspace.OpenConfiguration()
            )
        } else {
            NSWorkspace.shared.open(URL(fileURLWithPath: path))
        }
    }

    private func loadProjectDetail() async {
        isLoadingDetail = true
        defer { isLoadingDetail = false }

        do {
            projectDetail = try await appState.getProjectDetail(path: project.path)
        } catch {
            // Silently fail - detail is optional enhancement
        }
    }
}

// MARK: - Project Header View

struct ProjectHeaderView: View {
    let project: Project
    let detail: ProjectDetail?
    let onEdit: () -> Void
    let onToggle: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(project.name)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    StatusBadge(isRunning: project.isRunning)

                    if let detail = detail, detail.hasComposeFile {
                        Text("\(detail.runningServices)/\(detail.totalServices)")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.1))
                            .foregroundStyle(.blue)
                            .cornerRadius(4)
                    }
                }

                if let domain = project.domain {
                    HStack {
                        Image(systemName: "globe")
                            .foregroundStyle(.secondary)
                        Text(domain)
                            .font(.system(.body, design: .monospaced))
                        Button {
                            if let url = URL(string: "http://\(domain)") {
                                NSWorkspace.shared.open(url)
                            }
                        } label: {
                            Image(systemName: "arrow.up.forward.square")
                        }
                        .buttonStyle(.borderless)
                        .accessibilityIdentifier("openProjectUrlButton")
                    }
                }
            }

            Spacer()

            HStack(spacing: 8) {
                Button {
                    onEdit()
                } label: {
                    Label("Edit", systemImage: "pencil")
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("editProjectButton")

                Button {
                    onToggle()
                } label: {
                    Label(
                        project.isRunning ? "Stop" : "Start",
                        systemImage: project.isRunning ? "stop.fill" : "play.fill"
                    )
                }
                .buttonStyle(.borderedProminent)
                .tint(project.isRunning ? .red : .green)
                .accessibilityIdentifier("toggleProjectButton")

                Button(role: .destructive) {
                    onDelete()
                } label: {
                    Image(systemName: "trash")
                }
                .accessibilityIdentifier("deleteProjectButton")
            }
        }
    }
}

// MARK: - Quick Actions View

struct QuickActionsView: View {
    let project: Project

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeader(title: "Quick Actions")

            HStack(spacing: 12) {
                ActionButton(
                    title: "Open in Finder",
                    icon: "folder",
                    color: .blue
                ) {
                    NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: project.path)
                }
                .accessibilityIdentifier("openInFinderButton")

                ActionButton(
                    title: "Open in Terminal",
                    icon: "terminal",
                    color: .green
                ) {
                    openInTerminal(path: project.path)
                }
                .accessibilityIdentifier("openInTerminalButton")

                ActionButton(
                    title: "Open in Editor",
                    icon: "chevron.left.forwardslash.chevron.right",
                    color: .purple
                ) {
                    openInEditor(path: project.path)
                }
                .accessibilityIdentifier("openInEditorButton")

                ActionButton(
                    title: "View Logs",
                    icon: "doc.text",
                    color: .orange
                ) {
                    // Would navigate to logs filtered by project
                }
                .accessibilityIdentifier("viewLogsButton")
            }
        }
    }

    private func openInTerminal(path: String) {
        let script = """
        tell application "Terminal"
            do script "cd '\(path)'"
            activate
        end tell
        """
        if let appleScript = NSAppleScript(source: script) {
            var error: NSDictionary?
            appleScript.executeAndReturnError(&error)
        }
    }

    private func openInEditor(path: String) {
        let vscodeURL = URL(fileURLWithPath: "/Applications/Visual Studio Code.app")
        if FileManager.default.fileExists(atPath: vscodeURL.path) {
            NSWorkspace.shared.open(
                [URL(fileURLWithPath: path)],
                withApplicationAt: vscodeURL,
                configuration: NSWorkspace.OpenConfiguration()
            )
        } else {
            NSWorkspace.shared.open(URL(fileURLWithPath: path))
        }
    }
}

// MARK: - Collapsible Section

struct CollapsibleSection<Content: View>: View {
    let title: String
    let count: Int
    @Binding var isExpanded: Bool
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .frame(width: 16)

                    Text(title)
                        .font(.headline)
                        .foregroundStyle(.primary)

                    Text("\(count)")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.2))
                        .cornerRadius(4)

                    Spacer()
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                content()
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }
}

struct SectionHeader: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.headline)
            .foregroundStyle(.secondary)
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    var monospace: Bool = false

    var body: some View {
        HStack {
            Text(label)
                .foregroundStyle(.secondary)
                .frame(width: 120, alignment: .leading)
            if monospace {
                Text(value)
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
            } else {
                Text(value)
            }
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                Text(title)
                    .font(.caption)
            }
            .frame(width: 100, height: 70)
            .background(color.opacity(0.1))
            .foregroundStyle(color)
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}

struct EditProjectSheet: View {
    let project: Project
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var domain: String = ""
    @State private var portString: String = ""
    @State private var startCommand: String = ""
    @State private var buildCommand: String = ""
    @State private var testCommand: String = ""

    var port: Int? {
        Int(portString)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Edit Project")
                        .font(.headline)
                    Spacer()
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("closeEditProjectButton")
                }
                .padding()

                Divider()

                // Form
                VStack(alignment: .leading, spacing: 20) {
                    // Project info (read-only)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Project")
                            .font(.headline)
                            .foregroundStyle(.secondary)

                        HStack {
                            Text(project.name)
                                .fontWeight(.medium)
                            if let framework = project.framework {
                                Text(framework)
                                    .font(.caption)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.blue.opacity(0.1))
                                    .foregroundStyle(.blue)
                                    .cornerRadius(4)
                            }
                        }

                        Text(project.path)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(8)

                    // Domain & Port
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Network Configuration")
                            .font(.headline)
                            .foregroundStyle(.secondary)

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Domain")
                                .fontWeight(.medium)
                            TextField("myapp.test", text: $domain)
                                .textFieldStyle(.roundedBorder)
                                .accessibilityIdentifier("editProjectDomainField")
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Port")
                                .fontWeight(.medium)
                            TextField("3000", text: $portString)
                                .textFieldStyle(.roundedBorder)
                                .accessibilityIdentifier("editProjectPortField")
                        }
                    }

                    // Commands
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Custom Commands")
                            .font(.headline)
                            .foregroundStyle(.secondary)

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Start Command")
                                .fontWeight(.medium)
                            TextField("npm run dev", text: $startCommand)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(.body, design: .monospaced))
                                .accessibilityIdentifier("editProjectStartCommand")
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Build Command")
                                .fontWeight(.medium)
                            TextField("npm run build", text: $buildCommand)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(.body, design: .monospaced))
                                .accessibilityIdentifier("editProjectBuildCommand")
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Test Command")
                                .fontWeight(.medium)
                            TextField("npm test", text: $testCommand)
                                .textFieldStyle(.roundedBorder)
                                .font(.system(.body, design: .monospaced))
                                .accessibilityIdentifier("editProjectTestCommand")
                        }
                    }
                }
                .padding()

                Spacer(minLength: 20)

                Divider()

                // Actions
                HStack {
                    Button("Cancel") {
                        dismiss()
                    }
                    .keyboardShortcut(.cancelAction)
                    .accessibilityIdentifier("cancelEditProjectButton")

                    Spacer()

                    Button("Save Changes") {
                        Task {
                            let commands = ProjectCommands(
                                start: startCommand.isEmpty ? nil : startCommand,
                                build: buildCommand.isEmpty ? nil : buildCommand,
                                test: testCommand.isEmpty ? nil : testCommand
                            )
                            await appState.updateProject(
                                project,
                                domain: domain.isEmpty ? nil : domain,
                                port: port,
                                commands: commands
                            )
                            dismiss()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .keyboardShortcut(.defaultAction)
                    .accessibilityIdentifier("saveEditProjectButton")
                }
                .padding()
            }
        }
        .frame(width: 450, height: 550)
        .accessibilityIdentifier("editProjectSheet")
        .onAppear {
            // Initialize fields with current values
            domain = project.domain ?? ""
            portString = project.port.map(String.init) ?? ""
        }
    }
}

#Preview {
    ProjectDetailView(project: Project(
        name: "My App",
        path: "/Users/test/projects/myapp",
        domain: "myapp.test",
        port: 3000,
        isRunning: true,
        framework: "Next.js"
    ))
    .environment(AppState())
    .frame(width: 600, height: 500)
}
