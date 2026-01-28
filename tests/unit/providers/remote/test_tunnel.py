"""Tests for tunnel provider interface."""

from devflow.providers.remote.tunnel import TunnelHealth, TunnelStatus


class TestTunnelStatus:
    """Tests for TunnelStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values exist."""
        assert TunnelStatus.STOPPED.value == "stopped"
        assert TunnelStatus.STARTING.value == "starting"
        assert TunnelStatus.RUNNING.value == "running"
        assert TunnelStatus.RECONNECTING.value == "reconnecting"
        assert TunnelStatus.FAILED.value == "failed"


class TestTunnelHealth:
    """Tests for TunnelHealth dataclass."""

    def test_default_values(self) -> None:
        """Test health with default values."""
        health = TunnelHealth(status=TunnelStatus.STOPPED)
        assert health.status == TunnelStatus.STOPPED
        assert health.pid is None
        assert health.latency_ms is None
        assert health.error is None
        assert health.uptime_seconds is None

    def test_running_health(self) -> None:
        """Test health when tunnel is running."""
        health = TunnelHealth(
            status=TunnelStatus.RUNNING,
            pid=12345,
            latency_ms=5.2,
            uptime_seconds=3600,
        )
        assert health.status == TunnelStatus.RUNNING
        assert health.pid == 12345
        assert health.latency_ms == 5.2
        assert health.uptime_seconds == 3600
        assert health.error is None

    def test_failed_health(self) -> None:
        """Test health when tunnel has failed."""
        health = TunnelHealth(
            status=TunnelStatus.FAILED,
            error="Connection refused",
        )
        assert health.status == TunnelStatus.FAILED
        assert health.error == "Connection refused"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        health = TunnelHealth(
            status=TunnelStatus.RUNNING,
            pid=12345,
            latency_ms=5.2,
            uptime_seconds=3600,
        )
        result = health.to_dict()

        assert result["status"] == "running"
        assert result["pid"] == 12345
        assert result["latency_ms"] == 5.2
        assert result["uptime_seconds"] == 3600
        assert result["error"] is None

    def test_to_dict_with_error(self) -> None:
        """Test dictionary conversion with error."""
        health = TunnelHealth(
            status=TunnelStatus.FAILED,
            error="Connection timeout",
        )
        result = health.to_dict()

        assert result["status"] == "failed"
        assert result["error"] == "Connection timeout"
