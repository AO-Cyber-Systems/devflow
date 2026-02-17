import SwiftUI

struct CodeSearchView: View {
    @Environment(AppState.self) private var appState
    let projectPath: String?

    @State private var selectedResult: CodeSearchResult?
    @State private var showScanSheet = false
    @State private var selectedProjectPath: String?

    // Computed property for effective project path
    private var effectiveProjectPath: String? {
        projectPath ?? selectedProjectPath
    }

    var body: some View {
        VStack(spacing: 0) {
            // Search and scan bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search code...", text: Binding(
                    get: { appState.codeSearchQuery },
                    set: { appState.codeSearchQuery = $0 }
                ))
                .textFieldStyle(.plain)
                .accessibilityIdentifier("codeSearchField")
                .onSubmit {
                    Task {
                        await appState.searchCode(query: appState.codeSearchQuery, projectPath: effectiveProjectPath)
                    }
                }

                if !appState.codeSearchQuery.isEmpty {
                    Button {
                        appState.codeSearchQuery = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Divider()
                    .frame(height: 20)
                    .padding(.horizontal, 8)

                // Project picker (when not in project context)
                if projectPath == nil {
                    Picker("Project", selection: $selectedProjectPath) {
                        Text("Select Project").tag(nil as String?)
                        ForEach(appState.projects) { project in
                            Text(project.name)
                                .tag(project.path as String?)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 180)
                    .onChange(of: selectedProjectPath) { _, newPath in
                        if let path = newPath {
                            Task {
                                await appState.getCodeScanStatus(projectPath: path)
                            }
                        }
                    }
                }

                // Scan status indicator
                if let status = appState.codeScanStatus {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(status.indexed ? Color.green : Color.orange)
                            .frame(width: 8, height: 8)
                        Text(status.indexed ? "\(status.entityCount ?? 0) entities" : "Not indexed")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                // AI Status
                if appState.isAIAvailable {
                    AIStatusButton()
                }

                Button {
                    showScanSheet = true
                } label: {
                    Label("Scan", systemImage: "doc.text.magnifyingglass")
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("codeScanButton")
            }
            .padding()

            Divider()

            // Main content
            if appState.isLoadingCode || appState.isScanningCode {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text(appState.isScanningCode ? "Scanning code..." : "Searching...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.codeSearchResults.isEmpty {
                VStack(spacing: 16) {
                    if let status = appState.codeScanStatus, status.indexed, let entityCount = status.entityCount, entityCount > 0 {
                        // Indexed but no search yet
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 48))
                            .foregroundStyle(.blue)
                        Text("\(entityCount) entities indexed")
                            .font(.title2)
                        Text("Enter a search term above to find code")
                            .foregroundStyle(.secondary)

                        HStack(spacing: 12) {
                            Button("Search Functions") {
                                appState.codeSearchQuery = "function"
                                Task {
                                    await appState.searchCode(query: "function", projectPath: effectiveProjectPath)
                                }
                            }
                            .buttonStyle(.bordered)

                            Button("Search Classes") {
                                appState.codeSearchQuery = "class"
                                Task {
                                    await appState.searchCode(query: "class", projectPath: effectiveProjectPath)
                                }
                            }
                            .buttonStyle(.bordered)

                            Button("Show All") {
                                appState.codeSearchQuery = ""
                                Task {
                                    if let path = effectiveProjectPath {
                                        await appState.listCodeEntities(projectPath: path)
                                    }
                                }
                            }
                            .buttonStyle(.borderedProminent)
                        }
                    } else {
                        // Not indexed
                        Image(systemName: "chevron.left.forwardslash.chevron.right")
                            .font(.system(size: 48))
                            .foregroundStyle(.secondary)
                        Text("No code indexed yet")
                            .font(.title2)

                        if let path = effectiveProjectPath {
                            Text("Scan the project to index its code")
                                .foregroundStyle(.secondary)
                            Button("Scan Project") {
                                Task {
                                    await appState.scanCode(projectPath: path)
                                }
                            }
                            .buttonStyle(.borderedProminent)
                        } else {
                            Text("Select a project above to scan and search code")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(selection: $selectedResult) {
                    ForEach(appState.codeSearchResults) { result in
                        CodeSearchResultRow(result: result)
                            .tag(result)
                    }
                }
                .listStyle(.inset)
            }
        }
        .sheet(isPresented: $showScanSheet) {
            CodeScanSheet(projectPath: effectiveProjectPath)
        }
        .sheet(item: $selectedResult) { result in
            CodeEntityDetailSheet(result: result, projectPath: effectiveProjectPath)
        }
        .accessibilityIdentifier("codeSearchView")
        .task {
            // Load projects if not already loaded
            if appState.projects.isEmpty {
                await appState.loadProjects()
            }
            // Check scan status if we have a project path
            if let path = effectiveProjectPath {
                await appState.getCodeScanStatus(projectPath: path)
            }
            await appState.loadCodeEntityTypes()
        }
    }
}

struct CodeSearchResultRow: View {
    let result: CodeSearchResult

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: iconForEntityType(result.entityType))
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(result.name)
                    .font(.headline)

                HStack(spacing: 8) {
                    Text(result.entityType.capitalized)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.15))
                        .cornerRadius(4)

                    Text(result.language)
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    if let similarity = result.similarity {
                        Text(String(format: "%.0f%%", similarity * 100))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                Text(result.filePath)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .lineLimit(1)
            }

            Spacer()

            Text(":\(result.lineStart)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }

    func iconForEntityType(_ type: String) -> String {
        switch type {
        case "function": return "function"
        case "method": return "m.square"
        case "class": return "c.square"
        case "module": return "folder"
        case "import": return "arrow.down.square"
        default: return "doc.text"
        }
    }
}

struct CodeScanSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    let projectPath: String?

    @State private var scanLanguages: Set<String> = []
    @State private var isScanning = false
    @State private var scanResult: ScanResult?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Scan Code")
                    .font(.headline)
                Spacer()
                Button("Done") {
                    dismiss()
                }
            }
            .padding()

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    if let path = projectPath {
                        // Project path
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Project")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Text(path)
                                .font(.system(.body, design: .monospaced))
                        }

                        // Supported languages
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Languages")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Text("All supported languages will be scanned")
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                        }

