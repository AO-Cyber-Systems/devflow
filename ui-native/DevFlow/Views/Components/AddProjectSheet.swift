import SwiftUI
import UniformTypeIdentifiers

struct AddProjectSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var path = ""
    @State private var showFolderPicker = false

    var isValid: Bool {
        !path.isEmpty &&
        FileManager.default.fileExists(atPath: path)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Add Project")
                        .font(.headline)
                    Spacer()
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("closeAddProjectButton")
                }
                .padding()

                Divider()

                // Form
                VStack(alignment: .leading, spacing: 20) {
                    // Path field
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Project Path")
                            .fontWeight(.medium)
                        HStack {
                            TextField("/path/to/project", text: $path)
                                .textFieldStyle(.roundedBorder)
                                .accessibilityIdentifier("projectPathField")

                            Button("Browse...") {
                                showFolderPicker = true
                            }
                            .accessibilityIdentifier("browseProjectPathButton")
                        }

                        if !path.isEmpty && !FileManager.default.fileExists(atPath: path) {
                            Label("Path does not exist", systemImage: "exclamationmark.triangle.fill")
                                .font(.caption)
                                .foregroundStyle(.orange)
                        }

                        Text("The project name will be detected from the directory or devflow.yml config")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    // Auto-detect info
                    if !path.isEmpty && FileManager.default.fileExists(atPath: path) {
                        DetectedProjectInfo(path: path)
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
                    .accessibilityIdentifier("cancelAddProjectButton")

                    Spacer()

                    Button("Add Project") {
                        Task {
                            await appState.addProject(path: path)
                            dismiss()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!isValid)
                    .keyboardShortcut(.defaultAction)
                    .accessibilityIdentifier("confirmAddProjectButton")
                }
                .padding()
            }
        }
        .frame(width: 450, height: 400)
        .fileImporter(
            isPresented: $showFolderPicker,
            allowedContentTypes: [.folder],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    path = url.path
                }
            case .failure:
                break
            }
        }
        .accessibilityIdentifier("addProjectSheet")
    }
}

struct DetectedProjectInfo: View {
    let path: String
    @State private var detectedFramework: String?
    @State private var detectedPort: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Detected Configuration")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundStyle(.secondary)

            HStack(spacing: 16) {
                if let framework = detectedFramework {
                    Label(framework, systemImage: "hammer.fill")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.blue.opacity(0.1))
                        .foregroundStyle(.blue)
                        .cornerRadius(4)
                }

                if let port = detectedPort {
                    Label("Port \(port)", systemImage: "network")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.purple.opacity(0.1))
                        .foregroundStyle(.purple)
                        .cornerRadius(4)
                }

                if detectedFramework == nil && detectedPort == nil {
                    Text("No framework detected")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
        .task {
            await detectProject()
        }
    }

    private func detectProject() async {
        let fm = FileManager.default

        // Detect framework based on files
        if fm.fileExists(atPath: "\(path)/package.json") {
            // Check for specific frameworks
            if fm.fileExists(atPath: "\(path)/next.config.js") || fm.fileExists(atPath: "\(path)/next.config.mjs") {
                detectedFramework = "Next.js"
                detectedPort = 3000
            } else if fm.fileExists(atPath: "\(path)/nuxt.config.ts") || fm.fileExists(atPath: "\(path)/nuxt.config.js") {
                detectedFramework = "Nuxt"
                detectedPort = 3000
            } else if fm.fileExists(atPath: "\(path)/svelte.config.js") {
                detectedFramework = "SvelteKit"
                detectedPort = 5173
            } else if fm.fileExists(atPath: "\(path)/vite.config.ts") || fm.fileExists(atPath: "\(path)/vite.config.js") {
                detectedFramework = "Vite"
                detectedPort = 5173
            } else if fm.fileExists(atPath: "\(path)/angular.json") {
                detectedFramework = "Angular"
                detectedPort = 4200
            } else {
                detectedFramework = "Node.js"
                detectedPort = 3000
            }
        } else if fm.fileExists(atPath: "\(path)/requirements.txt") || fm.fileExists(atPath: "\(path)/pyproject.toml") {
            if fm.fileExists(atPath: "\(path)/manage.py") {
                detectedFramework = "Django"
                detectedPort = 8000
            } else if fm.fileExists(atPath: "\(path)/app.py") || fm.fileExists(atPath: "\(path)/main.py") {
                detectedFramework = "Flask/FastAPI"
                detectedPort = 8000
            } else {
                detectedFramework = "Python"
            }
        } else if fm.fileExists(atPath: "\(path)/Cargo.toml") {
            detectedFramework = "Rust"
        } else if fm.fileExists(atPath: "\(path)/go.mod") {
            detectedFramework = "Go"
            detectedPort = 8080
        } else if fm.fileExists(atPath: "\(path)/Package.swift") {
            detectedFramework = "Swift"
        }
    }
}

#Preview {
    AddProjectSheet()
        .environment(AppState())
}
