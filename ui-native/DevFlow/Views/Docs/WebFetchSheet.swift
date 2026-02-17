import SwiftUI

enum CrawlScope: String, CaseIterable {
    case allPages = "all"
    case directory = "directory"
    case singlePage = "single"

    var label: String {
        switch self {
        case .allPages: return "All Pages"
        case .directory: return "Directory Only"
        case .singlePage: return "Single Page"
        }
    }

    var description: String {
        switch self {
        case .allPages: return "Crawl all linked pages on the site"
        case .directory: return "Only crawl pages under the URL path"
        case .singlePage: return "Import only this page"
        }
    }
}

struct WebFetchSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    let projectPath: String?

    @State private var url: String = ""
    @State private var selectedDocType: String = "reference"
    @State private var customTitle: String = ""
    @State private var crawlScope: CrawlScope = .allPages
    @State private var maxPages: Int = 500
    @State private var maxDepth: Int = 10
    @State private var isLoading = false
    @State private var importResult: ImportDocsSiteResponse?
    @State private var singleImportResult: Documentation?
    @State private var errorMessage: String?

    private var directoryPath: String {
        guard let urlObj = URL(string: url) else { return "/" }
        let path = urlObj.path
        return path.isEmpty ? "/" : path
    }

    private var isCrawlMode: Bool {
        crawlScope != .singlePage
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Import from Web")
                    .font(.headline)
                Spacer()
                Button("Cancel") {
                    dismiss()
                }
            }
            .padding()

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // URL input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("URL")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        TextField("https://docs.example.com/...", text: $url)
                            .textFieldStyle(.roundedBorder)
                    }

                    // Crawl scope
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Scope")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Picker("Scope", selection: $crawlScope) {
                            ForEach(CrawlScope.allCases, id: \.self) { scope in
                                Text(scope.label).tag(scope)
                            }
                        }
                        .pickerStyle(.segmented)
                        Text(crawlScope.description)
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }

                    // Crawl options (for multi-page modes)
                    if crawlScope != .singlePage {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("Max Pages")
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Stepper("\(maxPages)", value: $maxPages, in: 10...1000, step: 50)
                                    .frame(width: 140)
                            }

                            HStack {
                                Text("Max Depth")
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Stepper("\(maxDepth)", value: $maxDepth, in: 1...20)
                                    .frame(width: 120)
                            }

                            if crawlScope == .directory {
                                Text("Will only crawl pages under: \(directoryPath)")
                                    .font(.caption)
                                    .foregroundStyle(.blue)
                            }
                        }
                        .padding()
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(8)
                    }

                    // Doc type selection
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Document Type")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Picker("Type", selection: $selectedDocType) {
                            ForEach(appState.docTypes) { docType in
                                Label(docType.name, systemImage: docType.icon)
                                    .tag(docType.typeId)
                            }
                        }
                        .pickerStyle(.menu)
                    }

                    // Custom title (single page only)
                    if crawlScope == .singlePage {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Custom Title (optional)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            TextField("Leave empty to use page title", text: $customTitle)
                                .textFieldStyle(.roundedBorder)
                        }
                    }

                    // Error message
                    if let error = errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(8)
                    }

                    // Import button
                    HStack {
                        Spacer()
                        if isLoading {
                            ProgressView()
                                .padding(.trailing, 8)
                            Text(isCrawlMode ? "Crawling site..." : "Importing...")
                        } else {
                            Button {
                                Task {
                                    await performImport()
                                }
                            } label: {
                                Label("Import", systemImage: "arrow.down.doc")
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(url.isEmpty)
                        }
                    }

                    // Import result
                    if let result = importResult {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                                Text("Import Complete")
                                    .font(.headline)
                            }

                            Grid(alignment: .leading, horizontalSpacing: 20, verticalSpacing: 8) {
                                GridRow {
                                    Text("Pages Fetched:")
                                        .foregroundStyle(.secondary)
                                    Text("\(result.totalFetched ?? 0)")
                                }
                                GridRow {
                                    Text("Docs Imported:")
                                        .foregroundStyle(.secondary)
                                    Text("\(result.totalImported ?? 0)")
                                }
                            }

                            if let docs = result.docs, !docs.isEmpty {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Imported Documents:")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    ForEach(docs.prefix(10)) { doc in
                                        Text("• \(doc.title)")
                                            .font(.caption)
                                            .lineLimit(1)
                                    }
                                    if docs.count > 10 {
                                        Text("... and \(docs.count - 10) more")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }

                            Button("Done") {
                                dismiss()
                            }
                            .buttonStyle(.borderedProminent)
                        }
                        .padding()
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(8)
                    }

                    if let doc = singleImportResult {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                                Text("Import Complete")
                                    .font(.headline)
                            }

                            Text("Imported: \(doc.title)")
                                .font(.subheadline)

                            Button("Done") {
                                dismiss()
                            }
                            .buttonStyle(.borderedProminent)
                        }
                        .padding()
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(8)
                    }
                }
                .padding()
            }
        }
        .frame(width: 500, height: 550)
        .task {
            if appState.docTypes.isEmpty {
                await appState.loadDocTypes()
            }
        }
    }

    func performImport() async {
        guard !url.isEmpty else { return }

        isLoading = true
        errorMessage = nil
        importResult = nil
        singleImportResult = nil

        if crawlScope != .singlePage {
            let pathPrefix = crawlScope == .directory ? directoryPath : nil
            let result = await appState.importDocsSite(
                url: url,
                projectPath: projectPath,
                docType: selectedDocType,
                maxPages: maxPages,
                maxDepth: maxDepth,
                pathPrefix: pathPrefix
            )
            if let result = result {
                if result.success {
                    importResult = result
                } else if let error = result.error {
                    errorMessage = error
                }
            } else {
                errorMessage = "Import failed"
            }
        } else {
            let doc = await appState.importDocFromUrl(
                url: url,
                projectPath: projectPath,
                docType: selectedDocType,
                title: customTitle.isEmpty ? nil : customTitle
            )
            if let doc = doc {
                singleImportResult = doc
            } else {
                errorMessage = "Failed to import URL"
            }
        }

        isLoading = false
    }
}

#Preview {
    WebFetchSheet(projectPath: nil)
        .environment(AppState())
}
