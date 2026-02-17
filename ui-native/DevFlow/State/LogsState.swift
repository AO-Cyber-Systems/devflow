import Foundation

/// Manages container log viewing and filtering.
@Observable
@MainActor
class LogsState {
    // MARK: - State

    var containers: [ContainerInfo] = []
    var selectedContainer: ContainerInfo?
    var logs: [LogEntry] = []
    var isLoadingContainers = false
    var isLoadingLogs = false
    var autoRefresh = false
    var filterText = ""
    var minimumLogLevel: LogLevel = .debug

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState
    @ObservationIgnored private var refreshTask: Task<Void, Never>?

    // MARK: - Computed Properties

    var filteredLogs: [LogEntry] {
        logs.filter { entry in
            // Filter by level
            guard entry.level.severity >= minimumLogLevel.severity else { return false }

            // Filter by text
            if !filterText.isEmpty {
                let searchText = filterText.lowercased()
                return entry.message.lowercased().contains(searchText)
                    || entry.source.lowercased().contains(searchText)
            }

            return true
        }
    }

    var errorCount: Int {
        logs.filter { $0.level == .error }.count
    }

    var warningCount: Int {
        logs.filter { $0.level == .warning }.count
    }

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Container Actions

    func loadContainers() async {
        isLoadingContainers = true
        defer { isLoadingContainers = false }

        do {
            let response: ContainersListResponse = try await bridge.call("logs.list_containers")
            containers = response.containers

            if let error = response.error {
                notifications.add(.error("Failed to list containers: \(error)"))
            }

            // Auto-select first container if none selected
            if selectedContainer == nil, let first = containers.first {
                await selectContainer(first)
            }
        } catch {
            notifications.add(.error("Failed to list containers: \(error.localizedDescription)"))
        }
    }

    func selectContainer(_ container: ContainerInfo?) async {
        selectedContainer = container
        logs = []

        if container != nil {
            await loadLogs()
        }
    }

    // MARK: - Log Actions

    func loadLogs(lines: Int = 200) async {
        guard let container = selectedContainer else { return }

        isLoadingLogs = true
        defer { isLoadingLogs = false }

        do {
            let response: LogsResponse = try await bridge.call(
                "logs.get_logs",
                params: [
                    "container": container.name,
                    "lines": lines,
                    "timestamps": true
                ]
            )
            logs = response.logs

            if let error = response.error {
                notifications.add(.error("Failed to get logs: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to get logs: \(error.localizedDescription)"))
        }
    }

    func loadTraefikLogs(lines: Int = 200) async {
        isLoadingLogs = true
        defer { isLoadingLogs = false }

        do {
            let response: LogsResponse = try await bridge.call(
                "logs.get_traefik_logs",
                params: ["lines": lines]
            )
            logs = response.logs

            if let error = response.error {
                notifications.add(.warning("Traefik logs: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to get Traefik logs: \(error.localizedDescription)"))
        }
    }

    func refresh() async {
        await loadContainers()
        if selectedContainer != nil {
            await loadLogs()
        }
    }

    // MARK: - Auto Refresh

    func startAutoRefresh(interval: TimeInterval = 5) {
        autoRefresh = true
        refreshTask = Task {
            while !Task.isCancelled && autoRefresh {
                try? await Task.sleep(for: .seconds(interval))
                guard !Task.isCancelled && autoRefresh else { break }
                await loadLogs()
            }
        }
    }

    func stopAutoRefresh() {
        autoRefresh = false
        refreshTask?.cancel()
        refreshTask = nil
    }

    // MARK: - Filtering

    func clearFilter() {
        filterText = ""
        minimumLogLevel = .debug
    }
}
