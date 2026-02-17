import SwiftUI

struct DocDetailView: View {
    let doc: Documentation
    let projectPath: String?

    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var fullDoc: Documentation?
    @State private var isLoading = true
    @State private var isEditing = false
    @State private var editedContent = ""
    @State private var editedAiContext = ""

    // AI State
    @State private var showAIPanel = false
    @State private var aiSummary: DocumentSummary?
    @State private var aiEntities: ExtractedEntities?
    @State private var isAIProcessing = false

    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let doc = fullDoc {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 16) {
                            // Header
                            HStack {
                                Image(systemName: doc.docTypeIcon)
                                    .font(.title)
                                    .foregroundStyle(.blue)

                                VStack(alignment: .leading) {
                                    Text(doc.title)
                                        .font(.title2)
                                        .fontWeight(.bold)

                                    HStack(spacing: 8) {
                                        Label(doc.docTypeDisplay, systemImage: doc.docTypeIcon)
                                            .font(.caption)
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(Color.blue.opacity(0.15))
                                            .cornerRadius(4)

                                        Text(doc.formatDisplay)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }

                                Spacer()

                                // AI Actions
                                if appState.isAIAvailable {
                                    Menu {
                                        Button {
                                            Task { await summarizeDoc() }
                                        } label: {
                                            Label("Summarize", systemImage: "text.quote")
                                        }
                                        .disabled(isAIProcessing)

                                        Button {
                                            Task { await extractEntities() }
                                        } label: {
                                            Label("Extract Entities", systemImage: "tag")
                                        }
                                        .disabled(isAIProcessing)

                                        Button {
                                            Task { await autoEnhance() }
                                        } label: {
                                            Label("Auto-Enhance", systemImage: "wand.and.stars")
                                        }
                                        .disabled(isAIProcessing)

                                        Divider()

                                        Button {
                                            showAIPanel.toggle()
                                        } label: {
                                            Label(showAIPanel ? "Hide AI Panel" : "Show AI Panel", systemImage: "brain")
                                        }
                                    } label: {
                                        Label(isAIProcessing ? "Processing..." : "AI", systemImage: "cpu")
                                    }
                                    .buttonStyle(.bordered)
                                }

                                Button(isEditing ? "Done" : "Edit") {
                                    if isEditing {
                                        Task {
                                            await saveChanges()
                                        }
                                    } else {
                                        editedContent = doc.content ?? ""
                                        editedAiContext = doc.aiContext ?? ""
                                        isEditing = true
                                    }
                                }
                                .buttonStyle(.bordered)
                            }

                            if !doc.description.isEmpty {
                                Text(doc.description)
                                    .foregroundStyle(.secondary)
                            }

                            if !doc.tags.isEmpty {
                                HStack {
                                    ForEach(doc.tags, id: \.self) { tag in
                                        Text(tag)
                                            .font(.caption)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.secondary.opacity(0.15))
                                            .cornerRadius(4)
                                    }
                                }
                            }

                            Divider()

                            // AI Panel (collapsible)
                            if showAIPanel {
                                VStack(alignment: .leading, spacing: 12) {
                                    HStack {
                                        Label("AI Analysis", systemImage: "cpu")
                                            .font(.headline)
                                        Spacer()
                                        Button {
                                            showAIPanel = false
                                        } label: {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundStyle(.secondary)
                                        }
                                        .buttonStyle(.plain)
                                    }

                                    if isAIProcessing {
                                        HStack {
                                            ProgressView()
                                            Text("Analyzing...")
                                        }
                                        .padding()
                                    }

                                    // Summary
                                    if let summary = aiSummary {
                                        VStack(alignment: .leading, spacing: 8) {
                                            Text("Summary")
                                                .font(.subheadline)
                                                .foregroundStyle(.secondary)
                                            Text(summary.summary)
                                                .padding(8)
                                                .background(Color.blue.opacity(0.1))
                                                .cornerRadius(6)

                                            if !summary.keyPoints.isEmpty {
                                                Text("Key Points")
                                                    .font(.subheadline)
                                                    .foregroundStyle(.secondary)
                                                ForEach(summary.keyPoints, id: \.self) { point in
                                                    HStack(alignment: .top) {
                                                        Image(systemName: "circle.fill")
                                                            .font(.system(size: 6))
                                                            .padding(.top, 6)
                                                        Text(point)
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    // Entities
                                    if let entities = aiEntities {
                                        VStack(alignment: .leading, spacing: 8) {
                                            if !entities.apis.isEmpty {
                                                EntitySection(title: "APIs", items: entities.apis, color: .blue)
                                            }
                                            if !entities.components.isEmpty {
                                                EntitySection(title: "Components", items: entities.components, color: .green)
                                            }
                                            if !entities.concepts.isEmpty {
                                                EntitySection(title: "Concepts", items: entities.concepts, color: .purple)
                                            }
                                            if !entities.suggestedTags.isEmpty {
                                                EntitySection(title: "Suggested Tags", items: entities.suggestedTags, color: .orange)
                                            }
                                        }
                                    }
                                }
                                .padding()
                                .background(Color.secondary.opacity(0.05))
                                .cornerRadius(8)

                                Divider()
                            }

                            // AI Context
                            if doc.aiContext != nil || isEditing {
                                VStack(alignment: .leading, spacing: 8) {
                                    Label("AI Context", systemImage: "brain")
                                        .font(.headline)

                                    if isEditing {
                                        TextEditor(text: $editedAiContext)
                                            .font(.system(.body, design: .monospaced))
                                            .frame(minHeight: 80)
                                            .padding(4)
                                            .background(Color.secondary.opacity(0.1))
                                            .cornerRadius(6)
                                    } else if let aiContext = doc.aiContext, !aiContext.isEmpty {
                                        Text(aiContext)
                                            .font(.system(.body, design: .monospaced))
                                            .padding()
                                            .background(Color.purple.opacity(0.1))
                                            .cornerRadius(8)
                                    }
                                }

                                Divider()
                            }

                            // Content
                            VStack(alignment: .leading, spacing: 8) {
                                Label("Content", systemImage: "doc.text")
                                    .font(.headline)

                                if isEditing {
                                    TextEditor(text: $editedContent)
                                        .font(.system(.body, design: .monospaced))
                                        .frame(minHeight: 300)
                                        .padding(4)
                                        .background(Color.secondary.opacity(0.1))
                                        .cornerRadius(6)
                                } else {
                                    Text(doc.content ?? "No content")
                                        .font(.system(.body, design: .monospaced))
                                        .textSelection(.enabled)
                                        .padding()
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .background(Color.secondary.opacity(0.1))
                                        .cornerRadius(8)
                                }
                            }

                            // Metadata
                            Divider()

                            VStack(alignment: .leading, spacing: 4) {
                                if let sourceFile = doc.sourceFile {
                                    HStack {
                                        Text("Source:")
                                            .foregroundStyle(.secondary)
                                        Text(sourceFile)
                                            .font(.system(.caption, design: .monospaced))
                                    }
                                }

                                HStack {
                                    Text("Created:")
                                        .foregroundStyle(.secondary)
                                    Text(doc.createdAt)
                                        .font(.caption)
                                }

                                HStack {
                                    Text("Updated:")
                                        .foregroundStyle(.secondary)
                                    Text(doc.updatedAt)
                                        .font(.caption)
                                }
                            }
                            .font(.caption)
                        }
                        .padding()
                    }
                } else {
                    VStack {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundStyle(.orange)
                        Text("Failed to load documentation")
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .navigationTitle(doc.title)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 600, minHeight: 500)
        .task {
            await loadFullDoc()
        }
    }

    private func loadFullDoc() async {
        isLoading = true
        defer { isLoading = false }

        fullDoc = await appState.getDoc(doc.id, projectPath: projectPath)
    }

    private func saveChanges() async {
        guard let fullDoc = fullDoc else { return }

        _ = await appState.updateDoc(
            docId: fullDoc.id,
            projectPath: projectPath,
            content: editedContent,
            aiContext: editedAiContext.isEmpty ? nil : editedAiContext
        )

        // Reload
        await loadFullDoc()
        isEditing = false
    }

    // MARK: - AI Methods

    private func summarizeDoc() async {
        guard let doc = fullDoc else { return }
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        aiSummary = await appState.summarizeDoc(doc.id, projectPath: projectPath)
    }

    private func extractEntities() async {
        guard let doc = fullDoc else { return }
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        aiEntities = await appState.extractDocEntities(doc.id, projectPath: projectPath)
    }

    private func autoEnhance() async {
        guard let doc = fullDoc else { return }
        isAIProcessing = true
        defer { isAIProcessing = false }

        _ = await appState.autoEnhanceDoc(doc.id, projectPath: projectPath)
        await loadFullDoc()
    }
}

// MARK: - Helper Views

struct EntitySection: View {
    let title: String
    let items: [String]
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            FlowLayout(spacing: 4) {
                ForEach(items, id: \.self) { item in
                    Text(item)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(color.opacity(0.15))
                        .cornerRadius(4)
                }
            }
        }
    }
}

// Simple flow layout for tags
struct FlowLayout: Layout {
    var spacing: CGFloat = 4

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = layout(in: proposal.replacingUnspecifiedDimensions().width, subviews: subviews)
        return CGSize(width: proposal.width ?? result.width, height: result.height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var lineHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)

