"""SSH-based tunnel provider using autossh or plain SSH."""

import json
import os
import shutil
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from devflow.core.config import RemoteContextConfig
from devflow.core.paths import get_devflow_home
from devflow.providers.remote.tunnel import TunnelHealth, TunnelProvider, TunnelStatus


class SSHTunnelProvider(TunnelProvider):
    """SSH-based tunnel provider using autossh for automatic reconnection.

    Falls back to plain SSH if autossh is not available.
    """

    STATE_FILE = get_devflow_home() / "state" / "tunnel.json"

    def __init__(self, config: RemoteContextConfig):
        """Initialize the SSH tunnel provider.

        Args:
            config: Remote context configuration with host, user, and tunnel settings.
        """
        self.config = config
        self._use_autossh = shutil.which("autossh") is not None

    def is_available(self) -> bool:
        """Check if SSH is available on the system."""
        return shutil.which("ssh") is not None

    def start(self) -> None:
        """Start the SSH tunnel.

        Uses autossh if available for automatic reconnection, otherwise falls back
        to plain SSH with keepalive settings.

        Raises:
            RuntimeError: If the tunnel fails to start.
        """
        if self.is_running():
            return

        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        tunnel_args = self._build_tunnel_args()
        ssh_opts = self._build_ssh_opts()

        if self._use_autossh:
            cmd = [
                "autossh",
                "-M",
                "0",  # Disable autossh monitoring port, use SSH keepalive instead
                "-f",  # Background after authentication
                "-N",  # No remote command
                *ssh_opts,
                *tunnel_args,
                f"{self.config.user}@{self.config.host}",
            ]
        else:
            cmd = [
                "ssh",
                "-f",  # Background after authentication
                "-N",  # No remote command
                *ssh_opts,
                *tunnel_args,
                f"{self.config.user}@{self.config.host}",
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"SSH tunnel failed to start: {result.stderr}")

            # Give SSH time to background and establish connection
            time.sleep(1)

            # Find and save the PID
            pid = self._find_tunnel_pid()
            if pid:
                self._save_state(pid)
            else:
                raise RuntimeError("Tunnel started but PID not found")

        except subprocess.TimeoutExpired:
            raise RuntimeError("SSH tunnel timed out during connection")

    def stop(self) -> None:
        """Stop the SSH tunnel."""
        state = self._load_state()
        if state and state.get("pid"):
            try:
                os.kill(state["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass  # Process already dead
            except PermissionError:
                pass  # Not allowed to kill (shouldn't happen for our process)
        self._clear_state()

    def health(self) -> TunnelHealth:
        """Check the health of the tunnel.

        Returns:
            TunnelHealth with current status, latency, and uptime.
        """
        state = self._load_state()
        if not state:
            return TunnelHealth(status=TunnelStatus.STOPPED)

        pid = state.get("pid")
        if not self._pid_exists(pid):
            return TunnelHealth(
                status=TunnelStatus.FAILED,
                error="Tunnel process died unexpectedly",
            )

        # Test connectivity through the tunnel
        latency = self._measure_latency()
        if latency is None:
            return TunnelHealth(
                status=TunnelStatus.RECONNECTING,
                pid=pid,
                error="Tunnel unresponsive - connection may be recovering",
            )

        uptime = int(time.time() - state.get("started_at", time.time()))
        return TunnelHealth(
            status=TunnelStatus.RUNNING,
            pid=pid,
            latency_ms=latency,
            uptime_seconds=uptime,
        )

    def _build_tunnel_args(self) -> list[str]:
        """Build the -L arguments for SSH port forwarding.

        Returns:
            List of -L arguments for each configured tunnel.
        """
        args = []
        for tunnel in self.config.tunnels:
            # -L local_port:localhost:remote_port
            args.extend(["-L", f"{tunnel.local}:localhost:{tunnel.remote}"])
        return args

    def _build_ssh_opts(self) -> list[str]:
        """Build SSH options for reliable connections.

        Returns:
            List of SSH options.
        """
        opts = [
            "-o",
            "ServerAliveInterval=30",  # Send keepalive every 30 seconds
            "-o",
            "ServerAliveCountMax=3",  # Disconnect after 3 missed keepalives
            "-o",
            "ExitOnForwardFailure=yes",  # Exit if port forwarding fails
            "-o",
            "StrictHostKeyChecking=accept-new",  # Accept new host keys automatically
            "-o",
            "BatchMode=yes",  # Disable password prompts (requires key auth)
            "-p",
            str(self.config.ssh_port),
        ]
        if self.config.ssh_key:
            key_path = Path(self.config.ssh_key).expanduser()
            opts.extend(["-i", str(key_path)])
        return opts

    def _measure_latency(self) -> Optional[float]:
        """Measure latency by connecting to a tunneled port.

        Returns:
            Latency in milliseconds, or None if connection failed.
        """
        if not self.config.tunnels:
            return 0.0  # No tunnels configured, can't measure

        test_port = self.config.tunnels[0].local
        start = time.perf_counter()
        try:
            sock = socket.create_connection(("localhost", test_port), timeout=5)
            sock.close()
            return (time.perf_counter() - start) * 1000
        except (socket.error, socket.timeout, OSError):
            return None

    def _find_tunnel_pid(self) -> Optional[int]:
        """Find the PID of the SSH tunnel process.

        Returns:
            PID if found, None otherwise.
        """
        try:
            # Look for our specific SSH connection
            result = subprocess.run(
                ["pgrep", "-f", f"ssh.*{self.config.host}.*-N"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Return the first matching PID
                return int(result.stdout.strip().split()[0])
        except (subprocess.SubprocessError, ValueError):
            pass
        return None

    def _pid_exists(self, pid: Optional[int]) -> bool:
        """Check if a process with the given PID exists.

        Args:
            pid: Process ID to check.

        Returns:
            True if the process exists.
        """
        if not pid:
            return False
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # Process exists but we can't signal it

    def _save_state(self, pid: int) -> None:
        """Save tunnel state to disk.

        Args:
            pid: Process ID of the tunnel.
        """
        state = {
            "pid": pid,
            "started_at": time.time(),
            "host": self.config.host,
            "user": self.config.user,
            "tunnels": [{"local": t.local, "remote": t.remote} for t in self.config.tunnels],
        }
        self.STATE_FILE.write_text(json.dumps(state, indent=2))

    def _load_state(self) -> Optional[dict]:
        """Load tunnel state from disk.

        Returns:
            State dictionary or None if no state exists.
        """
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _clear_state(self) -> None:
        """Clear saved tunnel state."""
        self.STATE_FILE.unlink(missing_ok=True)
