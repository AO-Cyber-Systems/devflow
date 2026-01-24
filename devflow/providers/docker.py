"""Docker and Docker Swarm provider."""

import json
import shutil
import subprocess

from devflow.core.paths import get_docker_socket
from devflow.providers.base import Provider


class DockerProvider(Provider):
    """Wrapper for Docker CLI."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def binary(self) -> str:
        return "docker"

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        # For Docker, "authenticated" means the daemon is running
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                [self.binary, "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    # -------------------------------------------------------------------------
    # Platform-Aware Socket Handling
    # -------------------------------------------------------------------------

    def get_socket_path(self) -> str:
        """Get Docker socket path for current platform.

        Returns:
            Path to the Docker socket.
        """
        return get_docker_socket()

    def get_socket_mount(self) -> str:
        """Get Docker socket mount string for compose/swarm.

        Returns:
            Mount string in format 'source:target'.
        """
        socket = self.get_socket_path()
        return f"{socket}:/var/run/docker.sock"

    # -------------------------------------------------------------------------
    # Docker Secrets
    # -------------------------------------------------------------------------

    def list_secrets(self) -> list[dict]:
        """List Docker secrets."""
        try:
            result = self.run(["secret", "ls", "--format", "json"])
            # Docker outputs one JSON object per line
            lines = result.stdout.strip().split("\n")
            return [json.loads(line) for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    def create_secret(self, name: str, value: str) -> bool:
        """Create a Docker secret."""
        try:
            # Use stdin to avoid exposing secret
            result = subprocess.run(
                [self.binary, "secret", "create", name, "-"],
                input=value,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def remove_secret(self, name: str) -> bool:
        """Remove a Docker secret."""
        try:
            self.run(["secret", "rm", name])
            return True
        except subprocess.CalledProcessError:
            return False

    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists."""
        secrets = self.list_secrets()
        return any(s.get("Name") == name for s in secrets)

    # -------------------------------------------------------------------------
    # Docker Services (Swarm)
    # -------------------------------------------------------------------------

    def list_services(self, filter_name: str | None = None) -> list[dict]:
        """List Docker Swarm services."""
        args = ["service", "ls", "--format", "json"]
        if filter_name:
            args.extend(["--filter", f"name={filter_name}"])

        try:
            result = self.run(args)
            lines = result.stdout.strip().split("\n")
            return [json.loads(line) for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    def service_update(
        self,
        service_name: str,
        image: str | None = None,
        force: bool = False,
        with_registry_auth: bool = True,
    ) -> bool:
        """Update a Docker Swarm service."""
        args = ["service", "update"]

        if image:
            args.extend(["--image", image])
        if force:
            args.append("--force")
        if with_registry_auth:
            args.append("--with-registry-auth")

        args.append(service_name)

        try:
            self.run(args, timeout=120)
            return True
        except subprocess.CalledProcessError:
            return False

    def service_logs(
        self,
        service_name: str,
        tail: int = 100,
        follow: bool = False,
    ) -> subprocess.Popen:
        """Get logs from a service (returns a Popen for streaming)."""
        args = [self.binary, "service", "logs", f"--tail={tail}"]
        if follow:
            args.append("-f")
        args.append(service_name)

        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def service_logs_text(
        self,
        service_name: str,
        tail: int = 100,
        since: str | None = None,
    ) -> str:
        """Get logs from a service as text.

        Args:
            service_name: Name of the service
            tail: Number of lines to return
            since: Show logs since timestamp (e.g., "2021-01-01T00:00:00Z" or "10m")

        Returns:
            Log output as string
        """
        args = ["service", "logs", f"--tail={tail}", "--no-trunc"]
        if since:
            args.extend(["--since", since])
        args.append(service_name)

        try:
            result = self.run(args, timeout=30)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def service_rollback(self, service_name: str) -> bool:
        """Rollback a service to its previous version."""
        try:
            self.run(["service", "rollback", service_name])
            return True
        except subprocess.CalledProcessError:
            return False

    # -------------------------------------------------------------------------
    # Docker Stack (Swarm)
    # -------------------------------------------------------------------------

    def stack_deploy(self, stack_name: str, compose_file: str, with_registry_auth: bool = True) -> bool:
        """Deploy a Docker stack."""
        args = ["stack", "deploy", "-c", compose_file]
        if with_registry_auth:
            args.append("--with-registry-auth")
        args.append(stack_name)

        try:
            self.run(args, timeout=120)
            return True
        except subprocess.CalledProcessError:
            return False

    def stack_services(self, stack_name: str) -> list[dict]:
        """List services in a stack."""
        return self.list_services(filter_name=stack_name)

    # -------------------------------------------------------------------------
    # Docker Compose
    # -------------------------------------------------------------------------

    def compose_up(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
        detach: bool = True,
        services: list[str] | None = None,
    ) -> bool:
        """Start services with docker compose.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context
            detach: Run in detached mode
            services: Specific services to start

        Returns:
            True if successful
        """
        args = ["compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "up"])
        if detach:
            args.append("-d")
        if services:
            args.extend(services)

        try:
            self.run(args, timeout=180)
            return True
        except subprocess.CalledProcessError:
            return False

    def compose_down(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
        volumes: bool = False,
        services: list[str] | None = None,
    ) -> bool:
        """Stop services with docker compose.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context
            volumes: Also remove volumes
            services: Specific services to stop (if None, stops all)

        Returns:
            True if successful
        """
        args = ["compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "down"])
        if volumes:
            args.append("-v")
        # Note: compose down doesn't support service filtering

        try:
            self.run(args, timeout=60)
            return True
        except subprocess.CalledProcessError:
            return False

    def compose_ps(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
    ) -> list[dict]:
        """List compose containers.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context

        Returns:
            List of container info dicts with Service, State, Image, Ports, Health
        """
        args = ["compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "ps", "--format", "json"])

        try:
            result = self.run(args)
            # Docker compose outputs JSON array or newline-delimited JSON objects
            output = result.stdout.strip()
            if not output:
                return []

            # Try parsing as JSON array first
            if output.startswith("["):
                return json.loads(output)

            # Otherwise, parse newline-delimited JSON
            lines = output.split("\n")
            return [json.loads(line) for line in lines if line]
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def compose_restart(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
        services: list[str] | None = None,
    ) -> bool:
        """Restart compose services.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context
            services: Specific services to restart

        Returns:
            True if successful
        """
        args = ["compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "restart"])
        if services:
            args.extend(services)

        try:
            self.run(args, timeout=120)
            return True
        except subprocess.CalledProcessError:
            return False

    def compose_logs(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
        services: list[str] | None = None,
        tail: int = 100,
        follow: bool = False,
        since: str | None = None,
    ) -> str:
        """Get compose service logs.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context
            services: Specific services to get logs from
            tail: Number of lines to show
            follow: Follow log output (not recommended for RPC)
            since: Show logs since timestamp (e.g., "2021-01-01T00:00:00Z" or "10m")

        Returns:
            Log output as string
        """
        args = ["compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "logs", f"--tail={tail}"])
        if since:
            args.extend(["--since", since])
        if follow:
            args.append("-f")
        if services:
            args.extend(services)

        try:
            result = self.run(args, timeout=30)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def compose_run(
        self,
        compose_file: str = "docker-compose.yml",
        project_dir: str | None = None,
        service: str = "",
        command: list[str] | None = None,
        remove: bool = True,
        no_deps: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a one-off command in a compose service.

        Args:
            compose_file: Path to compose file
            project_dir: Project directory for compose context
            service: Service to run command in
            command: Command to run
            remove: Remove container after run
            no_deps: Don't start linked services

        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        args = [self.binary, "compose"]
        if project_dir:
            args.extend(["--project-directory", project_dir])
        args.extend(["-f", compose_file, "run"])
        if remove:
            args.append("--rm")
        if no_deps:
            args.append("--no-deps")
        args.append(service)
        if command:
            args.extend(command)

        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300,
        )
