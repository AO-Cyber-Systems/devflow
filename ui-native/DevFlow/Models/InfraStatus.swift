import Foundation

/// A project registered with the infrastructure
struct RegisteredInfraProject: Codable, Hashable, Identifiable {
    var id: String { path }
    let name: String
    let path: String
    let domains: [String]
    let composeFiles: [String]
    let configuredAt: String
    let backupPath: String?

    enum CodingKeys: String, CodingKey {
        case name
        case path
        case domains
        case composeFiles = "compose_files"
        case configuredAt = "configured_at"
        case backupPath = "backup_path"
    }
}

struct InfraStatus: Codable {
    var networkExists: Bool
    var networkName: String
    var traefikRunning: Bool
    var traefikContainerId: String?
    var traefikUrl: String?
    var certificatesValid: Bool
    var certificatesPath: String?
    var registeredProjects: [RegisteredInfraProject]
    var remoteConfigured: Bool
    var remoteHost: String?
    var tunnelStatus: String?
    var tunnelLatencyMs: Double?

    var allRunning: Bool {
        networkExists && traefikRunning
    }

    var anyRunning: Bool {
        traefikRunning
    }

    static let unknown = InfraStatus(
        networkExists: false,
        networkName: "devflow-proxy",
        traefikRunning: false,
        traefikContainerId: nil,
        traefikUrl: nil,
        certificatesValid: false,
        certificatesPath: nil,
        registeredProjects: [],
        remoteConfigured: false,
        remoteHost: nil,
        tunnelStatus: nil,
        tunnelLatencyMs: nil
    )

    enum CodingKeys: String, CodingKey {
        case networkExists = "network_exists"
        case networkName = "network_name"
        case traefikRunning = "traefik_running"
        case traefikContainerId = "traefik_container_id"
        case traefikUrl = "traefik_url"
        case certificatesValid = "certificates_valid"
        case certificatesPath = "certificates_path"
        case registeredProjects = "registered_projects"
        case remoteConfigured = "remote_configured"
        case remoteHost = "remote_host"
        case tunnelStatus = "tunnel_status"
        case tunnelLatencyMs = "tunnel_latency_ms"
    }
}

