"""Tests for domains handler."""

from unittest.mock import MagicMock, patch

import pytest

from bridge.handlers.domains import DomainsHandler


@pytest.fixture
def domains_handler() -> DomainsHandler:
    """Create a DomainsHandler for testing."""
    return DomainsHandler()


@pytest.fixture
def mock_manager():
    """Create a mock DomainManager."""
    return MagicMock()


class TestDomainsHandlerList:
    """Tests for list method."""

    def test_list_domains_success(self, domains_handler: DomainsHandler) -> None:
        """Test listing domains successfully."""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "domains": [
                {"domain": "app.local", "source": "default", "in_cert": True},
                {"domain": "api.local", "source": "user", "in_cert": True},
            ],
            "cert_info": {"valid": True, "domains": ["app.local", "api.local"]},
            "hosts_entries": ["127.0.0.1 app.local", "127.0.0.1 api.local"],
        }

        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.list_domains.return_value = mock_response
            mock_get_manager.return_value = mock_manager

            result = domains_handler.list()

            assert len(result["domains"]) == 2
            assert result["domains"][0]["domain"] == "app.local"
            assert result["cert_info"]["valid"] is True

    def test_list_domains_exception(self, domains_handler: DomainsHandler) -> None:
        """Test listing domains when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_get_manager.side_effect = Exception("Config error")

            result = domains_handler.list()

            assert "error" in result
            assert "Config error" in result["error"]


class TestDomainsHandlerAdd:
    """Tests for add method."""

    def test_add_domain_success(self, domains_handler: DomainsHandler) -> None:
        """Test adding a domain successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.add_domain.return_value = (True, "Domain added", True)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.add("new.local", source="user")

            assert result["success"] is True
            assert result["message"] == "Domain added"
            assert result["needs_cert_regen"] is True
            mock_manager.add_domain.assert_called_once_with("new.local", "user")

    def test_add_domain_failure(self, domains_handler: DomainsHandler) -> None:
        """Test adding a domain that fails."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.add_domain.return_value = (False, "Domain already exists", False)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.add("existing.local")

            assert result["success"] is False
            assert "already exists" in result["message"]
            assert result["needs_cert_regen"] is False

    def test_add_domain_exception(self, domains_handler: DomainsHandler) -> None:
        """Test adding a domain when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.add_domain.side_effect = Exception("Write error")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.add("test.local")

            assert result["success"] is False
            assert "Write error" in result["error"]


class TestDomainsHandlerRemove:
    """Tests for remove method."""

    def test_remove_domain_success(self, domains_handler: DomainsHandler) -> None:
        """Test removing a domain successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.remove_domain.return_value = (True, "Domain removed", True)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.remove("old.local")

            assert result["success"] is True
            assert result["message"] == "Domain removed"
            assert result["needs_cert_regen"] is True

    def test_remove_default_domain_fails(self, domains_handler: DomainsHandler) -> None:
        """Test removing a default domain fails."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.remove_domain.return_value = (False, "Cannot remove default domain", False)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.remove("traefik.local")

            assert result["success"] is False
            assert "Cannot remove" in result["message"]

    def test_remove_domain_exception(self, domains_handler: DomainsHandler) -> None:
        """Test removing a domain when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.remove_domain.side_effect = Exception("Permission denied")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.remove("test.local")

            assert result["success"] is False
            assert "Permission denied" in result["error"]


class TestDomainsHandlerCertInfo:
    """Tests for get_cert_info method."""

    def test_get_cert_info_success(self, domains_handler: DomainsHandler) -> None:
        """Test getting certificate info successfully."""
        mock_cert_info = MagicMock()
        mock_cert_info.to_dict.return_value = {
            "valid": True,
            "path": "/path/to/cert.pem",
            "domains": ["app.local", "api.local"],
            "expires_at": "2025-01-01T00:00:00Z",
            "issuer": "mkcert",
        }

        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_cert_info.return_value = mock_cert_info
            mock_get_manager.return_value = mock_manager

            result = domains_handler.get_cert_info()

            assert result["valid"] is True
            assert result["issuer"] == "mkcert"
            assert len(result["domains"]) == 2

    def test_get_cert_info_exception(self, domains_handler: DomainsHandler) -> None:
        """Test getting certificate info when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_get_manager.side_effect = Exception("Cert not found")

            result = domains_handler.get_cert_info()

            assert "error" in result
            assert "Cert not found" in result["error"]


