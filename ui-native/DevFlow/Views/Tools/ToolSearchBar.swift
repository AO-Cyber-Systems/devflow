import SwiftUI

struct ToolSearchBar: View {
    @Binding var searchText: String
    @Binding var showFilters: Bool
    var onSearch: () -> Void
    var onRefresh: () -> Void

    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(spacing: 10) {
            HStack(spacing: 12) {
                // Search field
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search tools...", text: $searchText)
                        .textFieldStyle(.plain)
                        .accessibilityIdentifier("toolSearchField")
                        .onSubmit {
                            onSearch()
                        }
                    if !searchText.isEmpty {
                        Button {
                            searchText = ""
                            onSearch()
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(8)
                .background(Color(.textBackgroundColor))
                .cornerRadius(8)

                // Filter button with badge
                Button {
                    showFilters = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "line.3.horizontal.decrease.circle")
                        Text("Filters")
                        if filterCount > 0 {
                            Text("\(filterCount)")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.accentColor)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                    }
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("toolCategoryFilter")

                // Refresh button
                Button {
                    onRefresh()
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("refreshToolCacheButton")
                .disabled(appState.isLoadingBrowsableTools)
                .help("Refresh tool cache")
            }

            // Quick source filters
            HStack(spacing: 8) {
                ForEach(ToolSource.allCases, id: \.self) { source in
                    SourceFilterChip(
                        source: source,
                        count: sourceCount(for: source),
                        isSelected: appState.selectedToolSources.contains(source)
                    ) {
                        toggleSource(source)
                    }
                }

                Spacer()

                // Installed only toggle
                Toggle(isOn: Binding(
                    get: { appState.showInstalledToolsOnly },
                    set: { newValue in
                        appState.showInstalledToolsOnly = newValue
                        onSearch()
                    }
                )) {
                    Label("Installed", systemImage: "checkmark.circle")
                        .font(.caption)
                }
                .toggleStyle(.button)
                .buttonStyle(.bordered)
                .tint(appState.showInstalledToolsOnly ? .green : nil)
            }
            .accessibilityIdentifier("toolSourceFilter")
        }
    }

    private func sourceCount(for source: ToolSource) -> Int {
        appState.toolSources.first { $0.sourceId == source.rawValue }?.count ?? 0
    }

    private func toggleSource(_ source: ToolSource) {
        if appState.selectedToolSources.contains(source) {
            // Don't allow deselecting all sources
            if appState.selectedToolSources.count > 1 {
                appState.selectedToolSources.remove(source)
            }
        } else {
            appState.selectedToolSources.insert(source)
        }
        onSearch()
    }

    private var filterCount: Int {
        var count = 0
        if !appState.selectedToolCategories.isEmpty {
            count += 1
        }
        return count
    }
}

struct SourceFilterChip: View {
    let source: ToolSource
    let count: Int
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 4) {
                Image(systemName: source.icon)
                    .font(.caption)
                Text(source.displayName)
                    .font(.caption)
                Text("(\(formatCount(count)))")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(isSelected ? sourceColor.opacity(0.15) : Color.secondary.opacity(0.1))
            .foregroundStyle(isSelected ? sourceColor : .secondary)
            .cornerRadius(16)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .strokeBorder(isSelected ? sourceColor.opacity(0.5) : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    private var sourceColor: Color {
        switch source {
        case .mise: return .orange
        case .homebrew: return .brown
        case .cask: return .blue
        }
    }

    private func formatCount(_ count: Int) -> String {
        if count >= 1000 {
            return String(format: "%.1fK", Double(count) / 1000)
        }
        return "\(count)"
    }
}

#Preview {
    ToolSearchBar(
        searchText: .constant(""),
        showFilters: .constant(false),
        onSearch: {},
        onRefresh: {}
    )
    .environment(AppState())
    .padding()
}
