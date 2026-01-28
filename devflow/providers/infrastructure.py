"""Infrastructure provider for managing shared development infrastructure."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devflow.core.config import InfrastructureConfig, RemoteContextConfig
from devflow.core.paths import get_devflow_home, get_docker_socket, get_hosts_file
from devflow.providers.docker import DockerProvider
from devflow.providers.mkcert import MkcertProvider


@dataclass
class InfraStatus:
    """Status of the infrastructure components."""

    network_exists: bool = False
    network_name: str = ""
    traefik_running: bool = False
    traefik_container_id: str | None = None
    traefik_url: str | None = None
    certificates_valid: bool = False
    certificates_path: str | None = None
    registered_projects: list[dict] = field(default_factory=list)
    # Remote context / tunnel status
    remote_configured: bool = False
    remote_host: str | None = None
    tunnel_status: str | None = None
    tunnel_latency_ms: float | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "network_exists": self.network_exists,
            "network_name": self.network_name,
            "traefik_running": self.traefik_running,
            "traefik_container_id": self.traefik_container_id,
            "traefik_url": self.traefik_url,
            "certificates_valid": self.certificates_valid,
            "certificates_path": self.certificates_path,
            "registered_projects": self.registered_projects,
            "remote_configured": self.remote_configured,
            "remote_host": self.remote_host,
            "tunnel_status": self.tunnel_status,
            "tunnel_latency_ms": self.tunnel_latency_ms,
        }


@dataclass
class InfraResult:
    """Result of an infrastructure operation."""

    success: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class RegisteredProject:
    """A project registered with the infrastructure."""

    name: str
    path: str
    domains: list[str]
    compose_files: list[str]
    configured_at: str
    backup_path: str | None = None


class InfrastructureProvider:
    """Manages shared Docker infrastructure for local development."""

    # Use platform-aware path for DevFlow home
    DEVFLOW_HOME = get_devflow_home()
    TRAEFIK_CONTAINER_NAME = "devflow-traefik"
    PROJECTS_FILE = "projects.json"

    def __init__(
        self,
        config: InfrastructureConfig | None = None,
        remote_config: RemoteContextConfig | None = None,
    ):
        """Initialize the infrastructure provider.

        Args:
            config: Infrastructure configuration. Uses defaults if not provided.
            remote_config: Optional remote context configuration for tunnel management.
        """
        self.config = config or InfrastructureConfig()
        self.remote_config = remote_config
        self.docker = DockerProvider()
        self.mkcert = MkcertProvider()

    @property
    def infrastructure_dir(self) -> Path:
        """Get the infrastructure directory."""
        return self.DEVFLOW_HOME / "infrastructure"

    @property
    def certs_dir(self) -> Path:
        """Get the certificates directory."""
        return Path(self.config.certificates.cert_dir).expanduser()

    @property
    def projects_file(self) -> Path:
        """Get the projects registry file path."""
        return self.DEVFLOW_HOME / self.PROJECTS_FILE

    # -------------------------------------------------------------------------
    # Main Operations
    # -------------------------------------------------------------------------

    def start(self, force_recreate: bool = False) -> InfraResult:
        """Start the shared infrastructure.

        Args:
            force_recreate: Force recreation of containers even if running

        Returns:
            InfraResult indicating success or failure
        """
        # If remote context is configured with auto_tunnel, ensure tunnel is running first
        tunnel_info = None
        if self.remote_config and self.remote_config.enabled and self.remote_config.auto_tunnel:
            tunnel_ok, tunnel_msg, tunnel_info = self._ensure_tunnel_running()
            if not tunnel_ok:
                return InfraResult(False, f"Failed to start tunnel: {tunnel_msg}")

        if not self.docker.is_available():
            return InfraResult(False, "Docker is not available")

        if not self.docker.is_authenticated():
            return InfraResult(False, "Docker daemon is not running")

        # Ensure network exists
        network_ok, network_msg = self._ensure_network()
        if not network_ok:
            return InfraResult(False, f"Failed to create network: {network_msg}")

        # Ensure certificates exist
        certs_ok, certs_msg = self._ensure_certificates()
        if not certs_ok:
            return InfraResult(False, f"Failed to set up certificates: {certs_msg}")

        # Ensure Traefik is running
        traefik_ok, traefik_msg = self._ensure_traefik(force_recreate)
        if not traefik_ok:
            return InfraResult(False, f"Failed to start Traefik: {traefik_msg}")

        details = {
            "network": self.config.network_name,
            "traefik_url": f"https://traefik.localhost:{self.config.traefik.https_port}",
            "dashboard_url": f"http://localhost:{self.config.traefik.dashboard_port}",
        }

        # Add tunnel info if applicable
        if tunnel_info:
            details["tunnel"] = tunnel_info

        return InfraResult(True, "Infrastructure started successfully", details)

    def stop(self, remove_volumes: bool = False, remove_network: bool = False) -> InfraResult:
        """Stop the shared infrastructure.

        Args:
            remove_volumes: Remove volumes when stopping
            remove_network: Remove the network after stopping containers

        Returns:
            InfraResult indicating success or failure
        """
        messages = []

        # Stop Traefik
        if self._is_traefik_running():
            try:
                subprocess.run(
                    ["docker", "stop", self.TRAEFIK_CONTAINER_NAME],
                    capture_output=True,
                    check=True,
                    timeout=30,
                )
                subprocess.run(
                    ["docker", "rm", self.TRAEFIK_CONTAINER_NAME],
                    capture_output=True,
                    check=False,  # OK if container doesn't exist
                    timeout=10,
                )
                messages.append("Traefik stopped")
            except subprocess.SubprocessError as e:
                return InfraResult(False, f"Failed to stop Traefik: {e}")

        # Remove network if requested
        if remove_network:
            try:
                subprocess.run(
                    ["docker", "network", "rm", self.config.network_name],
                    capture_output=True,
                    check=True,
                    timeout=10,
                )
                messages.append(f"Network {self.config.network_name} removed")
            except subprocess.CalledProcessError:
                messages.append(f"Network {self.config.network_name} not removed (may be in use)")

        return InfraResult(True, "; ".join(messages) if messages else "Infrastructure stopped")

    def status(self) -> InfraStatus:
        """Get the current status of the infrastructure.

        Returns:
            InfraStatus with current state information
        """
        status = InfraStatus()

        # Check network
        status.network_name = self.config.network_name
        status.network_exists = self._network_exists()

        # Check Traefik
        status.traefik_running = self._is_traefik_running()
        if status.traefik_running:
            status.traefik_container_id = self._get_traefik_container_id()
            status.traefik_url = f"https://traefik.localhost:{self.config.traefik.https_port}"

        # Check certificates
        status.certificates_path = str(self.certs_dir)
        status.certificates_valid = self.mkcert.cert_exists(str(self.certs_dir))

        # Get registered projects
        status.registered_projects = [p.__dict__ for p in self.get_registered_projects()]

        # Check remote context / tunnel status
        if self.remote_config and self.remote_config.enabled:
            status.remote_configured = True
            status.remote_host = self.remote_config.host

            from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

            tunnel = SSHTunnelProvider(self.remote_config)
            health = tunnel.health()
            status.tunnel_status = health.status.value
            status.tunnel_latency_ms = health.latency_ms

        return status

    def doctor(self) -> dict[str, Any]:
        """Run diagnostics on infrastructure prerequisites.

        Returns:
            Dictionary with diagnostic information
        """
        return {
            "docker": {
                "available": self.docker.is_available(),
                "daemon_running": self.docker.is_authenticated(),
                "version": self.docker.get_version(),
            },
            "mkcert": {
                "available": self.mkcert.is_available(),
                "ca_installed": self.mkcert.is_ca_installed(),
                "ca_root": self.mkcert.get_ca_root(),
                "version": self.mkcert.get_version(),
            },
            "infrastructure": {
                "network_exists": self._network_exists(),
                "traefik_running": self._is_traefik_running(),
                "certificates_exist": self.mkcert.cert_exists(str(self.certs_dir)),
                "devflow_home": str(self.DEVFLOW_HOME),
            },
        }

    # -------------------------------------------------------------------------
    # Remote Context / Tunnel Management
    # -------------------------------------------------------------------------

    def _ensure_tunnel_running(self) -> tuple[bool, str, dict | None]:
        """Ensure SSH tunnel is running for remote context.

        Returns:
            Tuple of (success, message, tunnel_info_dict).
        """
        if not self.remote_config:
            return True, "No remote config", None

        from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider
        from devflow.providers.remote.tunnel import TunnelStatus

        tunnel = SSHTunnelProvider(self.remote_config)

        if not tunnel.is_available():
            return False, "SSH is not available on this system", None

        health = tunnel.health()

        if health.status == TunnelStatus.RUNNING:
            return True, "Tunnel already running", health.to_dict()

        # Start the tunnel
        try:
            tunnel.start()

            # Wait for tunnel to establish connection
            import time

            for _ in range(10):
                time.sleep(1)
                health = tunnel.health()
                if health.status == TunnelStatus.RUNNING:
                    return True, "Tunnel started", health.to_dict()

            return False, "Tunnel failed to establish connection", health.to_dict()

        except RuntimeError as e:
            return False, str(e), None

    # -------------------------------------------------------------------------
    # Network Management
    # -------------------------------------------------------------------------

    def _network_exists(self) -> bool:
        """Check if the devflow network exists."""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--filter", f"name=^{self.config.network_name}$", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return self.config.network_name in result.stdout.strip().split("\n")
        except subprocess.SubprocessError:
            return False

    def _ensure_network(self) -> tuple[bool, str]:
        """Ensure the devflow network exists.

        Returns:
            Tuple of (success, message)
        """
        if self._network_exists():
            return True, "Network already exists"

        try:
            subprocess.run(
                ["docker", "network", "create", "--driver", "bridge", self.config.network_name],
                capture_output=True,
                check=True,
                timeout=30,
            )
            return True, f"Network {self.config.network_name} created"
        except subprocess.CalledProcessError as e:
            return False, e.stderr if hasattr(e, "stderr") else str(e)

    def create_network(self) -> InfraResult:
        """Create the devflow network.

        Returns:
            InfraResult indicating success or failure
        """
        success, message = self._ensure_network()
        return InfraResult(success, message)

    def remove_network(self) -> InfraResult:
        """Remove the devflow network.

        Returns:
            InfraResult indicating success or failure
        """
        if not self._network_exists():
            return InfraResult(True, "Network does not exist")

        try:
            subprocess.run(
                ["docker", "network", "rm", self.config.network_name],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return InfraResult(True, f"Network {self.config.network_name} removed")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            if "has active endpoints" in stderr:
                return InfraResult(False, "Network is in use by running containers")
            return InfraResult(False, f"Failed to remove network: {stderr}")

    # -------------------------------------------------------------------------
    # Certificate Management
    # -------------------------------------------------------------------------

    def _ensure_certificates(self) -> tuple[bool, str]:
        """Ensure TLS certificates exist.

        Returns:
            Tuple of (success, message)
        """
        if not self.mkcert.is_available():
            return False, "mkcert is not installed. Install it from https://github.com/FiloSottile/mkcert"

        if not self.mkcert.is_ca_installed():
            success, msg = self.mkcert.install_ca()
            if not success:
                return False, f"Failed to install mkcert CA: {msg}"

        if self.mkcert.cert_exists(str(self.certs_dir)):
            return True, "Certificates already exist"

        return self.mkcert.generate_cert(
            domains=self.config.certificates.domains,
            output_dir=str(self.certs_dir),
        )

    def regenerate_certificates(self) -> InfraResult:
        """Regenerate TLS certificates.

        Returns:
            InfraResult indicating success or failure
        """
        if not self.mkcert.is_available():
            return InfraResult(False, "mkcert is not installed")

        success, message = self.mkcert.generate_cert(
            domains=self.config.certificates.domains,
            output_dir=str(self.certs_dir),
        )
        return InfraResult(success, message)

    # -------------------------------------------------------------------------
    # Traefik Management
    # -------------------------------------------------------------------------

    def _is_traefik_running(self) -> bool:
        """Check if Traefik container is running."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name=^{self.TRAEFIK_CONTAINER_NAME}$",
                    "--filter",
                    "status=running",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return self.TRAEFIK_CONTAINER_NAME in result.stdout.strip()
        except subprocess.SubprocessError:
            return False

    def _get_traefik_container_id(self) -> str | None:
        """Get the Traefik container ID."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name=^{self.TRAEFIK_CONTAINER_NAME}$", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            container_id = result.stdout.strip()
            return container_id if container_id else None
        except subprocess.SubprocessError:
            return None

    def _ensure_traefik(self, force_recreate: bool = False) -> tuple[bool, str]:
        """Ensure Traefik is running.

        Args:
            force_recreate: Force recreation even if already running

        Returns:
            Tuple of (success, message)
        """
        if self._is_traefik_running() and not force_recreate:
            return True, "Traefik is already running"

        # Stop existing container if force_recreate
        if force_recreate and self._is_traefik_running():
            subprocess.run(
                ["docker", "stop", self.TRAEFIK_CONTAINER_NAME],
                capture_output=True,
                check=False,
                timeout=30,
            )
            subprocess.run(
                ["docker", "rm", self.TRAEFIK_CONTAINER_NAME],
                capture_output=True,
                check=False,
                timeout=10,
            )

        # Remove stopped container if exists
        subprocess.run(
            ["docker", "rm", self.TRAEFIK_CONTAINER_NAME],
            capture_output=True,
            check=False,
            timeout=10,
        )

        # Use Docker volumes instead of bind mounts to work around Docker Desktop WSL2 bugs
        # where bind-mounted files appear as directories inside containers
        self._ensure_traefik_volumes()

        # Start Traefik using docker run
        # Note: Using Traefik v2.11 due to Docker API compatibility issues with v3.x on Docker Desktop
        try:
            cmd = [
                "docker",
                "run",
                "-d",
                "--name",
                self.TRAEFIK_CONTAINER_NAME,
                "--restart",
                "unless-stopped",
                "-p",
                f"{self.config.traefik.http_port}:80",
                "-p",
                f"{self.config.traefik.https_port}:443",
                "-p",
                f"{self.config.traefik.dashboard_port}:8080",
                "-v",
                f"{get_docker_socket()}:/var/run/docker.sock",
                "-v",
                "devflow-traefik-config:/etc/traefik:ro",
                "-v",
                "devflow-certs:/certs:ro",
                "--network",
                self.config.network_name,
                "--label",
                "traefik.enable=true",
                "--label",
                "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)",
                "--label",
                "traefik.http.routers.dashboard.service=api@internal",
                "--label",
                "traefik.http.routers.dashboard.tls=true",
                "traefik:v2.11",
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )

            return True, "Traefik started"
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if e.stderr else str(e)
            return False, f"Failed to start Traefik: {stderr}"

    def _ensure_traefik_volumes(self) -> None:
        """Create and populate Docker volumes for Traefik config and certs.

        Uses Docker volumes instead of bind mounts to work around Docker Desktop
        WSL2 bugs where bind-mounted files appear as directories inside containers.
        """
        # Create volumes if they don't exist
        subprocess.run(
            ["docker", "volume", "create", "devflow-traefik-config"],
            capture_output=True,
            check=False,
            timeout=10,
        )
        subprocess.run(
            ["docker", "volume", "create", "devflow-certs"],
            capture_output=True,
            check=False,
            timeout=10,
        )

        # Generate config content
        traefik_config = f"""api:
  dashboard: {str(self.config.traefik.dashboard_enabled).lower()}
  insecure: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true

