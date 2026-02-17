import SwiftUI

struct ToolBrowserView: View {
    @Environment(AppState.self) private var appState
    @State private var showFilters = false
    @State private var selectedTool: BrowsableTool?

    var body: some View {
        VStack(spacing: 0) {
            // Search and filter bar
            ToolSearchBar(
                searchText: Binding(
                    get: { appState.toolSearchQuery },
                    set: { appState.toolSearchQuery = $0 }
                ),
                showFilters: $showFilters,
                onSearch: {
                    Task {
                        await appState.searchBrowsableTools()
                    }
                },
                onRefresh: {
                    Task {
                        await appState.refreshToolCache()
                    }
                }
            )
            .padding()

            Divider()

            // Main content
            if appState.isLoadingBrowsableTools && appState.browsableTools.isEmpty {
                // Initial loading state
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Loading tools...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.browsableTools.isEmpty {
                // Empty state
                VStack(spacing: 16) {
                    Image(systemName: "wrench.and.screwdriver")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No tools found")
                        .font(.title2)
                    Text("Try adjusting your search or filters")
                        .foregroundStyle(.secondary)
                    Button("Clear Filters") {
                        appState.toolSearchQuery = ""
                        appState.selectedToolSources = Set(ToolSource.allCases)
                        appState.selectedToolCategories = []
                        appState.showInstalledToolsOnly = false
                        Task {
                            await appState.searchBrowsableTools()
                        }
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                // Results header
                HStack {
                    Text("Showing \(appState.browsableTools.count) of \(appState.toolsTotal) tools")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    if hasActiveFilters {
                        Button(action: clearFilters) {
                            Label("Clear Filters", systemImage: "xmark.circle")
                                .font(.caption)
                        }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)

                // Tool list
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(appState.browsableTools) { tool in
                            ToolCard(tool: tool) {
                                selectedTool = tool
                            } onInstall: {
                                Task {
                                    await appState.installBrowsableTool(tool.id)
                                }
                            }
                            .id(tool.id)
                        }

                        // Load more button
                        if appState.toolsHasMore {
                            Button {
                                Task {
                                    await appState.loadMoreBrowsableTools()
                                }
                            } label: {
                                if appState.isLoadingBrowsableTools {
                                    ProgressView()
                                        .frame(maxWidth: .infinity)
                                        .padding()
                                } else {
                                    Text("Load More")
                                        .frame(maxWidth: .infinity)
                                        .padding()
                                }
                            }
                            .buttonStyle(.bordered)
                            .disabled(appState.isLoadingBrowsableTools)
                        }
                    }
                    .padding()
                }
            }
        }
        .sheet(isPresented: $showFilters) {
            ToolFilterSheet()
        }
        .sheet(item: $selectedTool) { tool in
            ToolDetailSheet(tool: tool)
        }
        .task {
            // Initial load
            if appState.browsableTools.isEmpty {
                async let categories: Void = appState.loadToolCategories()
                async let sources: Void = appState.loadToolSources()
                async let search: Void = appState.searchBrowsableTools()
                _ = await (categories, sources, search)
            }
        }
        .accessibilityIdentifier("toolBrowserView")
    }

    private var hasActiveFilters: Bool {
        !appState.toolSearchQuery.isEmpty ||
        appState.selectedToolSources.count < ToolSource.allCases.count ||
        !appState.selectedToolCategories.isEmpty ||
        appState.showInstalledToolsOnly
    }

    private func clearFilters() {
        appState.toolSearchQuery = ""
        appState.selectedToolSources = Set(ToolSource.allCases)
        appState.selectedToolCategories = []
        appState.showInstalledToolsOnly = false
        Task {
            await appState.searchBrowsableTools()
        }
    }
}

#Preview {
    ToolBrowserView()
        .environment(AppState())
        .frame(width: 800, height: 600)
}
