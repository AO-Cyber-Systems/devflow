import Foundation

/// Manages projects - listing, adding, removing, and project operations.
@Observable
@MainActor
class ProjectsState {
    // MARK: - State

    var projects: [Project] = []
    var isLoadingProjects = false
    var showAddProject = false

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
        isLoadingProjects = true
        defer { isLoadingProjects = false }

        do {
            let response: ProjectListResponse = try await bridge.call("projects.list")
            projects = response.projects
        } catch {
            notifications.add(.error("Failed to load projects: \(error.localizedDescription)"))
        }
    }

    func add(path: String) async {
        do {
            struct AddResponse: Codable {
                let success: Bool?
                let error: String?
                let project: Project?
            }
            let response: AddResponse = try await bridge.call("projects.add", params: ["path": path])
            if response.success == true, let project = response.project {
                notifications.add(.success("Project '\(project.name)' added"))
                await load()
            } else if let error = response.error {
                notifications.add(.error("Failed to add project: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to add project: \(error.localizedDescription)"))
        }
    }

    func remove(_ project: Project) async {
        do {
            let _: Bool = try await bridge.call("projects.remove", params: ["id": project.id])
            notifications.add(.success("Project '\(project.name)' removed"))
            await load()
        } catch {
            notifications.add(.error("Failed to remove project: \(error.localizedDescription)"))
        }
    }

    func start(_ project: Project) async {
        do {
            let _: Bool = try await bridge.call("projects.start", params: ["id": project.id])
            notifications.add(.success("Project '\(project.name)' started"))
            await load()
        } catch {
            notifications.add(.error("Failed to start project: \(error.localizedDescription)"))
        }
    }

    func stop(_ project: Project) async {
        do {
            let _: Bool = try await bridge.call("projects.stop", params: ["id": project.id])
            notifications.add(.success("Project '\(project.name)' stopped"))
            await load()
        } catch {
            notifications.add(.error("Failed to stop project: \(error.localizedDescription)"))
        }
    }

    func update(_ project: Project, domain: String?, port: Int?, commands: ProjectCommands?) async {
        do {
            var params: [String: any Sendable] = ["id": project.id]
            if let domain = domain {
                params["domain"] = domain
            }
            if let port = port {
                params["port"] = port
            }
            if let commands = commands {
                var commandsDict: [String: String] = [:]
                if let start = commands.start { commandsDict["start"] = start }
                if let build = commands.build { commandsDict["build"] = build }
                if let test = commands.test { commandsDict["test"] = test }
                if !commandsDict.isEmpty {
                    params["commands"] = commandsDict
                }
            }
            let _: Bool = try await bridge.call("projects.update", params: params)
            notifications.add(.success("Project '\(project.name)' updated"))
            await load()
        } catch {
            notifications.add(.error("Failed to update project: \(error.localizedDescription)"))
        }
    }

    func getDetail(path: String) async throws -> ProjectDetail {
        try await bridge.call("projects.get_detail", params: ["path": path])
    }
}