                        // Scan button
                        if isScanning {
                            HStack {
                                ProgressView()
                                Text("Scanning...")
                            }
                        } else {
                            Button {
                                Task {
                                    isScanning = true
                                    scanResult = await appState.scanCode(projectPath: path)
                                    isScanning = false
                                }
                            } label: {
                                Label("Start Scan", systemImage: "play.fill")
                            }
                            .buttonStyle(.borderedProminent)
                        }

                        // Scan result
                        if let result = scanResult {
                            VStack(alignment: .leading, spacing: 12) {
                                Text("Scan Complete")
                                    .font(.headline)
                                    .foregroundStyle(.green)

                                Grid(alignment: .leading, horizontalSpacing: 20, verticalSpacing: 8) {
                                    GridRow {
                                        Text("Files Scanned:")
                                            .foregroundStyle(.secondary)
                                        Text("\(result.filesScanned)")
                                    }
                                    GridRow {
                                        Text("Entities Found:")
                                            .foregroundStyle(.secondary)
                                        Text("\(result.entityCount)")
                                    }
                                    GridRow {
                                        Text("Scan Time:")
                                            .foregroundStyle(.secondary)
                                        Text("\(result.scanTimeMs)ms")
                                    }
                                }

                                if !result.languages.isEmpty {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Languages:")
                                            .foregroundStyle(.secondary)
                                        ForEach(Array(result.languages.keys.sorted()), id: \.self) { lang in
                                            HStack {
                                                Text(lang.capitalized)
                                                Spacer()
                                                Text("\(result.languages[lang] ?? 0) entities")
                                                    .foregroundStyle(.secondary)
                                            }
                                            .font(.caption)
                                        }
                                    }
                                }
                            }
                            .padding()
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(8)
                        }
                    } else {
                        Text("Select a project to scan its code")
                            .foregroundStyle(.secondary)
                    }
                }
                .padding()
            }
        }
        .frame(width: 500, height: 500)
    }
}

