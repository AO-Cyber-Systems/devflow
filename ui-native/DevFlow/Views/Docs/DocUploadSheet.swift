import SwiftUI

struct DocUploadSheet: View {
    let projectPath: String?
    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var title = ""
    @State private var content = ""
    @State private var selectedDocType = "guide"
    @State private var selectedFormat = "markdown"
    @State private var description = ""
    @State private var tags = ""
    @State private var aiContext = ""
    @State private var isSaving = false

    // For file import
    @State private var showFileImporter = false
    @State private var importFilePath: String?

    // AI Enhancement options
    @State private var autoSummarize = false
    @State private var autoTag = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Basic Info") {
                    TextField("Title", text: $title)

                    Picker("Type", selection: $selectedDocType) {
                        ForEach(appState.docTypes) { docType in
                            Label(docType.name, systemImage: docType.icon)
                                .tag(docType.typeId)
                        }
                    }

                    Picker("Format", selection: $selectedFormat) {
                        ForEach(appState.docFormats) { format in
                            Text(format.name).tag(format.formatId)
                        }
                    }

                    TextField("Description (optional)", text: $description)
                }

                Section("Content") {
                    HStack {
                        Button("Import from File...") {
                            showFileImporter = true
                        }
                        .buttonStyle(.bordered)

                        Spacer()

                        if importFilePath != nil {
                            Label("File selected", systemImage: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                        }
                    }

                    if importFilePath == nil {
                        TextEditor(text: $content)
                            .font(.system(.body, design: .monospaced))
                            .frame(minHeight: 200)
                    }
                }

                Section("AI Context (optional)") {
                    Text("Add hints to help AI tools understand this documentation better.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    TextEditor(text: $aiContext)
                        .font(.system(.body, design: .monospaced))
                        .frame(minHeight: 80)
                }

                Section("Tags (optional)") {
                    TextField("Comma-separated tags", text: $tags)
                }

                // AI Enhancement section
                if appState.isAIAvailable {
                    Section("AI Enhancement") {
                        Toggle("Auto-generate summary", isOn: $autoSummarize)
                            .help("Use on-device AI to generate a summary for this document")

                        Toggle("Auto-generate tags", isOn: $autoTag)
                            .help("Use on-device AI to suggest relevant tags")

                        if autoSummarize || autoTag {
                            HStack {
                                Image(systemName: "info.circle")
                                    .foregroundStyle(.secondary)
                                Text("AI features use on-device processing and may take a moment.")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Add Documentation")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await saveDoc()
                        }
                    }
                    .disabled(isSaving || !isValid)
                }
            }
            .fileImporter(
                isPresented: $showFileImporter,
                allowedContentTypes: [.plainText, .json, .yaml],
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    if let url = urls.first {
                        importFilePath = url.path
                        // Auto-fill title from filename
                        if title.isEmpty {
                            title = url.deletingPathExtension().lastPathComponent
                                .replacingOccurrences(of: "_", with: " ")
                                .replacingOccurrences(of: "-", with: " ")
                                .capitalized
                        }
                    }
                case .failure:
                    break
                }
            }
        }
        .frame(minWidth: 500, minHeight: 600)
        .task {
            // Ensure doc types and formats are loaded
            if appState.docTypes.isEmpty {
                await appState.loadDocTypes()
            }
            if appState.docFormats.isEmpty {
                await appState.loadDocFormats()
            }
        }
    }

    private var isValid: Bool {
        !title.isEmpty && (importFilePath != nil || !content.isEmpty)
    }

    private func saveDoc() async {
        isSaving = true
        defer { isSaving = false }

        let tagList = tags.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        if let filePath = importFilePath {
            // Import from file
            _ = await appState.importDocFromFile(
                filePath: filePath,
                projectPath: projectPath,
                docType: selectedDocType,
                aiContext: aiContext.isEmpty ? nil : aiContext,
                autoSummarize: autoSummarize,
                autoTag: autoTag
            )
        } else {
            // Create from content
            _ = await appState.createDoc(
                title: title,
                content: content,
                docType: selectedDocType,
                format: selectedFormat,
                projectPath: projectPath,
                description: description,
                tags: tagList,
                aiContext: aiContext.isEmpty ? nil : aiContext,
                autoSummarize: autoSummarize,
                autoTag: autoTag
            )
        }

        dismiss()
    }
}

#Preview {
    DocUploadSheet(projectPath: nil)
        .environment(AppState())
}
