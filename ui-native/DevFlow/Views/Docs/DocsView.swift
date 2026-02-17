import SwiftUI

struct DocsView: View {
    @Environment(AppState.self) private var appState
    let projectPath: String?

    @State private var selectedDoc: Documentation?
    @State private var showUploadSheet = false
    @State private var showWebFetchSheet = false
    @State private var showScanSheet = false
    @State private var selectedProjectPath: String?

    // Computed property for effective project path (nil means global docs)
    private var effectiveProjectPath: String? {
        projectPath ?? selectedProjectPath
    }

    var body: some View {
        VStack(spacing: 0) {
            // Search and filter bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search documentation...", text: Binding(
                    get: { appState.docsSearchQuery },
                    set: { appState.docsSearchQuery = $0 }
                ))
                .textFieldStyle(.plain)
                .accessibilityIdentifier("docsSearchField")
                .onSubmit {
                    Task {
                        await appState.loadDocs(projectPath: effectiveProjectPath)
                    }
                }

                if !appState.docsSearchQuery.isEmpty {
                    Button {
                        appState.docsSearchQuery = ""
                        Task {
                            await appState.loadDocs(projectPath: effectiveProjectPath)
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Divider()
                    .frame(height: 20)
                    .padding(.horizontal, 8)

                // Project filter (when not in project context)
                if projectPath == nil {
                    Picker("Scope", selection: $selectedProjectPath) {
                        Text("Global Docs").tag(nil as String?)
                        ForEach(appState.projects) { project in
                            Text(project.name)
                                .tag(project.path as String?)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 150)
                    .onChange(of: selectedProjectPath) { _, _ in
                        Task {
                            await appState.loadDocs(projectPath: effectiveProjectPath)
                        }
                    }
                }

                // Doc type filter
                Picker("Type", selection: Binding(
                    get: { appState.selectedDocType ?? "all" },
                    set: {
                        appState.selectedDocType = $0 == "all" ? nil : $0
                        Task {
                            await appState.loadDocs(projectPath: projectPath)
                        }
                    }
                )) {
                    Text("All Types").tag("all")
                    ForEach(appState.docTypes) { docType in
                        Label(docType.name, systemImage: docType.icon)
                            .tag(docType.typeId)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 150)

                // AI Status
                if appState.isAIAvailable {
                    AIStatusButton()
                }

                Button {
                    showScanSheet = true
                } label: {
                    Label("Scan", systemImage: "doc.viewfinder")
                }
                .buttonStyle(.bordered)
                .help("Import from image or PDF using OCR")

                Button {
                    showWebFetchSheet = true
                } label: {
                    Label("Web", systemImage: "globe")
                }
                .buttonStyle(.bordered)

                Button {
                    showUploadSheet = true
                } label: {
                    Label("Add", systemImage: "plus")
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("addDocButton")
            }
            .padding()

            Divider()

            // Main content
            if appState.isLoadingDocs && appState.docs.isEmpty {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Loading documentation...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.docs.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No documentation yet")
                        .font(.title2)
                    Text("Upload documentation to help AI tools understand your project")
                        .foregroundStyle(.secondary)
                    Button("Add Documentation") {
                        showUploadSheet = true
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(selection: $selectedDoc) {
                    ForEach(appState.docs) { doc in
                        DocRowView(doc: doc)
                            .tag(doc)
                            .contextMenu {
                                if appState.isAIAvailable {
                                    Button {
                                        Task {
                                            _ = await appState.summarizeDoc(doc.id, projectPath: effectiveProjectPath)
                                        }
                                    } label: {
                                        Label("Summarize", systemImage: "text.quote")
                                    }

                                    Button {
                                        Task {
                                            _ = await appState.extractDocEntities(doc.id, projectPath: effectiveProjectPath)
                                        }
                                    } label: {
                                        Label("Extract Entities", systemImage: "tag")
                                    }

                                    Button {
                                        Task {
                                            _ = await appState.autoEnhanceDoc(doc.id, projectPath: effectiveProjectPath)
                                        }
                                    } label: {
                                        Label("Auto-Enhance", systemImage: "wand.and.stars")
                                    }

                                    Divider()
                                }

                                Button("Delete", role: .destructive) {
                                    Task {
                                        await appState.deleteDoc(doc.id, projectPath: effectiveProjectPath)
                                    }
                                }
                            }
                    }
                }
                .listStyle(.inset)
            }
        }
        .sheet(isPresented: $showUploadSheet) {
            DocUploadSheet(projectPath: effectiveProjectPath)
        }
        .sheet(isPresented: $showWebFetchSheet) {
            WebFetchSheet(projectPath: effectiveProjectPath)
        }
        .sheet(isPresented: $showScanSheet) {
            ScanDocumentSheet(projectPath: effectiveProjectPath)
        }
        .sheet(item: $selectedDoc) { doc in
            DocDetailView(doc: doc, projectPath: effectiveProjectPath)
        }
        .accessibilityIdentifier("docsView")
        .task {
            // Load projects for the picker
            if appState.projects.isEmpty {
                await appState.loadProjects()
            }
            if appState.docs.isEmpty {
                await appState.loadDocTypes()
                await appState.loadDocFormats()
                await appState.loadDocs(projectPath: effectiveProjectPath)
            }
        }
    }
}

struct DocRowView: View {
    let doc: Documentation

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: doc.docTypeIcon)
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(doc.title)
                    .font(.headline)

                HStack(spacing: 8) {
                    Text(doc.docTypeDisplay)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.15))
                        .cornerRadius(4)

                    Text(doc.formatDisplay)
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    if !doc.tags.isEmpty {
                        Text(doc.tags.joined(separator: ", "))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }
            }

            Spacer()

            if doc.aiContext != nil {
                Image(systemName: "brain")
                    .foregroundStyle(.purple)
                    .help("Has AI context")
            }

            // AI enhanced indicator
            if doc.description.contains("AI-generated") || doc.tags.contains("ai-enhanced") {
                Image(systemName: "sparkles")
                    .foregroundStyle(.orange)
                    .help("AI enhanced")
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    DocsView(projectPath: nil)
        .environment(AppState())
        .frame(width: 600, height: 400)
}
