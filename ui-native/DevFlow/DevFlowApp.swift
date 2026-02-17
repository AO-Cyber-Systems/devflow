import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Ignore SIGPIPE to prevent crashes when writing to closed pipes
        signal(SIGPIPE, SIG_IGN)

        // Ensure the app stays running
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

@main
struct DevFlowApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @State private var appState = AppState()
    @State private var showCommandPalette = false
    @State private var selectedNavigation: NavigationItem? = .dashboard

    var body: some Scene {
        WindowGroup("DevFlow") {
            ContentView(selectedItem: $selectedNavigation)
                .environment(appState)
                .frame(minWidth: 800, minHeight: 600)
                .sheet(isPresented: $showCommandPalette) {
                    CommandPaletteView(selectedNavigation: $selectedNavigation)
                        .environment(appState)
                }
        }
        .defaultSize(width: 1200, height: 800)
        .commands {
            CommandGroup(replacing: .newItem) { }

            CommandGroup(after: .toolbar) {
                Button("Command Palette...") {
                    showCommandPalette = true
                }
                .keyboardShortcut("k", modifiers: .command)

                Divider()

                // Section navigation shortcuts
                Button("Dashboard") {
                    selectedNavigation = .dashboard
                }
                .keyboardShortcut("1", modifiers: .command)

                Button("Templates") {
                    selectedNavigation = .templates
                }
                .keyboardShortcut("2", modifiers: .command)

                Button("Tools") {
                    selectedNavigation = .tools
                }
                .keyboardShortcut("3", modifiers: .command)

                Button("AI Agents") {
                    selectedNavigation = .agents
                }
                .keyboardShortcut("a", modifiers: [.command, .shift])

                Button("Documentation") {
                    selectedNavigation = .documentation
                }
                .keyboardShortcut("d", modifiers: [.command, .shift])

                Button("Code") {
                    selectedNavigation = .code
                }
                .keyboardShortcut("c", modifiers: [.command, .shift])

                Button("Infrastructure") {
                    selectedNavigation = .infrastructure
                }
                .keyboardShortcut("4", modifiers: .command)

                Button("Projects") {
                    selectedNavigation = .projects
                }
                .keyboardShortcut("5", modifiers: .command)

                Button("Databases") {
                    selectedNavigation = .databases
                }
                .keyboardShortcut("6", modifiers: .command)

                Button("Secrets") {
                    selectedNavigation = .secrets
                }
                .keyboardShortcut("7", modifiers: .command)

                Button("Logs") {
                    selectedNavigation = .logs
                }
                .keyboardShortcut("8", modifiers: .command)

                Button("Settings") {
                    selectedNavigation = .config
                }
                .keyboardShortcut("9", modifiers: .command)
            }

            CommandMenu("Infrastructure") {
                Button("Start All") {
                    Task { await appState.startInfrastructure() }
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])
                .accessibilityIdentifier("menuStartInfra")

                Button("Stop All") {
                    Task { await appState.stopInfrastructure() }
                }
                .keyboardShortcut("s", modifiers: [.command, .shift])
                .accessibilityIdentifier("menuStopInfra")

                Divider()

                Button("Refresh Status") {
                    Task { await appState.refreshInfraStatus() }
                }
                .keyboardShortcut("r", modifiers: .command)
                .accessibilityIdentifier("menuRefreshStatus")
            }

            CommandMenu("Projects") {
                Button("Add Project...") {
                    appState.showAddProject = true
                }
                .keyboardShortcut("n", modifiers: .command)
                .accessibilityIdentifier("menuAddProject")

                Button("Refresh Projects") {
                    Task { await appState.loadProjects() }
                }
                .accessibilityIdentifier("menuRefreshProjects")
            }
        }
    }
}
