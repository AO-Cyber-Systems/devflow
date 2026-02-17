import Foundation

/// Manages databases - listing, creating, deleting, starting, and stopping.
@Observable
@MainActor
class DatabaseState {
    // MARK: - State

    var databases: [Database] = []
    var isLoadingDatabases = false
    var showAddDatabase = false

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - Actions

    func load() async {
        isLoadingDatabases = true
        defer { isLoadingDatabases = false }

        // Databases are project-specific - show empty state when no project is selected
        databases = []
    }

    func create(name: String, type: DatabaseType) async {
        do {
            let _: Database = try await bridge.call("database.create", params: [
                "name": name,
                "type": type.rawValue
            ])
            notifications.add(.success("Database '\(name)' created"))
            await load()
        } catch {
            notifications.add(.error("Failed to create database: \(error.localizedDescription)"))
        }
    }

    func delete(_ database: Database) async {
        do {
            let _: Bool = try await bridge.call("database.delete", params: ["id": database.id])
            notifications.add(.success("Database '\(database.name)' deleted"))
            await load()
        } catch {
            notifications.add(.error("Failed to delete database: \(error.localizedDescription)"))
        }
    }

    func start(_ database: Database) async {
        do {
            let _: Bool = try await bridge.call("database.start", params: ["id": database.id])
            notifications.add(.success("Database '\(database.name)' started"))
            await load()
        } catch {
            notifications.add(.error("Failed to start database: \(error.localizedDescription)"))
        }
    }

    func stop(_ database: Database) async {
        do {
            let _: Bool = try await bridge.call("database.stop", params: ["id": database.id])
            notifications.add(.success("Database '\(database.name)' stopped"))
            await load()
        } catch {
            notifications.add(.error("Failed to stop database: \(error.localizedDescription)"))
        }
    }
}
