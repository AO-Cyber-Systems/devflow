"""Abstract tunnel provider interface for remote Docker contexts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TunnelStatus(Enum):
    """Status of a tunnel connection."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class TunnelHealth:
    """Health information for a tunnel."""

    status: TunnelStatus
    pid: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    uptime_seconds: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "pid": self.pid,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "uptime_seconds": self.uptime_seconds,
        }


class TunnelProvider(ABC):
    """Abstract base class for tunnel implementations.

    Tunnel providers handle creating secure connections from the local machine
    to a remote Docker host, forwarding ports so that services running on the
    remote host can be accessed locally.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the tunnel.

        Raises:
            RuntimeError: If the tunnel fails to start.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the tunnel."""
        pass

    @abstractmethod
    def health(self) -> TunnelHealth:
        """Check the health of the tunnel.

        Returns:
            TunnelHealth with current status, latency, and any errors.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this tunnel type is available on the system.

        Returns:
            True if the required tools are installed.
        """
        pass

    def is_running(self) -> bool:
        """Check if the tunnel is currently running.

        Returns:
            True if the tunnel is running.
        """
        return self.health().status == TunnelStatus.RUNNING
