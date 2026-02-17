import Foundation

struct Project: Identifiable, Codable, Hashable {
    let id: String
    var name: String
    var path: String
    var domain: String?
    var port: Int?
    var isRunning: Bool
    var framework: String?
    var lastAccessed: String?
    // Extra fields from backend (optional)
    var exists: Bool?
    var hasDevflowConfig: Bool?

    init(
        id: String = UUID().uuidString,
        name: String,
        path: String,
        domain: String? = nil,
        port: Int? = nil,
        isRunning: Bool = false,
        framework: String? = nil,
        lastAccessed: String? = nil,
        exists: Bool? = nil,
        hasDevflowConfig: Bool? = nil
    ) {
        self.id = id
        self.name = name
        self.path = path
        self.domain = domain
        self.port = port
        self.isRunning = isRunning
        self.framework = framework
        self.lastAccessed = lastAccessed
        self.exists = exists
        self.hasDevflowConfig = hasDevflowConfig
    }

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case path
        case domain
        case port
        case isRunning = "is_running"
        case framework
        case lastAccessed = "last_accessed"
        case exists
        case hasDevflowConfig = "has_devflow_config"
    }
}

// MARK: - Project Detail Models

/// Detailed project information including services, ports, and volumes.
struct ProjectDetail: Codable, Identifiable {
    var id: String { project.id }
    let project: Project
    let services: [ProjectService]
    let ports: [PortMapping]
    let volumes: [VolumeMount]
    let hasComposeFile: Bool
    let composeFilePath: String?

    var runningServices: Int {
        services.filter { $0.isRunning }.count
    }

    var totalServices: Int {
        services.count
    }

    enum CodingKeys: String, CodingKey {
        case project
        case services
        case ports
        case volumes
        case hasComposeFile = "has_compose_file"
        case composeFilePath = "compose_file_path"
    }
}

/// A service within a project (from Docker Compose).
struct ProjectService: Identifiable, Codable, Hashable {
    var id: String { name }
    let name: String
    let status: String
    let image: String
    let containerId: String?
    let ports: [String]
    let health: String?

    var isRunning: Bool {
        status.lowercased().contains("up") || status.lowercased().contains("running")
    }

    var statusColor: String {
        if isRunning {
            return health == "unhealthy" ? "orange" : "green"
        }
        return status.lowercased().contains("exit") ? "red" : "gray"
    }

    enum CodingKeys: String, CodingKey {
        case name
        case status
        case image
        case containerId = "container_id"
        case ports
        case health
    }
}

/// A port mapping from container to host.
struct PortMapping: Identifiable, Codable, Hashable {
    var id: String { "\(hostPort)-\(containerPort)-\(service)" }
    let service: String
    let hostPort: Int
    let containerPort: Int
    let hostIp: String

    var displayString: String {
        if hostIp == "0.0.0.0" {
            return "\(hostPort) → \(containerPort)"
        }
        return "\(hostIp):\(hostPort) → \(containerPort)"
    }

    enum CodingKeys: String, CodingKey {
        case service
        case hostPort = "host_port"
        case containerPort = "container_port"
        case hostIp = "host_ip"
    }
}

/// A volume mount in a project.
struct VolumeMount: Identifiable, Codable, Hashable {
    var id: String { "\(service)-\(containerPath)" }
    let service: String
    let hostPath: String
    let containerPath: String
    let mode: String  // "rw" or "ro"

    var isReadOnly: Bool {
        mode == "ro"
    }

    enum CodingKeys: String, CodingKey {
        case service
        case hostPath = "host_path"
        case containerPath = "container_path"
        case mode
    }
}

struct ProjectConfig: Codable {
    var domain: String?
    var port: Int?
    var env: [String: String]?
    var commands: ProjectCommands?
}

struct ProjectCommands: Codable {
    var start: String?
    var build: String?
    var test: String?
}

// MARK: - API Responses

struct ProjectListResponse: Codable {
    let projects: [Project]
    let total: Int
}