            if x + size.width > bounds.maxX {
                x = bounds.minX
                y += lineHeight + spacing
                lineHeight = 0
            }

            subview.place(at: CGPoint(x: x, y: y), proposal: .unspecified)
            x += size.width + spacing
            lineHeight = max(lineHeight, size.height)
        }
    }

    private func layout(in width: CGFloat, subviews: Subviews) -> (width: CGFloat, height: CGFloat) {
        var x: CGFloat = 0
        var y: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxWidth: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)

            if x + size.width > width {
                x = 0
                y += lineHeight + spacing
                lineHeight = 0
            }

            x += size.width + spacing
            maxWidth = max(maxWidth, x)
            lineHeight = max(lineHeight, size.height)
        }

        return (maxWidth, y + lineHeight)
    }
}

#Preview {
    DocDetailView(
        doc: Documentation(
            id: "test-123",
            title: "API Documentation",
            docType: "api",
            docTypeDisplay: "API Documentation",
            docTypeIcon: "network",
            format: "markdown",
            formatDisplay: "Markdown",
            projectId: nil,
            description: "REST API endpoints documentation",
            tags: ["api", "rest"],
            aiContext: "Use this for understanding the API endpoints",
            createdAt: "2024-01-30T12:00:00",
            updatedAt: "2024-01-30T12:00:00",
            sourceFile: nil,
            content: "# API\n\n## Endpoints\n\n- GET /api/users"
        ),
        projectPath: nil
    )
    .environment(AppState())
}
