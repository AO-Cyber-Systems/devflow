import SwiftUI

struct ToolFilterSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    var body: some View {
        NavigationStack {
            Form {
                // Sources section
                Section("Sources") {
                    ForEach(ToolSource.allCases, id: \.self) { source in
                        Toggle(isOn: Binding(
                            get: { appState.selectedToolSources.contains(source) },
                            set: { isSelected in
                                if isSelected {
                                    appState.selectedToolSources.insert(source)
                                } else {
                                    appState.selectedToolSources.remove(source)
                                }
                            }
                        )) {
                            HStack {
                                Image(systemName: source.icon)
                                    .frame(width: 20)
                                Text(source.displayName)
                                Spacer()
                                Text("\(sourceCount(for: source))")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }

                // Categories section
                Section("Categories") {
                    ForEach(appState.toolCategories) { category in
                        Toggle(isOn: Binding(
                            get: {
                                guard let cat = ToolBrowserCategory(rawValue: category.categoryId) else { return false }
                                return appState.selectedToolCategories.contains(cat)
                            },
                            set: { isSelected in
                                guard let cat = ToolBrowserCategory(rawValue: category.categoryId) else { return }
                                if isSelected {
                                    appState.selectedToolCategories.insert(cat)
                                } else {
                                    appState.selectedToolCategories.remove(cat)
                                }
                            }
                        )) {
                            HStack {
                                Image(systemName: category.icon)
                                    .frame(width: 20)
                                Text(category.name)
                                Spacer()
                                Text("\(category.count)")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }

                // Install status section
                Section("Status") {
                    Toggle(isOn: Binding(
                        get: { appState.showInstalledToolsOnly },
                        set: { appState.showInstalledToolsOnly = $0 }
                    )) {
                        Label("Installed Only", systemImage: "checkmark.circle")
                    }
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Filter Tools")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Reset") {
                        resetFilters()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Apply") {
                        applyFilters()
                    }
                    .keyboardShortcut(.defaultAction)
                }
            }
        }
        .frame(minWidth: 400, minHeight: 500)
    }

    private func sourceCount(for source: ToolSource) -> Int {
        appState.toolSources.first { $0.sourceId == source.rawValue }?.count ?? 0
    }

    private func resetFilters() {
        appState.selectedToolSources = Set(ToolSource.allCases)
        appState.selectedToolCategories = []
        appState.showInstalledToolsOnly = false
    }

    private func applyFilters() {
        dismiss()
        Task {
            await appState.searchBrowsableTools()
        }
    }
}

#Preview {
    ToolFilterSheet()
        .environment(AppState())
}
