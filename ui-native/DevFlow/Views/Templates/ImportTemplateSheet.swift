import SwiftUI

struct ImportTemplateSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var gitUrl = ""
    @State private var branch = ""
    @State private var subdirectory = ""
    @State private var showAdvanced = false
    @State private var isImporting = false
    @State private var importResult: ImportTemplateResponse?
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Import Template")
                    .font(.headline)
                Spacer()
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            .padding()

            Divider()

            // Content
            if let result = importResult {
                if result.success {
                    successView(result)
                } else {
                    errorView(result.errors)
                }
            } else {
                importForm
            }

            Divider()

            // Actions
            HStack {
                if importResult == nil {
                    Button("Cancel") {
                        dismiss()
                    }
                    .keyboardShortcut(.cancelAction)
                }

                Spacer()

                if let result = importResult {
                    if result.success {
                        Button("Done") {
                            dismiss()
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Button("Try Again") {
                            importResult = nil
                            errorMessage = nil
                        }
                        .buttonStyle(.bordered)

                        Button("Close") {
                            dismiss()
                        }
                    }
                } else {
                    Button("Import") {
                        Task {
                            await importTemplate()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(gitUrl.isEmpty || isImporting)
                }
            }
            .padding()
        }
        .frame(width: 500, height: 400)
    }

    // MARK: - Import Form

    private var importForm: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Git URL
                VStack(alignment: .leading, spacing: 8) {
                    Text("Git Repository URL")
                        .font(.headline)

                    TextField("https://github.com/user/template.git", text: $gitUrl)
                        .textFieldStyle(.roundedBorder)

                    Text("Enter the URL of a Git repository containing a template.yml file.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                // Advanced options
                DisclosureGroup("Advanced Options", isExpanded: $showAdvanced) {
                    VStack(alignment: .leading, spacing: 16) {
                        // Branch
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Branch or Tag")
                                .font(.subheadline)
                            TextField("main", text: $branch)
                                .textFieldStyle(.roundedBorder)
                            Text("Leave empty to use the default branch")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        // Subdirectory
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Subdirectory")
                                .font(.subheadline)
                            TextField("templates/my-template", text: $subdirectory)
                                .textFieldStyle(.roundedBorder)
                            Text("If the template is in a subdirectory of the repository")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.top, 12)
                }

                // Loading indicator
                if isImporting {
                    HStack {
                        ProgressView()
                            .controlSize(.small)
                        Text("Cloning repository...")
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color(nsColor: .controlBackgroundColor))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }

                // Error message
                if let error = errorMessage {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                        Text(error)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.orange.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }
            }
            .padding()
        }
    }

    // MARK: - Success View

    private func successView(_ result: ImportTemplateResponse) -> some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.green)

            Text("Template Imported!")
                .font(.title2)
                .fontWeight(.semibold)

            if let template = result.template {
                VStack(spacing: 8) {
                    Text(template.displayName)
                        .font(.headline)
                    Text(template.description)
                        .font(.body)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
                .background(Color(nsColor: .controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            if let path = result.installedPath {
                HStack {
                    Text("Installed to:")
                        .foregroundStyle(.secondary)
                    Text(path)
                        .font(.system(.caption, design: .monospaced))
                }
            }

            Spacer()
        }
        .padding()
    }

    // MARK: - Error View

    private func errorView(_ errors: [String]) -> some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "xmark.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.red)

            Text("Import Failed")
                .font(.title2)
                .fontWeight(.semibold)

            VStack(alignment: .leading, spacing: 8) {
                ForEach(errors, id: \.self) { error in
                    HStack(alignment: .top) {
                        Image(systemName: "exclamationmark.circle")
                            .foregroundStyle(.red)
                        Text(error)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .padding()
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            Spacer()
        }
        .padding()
    }

    // MARK: - Actions

    private func importTemplate() async {
        isImporting = true
        errorMessage = nil
        defer { isImporting = false }

        importResult = await appState.importTemplate(
            gitUrl: gitUrl,
            branch: branch.isEmpty ? nil : branch,
            subdirectory: subdirectory.isEmpty ? nil : subdirectory
        )

        // Refresh templates list on success
        if importResult?.success == true {
            await appState.loadTemplates()
        }
    }
}

#Preview {
    ImportTemplateSheet()
        .environment(AppState())
}
