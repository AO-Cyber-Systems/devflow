import SwiftUI

struct LogViewerView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        HSplitView {
            // Container list sidebar
            ContainerListView()
                .frame(minWidth: 180, idealWidth: 220, maxWidth: 280)
                .accessibilityIdentifier("containerList")

            // Main log content
            VStack(spacing: 0) {
                // Toolbar
                LogToolbarView()

                Divider()

                // Log content
                LogContentView()
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("logViewerView")
        .task {
            await appState.logsManager.loadContainers()
        }
    }
}

// MARK: - Container List

struct ContainerListView: View {
    @Environment(AppState.self) private var appState

    var logsManager: LogsState {
        appState.logsManager
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Text("Containers")
                    .font(.headline)
                Spacer()
                if logsManager.isLoadingContainers {
                    ProgressView()
                        .scaleEffect(0.6)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)

            Divider()

            // Container list
            if logsManager.containers.isEmpty && !logsManager.isLoadingContainers {
                VStack(spacing: 8) {
                    Image(systemName: "shippingbox")
                        .font(.largeTitle)
                        .foregroundStyle(.secondary)
                    Text("No containers running")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(selection: Binding(
                    get: { logsManager.selectedContainer?.id },
                    set: { id in
                        if let container = logsManager.containers.first(where: { $0.id == id }) {
                            Task { await logsManager.selectContainer(container) }
                        }
                    }
                )) {
                    // Quick access: Traefik
                    Section("Infrastructure") {
                        Button {
                            Task { await logsManager.loadTraefikLogs() }
                        } label: {
                            Label("Traefik", systemImage: "arrow.triangle.branch")
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("traefikLogsButton")
                    }

                    Section("Containers") {
                        ForEach(logsManager.containers) { container in
                            ContainerRowView(container: container)
                                .tag(container.id)
                        }
                    }
                }
                .listStyle(.sidebar)
            }
        }
        .background(Color(nsColor: .controlBackgroundColor))
    }
}

struct ContainerRowView: View {
    let container: ContainerInfo

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(container.isRunning ? Color.green : Color.gray)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(container.name)
                    .font(.system(.body, design: .monospaced))
                    .lineLimit(1)
                Text(container.image)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Log Toolbar

struct LogToolbarView: View {
    @Environment(AppState.self) private var appState

    var logsManager: LogsState {
        appState.logsManager
    }

    var body: some View {
        HStack(spacing: 12) {
            // Search field
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Filter logs...", text: Binding(
                    get: { logsManager.filterText },
                    set: { logsManager.filterText = $0 }
                ))
                .textFieldStyle(.plain)
                .accessibilityIdentifier("logSearchField")

                if !logsManager.filterText.isEmpty {
                    Button {
                        logsManager.filterText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(8)
            .frame(maxWidth: 300)

            // Level filter
            Picker("Level", selection: Binding(
                get: { logsManager.minimumLogLevel },
                set: { logsManager.minimumLogLevel = $0 }
            )) {
                ForEach(LogLevel.allCases, id: \.self) { level in
                    Text(level.rawValue.capitalized).tag(level)
                }
            }
            .pickerStyle(.menu)
            .frame(width: 100)
            .accessibilityIdentifier("logLevelPicker")

            Spacer()

            // Stats
            if logsManager.errorCount > 0 {
                HStack(spacing: 4) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.red)
                    Text("\(logsManager.errorCount)")
                        .foregroundStyle(.red)
                }
            }

            if logsManager.warningCount > 0 {
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text("\(logsManager.warningCount)")
                        .foregroundStyle(.orange)
                }
            }

            // Auto-refresh toggle
            Toggle(isOn: Binding(
                get: { logsManager.autoRefresh },
                set: { newValue in
                    if newValue {
                        logsManager.startAutoRefresh()
                    } else {
                        logsManager.stopAutoRefresh()
                    }
                }
            )) {
                Label("Auto", systemImage: "arrow.clockwise")
            }
            .toggleStyle(.button)
            .accessibilityIdentifier("autoRefreshToggle")

            // Refresh button
            Button {
                Task { await logsManager.refresh() }
            } label: {
                if logsManager.isLoadingLogs {
                    ProgressView()
                        .scaleEffect(0.7)
                } else {
                    Image(systemName: "arrow.clockwise")
                }
            }
            .disabled(logsManager.isLoadingLogs)
            .accessibilityIdentifier("refreshLogsButton")

            // Clear filter
            Button {
                logsManager.clearFilter()
            } label: {
                Image(systemName: "line.3.horizontal.decrease.circle")
            }
            .help("Clear filters")
            .accessibilityIdentifier("clearFilterButton")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }
}

// MARK: - Log Content

struct LogContentView: View {
    @Environment(AppState.self) private var appState

    var logsManager: LogsState {
        appState.logsManager
    }

    var body: some View {
        Group {
            if logsManager.selectedContainer == nil && logsManager.logs.isEmpty {
                // Empty state
                VStack(spacing: 12) {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("Select a container to view logs")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if logsManager.isLoadingLogs && logsManager.logs.isEmpty {
                // Loading state
                VStack(spacing: 12) {
                    ProgressView()
                    Text("Loading logs...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if logsManager.filteredLogs.isEmpty {
                // No results
                VStack(spacing: 12) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No logs match your filter")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                    Button("Clear Filter") {
                        logsManager.clearFilter()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                // Log entries
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 0) {
                            ForEach(logsManager.filteredLogs) { entry in
                                LogEntryRow(entry: entry)
                                    .id(entry.id)
                            }
                        }
                        .padding(.vertical, 8)
                    }
                    .onChange(of: logsManager.logs.count) { _, _ in
                        // Auto-scroll to bottom on new logs
                        if let lastEntry = logsManager.filteredLogs.last {
                            withAnimation {
                                proxy.scrollTo(lastEntry.id, anchor: .bottom)
                            }
                        }
                    }
                }
            }
        }
        .background(Color(nsColor: .textBackgroundColor))
    }
}

// MARK: - Log Entry Row

struct LogEntryRow: View {
    let entry: LogEntry
    @State private var isHovered = false

    var levelColor: Color {
        switch entry.level {
        case .debug: return .gray
        case .info: return .blue
        case .warning: return .orange
        case .error: return .red
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            // Timestamp
            Text(entry.timestampFormatted)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)
                .frame(width: 90, alignment: .leading)

            // Level indicator
            Circle()
                .fill(levelColor)
                .frame(width: 8, height: 8)
                .padding(.top, 4)

            // Source
            Text(entry.source)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)
                .frame(width: 120, alignment: .leading)
                .lineLimit(1)

            // Message
            Text(entry.message)
                .font(.system(.body, design: .monospaced))
                .foregroundStyle(entry.level == .error ? .red : .primary)
                .textSelection(.enabled)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 4)
        .background(isHovered ? Color(nsColor: .selectedContentBackgroundColor).opacity(0.3) : Color.clear)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

#Preview {
    LogViewerView()
        .environment(AppState())
        .frame(width: 1000, height: 600)
}
