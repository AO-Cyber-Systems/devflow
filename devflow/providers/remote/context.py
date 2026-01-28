"""Docker context manager for remote development environments."""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional

from devflow.core.config import RemoteContextConfig


@dataclass
class DockerContext:
    """Represents a Docker context."""

    name: str
    description: str
    docker_endpoint: str
    is_current: bool

    def is_devflow_context(self) -> bool:
        """Check if this is a DevFlow-managed context."""
        return self.name.startswith(DockerContextManager.CONTEXT_PREFIX)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "docker_endpoint": self.docker_endpoint,
            "is_current": self.is_current,
            "is_devflow": self.is_devflow_context(),
        }


class DockerContextManager:
    """Manages Docker contexts for local and remote development.

    Docker contexts allow switching between different Docker daemons (local, remote,
    or cloud-based). This manager handles creating SSH-based contexts for remote
    development and switching between them.
    """

    CONTEXT_PREFIX = "devflow-"

    def __init__(self, config: Optional[RemoteContextConfig] = None):
        """Initialize the Docker context manager.

        Args:
            config: Optional remote context configuration.
        """
        self.config = config

    def list_contexts(self) -> list[DockerContext]:
        """List all available Docker contexts.

        Returns:
            List of DockerContext objects.
        """
        try:
            result = subprocess.run(
                ["docker", "context", "ls", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
        except subprocess.SubprocessError:
            return []

        contexts = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                contexts.append(
                    DockerContext(
                        name=data.get("Name", ""),
                        description=data.get("Description", ""),
                        docker_endpoint=data.get("DockerEndpoint", ""),
                        is_current=data.get("Current", False),
                    )
                )
            except json.JSONDecodeError:
                continue

        return contexts

    def create_remote_context(self, name: str, config: RemoteContextConfig) -> tuple[bool, str]:
        """Create a Docker context for remote SSH access.

        Args:
            name: Name for the context (will be prefixed with 'devflow-').
            config: Remote context configuration.

        Returns:
            Tuple of (success, message).
        """
        context_name = f"{self.CONTEXT_PREFIX}{name}"

        # Remove existing context if it exists
        subprocess.run(
            ["docker", "context", "rm", "-f", context_name],
            capture_output=True,
            timeout=10,
        )

        # Build the Docker host URL
        docker_host = f"ssh://{config.user}@{config.host}"
        if config.ssh_port != 22:
            docker_host = f"ssh://{config.user}@{config.host}:{config.ssh_port}"

        try:
            result = subprocess.run(
                [
                    "docker",
                    "context",
                    "create",
                    context_name,
                    "--docker",
                    f"host={docker_host}",
                    "--description",
                    f"DevFlow remote: {config.host}",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return True, f"Created context: {context_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to create context: {e.stderr}"

    def delete_context(self, name: str) -> tuple[bool, str]:
        """Delete a Docker context.

        Args:
            name: Context name (with or without 'devflow-' prefix).

        Returns:
            Tuple of (success, message).
        """
        # Ensure we have the full name
        context_name = name if name.startswith(self.CONTEXT_PREFIX) else f"{self.CONTEXT_PREFIX}{name}"

        # Don't delete non-devflow contexts
        if not context_name.startswith(self.CONTEXT_PREFIX):
            return False, "Can only delete DevFlow-managed contexts"

        # Check if this is the current context
        current = self.current_context()
        if current and current.name == context_name:
            # Switch to default first
            self.use_local()

        try:
            result = subprocess.run(
                ["docker", "context", "rm", "-f", context_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return True, f"Deleted context: {context_name}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to delete context: {e.stderr}"

    def use_context(self, name: str) -> tuple[bool, str]:
        """Switch to a Docker context.

        Args:
            name: Context name (with or without 'devflow-' prefix for DevFlow contexts).

        Returns:
            Tuple of (success, message).
        """
        # For DevFlow contexts, ensure prefix
        if not name.startswith(self.CONTEXT_PREFIX) and name != "default":
            # Check if it's a DevFlow context
            contexts = self.list_contexts()
            devflow_name = f"{self.CONTEXT_PREFIX}{name}"
            if any(c.name == devflow_name for c in contexts):
                name = devflow_name

        try:
            result = subprocess.run(
                ["docker", "context", "use", name],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return True, f"Switched to context: {name}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to switch context: {e.stderr}"

    def use_local(self) -> tuple[bool, str]:
        """Switch back to the default local Docker context.

        Returns:
            Tuple of (success, message).
        """
        return self.use_context("default")

    def current_context(self) -> Optional[DockerContext]:
        """Get the currently active Docker context.

        Returns:
            Current DockerContext or None if not determinable.
        """
        for ctx in self.list_contexts():
            if ctx.is_current:
                return ctx
        return None

    def is_remote(self) -> bool:
        """Check if the current context is a remote DevFlow context.

        Returns:
            True if using a DevFlow remote context.
        """
        current = self.current_context()
        return current is not None and current.is_devflow_context()

    def get_devflow_contexts(self) -> list[DockerContext]:
        """Get only DevFlow-managed contexts.

        Returns:
            List of DevFlow DockerContext objects.
        """
        return [ctx for ctx in self.list_contexts() if ctx.is_devflow_context()]

    def test_connection(self, context_name: Optional[str] = None) -> tuple[bool, str]:
        """Test connection to a Docker context.

        Args:
            context_name: Context to test. If None, tests current context.

        Returns:
            Tuple of (success, message).
        """
        cmd = ["docker"]
        if context_name:
            cmd.extend(["--context", context_name])
        cmd.extend(["info", "--format", "{{.ServerVersion}}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            version = result.stdout.strip()
            return True, f"Connected to Docker {version}"
        except subprocess.CalledProcessError as e:
            return False, f"Connection failed: {e.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