struct CodeEntityDetailSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    let result: CodeSearchResult
    let projectPath: String?

    @State private var callers: [CodeEntity] = []
    @State private var callees: [CodeEntity] = []
    @State private var isLoadingRelationships = false

    // AI State
    @State private var showAIPanel = false
    @State private var aiExplanation: CodeExplanation?
    @State private var aiDocstring: String?
    @State private var aiImprovements: [String] = []
    @State private var similarCode: [SimilarCodeResult] = []
    @State private var isAIProcessing = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading) {
                    Text(result.name)
                        .font(.headline)
                    Text(result.qualifiedName)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()

                // AI Actions
                if appState.isAIAvailable, let path = projectPath {
                    Menu {
                        Button {
                            Task { await explainCode(path) }
                        } label: {
                            Label("Explain Code", systemImage: "lightbulb")
                        }
                        .disabled(isAIProcessing)

                        Button {
                            Task { await generateDocstring(path) }
                        } label: {
                            Label("Generate Docstring", systemImage: "doc.text")
                        }
                        .disabled(isAIProcessing)

                        Button {
                            Task { await suggestImprovements(path) }
                        } label: {
                            Label("Suggest Improvements", systemImage: "wand.and.stars")
                        }
                        .disabled(isAIProcessing)

                        Button {
                            Task { await findSimilar(path) }
                        } label: {
                            Label("Find Similar Code", systemImage: "doc.on.doc")
                        }
                        .disabled(isAIProcessing)

                        Divider()

                        Button {
                            showAIPanel.toggle()
                        } label: {
                            Label(showAIPanel ? "Hide AI Panel" : "Show AI Panel", systemImage: "cpu")
                        }
                    } label: {
                        Label(isAIProcessing ? "Processing..." : "AI", systemImage: "cpu")
                    }
                    .buttonStyle(.bordered)
                }

                Button("Done") {
                    dismiss()
                }
            }
            .padding()

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Basic info
                    Grid(alignment: .leading, horizontalSpacing: 20, verticalSpacing: 8) {
                        GridRow {
                            Text("Type:")
                                .foregroundStyle(.secondary)
                            Text(result.entityType.capitalized)
                        }
                        GridRow {
                            Text("Language:")
                                .foregroundStyle(.secondary)
                            Text(result.language.capitalized)
                        }
                        GridRow {
                            Text("File:")
                                .foregroundStyle(.secondary)
                            Text(result.filePath)
                                .font(.system(.body, design: .monospaced))
                        }
                        GridRow {
                            Text("Line:")
                                .foregroundStyle(.secondary)
                            Text("\(result.lineStart)")
                        }
                    }

                    // Docstring
                    if let docstring = result.docstring, !docstring.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Documentation")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Text(docstring)
                                .font(.system(.body, design: .default))
                                .padding()
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.secondary.opacity(0.1))
                                .cornerRadius(8)
                        }
                    }

                    // AI Panel
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

                            // Explanation
                            if let explanation = aiExplanation {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Explanation")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    Text(explanation.summary)
                                        .padding(8)
                                        .background(Color.blue.opacity(0.1))
                                        .cornerRadius(6)

                                    if !explanation.algorithmSteps.isEmpty {
                                        Text("Algorithm Steps")
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                        ForEach(Array(explanation.algorithmSteps.enumerated()), id: \.offset) { index, step in
                                            HStack(alignment: .top) {
                                                Text("\(index + 1).")
                                                    .font(.caption)
                                                    .foregroundStyle(.secondary)
                                                Text(step)
                                            }
                                        }
                                    }
                                }
                            }

                            // Generated Docstring
                            if let docstring = aiDocstring {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Generated Docstring")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    Text(docstring)
                                        .font(.system(.body, design: .monospaced))
                                        .padding(8)
                                        .background(Color.green.opacity(0.1))
                                        .cornerRadius(6)
                                        .textSelection(.enabled)
                                }
                            }

                            // Improvements
                            if !aiImprovements.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Suggested Improvements")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    ForEach(aiImprovements, id: \.self) { improvement in
                                        HStack(alignment: .top) {
                                            Image(systemName: "lightbulb")
                                                .foregroundStyle(.orange)
                                            Text(improvement)
                                        }
                                    }
                                }
                            }

                            // Similar Code
                            if !similarCode.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Similar Code")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    ForEach(similarCode) { similar in
                                        HStack {
                                            Text(similar.entityName)
                                                .font(.system(.caption, design: .monospaced))
                                            Spacer()
                                            Text(String(format: "%.0f%%", similar.similarity * 100))
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                        }
                                    }
                                }
                            }
                        }
                        .padding()
                        .background(Color.secondary.opacity(0.05))
                        .cornerRadius(8)

                        Divider()
                    }

                    // Relationships
                    if isLoadingRelationships {
                        HStack {
                            ProgressView()
                            Text("Loading relationships...")
                        }
                    } else {
                        // Callers
                        if !callers.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Called By (\(callers.count))")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                ForEach(callers) { caller in
                                    HStack {
                                        Image(systemName: "arrow.left")
                                            .foregroundStyle(.blue)
                                        Text(caller.qualifiedName)
                                            .font(.system(.caption, design: .monospaced))
                                    }
                                }
                            }
                        }

                        // Callees
                        if !callees.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Calls (\(callees.count))")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                ForEach(callees) { callee in
                                    HStack {
                                        Image(systemName: "arrow.right")
                                            .foregroundStyle(.green)
                                        Text(callee.qualifiedName)
                                            .font(.system(.caption, design: .monospaced))
                                    }
                                }
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .frame(width: 600, height: 600)
        .task {
            isLoadingRelationships = true
            async let callersTask = appState.getCallers(entityId: result.entityId, projectPath: projectPath)
            async let calleesTask = appState.getCallees(entityId: result.entityId, projectPath: projectPath)
            callers = await callersTask
            callees = await calleesTask
            isLoadingRelationships = false
        }
    }

    // MARK: - AI Methods

    private func explainCode(_ path: String) async {
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        aiExplanation = await appState.explainCodeEntity(result.entityId, projectPath: path)
    }

    private func generateDocstring(_ path: String) async {
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        aiDocstring = await appState.generateEntityDocstring(result.entityId, projectPath: path)
    }

    private func suggestImprovements(_ path: String) async {
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        aiImprovements = await appState.suggestEntityImprovements(result.entityId, projectPath: path)
    }

    private func findSimilar(_ path: String) async {
        isAIProcessing = true
        showAIPanel = true
        defer { isAIProcessing = false }

        similarCode = await appState.findSimilarCode(result.entityId, projectPath: path)
    }
}

#Preview {
    CodeSearchView(projectPath: nil)
        .environment(AppState())
        .frame(width: 800, height: 600)
}
