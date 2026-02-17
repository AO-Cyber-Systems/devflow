import Foundation

struct GlobalConfig: Codable {
    var baseDomain: String
    var traefikPort: Int
    var traefikDashboardPort: Int
    var dnsEnabled: Bool
    var dockerHost: String?
    var secretsProvider: SecretsProvider

    init(
        baseDomain: String = "test",
        traefikPort: Int = 80,
        traefikDashboardPort: Int = 8080,
        dnsEnabled: Bool = true,
        dockerHost: String? = nil,
        secretsProvider: SecretsProvider = .system
    ) {
        self.baseDomain = baseDomain
        self.traefikPort = traefikPort
        self.traefikDashboardPort = traefikDashboardPort
        self.dnsEnabled = dnsEnabled
        self.dockerHost = dockerHost
        self.secretsProvider = secretsProvider
    }

    enum CodingKeys: String, CodingKey {
        case baseDomain = "base_domain"
        case traefikPort = "traefik_port"
        case traefikDashboardPort = "traefik_dashboard_port"
        case dnsEnabled = "dns_enabled"
        case dockerHost = "docker_host"
        case secretsProvider = "secrets_provider"
    }
}

enum SecretsProvider: String, Codable, CaseIterable, Identifiable {
    case system = "system"
    case onePassword = "1password"
    case bitwarden = "bitwarden"
    case env = "env"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .system: return "System Keychain"
        case .onePassword: return "1Password"
        case .bitwarden: return "Bitwarden"
        case .env: return "Environment Variables"
        }
    }

    var icon: String {
        switch self {
        case .system: return "key.fill"
        case .onePassword: return "lock.shield.fill"
        case .bitwarden: return "lock.rectangle.fill"
        case .env: return "terminal.fill"
        }
    }
}

struct Secret: Identifiable, Codable {
    let id: String
    var key: String
    var value: String?
    var provider: SecretsProvider
    var projectId: String?

    init(id: String = UUID().uuidString, key: String, value: String? = nil, provider: SecretsProvider = .system, projectId: String? = nil) {
        self.id = id
        self.key = key
        self.value = value
        self.provider = provider
        self.projectId = projectId
    }

    enum CodingKeys: String, CodingKey {
        case id
        case key
        case value
        case provider
        case projectId = "project_id"
    }
}