class TestDomainsHandlerRegenerateCerts:
    """Tests for regenerate_certs method."""

    def test_regenerate_certs_success(self, domains_handler: DomainsHandler) -> None:
        """Test regenerating certificates successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.regenerate_certs.return_value = (True, "Certificates regenerated", 5)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.regenerate_certs()

            assert result["success"] is True
            assert result["domains_count"] == 5

    def test_regenerate_certs_failure(self, domains_handler: DomainsHandler) -> None:
        """Test regenerating certificates when it fails."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.regenerate_certs.return_value = (False, "mkcert not installed", 0)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.regenerate_certs()

            assert result["success"] is False
            assert "mkcert" in result["message"]

    def test_regenerate_certs_exception(self, domains_handler: DomainsHandler) -> None:
        """Test regenerating certificates when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.regenerate_certs.side_effect = Exception("mkcert failed")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.regenerate_certs()

            assert result["success"] is False
            assert "mkcert failed" in result["error"]


class TestDomainsHandlerUpdateHosts:
    """Tests for update_hosts method."""

    def test_update_hosts_success(self, domains_handler: DomainsHandler) -> None:
        """Test updating hosts file successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.update_hosts_file.return_value = (True, "Hosts updated", 3)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.update_hosts()

            assert result["success"] is True
            assert result["entries_added"] == 3

    def test_update_hosts_no_changes(self, domains_handler: DomainsHandler) -> None:
        """Test updating hosts when no changes needed."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.update_hosts_file.return_value = (True, "No changes needed", 0)
            mock_get_manager.return_value = mock_manager

            result = domains_handler.update_hosts()

            assert result["success"] is True
            assert result["entries_added"] == 0

    def test_update_hosts_exception(self, domains_handler: DomainsHandler) -> None:
        """Test updating hosts when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.update_hosts_file.side_effect = Exception("Permission denied")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.update_hosts()

            assert result["success"] is False
            assert "Permission denied" in result["error"]


class TestDomainsHandlerSyncCerts:
    """Tests for sync_certs method."""

    def test_sync_certs_success(self, domains_handler: DomainsHandler) -> None:
        """Test syncing certificates to Docker successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.sync_certs_to_docker.return_value = (True, "Certificates synced")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.sync_certs()

            assert result["success"] is True
            assert "synced" in result["message"]

    def test_sync_certs_exception(self, domains_handler: DomainsHandler) -> None:
        """Test syncing certificates when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.sync_certs_to_docker.side_effect = Exception("Docker not running")
            mock_get_manager.return_value = mock_manager

            result = domains_handler.sync_certs()

            assert result["success"] is False
            assert "Docker not running" in result["error"]


class TestDomainsHandlerHostsStatus:
    """Tests for get_hosts_status method."""

    def test_get_hosts_status_success(self, domains_handler: DomainsHandler) -> None:
        """Test getting hosts status successfully."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_hosts_status.return_value = {
                "app.local": True,
                "api.local": True,
                "new.local": False,
            }
            mock_get_manager.return_value = mock_manager

            result = domains_handler.get_hosts_status()

            assert result["domains"]["app.local"] is True
            assert result["domains"]["new.local"] is False

    def test_get_hosts_status_exception(self, domains_handler: DomainsHandler) -> None:
        """Test getting hosts status when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_get_manager.side_effect = Exception("File read error")

            result = domains_handler.get_hosts_status()

            assert "error" in result


class TestDomainsHandlerNeedsRegen:
    """Tests for needs_regen method."""

    def test_needs_regen_true(self, domains_handler: DomainsHandler) -> None:
        """Test checking if regen is needed (yes)."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.needs_cert_regeneration.return_value = True
            mock_get_manager.return_value = mock_manager

            result = domains_handler.needs_regen()

            assert result["needs_regen"] is True

    def test_needs_regen_false(self, domains_handler: DomainsHandler) -> None:
        """Test checking if regen is needed (no)."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.needs_cert_regeneration.return_value = False
            mock_get_manager.return_value = mock_manager

            result = domains_handler.needs_regen()

            assert result["needs_regen"] is False

    def test_needs_regen_exception(self, domains_handler: DomainsHandler) -> None:
        """Test checking regen when an exception occurs."""
        with patch.object(domains_handler, "_get_manager") as mock_get_manager:
            mock_get_manager.side_effect = Exception("Manager error")

            result = domains_handler.needs_regen()

            assert "error" in result


class TestDomainsHandlerGetManager:
    """Tests for _get_manager method."""

    def test_get_manager_creates_once(self, domains_handler: DomainsHandler) -> None:
        """Test that manager is created only once (cached)."""
        with patch("bridge.handlers.domains.load_global_config") as mock_load:
            with patch("bridge.handlers.domains.InfrastructureProvider") as mock_provider:
                with patch("bridge.handlers.domains.DomainManager") as mock_domain_manager:
                    mock_config = MagicMock()
                    mock_config.defaults.network_name = "test-network"
                    mock_load.return_value = mock_config

                    # Call twice
                    domains_handler._get_manager()
                    domains_handler._get_manager()

                    # Should only create manager once
                    assert mock_domain_manager.call_count == 1

    def test_get_manager_fallback_on_config_error(self, domains_handler: DomainsHandler) -> None:
        """Test that manager falls back when config fails."""
        with patch("bridge.handlers.domains.load_global_config") as mock_load:
            with patch("bridge.handlers.domains.InfrastructureProvider") as mock_provider:
                with patch("bridge.handlers.domains.DomainManager") as mock_domain_manager:
                    mock_load.side_effect = Exception("Config not found")

                    domains_handler._get_manager()

                    # Should create manager with None config
                    mock_provider.assert_called_once_with(None)
