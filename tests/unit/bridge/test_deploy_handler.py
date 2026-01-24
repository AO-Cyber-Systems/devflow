"""Tests for deploy bridge handler."""

from unittest.mock import MagicMock, patch


class TestDeployHandlerStatus:
    """Tests for DeployHandler.status()."""

    @patch("bridge.handlers.deploy.load_project_config")
    def test_status_no_config(self, mock_load: MagicMock) -> None:
        """Test status when no config found."""
        from bridge.handlers.deploy import DeployHandler

        mock_load.return_value = None

        handler = DeployHandler()
        result = handler.status("/some/path", "staging")

        assert "error" in result
        assert "devflow.yml" in result["error"]

    @patch("bridge.handlers.deploy.load_project_config")
    def test_status_no_deployment_config(self, mock_load: MagicMock) -> None:
        """Test status when no deployment section in config."""
        from bridge.handlers.deploy import DeployHandler

        mock_config = MagicMock()
        mock_config.deployment = None
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.status("/some/path", "staging")

        assert "error" in result
        assert "deployment" in result["error"].lower()

    @patch("bridge.handlers.deploy.load_project_config")
    def test_status_environment_not_found(self, mock_load: MagicMock) -> None:
        """Test status when environment doesn't exist."""
        from bridge.handlers.deploy import DeployHandler

        mock_config = MagicMock()
        mock_config.deployment.environments = {}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.status("/some/path", "unknown")

        assert "error" in result
        assert "unknown" in result["error"]

    @patch("bridge.handlers.deploy.SSHProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_status_remote_success(self, mock_load: MagicMock, mock_ssh_class: MagicMock) -> None:
        """Test status for remote environment with SSH."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_service = MagicMock()
        mock_service.stack = "mystack"
        mock_service.image = "api:latest"
        mock_service.replicas = 2

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_ssh_result = MagicMock()
        mock_ssh_result.success = True
        mock_ssh_result.stdout = '{"Name":"mystack_api","Mode":"replicated","Replicas":"2/2"}'

        mock_ssh = MagicMock()
        mock_ssh.execute.return_value = mock_ssh_result
        mock_ssh_class.return_value = mock_ssh

        handler = DeployHandler()
        handler._ssh = mock_ssh

        result = handler.status("/some/path", "staging")

        assert result["environment"] == "staging"
        assert result["host"] == "staging.example.com"
        assert len(result["services"]) == 1
        assert result["services"][0]["name"] == "api"

    @patch("bridge.handlers.deploy.DockerProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_status_local_success(self, mock_load: MagicMock, mock_docker_class: MagicMock) -> None:
        """Test status for local environment without SSH."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = None  # Local deployment

        mock_service = MagicMock()
        mock_service.stack = "mystack"
        mock_service.image = "api:latest"
        mock_service.replicas = 1

        mock_config = MagicMock()
        mock_config.deployment.environments = {"local": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_docker = MagicMock()
        mock_docker.list_services.return_value = [{"Name": "mystack_api", "Replicas": "1/1", "Mode": "replicated"}]
        mock_docker_class.return_value = mock_docker

        handler = DeployHandler()
        handler._docker = mock_docker

        result = handler.status("/some/path", "local")

        assert result["host"] is None
        assert result["services"][0]["status"] == "running"


class TestDeployHandlerDeploy:
    """Tests for DeployHandler.deploy()."""

    @patch("bridge.handlers.deploy.load_project_config")
    def test_deploy_require_approval(self, mock_load: MagicMock) -> None:
        """Test deploy when approval is required."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.require_approval = True
        mock_env.approval_environment = "production-approval"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"production": mock_env}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.deploy("/some/path", "production")

        assert result["success"] is False
        assert result["requires_approval"] is True

    @patch("bridge.handlers.deploy.load_project_config")
    def test_deploy_dry_run(self, mock_load: MagicMock) -> None:
        """Test deploy with dry_run flag."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.require_approval = False

        mock_service = MagicMock()
        mock_service.stack = "mystack"
        mock_service.image = "api:latest"

        mock_config = MagicMock()
        mock_config.deployment.registry = "ghcr.io"
        mock_config.deployment.organization = "test-org"
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.deploy("/some/path", "staging", dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["results"][0]["status"] == "would_deploy"

    @patch("bridge.handlers.deploy.SSHProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_deploy_remote_success(self, mock_load: MagicMock, mock_ssh_class: MagicMock) -> None:
        """Test successful remote deployment."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"
        mock_env.require_approval = False

        mock_service = MagicMock()
        mock_service.stack = "mystack"
        mock_service.image = "api:latest"

        mock_config = MagicMock()
        mock_config.deployment.registry = "ghcr.io"
        mock_config.deployment.organization = "test-org"
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_ssh_result = MagicMock()
        mock_ssh_result.success = True

        mock_ssh = MagicMock()
        mock_ssh.execute.return_value = mock_ssh_result
        mock_ssh_class.return_value = mock_ssh

        handler = DeployHandler()
        handler._ssh = mock_ssh

        result = handler.deploy("/some/path", "staging")

        assert result["success"] is True
        assert result["deployed"] == 1
        assert result["results"][0]["status"] == "deployed"


class TestDeployHandlerRollback:
    """Tests for DeployHandler.rollback()."""

    @patch("bridge.handlers.deploy.SSHProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_rollback_remote_success(self, mock_load: MagicMock, mock_ssh_class: MagicMock) -> None:
        """Test successful remote rollback."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_service = MagicMock()
        mock_service.stack = "mystack"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_ssh_result = MagicMock()
        mock_ssh_result.success = True

        mock_ssh = MagicMock()
        mock_ssh.execute.return_value = mock_ssh_result
        mock_ssh_class.return_value = mock_ssh

        handler = DeployHandler()
        handler._ssh = mock_ssh

        result = handler.rollback("/some/path", "staging")

        assert result["success"] is True
        assert result["rolled_back"] == 1

    @patch("bridge.handlers.deploy.DockerProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_rollback_local_success(self, mock_load: MagicMock, mock_docker_class: MagicMock) -> None:
        """Test successful local rollback."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = None

        mock_service = MagicMock()
        mock_service.stack = "mystack"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"local": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_docker = MagicMock()
        mock_docker.service_rollback.return_value = True
        mock_docker_class.return_value = mock_docker

        handler = DeployHandler()
        handler._docker = mock_docker

        result = handler.rollback("/some/path", "local")

        assert result["success"] is True
        assert result["rolled_back"] == 1


class TestDeployHandlerLogs:
    """Tests for DeployHandler.logs()."""

    @patch("bridge.handlers.deploy.SSHProvider")
    @patch("bridge.handlers.deploy.load_project_config")
    def test_logs_remote_success(self, mock_load: MagicMock, mock_ssh_class: MagicMock) -> None:
        """Test getting logs from remote service."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_service = MagicMock()
        mock_service.stack = "mystack"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load.return_value = mock_config

        mock_ssh_result = MagicMock()
        mock_ssh_result.success = True
        mock_ssh_result.stdout = "2024-01-15T10:30:00Z api.1 | Log line 1\n2024-01-15T10:31:00Z api.1 | Log line 2"

        mock_ssh = MagicMock()
        mock_ssh.execute.return_value = mock_ssh_result
        mock_ssh_class.return_value = mock_ssh

        handler = DeployHandler()
        handler._ssh = mock_ssh

        result = handler.logs("/some/path", "staging", "api", tail=50)

        assert "logs" in result
        assert "Log line" in result["logs"]

    @patch("bridge.handlers.deploy.load_project_config")
    def test_logs_service_not_found(self, mock_load: MagicMock) -> None:
        """Test logs when service doesn't exist."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.logs("/some/path", "staging", "unknown")

        assert "error" in result
        assert "unknown" in result["error"]


class TestDeployHandlerSSHCommand:
    """Tests for DeployHandler.ssh_command()."""

    @patch("bridge.handlers.deploy.load_project_config")
    def test_ssh_command_success(self, mock_load: MagicMock) -> None:
        """Test getting SSH command."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.ssh_command("/some/path", "staging")

        assert result["command"] == "ssh deploy@staging.example.com"
        assert result["user"] == "deploy"
        assert result["host"] == "staging.example.com"

    @patch("bridge.handlers.deploy.load_project_config")
    def test_ssh_command_no_host(self, mock_load: MagicMock) -> None:
        """Test SSH command when no host configured."""
        from bridge.handlers.deploy import DeployHandler

        mock_env = MagicMock()
        mock_env.host = None

        mock_config = MagicMock()
        mock_config.deployment.environments = {"local": mock_env}
        mock_load.return_value = mock_config

        handler = DeployHandler()
        result = handler.ssh_command("/some/path", "local")

        assert "error" in result
        assert "host" in result["error"].lower()


class TestDeployHandlerHelpers:
    """Tests for DeployHandler helper methods."""

    def test_build_service_name(self) -> None:
        """Test building service name."""
        from bridge.handlers.deploy import DeployHandler

        handler = DeployHandler()
        result = handler._build_service_name("mystack", "api")

        assert result == "mystack_api"

    def test_build_image_tag_full(self) -> None:
        """Test building image tag with all components."""
        from bridge.handlers.deploy import DeployHandler

        handler = DeployHandler()
        result = handler._build_image_tag("ghcr.io", "test-org", "api:latest")

        assert result == "ghcr.io/test-org/api:latest"

    def test_build_image_tag_no_registry(self) -> None:
        """Test building image tag without registry."""
        from bridge.handlers.deploy import DeployHandler

        handler = DeployHandler()
        result = handler._build_image_tag(None, "test-org", "api:latest")

        assert result == "test-org/api:latest"

    def test_build_image_tag_only_image(self) -> None:
        """Test building image tag with only image name."""
        from bridge.handlers.deploy import DeployHandler

        handler = DeployHandler()
        result = handler._build_image_tag(None, None, "api:latest")

        assert result == "api:latest"