log:
  level: {self.config.traefik.log_level}
"""

        tls_config = """tls:
  certificates:
    - certFile: /certs/cert.pem
      keyFile: /certs/key.pem
  stores:
    default:
      defaultCertificate:
        certFile: /certs/cert.pem
        keyFile: /certs/key.pem
"""

        # Write config to volume using a temporary container
        config_script = f"""
mkdir -p /config/dynamic
cat > /config/traefik.yml << 'TRAEFIK_EOF'
{traefik_config}
TRAEFIK_EOF
cat > /config/dynamic/tls.yml << 'TLS_EOF'
{tls_config}
TLS_EOF
"""
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "devflow-traefik-config:/config",
                "alpine:latest",
                "sh",
                "-c",
                config_script,
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )

        # Copy certificates to volume
        cert_file = self.certs_dir / "cert.pem"
        key_file = self.certs_dir / "key.pem"

        if cert_file.exists() and key_file.exists():
            # Read cert and key content
            cert_content = cert_file.read_text()
            key_content = key_file.read_text()

            # Write to volume using stdin
            cert_cmd = [
                "docker",
                "run",
                "--rm",
                "-i",
                "-v",
                "devflow-certs:/certs",
                "alpine:latest",
                "sh",
                "-c",
                "cat > /certs/cert.pem",
            ]
            subprocess.run(cert_cmd, input=cert_content.encode(), capture_output=True, check=False, timeout=10)

            key_cmd = [
                "docker",
                "run",
                "--rm",
                "-i",
                "-v",
                "devflow-certs:/certs",
                "alpine:latest",
                "sh",
                "-c",
                "cat > /certs/key.pem",
            ]
            subprocess.run(key_cmd, input=key_content.encode(), capture_output=True, check=False, timeout=10)

    def _write_traefik_templates(self) -> None:
        """Write Traefik configuration templates to disk for reference.

        Note: The actual runtime config is written to Docker volumes via
        _ensure_traefik_volumes() to work around Docker Desktop WSL2 bind mount issues.
        These files are kept for documentation and debugging purposes.
        """
        self.infrastructure_dir.mkdir(parents=True, exist_ok=True)
        dynamic_dir = self.infrastructure_dir / "dynamic"
        dynamic_dir.mkdir(parents=True, exist_ok=True)

        # Write static configuration
        traefik_yml = self.infrastructure_dir / "traefik.yml"
        traefik_config = f"""# Traefik Static Configuration
