import Foundation

/// Manages UI component documentation - browsing, creating, and scanning.
@Observable
@MainActor
class ComponentsState {
    // MARK: - State

    var components: [ComponentDoc] = []
    var categories: [ComponentCategoryInfo] = []
    var allCategories: [ComponentCategoryInfo] = []
    var isLoading = false
    var isScanning = false
    var searchQuery: String = ""
    var selectedCategory: String? = nil
    var currentProjectPath: String? = nil

    // MARK: - Dependencies

    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // MARK: - Initialization

    init(bridge: PythonBridge, notifications: NotificationState) {
        self.bridge = bridge
        self.notifications = notifications
    }

    // MARK: - List Actions

    func load(projectPath: String) async {
        currentProjectPath = projectPath
        isLoading = true
        defer { isLoading = false }

        do {
            var params: [String: any Sendable] = ["project_path": projectPath]

            if let category = selectedCategory {
                params["category"] = category
            }

            if !searchQuery.isEmpty {
                params["search"] = searchQuery
            }

            let response: ComponentsListResponse = try await bridge.call(
                "components.list_components",
                params: params
            )

            if let error = response.error {
                notifications.add(.error("Failed to load components: \(error)"))
                return
            }

            components = response.components ?? []
        } catch {
            notifications.add(.error("Failed to load components: \(error.localizedDescription)"))
        }
    }

    func loadCategories(projectPath: String) async {
        do {
            let response: ComponentCategoriesResponse = try await bridge.call(
                "components.get_categories",
                params: ["project_path": projectPath]
            )
            categories = response.categories ?? []
        } catch {
            // Ignore
        }
    }

    func loadAllCategories() async {
        do {
            let response: ComponentCategoriesResponse = try await bridge.call("components.get_all_categories")
            allCategories = response.categories ?? []
        } catch {
            // Ignore
        }
    }

    // MARK: - Component Actions

    func getComponent(_ name: String, projectPath: String? = nil) async -> ComponentDoc? {
        guard let path = projectPath ?? currentProjectPath else { return nil }

        do {
            let response: ComponentDetailResponse = try await bridge.call(
                "components.get_component",
                params: [
                    "project_path": path,
                    "name": name,
                ]
            )
            return response.component
        } catch {
            return nil
        }
    }

    func createComponent(
        projectPath: String? = nil,
        name: String,
        category: String,
        description: String,
        props: [[String: Any]]? = nil,
        slots: [[String: Any]]? = nil,
        events: [[String: Any]]? = nil,
        examples: [[String: Any]]? = nil,
        aiGuidance: String? = nil,
        accessibility: [String]? = nil,
        tags: [String]? = nil
    ) async -> ComponentDoc? {
        guard let path = projectPath ?? currentProjectPath else { return nil }

        do {
            var params: [String: any Sendable] = [
                "project_path": path,
                "name": name,
                "category": category,
                "description": description,
            ]

            // Note: Complex nested params would need proper encoding
            // For simplicity, we'll handle basic cases

            if let ag = aiGuidance { params["ai_guidance"] = ag }
            if let acc = accessibility { params["accessibility"] = acc }
            if let tg = tags { params["tags"] = tg }

            let response: ComponentCreateResponse = try await bridge.call(
                "components.create_component",
                params: params
            )

            if response.success, let component = response.component {
                notifications.add(.success("Component documentation created"))
                components.append(component)
                return component
            } else if let error = response.error {
                notifications.add(.error("Failed to create component: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to create component: \(error.localizedDescription)"))
        }
        return nil
    }

    func updateComponent(
        projectPath: String? = nil,
        name: String,
        category: String? = nil,
        description: String? = nil,
        aiGuidance: String? = nil,
        accessibility: [String]? = nil,
        tags: [String]? = nil
    ) async -> ComponentDoc? {
        guard let path = projectPath ?? currentProjectPath else { return nil }

        do {
            var params: [String: any Sendable] = [
                "project_path": path,
                "name": name,
            ]

            if let c = category { params["category"] = c }
            if let d = description { params["description"] = d }
            if let ag = aiGuidance { params["ai_guidance"] = ag }
            if let acc = accessibility { params["accessibility"] = acc }
            if let tg = tags { params["tags"] = tg }

            let response: ComponentUpdateResponse = try await bridge.call(
                "components.update_component",
                params: params
            )

            if response.success, let component = response.component {
                notifications.add(.success("Component documentation updated"))
                if let index = components.firstIndex(where: { $0.name == name }) {
                    components[index] = component
                }
                return component
            } else if let error = response.error {
                notifications.add(.error("Failed to update component: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to update component: \(error.localizedDescription)"))
        }
        return nil
    }

    func deleteComponent(_ name: String, projectPath: String? = nil) async {
        guard let path = projectPath ?? currentProjectPath else { return }

        do {
            let response: ComponentDeleteResponse = try await bridge.call(
                "components.delete_component",
                params: [
                    "project_path": path,
                    "name": name,
                ]
            )

            if response.success {
                notifications.add(.success("Component documentation deleted"))
                components.removeAll { $0.name == name }
            } else if let error = response.error {
                notifications.add(.error("Failed to delete component: \(error)"))
            }
        } catch {
            notifications.add(.error("Failed to delete component: \(error.localizedDescription)"))
        }
    }

    func scanComponents(projectPath: String? = nil, save: Bool = false) async -> [ComponentDoc] {
        guard let path = projectPath ?? currentProjectPath else { return [] }

        isScanning = true
        defer { isScanning = false }

        do {
            let response: ComponentScanResponse = try await bridge.call(
                "components.scan_components",
                params: [
                    "project_path": path,
                    "save": save,
                ]
            )

            if let error = response.error {
                notifications.add(.error("Scan failed: \(error)"))
                return []
            }

            let scannedComponents = response.components ?? []

            if save {
                notifications.add(.success("Found and saved \(scannedComponents.count) components"))
                // Reload to get updated list
                await load(projectPath: path)
            } else {
                notifications.add(.info("Found \(scannedComponents.count) components"))
            }

            return scannedComponents
        } catch {
            notifications.add(.error("Failed to scan components: \(error.localizedDescription)"))
            return []
        }
    }

    func getAiContext(
        projectPath: String? = nil,
        componentNames: [String]? = nil,
        categories: [String]? = nil
    ) async -> String? {
        guard let path = projectPath ?? currentProjectPath else { return nil }

        do {
            var params: [String: any Sendable] = ["project_path": path]

            if let names = componentNames {
                params["component_names"] = names
            }

            if let cats = categories {
                params["categories"] = cats
            }

            let response: ComponentAiContextResponse = try await bridge.call(
                "components.get_ai_context",
                params: params
            )
            return response.context
        } catch {
            return nil
        }
    }
}
