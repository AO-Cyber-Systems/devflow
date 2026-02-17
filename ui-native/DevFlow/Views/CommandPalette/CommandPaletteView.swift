import SwiftUI

/// A Spotlight-style command palette for quick actions.
struct CommandPaletteView: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    @Binding var selectedNavigation: NavigationItem?

    @State private var query = ""
    @State private var selectedIndex = 0
    @FocusState private var isFocused: Bool

    var commands: [Command] {
        allCommands.filter { command in
            if query.isEmpty { return true }
            let searchText = query.lowercased()
            return command.title.lowercased().contains(searchText)
                || command.category.rawValue.lowercased().contains(searchText)
        }
    }

    var allCommands: [Command] {
        [
            // Navigation commands
            Command("Go to Dashboard", icon: "gauge.with.dots.needle.bottom.50percent", shortcut: "⌘1", category: .navigation) {
                selectedNavigation = .dashboard
                dismiss()
            },
            Command("Go to Templates", icon: "square.grid.2x2", shortcut: "⌘2", category: .navigation) {
                selectedNavigation = .templates
                dismiss()
            },
            Command("Go to Tools", icon: "wrench.and.screwdriver", shortcut: "⌘3", category: .navigation) {
                selectedNavigation = .tools
                dismiss()
            },
            Command("Go to Infrastructure", icon: "server.rack", shortcut: "⌘4", category: .navigation) {
                selectedNavigation = .infrastructure
                dismiss()
            },
            Command("Go to Projects", icon: "folder.fill", shortcut: "⌘5", category: .navigation) {
                selectedNavigation = .projects
                dismiss()
            },
            Command("Go to Databases", icon: "cylinder.split.1x2", shortcut: "⌘6", category: .navigation) {
                selectedNavigation = .databases
                dismiss()
            },
            Command("Go to Secrets", icon: "key.fill", shortcut: "⌘7", category: .navigation) {
                selectedNavigation = .secrets
                dismiss()
            },
            Command("Go to Logs", icon: "doc.text", shortcut: "⌘8", category: .navigation) {
                selectedNavigation = .logs
                dismiss()
            },
            Command("Go to Settings", icon: "gearshape.fill", shortcut: "⌘9", category: .navigation) {
                selectedNavigation = .config
                dismiss()
            },

            // Infrastructure commands
            Command("Start Infrastructure", icon: "play.fill", shortcut: "⇧⌘R", category: .infrastructure) {
                await appState.startInfrastructure()
                dismiss()
            },
            Command("Stop Infrastructure", icon: "stop.fill", shortcut: "⇧⌘S", category: .infrastructure) {
                await appState.stopInfrastructure()
                dismiss()
            },
            Command("Refresh Infrastructure Status", icon: "arrow.clockwise", shortcut: "⌘R", category: .infrastructure) {
                await appState.refreshInfraStatus()
                dismiss()
            },
            Command("Regenerate Certificates", icon: "lock.rotation", category: .infrastructure) {
                await appState.regenerateCertificates()
                dismiss()
            },
            Command("Add Domain", icon: "plus.circle", category: .infrastructure) {
                appState.showAddDomain = true
                dismiss()
            },

            // Project commands
            Command("Add Project", icon: "folder.badge.plus", shortcut: "⌘N", category: .projects) {
                appState.showAddProject = true
                dismiss()
            },
            Command("Refresh Projects", icon: "arrow.clockwise", category: .projects) {
                await appState.loadProjects()
                dismiss()
            },
            Command("New Project from Template", icon: "plus.square.on.square", category: .projects) {
                appState.showNewProjectWizard = true
                dismiss()
            },

            // Tools commands
            Command("Search Tools", icon: "magnifyingglass", category: .tools) {
                selectedNavigation = .tools
                dismiss()
            },
            Command("Refresh Tool Cache", icon: "arrow.clockwise", category: .tools) {
                await appState.refreshToolCache(force: true)
                dismiss()
            },

            // General commands
            Command("Show Setup Wizard", icon: "wand.and.stars", category: .general) {
                appState.showSetupWizard = true
                dismiss()
            },
            Command("Reload Dashboard", icon: "arrow.clockwise", category: .general) {
                await appState.loadDashboard()
                dismiss()
            },
            Command("Reconnect to Backend", icon: "link", category: .general) {
                await appState.reconnect()
                dismiss()
            },
        ]
    }

    var body: some View {
        VStack(spacing: 0) {
            // Search field
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .font(.title2)
                    .foregroundStyle(.secondary)

                TextField("Type a command...", text: $query)
                    .textFieldStyle(.plain)
                    .font(.title3)
                    .focused($isFocused)
                    .accessibilityIdentifier("commandSearchField")
                    .onSubmit {
                        executeSelected()
                    }

                if !query.isEmpty {
                    Button {
                        query = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Text("ESC")
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(4)
                    .foregroundStyle(.secondary)
            }
            .padding(16)

            Divider()

            // Commands list
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        ForEach(Array(commands.enumerated()), id: \.element.id) { index, command in
                            CommandRowView(
                                command: command,
                                isSelected: index == selectedIndex
                            )
                            .id(index)
                            .onTapGesture {
                                selectedIndex = index
                                executeSelected()
                            }
                        }
                    }
                    .padding(.vertical, 8)
                }
                .onChange(of: selectedIndex) { _, newIndex in
                    withAnimation {
                        proxy.scrollTo(newIndex, anchor: .center)
                    }
                }
            }

            // Footer
            HStack {
                Group {
                    Image(systemName: "arrow.up")
                    Image(systemName: "arrow.down")
                }
                .font(.caption)
                .foregroundStyle(.secondary)
                Text("to navigate")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer()

                Text("⏎ to select")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(nsColor: .controlBackgroundColor))
        }
        .frame(width: 550, height: 450)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(nsColor: .separatorColor), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.3), radius: 20, y: 10)
        .accessibilityIdentifier("commandPaletteView")
        .onAppear {
            isFocused = true
            selectedIndex = 0
        }
        .onChange(of: query) { _, _ in
            selectedIndex = 0
        }
        .onKeyPress(.downArrow) {
            if selectedIndex < commands.count - 1 {
                selectedIndex += 1
            }
            return .handled
        }
        .onKeyPress(.upArrow) {
            if selectedIndex > 0 {
                selectedIndex -= 1
            }
            return .handled
        }
        .onKeyPress(.escape) {
            dismiss()
            return .handled
        }
    }

    private func executeSelected() {
        guard selectedIndex < commands.count else { return }
        let command = commands[selectedIndex]
        Task {
            await command.action()
        }
    }
}

// MARK: - Command Row

struct CommandRowView: View {
    let command: Command
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: command.icon)
                .font(.body)
                .frame(width: 24)
                .foregroundStyle(isSelected ? .white : .secondary)

            VStack(alignment: .leading, spacing: 2) {
                Text(command.title)
                    .font(.body)
                    .foregroundStyle(isSelected ? .white : .primary)

                Text(command.category.rawValue)
                    .font(.caption)
                    .foregroundStyle(isSelected ? .white.opacity(0.7) : .secondary)
            }

            Spacer()

            if let shortcut = command.shortcut {
                Text(shortcut)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(isSelected ? .white.opacity(0.7) : .secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(
                        isSelected
                            ? Color.white.opacity(0.2)
                            : Color(nsColor: .controlBackgroundColor)
                    )
                    .cornerRadius(4)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(isSelected ? Color.accentColor : Color.clear)
        .contentShape(Rectangle())
    }
}

#Preview {
    CommandPaletteView(selectedNavigation: .constant(.dashboard))
        .environment(AppState())
}
