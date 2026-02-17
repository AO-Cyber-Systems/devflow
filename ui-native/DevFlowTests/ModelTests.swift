import XCTest
@testable import DevFlow

final class ModelTests: XCTestCase {

    // MARK: - Project Tests

    func testProjectInitialization() {
        let project = Project(
            name: "Test Project",
            path: "/path/to/project",
            domain: "test.local",
            port: 3000,
            isRunning: true,
            framework: "Next.js"
        )

        XCTAssertFalse(project.id.isEmpty)
        XCTAssertEqual(project.name, "Test Project")
        XCTAssertEqual(project.path, "/path/to/project")
        XCTAssertEqual(project.domain, "test.local")
        XCTAssertEqual(project.port, 3000)
        XCTAssertTrue(project.isRunning)
        XCTAssertEqual(project.framework, "Next.js")
    }

    func testProjectDecoding() throws {
        let json = """
        {
            "id": "123",
            "name": "My App",
            "path": "/Users/test/myapp",
            "domain": "myapp.test",
            "port": 8080,
            "is_running": false,
            "framework": "Django"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let project = try decoder.decode(Project.self, from: data)

        XCTAssertEqual(project.id, "123")
        XCTAssertEqual(project.name, "My App")
        XCTAssertEqual(project.path, "/Users/test/myapp")
        XCTAssertEqual(project.domain, "myapp.test")
        XCTAssertEqual(project.port, 8080)
        XCTAssertFalse(project.isRunning)
        XCTAssertEqual(project.framework, "Django")
    }

    // MARK: - InfraStatus Tests

    func testInfraStatusAllRunning() {
        let status = InfraStatus(
            networkExists: true,
            networkName: "devflow-proxy",
            traefikRunning: true,
            traefikContainerId: "abc123",
            traefikUrl: "http://traefik.test",
            certificatesValid: true,
            certificatesPath: "/path/to/certs",
            registeredProjects: [],
            remoteConfigured: false,
            remoteHost: nil,
            tunnelStatus: nil,
            tunnelLatencyMs: nil
        )

        XCTAssertTrue(status.allRunning)
        XCTAssertTrue(status.anyRunning)
    }

    func testInfraStatusPartiallyRunning() {
        let status = InfraStatus(
            networkExists: false,
            networkName: "devflow-proxy",
            traefikRunning: true,
            traefikContainerId: "abc123",
            traefikUrl: nil,
            certificatesValid: false,
            certificatesPath: "",
            registeredProjects: [],
            remoteConfigured: false,
            remoteHost: nil,
            tunnelStatus: nil,
            tunnelLatencyMs: nil
        )

        XCTAssertFalse(status.allRunning)
        XCTAssertTrue(status.anyRunning)
    }

    func testInfraStatusNoneRunning() {
        let status = InfraStatus.unknown

        XCTAssertFalse(status.allRunning)
        XCTAssertFalse(status.anyRunning)
    }

    func testInfraStatusDecoding() throws {
        let json = """
        {
            "network_exists": true,
            "network_name": "devflow-proxy",
            "traefik_running": true,
            "traefik_container_id": "abc123def456",
            "traefik_url": "http://traefik.test:8080",
            "certificates_valid": true,
            "certificates_path": "/Users/test/.local/share/mkcert",
            "registered_projects": [
                {
                    "name": "myapp",
                    "path": "/Users/test/projects/myapp",
                    "domains": ["myapp.localhost"],
                    "compose_files": [],
                    "configured_at": "2024-01-01T00:00:00Z",
                    "backup_path": null
                },
                {
                    "name": "api",
                    "path": "/Users/test/projects/api",
                    "domains": [],
                    "compose_files": ["docker-compose.yml"],
                    "configured_at": "2024-01-02T00:00:00Z",
                    "backup_path": "/backups/api"
                }
            ],
            "remote_configured": false,
            "remote_host": null,
            "tunnel_status": null,
            "tunnel_latency_ms": null
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let status = try decoder.decode(InfraStatus.self, from: data)

        XCTAssertTrue(status.networkExists)
        XCTAssertEqual(status.networkName, "devflow-proxy")
        XCTAssertTrue(status.traefikRunning)
        XCTAssertEqual(status.traefikContainerId, "abc123def456")
        XCTAssertEqual(status.registeredProjects.count, 2)
        XCTAssertEqual(status.registeredProjects[0].name, "myapp")
        XCTAssertEqual(status.registeredProjects[1].path, "/Users/test/projects/api")
        XCTAssertTrue(status.allRunning)
    }

    // MARK: - GlobalConfig Tests

    func testGlobalConfigDefaults() {
        let config = GlobalConfig()

        XCTAssertEqual(config.baseDomain, "test")
        XCTAssertEqual(config.traefikPort, 80)
        XCTAssertEqual(config.traefikDashboardPort, 8080)
        XCTAssertTrue(config.dnsEnabled)
        XCTAssertNil(config.dockerHost)
        XCTAssertEqual(config.secretsProvider, .system)
    }

    func testGlobalConfigDecoding() throws {
        let json = """
        {
            "base_domain": "local",
            "traefik_port": 8000,
            "traefik_dashboard_port": 9000,
            "dns_enabled": false,
            "docker_host": "tcp://localhost:2375",
            "secrets_provider": "1password"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let config = try decoder.decode(GlobalConfig.self, from: data)

        XCTAssertEqual(config.baseDomain, "local")
        XCTAssertEqual(config.traefikPort, 8000)
        XCTAssertEqual(config.traefikDashboardPort, 9000)
        XCTAssertFalse(config.dnsEnabled)
        XCTAssertEqual(config.dockerHost, "tcp://localhost:2375")
        XCTAssertEqual(config.secretsProvider, .onePassword)
    }

    // MARK: - Notification Tests

    func testNotificationFactoryMethods() {
        let success = AppNotification.success("Test success")
        XCTAssertEqual(success.type, .success)
        XCTAssertEqual(success.message, "Test success")
        XCTAssertTrue(success.autoDismiss)

        let error = AppNotification.error("Test error")
        XCTAssertEqual(error.type, .error)
        XCTAssertEqual(error.message, "Test error")
        XCTAssertFalse(error.autoDismiss)

        let warning = AppNotification.warning("Test warning")
        XCTAssertEqual(warning.type, .warning)
        XCTAssertEqual(warning.message, "Test warning")
        XCTAssertTrue(warning.autoDismiss)

        let info = AppNotification.info("Test info")
        XCTAssertEqual(info.type, .info)
        XCTAssertEqual(info.message, "Test info")
        XCTAssertTrue(info.autoDismiss)
    }

    // MARK: - SecretsProvider Tests

    func testSecretsProviderDisplayNames() {
        XCTAssertEqual(SecretsProvider.system.displayName, "System Keychain")
        XCTAssertEqual(SecretsProvider.onePassword.displayName, "1Password")
        XCTAssertEqual(SecretsProvider.bitwarden.displayName, "Bitwarden")
        XCTAssertEqual(SecretsProvider.env.displayName, "Environment Variables")
    }

    func testSecretsProviderIcons() {
        XCTAssertFalse(SecretsProvider.system.icon.isEmpty)
        XCTAssertFalse(SecretsProvider.onePassword.icon.isEmpty)
        XCTAssertFalse(SecretsProvider.bitwarden.icon.isEmpty)
        XCTAssertFalse(SecretsProvider.env.icon.isEmpty)
    }

    // MARK: - LogEntry Tests

    func testLogEntryDecoding() throws {
        let json = """
        {
            "timestamp": "2024-01-15T10:30:45.123Z",
            "message": "Server started",
            "level": "info",
            "source": "traefik"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let entry = try decoder.decode(LogEntry.self, from: data)

        XCTAssertEqual(entry.timestamp, "2024-01-15T10:30:45.123Z")
        XCTAssertEqual(entry.message, "Server started")
        XCTAssertEqual(entry.level, .info)
        XCTAssertEqual(entry.source, "traefik")
    }

    func testLogEntryDecodingWithoutTimestamp() throws {
        let json = """
        {
            "message": "Simple log",
            "level": "debug",
            "source": "app"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let entry = try decoder.decode(LogEntry.self, from: data)

        XCTAssertNil(entry.timestamp)
        XCTAssertEqual(entry.message, "Simple log")
        XCTAssertEqual(entry.level, .debug)
    }

    func testLogLevelAllCases() {
        XCTAssertEqual(LogLevel.allCases.count, 4)
        XCTAssertTrue(LogLevel.allCases.contains(.debug))
        XCTAssertTrue(LogLevel.allCases.contains(.info))
        XCTAssertTrue(LogLevel.allCases.contains(.warning))
        XCTAssertTrue(LogLevel.allCases.contains(.error))
    }

    func testLogLevelColors() {
        // Verify each level has a color (though we can't test actual SwiftUI color values)
        for level in LogLevel.allCases {
            let _ = level.color // Should not crash
        }
    }

    // MARK: - ContainerInfo Tests

    func testContainerInfoDecoding() throws {
        let json = """
        {
            "id": "abc123def456",
            "name": "traefik",
            "status": "Up 2 hours",
            "image": "traefik:latest"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let container = try decoder.decode(ContainerInfo.self, from: data)

        XCTAssertEqual(container.id, "abc123def456")
        XCTAssertEqual(container.name, "traefik")
        XCTAssertEqual(container.status, "Up 2 hours")
        XCTAssertEqual(container.image, "traefik:latest")
    }

    func testContainersListResponseDecoding() throws {
        let json = """
        {
            "success": true,
            "containers": [
                {"id": "abc", "name": "traefik", "status": "Up", "image": "traefik:latest"},
                {"id": "def", "name": "nginx", "status": "Up", "image": "nginx:alpine"}
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let response = try decoder.decode(ContainersListResponse.self, from: data)

        XCTAssertEqual(response.success, true)
        XCTAssertEqual(response.containers.count, 2)
        XCTAssertNil(response.error)
    }

    // MARK: - OperationResult Tests

    func testOperationResultSuccessDecoding() throws {
        let json = """
        {
            "success": true,
            "message": "Operation completed"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let result = try decoder.decode(OperationResult.self, from: data)

        XCTAssertTrue(result.success)
        XCTAssertEqual(result.message, "Operation completed")
        XCTAssertNil(result.error)
    }

    func testOperationResultFailureDecoding() throws {
        let json = """
        {
            "success": false,
            "error": "Permission denied"
        }
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let result = try decoder.decode(OperationResult.self, from: data)

        XCTAssertFalse(result.success)
        XCTAssertEqual(result.error, "Permission denied")
    }

    func testOperationResultDisplayMessage() throws {
        let successJson = """
        {"success": true, "message": "Done!"}
        """
        let successData = successJson.data(using: .utf8)!
        let successResult = try JSONDecoder().decode(OperationResult.self, from: successData)
        XCTAssertEqual(successResult.displayMessage, "Done!")

        let failureJson = """
        {"success": false, "error": "Failed!"}
        """
        let failureData = failureJson.data(using: .utf8)!
        let failureResult = try JSONDecoder().decode(OperationResult.self, from: failureData)
        XCTAssertEqual(failureResult.displayMessage, "Failed!")
    }

    func testOperationResultDisplayMessageDefaults() throws {
        let successJson = """
        {"success": true}
        """
        let successData = successJson.data(using: .utf8)!
        let successResult = try JSONDecoder().decode(OperationResult.self, from: successData)
        XCTAssertEqual(successResult.displayMessage, "Operation completed successfully")

        let failureJson = """
        {"success": false}
        """
        let failureData = failureJson.data(using: .utf8)!
        let failureResult = try JSONDecoder().decode(OperationResult.self, from: failureData)
        XCTAssertEqual(failureResult.displayMessage, "An unknown error occurred")
    }

    // MARK: - Command Tests

    func testCommandInitialization() {
        let command = Command("Test Command", icon: "star.fill", shortcut: "⌘T", category: .general) {
            // Empty action
        }

        XCTAssertEqual(command.title, "Test Command")
        XCTAssertEqual(command.icon, "star.fill")
        XCTAssertEqual(command.shortcut, "⌘T")
        XCTAssertEqual(command.category, .general)
        XCTAssertEqual(command.id, "test-command")
    }

    func testCommandIdGeneration() {
        let command1 = Command("Go to Dashboard", icon: "gauge") { }
        XCTAssertEqual(command1.id, "go-to-dashboard")

        let command2 = Command("Start Infrastructure", icon: "play.fill") { }
        XCTAssertEqual(command2.id, "start-infrastructure")
    }

    func testCommandCategoryAllCases() {
        XCTAssertEqual(CommandCategory.allCases.count, 5)
        XCTAssertTrue(CommandCategory.allCases.contains(.navigation))
        XCTAssertTrue(CommandCategory.allCases.contains(.infrastructure))
        XCTAssertTrue(CommandCategory.allCases.contains(.projects))
        XCTAssertTrue(CommandCategory.allCases.contains(.tools))
        XCTAssertTrue(CommandCategory.allCases.contains(.general))
    }

    func testCommandCategoryIcons() {
        XCTAssertFalse(CommandCategory.navigation.icon.isEmpty)
        XCTAssertFalse(CommandCategory.infrastructure.icon.isEmpty)
        XCTAssertFalse(CommandCategory.projects.icon.isEmpty)
        XCTAssertFalse(CommandCategory.tools.icon.isEmpty)
        XCTAssertFalse(CommandCategory.general.icon.isEmpty)
    }
}