# Generated by devflow infra
# Note: This is a reference copy. Runtime config is in Docker volume devflow-traefik-config.

api:
  dashboard: {str(self.config.traefik.dashboard_enabled).lower()}
  insecure: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true

log:
  level: {self.config.traefik.log_level}
"""
        traefik_yml.write_text(traefik_config)

        # Write dynamic configuration for TLS
        tls_yml = dynamic_dir / "tls.yml"
        tls_config = """# TLS Configuration
# Generated by devflow infra
# Note: This is a reference copy. Runtime config is in Docker volume devflow-traefik-config.

tls:
  certificates:
    - certFile: /certs/cert.pem
      keyFile: /certs/key.pem
  stores:
    default:
      defaultCertificate:
        certFile: /certs/cert.pem
        keyFile: /certs/key.pem
"""
        tls_yml.write_text(tls_config)

    # -------------------------------------------------------------------------
    # Project Registry
    # -------------------------------------------------------------------------

    def get_registered_projects(self) -> list[RegisteredProject]:
        """Get list of registered projects.

        Returns:
            List of RegisteredProject objects
        """
        if not self.projects_file.exists():
            return []

        try:
            with open(self.projects_file) as f:
                data = json.load(f)
            return [RegisteredProject(**p) for p in data.get("projects", [])]
        except (json.JSONDecodeError, TypeError):
            return []

    def register_project(self, project: RegisteredProject) -> InfraResult:
        """Register a project with the infrastructure.

        Args:
            project: Project to register

        Returns:
            InfraResult indicating success or failure
        """
        projects = self.get_registered_projects()

        # Update existing or add new
        existing = next((p for p in projects if p.path == project.path), None)
        if existing:
            projects = [p for p in projects if p.path != project.path]
        projects.append(project)

        return self._save_projects(projects)

    def unregister_project(self, project_path: str) -> InfraResult:
        """Unregister a project from the infrastructure.

        Args:
            project_path: Path to the project to unregister

        Returns:
            InfraResult indicating success or failure
        """
        projects = self.get_registered_projects()
        original_count = len(projects)
        projects = [p for p in projects if p.path != project_path]

        if len(projects) == original_count:
            return InfraResult(False, "Project not found in registry")

        return self._save_projects(projects)

    def _save_projects(self, projects: list[RegisteredProject]) -> InfraResult:
        """Save projects to the registry file.

        Args:
            projects: List of projects to save

        Returns:
            InfraResult indicating success or failure
        """
        self.DEVFLOW_HOME.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.projects_file, "w") as f:
                json.dump(
                    {"projects": [p.__dict__ for p in projects]},
                    f,
                    indent=2,
                )
            return InfraResult(True, "Projects registry updated")
        except OSError as e:
            return InfraResult(False, f"Failed to save projects: {e}")

    # -------------------------------------------------------------------------
    # Hosts File Management
    # -------------------------------------------------------------------------

    def get_hosts_entries(self) -> list[str]:
        """Get devflow-related entries from hosts file.

        Returns:
            List of devflow-managed host entries
        """
        hosts_file = get_hosts_file()
        try:
            with open(hosts_file) as f:
                lines = f.readlines()

            # Find entries with devflow marker
            entries = []
            in_devflow_section = False
            for line in lines:
                if "# devflow-managed-start" in line:
                    in_devflow_section = True
                    continue
                if "# devflow-managed-end" in line:
                    in_devflow_section = False
                    continue
                if in_devflow_section and line.strip():
                    entries.append(line.strip())

            return entries
        except OSError:
            return []

    def add_hosts_entries(self, domains: list[str]) -> InfraResult:
        """Add domains to the system hosts file.

        Note: This requires sudo/root access on Unix-like systems,
        or Administrator access on Windows.

        Args:
            domains: List of domains to add

        Returns:
            InfraResult indicating success or failure
        """
        hosts_file = get_hosts_file()

        # Generate hosts entries
        entries = [f"127.0.0.1 {domain}" for domain in domains if not domain.startswith("*")]

        # For wildcard domains, we can't add them directly - just skip with a note
        wildcard_domains = [d for d in domains if d.startswith("*")]

        if not entries:
            return InfraResult(
                True,
                "No non-wildcard domains to add. Wildcard domains require DNS or browser configuration.",
                {"wildcard_domains": wildcard_domains},
            )

        # Read current hosts file
        try:
            with open(hosts_file) as f:
                content = f.read()
        except OSError as e:
            return InfraResult(False, f"Cannot read {hosts_file}: {e}")

        # Check if devflow section exists
        if "# devflow-managed-start" in content:
            # Remove existing section
            lines = content.split("\n")
            new_lines = []
            skip = False
            for line in lines:
                if "# devflow-managed-start" in line:
                    skip = True
                    continue
                if "# devflow-managed-end" in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)
            content = "\n".join(new_lines)

        # Add new section
        section = "\n# devflow-managed-start\n"
        section += "\n".join(entries)
        section += "\n# devflow-managed-end\n"

        content = content.rstrip() + section

        # Write back - this typically requires sudo/admin access
        try:
            with open(hosts_file, "w") as f:
                f.write(content)
            return InfraResult(True, f"Added {len(entries)} hosts entries")
        except PermissionError:
            # Return instructions for manual update
            return InfraResult(
                False,
                f"Permission denied. Run with elevated privileges or manually add to {hosts_file}:\n" + section,
                {"entries": entries},
            )
        except OSError as e:
            return InfraResult(False, f"Failed to write {hosts_file}: {e}")

    def remove_hosts_entries(self) -> InfraResult:
        """Remove devflow-managed entries from the system hosts file.

        Returns:
            InfraResult indicating success or failure
        """
        hosts_file = get_hosts_file()
        try:
            with open(hosts_file) as f:
                content = f.read()

            if "# devflow-managed-start" not in content:
                return InfraResult(True, "No devflow entries found")

            # Remove devflow section
            lines = content.split("\n")
            new_lines = []
            skip = False
            for line in lines:
                if "# devflow-managed-start" in line:
                    skip = True
                    continue
                if "# devflow-managed-end" in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)

            content = "\n".join(new_lines)

            with open(hosts_file, "w") as f:
                f.write(content)
            return InfraResult(True, "Devflow hosts entries removed")
        except PermissionError:
            return InfraResult(False, f"Permission denied. Run with elevated privileges to modify {hosts_file}")
        except OSError as e:
            return InfraResult(False, f"Failed to modify {hosts_file}: {e}")
