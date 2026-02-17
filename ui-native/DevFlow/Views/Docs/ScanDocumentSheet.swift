import SwiftUI
import UniformTypeIdentifiers

/// Sheet for importing documentation from images or PDFs using OCR.
struct ScanDocumentSheet: View {
    let projectPath: String?

    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var selectedFileURL: URL?
    @State private var extractedText = ""
    @State private var isProcessing = false
    @State private var error: String?

    // Document metadata
    @State private var title = ""
    @State private var selectedDocType = "custom"
    @State private var description = ""
    @State private var autoSummarize = false
    @State private var autoTag = false

    @State private var showFilePicker = false

    var body: some View {
        NavigationStack {
            Form {
                // File Selection
                Section("Source File") {
                    HStack {
                        if let url = selectedFileURL {
                            VStack(alignment: .leading) {
                                Text(url.lastPathComponent)
                                    .font(.headline)
                                Text(url.deletingLastPathComponent().path)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        } else {
                            Text("No file selected")
                                .foregroundStyle(.secondary)
                        }

                        Spacer()

                        Button("Choose File...") {
                            showFilePicker = true
                        }
                        .buttonStyle(.bordered)
                    }

                    if isProcessing {
                        HStack {
                            ProgressView()
                            Text("Extracting text...")
                        }
                    }

                    if let error = error {
                        HStack {
                            Image(systemName: "exclamationmark.triangle")
                                .foregroundStyle(.orange)
                            Text(error)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                // Extracted Text Preview
                if !extractedText.isEmpty {
                    Section("Extracted Text") {
                        TextEditor(text: $extractedText)
                            .font(.system(.body, design: .monospaced))
                            .frame(minHeight: 200)
                    }
                }

                // Document Metadata
                Section("Document Info") {
                    TextField("Title", text: $title)

                    Picker("Type", selection: $selectedDocType) {
                        ForEach(appState.docTypes) { docType in
                            Label(docType.name, systemImage: docType.icon)
                                .tag(docType.typeId)
                        }
                    }

                    TextField("Description (optional)", text: $description)
                }

                // AI Enhancement
                if appState.isAIAvailable {
                    Section("AI Enhancement") {
                        Toggle("Auto-generate summary", isOn: $autoSummarize)
                            .help("Use on-device AI to generate a summary")

                        Toggle("Auto-generate tags", isOn: $autoTag)
                            .help("Use on-device AI to suggest relevant tags")
                    }
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Import from Image/PDF")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Import") {
                        Task {
                            await importDocument()
                        }
                    }
                    .disabled(!canImport)
                }
            }
            .fileImporter(
                isPresented: $showFilePicker,
                allowedContentTypes: supportedTypes,
                allowsMultipleSelection: false
            ) { result in
                handleFileSelection(result)
            }
        }
        .frame(minWidth: 500, minHeight: 600)
        .task {
            if appState.docTypes.isEmpty {
                await appState.loadDocTypes()
            }
        }
    }

    private var supportedTypes: [UTType] {
        [.pdf, .png, .jpeg, .tiff, .heic, .image]
    }

    private var canImport: Bool {
        !extractedText.isEmpty && !title.isEmpty && !isProcessing
    }

    private func handleFileSelection(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            selectedFileURL = url
            error = nil

            // Auto-fill title from filename
            if title.isEmpty {
                title = url.deletingPathExtension().lastPathComponent
                    .replacingOccurrences(of: "_", with: " ")
                    .replacingOccurrences(of: "-", with: " ")
                    .capitalized
            }

            // Start OCR extraction
            Task {
                await extractText(from: url)
            }

        case .failure(let err):
            error = err.localizedDescription
        }
    }

    private func extractText(from url: URL) async {
        isProcessing = true
        error = nil
        defer { isProcessing = false }

        do {
            // Start accessing security-scoped resource
            guard url.startAccessingSecurityScopedResource() else {
                error = "Unable to access file"
                return
            }
            defer { url.stopAccessingSecurityScopedResource() }

            let ocrService = OCRService.shared

            if url.pathExtension.lowercased() == "pdf" {
                // Extract from PDF
                let pages = try await ocrService.extractTextFromPDF(url)
                extractedText = pages.enumerated().map { index, text in
                    "--- Page \(index + 1) ---\n\(text)"
                }.joined(separator: "\n\n")
            } else {
                // Extract from image
                extractedText = try await ocrService.extractText(from: url)
            }

            if extractedText.isEmpty {
                error = "No text could be extracted from this file"
            }
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func importDocument() async {
        guard canImport else { return }

        isProcessing = true
        defer { isProcessing = false }

        // Create the document using the extracted text
        _ = await appState.createDoc(
            title: title,
            content: extractedText,
            docType: selectedDocType,
            format: "markdown",
            projectPath: projectPath,
            description: description,
            tags: [],
            aiContext: nil,
            autoSummarize: autoSummarize,
            autoTag: autoTag
        )

        dismiss()
    }
}

#Preview {
    ScanDocumentSheet(projectPath: nil)
        .environment(AppState())
}
