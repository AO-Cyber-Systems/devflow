import SwiftUI

struct ConfigView: View {
    @Environment(AppState.self) private var appState
    @State private var hasChanges = false

    var body: some View {
        @Bindable var state = appState

        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Settings")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        Text("Configure DevFlow preferences")
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    if hasChanges {
                        Button("Save Changes") {
                            Task {
                                await appState.saveConfig()
                                hasChanges = false
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .accessibilityIdentifier("saveConfigButton")
                    }
                }

                // Appearance
                SettingsSection(title: "Appearance", icon: "paintbrush.fill") {
                    AppearanceSettingsView()
                }

                // Domain Settings
                SettingsSection(title: "Domain Settings", icon: "globe") {
                    VStack(alignment: .leading, spacing: 16) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Base Domain")
                                .fontWeight(.medium)
                            TextField("Base domain", text: $state.globalConfig.baseDomain)
                                .textFieldStyle(.roundedBorder)
                                .accessibilityIdentifier("baseDomainField")
                                .onChange(of: state.globalConfig.baseDomain) { _, _ in hasChanges = true }
                            Text("Projects will be accessible at project.{base domain}")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                // Traefik Settings
                SettingsSection(title: "Traefik", icon: "arrow.triangle.branch") {
                    VStack(alignment: .leading, spacing: 16) {
                        HStack(spacing: 24) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("HTTP Port")
                                    .fontWeight(.medium)
                                TextField("Port", value: $state.globalConfig.traefikPort, format: .number)
                                    .textFieldStyle(.roundedBorder)
                                    .frame(width: 100)
                                    .accessibilityIdentifier("traefikPortField")
                                    .onChange(of: state.globalConfig.traefikPort) { _, _ in hasChanges = true }
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text("Dashboard Port")
                                    .fontWeight(.medium)
                                TextField("Port", value: $state.globalConfig.traefikDashboardPort, format: .number)
                                    .textFieldStyle(.roundedBorder)
                                    .frame(width: 100)
                                    .accessibilityIdentifier("traefikDashboardPortField")
                                    .onChange(of: state.globalConfig.traefikDashboardPort) { _, _ in hasChanges = true }
                            }
                        }
                    }
                }

                // DNS Settings
                SettingsSection(title: "DNS", icon: "network") {
                    VStack(alignment: .leading, spacing: 12) {
                        Toggle("Enable Local DNS", isOn: $state.globalConfig.dnsEnabled)
                            .accessibilityIdentifier("dnsEnabledToggle")
                            .onChange(of: state.globalConfig.dnsEnabled) { _, _ in hasChanges = true }

                        Text("Automatically resolve *.{base domain} to localhost")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                // Secrets Provider
                SettingsSection(title: "Secrets", icon: "key.fill") {
                    VStack(alignment: .leading, spacing: 12) {
                        Picker("Default Provider", selection: $state.globalConfig.secretsProvider) {
                            ForEach(SecretsProvider.allCases) { provider in
                                Label(provider.displayName, systemImage: provider.icon)
                                    .tag(provider)
                            }
                        }
                        .pickerStyle(.menu)
                        .accessibilityIdentifier("secretsProviderPicker")
                        .onChange(of: state.globalConfig.secretsProvider) { _, _ in hasChanges = true }

                        Text("Where to store new secrets by default")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                // Docker Settings
                SettingsSection(title: "Docker", icon: "shippingbox.fill") {
                    VStack(alignment: .leading, spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Docker Host (optional)")
                                .fontWeight(.medium)
                            TextField("unix:///var/run/docker.sock", text: Binding(
                                get: { state.globalConfig.dockerHost ?? "" },
                                set: { state.globalConfig.dockerHost = $0.isEmpty ? nil : $0 }
                            ))
                            .textFieldStyle(.roundedBorder)
                            .accessibilityIdentifier("dockerHostField")
                            .onChange(of: state.globalConfig.dockerHost) { _, _ in hasChanges = true }
                            Text("Leave empty for default Docker socket")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                // Keyboard Shortcuts
                SettingsSection(title: "Keyboard Shortcuts", icon: "keyboard") {
                    KeyboardShortcutsView()
                }

                // Data Management
                SettingsSection(title: "Data Management", icon: "folder.badge.gearshape") {
                    DataManagementView()
                }

                // About
                SettingsSection(title: "About", icon: "info.circle") {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("DevFlow")
                                .fontWeight(.medium)
                            Spacer()
                            Text("Version 1.0.0")
                                .foregroundStyle(.secondary)
                        }

                        Divider()

                        Link(destination: URL(string: "https://github.com/your/devflow")!) {
                            HStack {
                                Text("View on GitHub")
                                Spacer()
                                Image(systemName: "arrow.up.forward.square")
                            }
                        }
                        .accessibilityIdentifier("githubLink")
                    }
                }
            }
            .padding(24)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("configView")
        .task {
            await appState.loadConfig()
        }
    }
}

struct SettingsSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(.secondary)
                Text(title)
                    .font(.headline)
            }

            content
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(nsColor: .controlBackgroundColor))
                .cornerRadius(12)
        }
    }
}

#Preview {
    ConfigView()
        .environment(AppState())
        .frame(width: 700, height: 800)
}
