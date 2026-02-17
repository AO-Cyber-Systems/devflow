import Foundation

/// Manages the tool browser - searching, filtering, and installing tools.
@Observable
@MainActor
class ToolBrowserState {
    // MARK: - State

    var browsableTools: [BrowsableTool] = []
    var toolCategories: [ToolCategoryInfo] = []
    var toolSources: [ToolSourceInfo] = []
    var searchQuery: String = ""
    var selectedSources: Set<ToolSource> = Set(ToolSource.allCases)
    var selectedCategories: Set<ToolBrowserCategory> = []
    var showInstalledOnly: Bool = false
    var isLoading = false
    var total: Int = 0
    var hasMore: Bool = false
    var offset: Int = 0
    var installingToolIds: Set<String> = []

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Search Actions

    func search(reset: Bool = true) async {
        if reset {
            offset = 0
            browsableTools = []
        }

        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = [
                "query": searchQuery,
                "limit": 50,
                "offset": offset,
                "installed_only": showInstalledOnly
            ]

            // Add source filter if not all selected
            if selectedSources.count < ToolSource.allCases.count {
                params["sources"] = selectedSources.map { $0.rawValue }
            }

            // Add category filter if any selected
            if !selectedCategories.isEmpty {
                params["categories"] = selectedCategories.map { $0.rawValue }
            }

            let response: ToolBrowserSearchResponse = try await bridge.call("tools.search", params: params)
            if reset {
                browsableTools = response.tools
            } else {
                browsableTools.append(contentsOf: response.tools)
            }
            total = response.total
            hasMore = response.hasMore
            offset = response.offset + response.limit
        } catch {
            notifications.add(.error("Failed to search tools: \(error.localizedDescription)"))
        }
    }

    func loadMore() async {
        guard hasMore && !isLoading else { return }
        await search(reset: false)
    }

    func loadCategories() async {
        do {
            let response: ToolBrowserCategoriesResponse = try await bridge.call("tools.get_categories")
            toolCategories = response.categories
        } catch {
            // Ignore - categories will be empty
        }
    }

    func loadSources() async {
        do {
            let response: ToolBrowserSourcesResponse = try await bridge.call("tools.get_sources")
            toolSources = response.sources
        } catch {
            // Ignore - sources will be empty
        }
    }

    func refreshCache(force: Bool = true) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response: ToolBrowserRefreshCacheResponse = try await bridge.call(
                "tools.refresh_cache",
                params: ["force": force]
            )
            if response.success, let total = response.total {
                notifications.add(.success("Loaded \(total) tools"))
                // Reload categories and sources
                await loadCategories()
                await loadSources()
                // Re-run search
                await search()
            } else if let error = response.error {
                notifications.add(.error("Failed to refresh: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to refresh tool cache: \(error.localizedDescription)"))
        }
    }

    func install(_ toolId: String) async {
        installingToolIds.insert(toolId)
        defer { installingToolIds.remove(toolId) }

        do {
            let response: ToolBrowserInstallResponse = try await bridge.call(
                "tools.install",
                params: ["tool_id": toolId]
            )
            if response.success {
                notifications.add(.success(response.message ?? "Tool installed"))
                // Update the tool in the list
                if let index = browsableTools.firstIndex(where: { $0.id == toolId }) {
                    browsableTools[index].isInstalled = true
                }
            } else if let error = response.error {
                notifications.add(.error("Install failed: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to install tool: \(error.localizedDescription)"))
        }
    }

    func detectInstalled(_ toolIds: [String]) async {
        do {
            let response: ToolBrowserInstalledCheckResponse = try await bridge.call(
                "tools.detect_installed",
                params: ["tool_ids": toolIds]
            )
            // Update install status in the tools list
            for (toolId, isInstalled) in response.installed {
                if let index = browsableTools.firstIndex(where: { $0.id == toolId }) {
                    browsableTools[index].isInstalled = isInstalled
                }
            }
        } catch {
            // Ignore - detection is best-effort
        }
    }

    func clearFilters() {
        searchQuery = ""
        selectedSources = Set(ToolSource.allCases)
        selectedCategories = []
        showInstalledOnly = false
    }

    var hasActiveFilters: Bool {
        !searchQuery.isEmpty ||
        selectedSources.count < ToolSource.allCases.count ||
        !selectedCategories.isEmpty ||
        showInstalledOnly
    }
}
