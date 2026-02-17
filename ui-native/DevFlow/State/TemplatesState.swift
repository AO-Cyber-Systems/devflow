import Foundation

/// Manages templates - listing, loading details, creating projects, importing.
@Observable
@MainActor
class TemplatesState {
    // MARK: - State

    var templates: [Template] = []
    var isLoadingTemplates = false
    var showNewProjectWizard = false

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState
    @ObservationIgnored private weak var projectsState: ProjectsState?

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    func setProjectsState(_ projectsState: ProjectsState) {
        self.projectsState = projectsState
    }

    // MARK: - Actions

    func load(category: String? = nil, search: String? = nil) async {
        isLoadingTemplates = true
        defer { isLoadingTemplates = false }

        do {
            var params: [String: any Sendable] = [:]
            if let category = category { params["category"] = category }
            if let search = search { params["search"] = search }

            let response: TemplateListResponse = try await bridge.call(
                "templates.list_templates",
                params: params.isEmpty ? nil : params
            )
            templates = response.templates
        } catch {
            notifications.add(.error("Failed to load templates: \(error.localizedDescription)"))
        }
    }

    func loadDetail(_ templateId: String) async -> TemplateDetail? {
        do {
            let response: TemplateDetailResponse = try await bridge.call(
                "templates.get_template",
                params: ["template_id": templateId]
            )
            return response.template
        } catch {
            notifications.add(.error("Failed to load template: \(error.localizedDescription)"))
            return nil
        }
    }

    func checkRequiredTools(_ templateId: String) async -> ToolCheckResponse? {
        do {
            return try await bridge.call(
                "templates.check_required_tools",
                params: ["template_id": templateId]
            )
        } catch {
            notifications.add(.error("Failed to check tools: \(error.localizedDescription)"))
            return nil
        }
    }

    func createProject(templateId: String, values: [String: String]) async -> CreateProjectResponse? {
        do {
            let response: CreateProjectResponse = try await bridge.call(
                "templates.create_project",
                params: [
                    "template_id": templateId,
                    "wizard_values": values
                ]
            )
            if response.success {
                notifications.add(.success("Project created successfully"))
                // Add to projects list
                await projectsState?.load()
            } else if let error = response.error {
                notifications.add(.error("Failed to create project: \(error)"))
            }
            return response
        } catch {
            notifications.add(.error("Failed to create project: \(error.localizedDescription)"))
            return nil
        }
    }

    func importTemplate(gitUrl: String, branch: String?, subdirectory: String?) async -> ImportTemplateResponse? {
        do {
            var params: [String: any Sendable] = ["git_url": gitUrl]
            if let branch = branch { params["branch"] = branch }
            if let subdirectory = subdirectory { params["subdirectory"] = subdirectory }

            let response: ImportTemplateResponse = try await bridge.call(
                "templates.import_template",
                params: params
            )
            if response.success {
                notifications.add(.success("Template imported successfully"))
            } else if !response.errors.isEmpty {
                notifications.add(.error("Import failed: \(response.errors.first ?? "Unknown error")"))
            }
            return response
        } catch {
            notifications.add(.error("Failed to import template: \(error.localizedDescription)"))
            return nil
        }
    }

    func remove(_ templateId: String) async {
        do {
            let _: [String: Bool] = try await bridge.call(
                "templates.remove_template",
                params: ["template_id": templateId]
            )
            notifications.add(.success("Template removed"))
            await load()
        } catch {
            notifications.add(.error("Failed to remove template: \(error.localizedDescription)"))
        }
    }
}
