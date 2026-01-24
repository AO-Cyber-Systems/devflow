"""SSH provider for remote server operations."""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from devflow.core.paths import get_ssh_dir
from devflow.providers.base import Provider


@dataclass
class SSHResult:
    """Result of an SSH command execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int


@dataclass
class SSHTunnel:
    """Represents an active SSH tunnel."""

    local_port: int
    remote_host: str
    remote_port: int
    process: subprocess.Popen

    def close(self) -> None:
        """Close the SSH tunnel."""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def is_active(self) -> bool:
        """Check if the tunnel is still active."""
        return self.process.poll() is None


class SSHProvider(Provider):
    """Wrapper for SSH operations."""

    @property
    def name(self) -> str:
        return "ssh"

    @property
    def binary(self) -> str:
        return "ssh"

    def is_available(self) -> bool:
        """Check if SSH is installed."""
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        """Check if SSH is available (no authentication check needed for SSH)."""
        return self.is_available()

    def get_ssh_dir(self) -> Path:
        """Get SSH directory for current platform.

        Returns:
            Path to the SSH configuration directory.
        """
        return get_ssh_dir()

    def get_ssh_key_path(self, key_name: str = "id_rsa") -> Path:
        """Get SSH key path for current platform.

        Args:
            key_name: Name of the SSH key file.

        Returns:
            Path to the SSH key file.
        """
        return self.get_ssh_dir() / key_name

    def get_known_hosts_path(self) -> Path:
        """Get known_hosts file path for current platform.

        Returns:
            Path to the known_hosts file.
        """
        return self.get_ssh_dir() / "known_hosts"

    def get_ssh_config_path(self) -> Path:
        """Get SSH config file path for current platform.

        Returns:
            Path to the SSH config file.
        """
        return self.get_ssh_dir() / "config"

    def execute(
        self,
        host: str,
        user: str,
        command: str,
        key_path: str | None = None,
        timeout: int = 60,
    ) -> SSHResult:
        """Execute a command on a remote host via SSH.

        Args:
            host: Remote hostname or IP
            user: SSH username
            command: Command to execute
            key_path: Path to SSH private key (optional)
            timeout: Command timeout in seconds

        Returns:
            SSHResult with command output
        """
        args = [self.binary]

        # Add identity file if provided
        if key_path:
            args.extend(["-i", key_path])

        # Disable strict host key checking for automation
        # Reason: This is intended for internal/trusted infrastructure
        args.extend(["-o", "StrictHostKeyChecking=accept-new"])
        args.extend(["-o", "BatchMode=yes"])

        # Connect timeout
        args.extend(["-o", f"ConnectTimeout={min(timeout, 30)}"])

        # Add user@host
        args.append(f"{user}@{host}")

        # Add command
        args.append(command)

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return SSHResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return SSHResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=-1,
            )
        except Exception as e:
            return SSHResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )

    def create_tunnel(
        self,
        local_port: int,
        remote_host: str,
        remote_port: int,
        ssh_host: str,
        ssh_user: str,
        key_path: str | None = None,
    ) -> SSHTunnel | None:
        """Create an SSH tunnel.

        Args:
            local_port: Local port to bind
            remote_host: Remote host to tunnel to (from SSH server perspective)
            remote_port: Remote port to tunnel to
            ssh_host: SSH server hostname
            ssh_user: SSH username
            key_path: Path to SSH private key (optional)

        Returns:
            SSHTunnel instance if successful, None otherwise
        """
        args = [self.binary, "-N", "-L", f"{local_port}:{remote_host}:{remote_port}"]

        if key_path:
            args.extend(["-i", key_path])

        args.extend(["-o", "StrictHostKeyChecking=accept-new"])
        args.extend(["-o", "ExitOnForwardFailure=yes"])
        args.append(f"{ssh_user}@{ssh_host}")

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Give it a moment to establish or fail
            try:
                process.wait(timeout=2)
                # If it exited, it failed
                return None
            except subprocess.TimeoutExpired:
                # Still running - tunnel established
                return SSHTunnel(
                    local_port=local_port,
                    remote_host=remote_host,
                    remote_port=remote_port,
                    process=process,
                )
        except Exception:
            return None

    def connect(
        self,
        host: str,
        user: str,
        key_path: str | None = None,
    ) -> subprocess.Popen:
        """Start an interactive SSH session.

        Args:
            host: Remote hostname or IP
            user: SSH username
            key_path: Path to SSH private key (optional)

        Returns:
            Popen instance for the SSH process
        """
        args = [self.binary]

        if key_path:
            args.extend(["-i", key_path])

        args.extend(["-o", "StrictHostKeyChecking=accept-new"])
        args.append(f"{user}@{host}")

        # Run interactively
        return subprocess.Popen(args)

    def copy_to_remote(
        self,
        local_path: str,
        remote_path: str,
        host: str,
        user: str,
        key_path: str | None = None,
        timeout: int = 120,
    ) -> SSHResult:
        """Copy a file to a remote host using SCP.

        Args:
            local_path: Local file path
            remote_path: Remote destination path
            host: Remote hostname
            user: SSH username
            key_path: Path to SSH private key (optional)
            timeout: Command timeout in seconds

        Returns:
            SSHResult with operation status
        """
        scp = shutil.which("scp")
        if not scp:
            return SSHResult(
                success=False,
                stdout="",
                stderr="scp not found",
                exit_code=-1,
            )

        args = [scp]

        if key_path:
            args.extend(["-i", key_path])

        args.extend(["-o", "StrictHostKeyChecking=accept-new"])
        args.extend(["-o", "BatchMode=yes"])
        args.append(local_path)
        args.append(f"{user}@{host}:{remote_path}")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return SSHResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return SSHResult(
                success=False,
                stdout="",
                stderr=f"SCP timed out after {timeout} seconds",
                exit_code=-1,
            )
        except Exception as e:
            return SSHResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )

    def write_temp_key(self, key_content: str) -> str:
        """Write SSH key content to a temporary file with proper permissions.

        Args:
            key_content: SSH private key content

        Returns:
            Path to the temporary key file
        """
        fd, path = tempfile.mkstemp(prefix="devflow_ssh_", suffix=".key")
        try:
            os.write(fd, key_content.encode())
            os.close(fd)
            os.chmod(path, 0o600)
            return path
        except Exception:
            os.close(fd)
            os.unlink(path)
            raise

    @staticmethod
    def cleanup_temp_key(path: str) -> None:
        """Remove a temporary key file.

        Args:
            path: Path to the key file
        """
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass
