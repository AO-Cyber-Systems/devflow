import SwiftUI
import UniformTypeIdentifiers

/// Exportable configuration data structure.
struct ExportedConfig: Codable {
    let version: String
    let exportedAt: Date
    let globalConfig: GlobalConfig
    let domains: [String]
    let projects: [ExportedProject]
}

/// Minimal project data for export (paths only, not secrets).
struct ExportedProject: Codable {
    let name: String
    let path: String
    let domain: String?
}

/// View for managing configuration export and import.
struct DataManagementView: View {
    @Environment(AppState.self) private var appState
    @State private var showExportSuccess = false
    @State private var showImportSuccess = false
    @State private var showImportError = false
    @State private var errorMessage = ""
    @State private var isExporting = false
    @State private var isImporting = false

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Export Section
            VStack(alignment: .leading, spacing: 8) {
                Text("Export Configuration")
                    .fontWeight(.medium)

                Text("Export your settings, domains, and project list to a file")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button(action: exportConfiguration) {
                    HStack {
                        if isExporting {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 16, height: 16)
                        } else {
                            Image(systemName: "square.and.arrow.up")
                        }
                        Text("Export...")
                    }
                }
                .disabled(isExporting)
                .accessibilityIdentifier("exportConfigButton")
            }

            Divider()

            // Import Section
            VStack(alignment: .leading, spacing: 8) {
                Text("Import Configuration")
                    .fontWeight(.medium)

                Text("Import settings from a previously exported file")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button(action: importConfiguration) {
                    HStack {
                        if isImporting {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 16, height: 16)
                        } else {
                            Image(systemName: "square.and.arrow.down")
                        }
                        Text("Import...")
                    }
                }
                .disabled(isImporting)
                .accessibilityIdentifier("importConfigButton")

                if showImportError {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.yellow)
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Divider()

            // Reset Section
            VStack(alignment: .leading, spacing: 8) {
                Text("Reset Configuration")
                    .fontWeight(.medium)

                Text("Reset all settings to their default values")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button(role: .destructive, action: resetConfiguration) {
                    HStack {
                        Image(systemName: "arrow.counterclockwise")
                        Text("Reset to Defaults")
                    }
                }
                .accessibilityIdentifier("resetConfigButton")
            }
        }
        .alert("Configuration Exported", isPresented: $showExportSuccess) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Your configuration has been exported successfully.")
        }
        .alert("Configuration Imported", isPresented: $showImportSuccess) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Your configuration has been imported successfully. Some changes may require restarting DevFlow.")
        }
    }

    private func exportConfiguration() {
        isExporting = true

        Task {
            defer { isExporting = false }

            let exportData = ExportedConfig(
                version: "1.0",
                exportedAt: Date(),
                globalConfig: appState.globalConfig,
                domains: appState.domainStatuses.map { $0.domain },
                projects: appState.projects.map { project in
                    ExportedProject(
                        name: project.name,
                        path: project.path,
                        domain: project.domain
                    )
                }
            )

            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            encoder.dateEncodingStrategy = .iso8601

            guard let data = try? encoder.encode(exportData) else {
                return
            }

            await MainActor.run {
                let savePanel = NSSavePanel()
                savePanel.title = "Export DevFlow Configuration"
                savePanel.nameFieldStringValue = "devflow-config.json"
                savePanel.allowedContentTypes = [.json]
                savePanel.canCreateDirectories = true

                if savePanel.runModal() == .OK, let url = savePanel.url {
                    do {
                        try data.write(to: url)
                        showExportSuccess = true
                    } catch {
                        errorMessage = error.localizedDescription
                        showImportError = true
                    }
                }
            }
        }
    }

    private func importConfiguration() {
        isImporting = true
        showImportError = false

        Task {
            defer { isImporting = false }

            await MainActor.run {
                let openPanel = NSOpenPanel()
                openPanel.title = "Import DevFlow Configuration"
                openPanel.allowedContentTypes = [.json]
                openPanel.allowsMultipleSelection = false
                openPanel.canChooseDirectories = false

                if openPanel.runModal() == .OK, let url = openPanel.url {
                    do {
                        let data = try Data(contentsOf: url)
                        let decoder = JSONDecoder()
                        decoder.dateDecodingStrategy = .iso8601

                        let importedConfig = try decoder.decode(ExportedConfig.self, from: data)

                        // Apply imported configuration
                        applyImportedConfig(importedConfig)
                        showImportSuccess = true
                    } catch {
                        errorMessage = "Failed to import: \(error.localizedDescription)"
                        showImportError = true
                    }
                }
            }
        }
    }

    private func applyImportedConfig(_ config: ExportedConfig) {
        // Apply global config
        appState.configManager.globalConfig = config.globalConfig

        // Save the config
        Task {
            await appState.saveConfig()

            // Add domains that don't exist
            for domain in config.domains {
                if !appState.domainStatuses.contains(where: { $0.domain == domain }) {
                    await appState.addDomain(domain, source: "imported")
                }
            }

            // Note: Projects are not automatically added as they require valid paths
            // User should manually add projects after import
        }
    }

    private func resetConfiguration() {
        // Reset to defaults
        appState.configManager.globalConfig = GlobalConfig()
        Task {
            await appState.saveConfig()
        }
    }
}

#Preview {
    DataManagementView()
        .environment(AppState())
        .padding()
        .frame(width: 400)
}
