"""Domains RPC handlers."""

from typing import Any

from devflow.core.config import InfrastructureConfig, load_global_config
from devflow.domains.manager import DomainManager
from devflow.providers.infrastructure import InfrastructureProvider


class DomainsHandler:
    """Handler for domain management RPC methods."""

    def __init__(self) -> None:
        self._manager: DomainManager | None = None

    def _get_manager(self) -> DomainManager:
        """Get or create domain manager."""
        if self._manager is None:
            try:
                global_config = load_global_config()
                infra_config = InfrastructureConfig(
                    enabled=True,
                    network_name=global_config.defaults.network_name or "devflow-proxy",
                )
                provider = InfrastructureProvider(infra_config)
                self._manager = DomainManager(provider)
            except Exception:
                # Use default config if global config not found
                provider = InfrastructureProvider(None)
                self._manager = DomainManager(provider)
        return self._manager

    def list(self) -> dict[str, Any]:
        """Get all managed domains with status.

        Returns:
            {domains: [...], cert_info: {...}, hosts_entries: [...]}
        """
        try:
            manager = self._get_manager()
            response = manager.list_domains()
            return response.to_dict()
        except Exception as e:
            return {"error": str(e)}

    def add(self, domain: str, source: str = "user") -> dict[str, Any]:
        """Add a domain to the registry.

        Args:
            domain: The domain to add.
            source: Source of the domain.

        Returns:
            {success, message, needs_cert_regen}
        """
        try:
            manager = self._get_manager()
            success, message, needs_regen = manager.add_domain(domain, source)
            return {
                "success": success,
                "message": message,
                "needs_cert_regen": needs_regen,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove(self, domain: str) -> dict[str, Any]:
        """Remove a domain from the registry.

        Args:
            domain: The domain to remove.

        Returns:
            {success, message, needs_cert_regen}
        """
        try:
            manager = self._get_manager()
            success, message, needs_regen = manager.remove_domain(domain)
            return {
                "success": success,
                "message": message,
                "needs_cert_regen": needs_regen,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_cert_info(self) -> dict[str, Any]:
        """Get certificate information.

        Returns:
            {valid, path, domains, expires_at, issuer}
        """
        try:
            manager = self._get_manager()
            cert_info = manager.get_cert_info()
            return cert_info.to_dict()
        except Exception as e:
            return {"error": str(e)}

    def regenerate_certs(self) -> dict[str, Any]:
        """Regenerate certificates with all registered domains.

        Returns:
            {success, message, domains_count}
        """
        try:
            manager = self._get_manager()
            success, message, count = manager.regenerate_certs()
            return {
                "success": success,
                "message": message,
                "domains_count": count,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_hosts(self) -> dict[str, Any]:
        """Update /etc/hosts with missing entries.

        Returns:
            {success, message, entries_added}
        """
        try:
            manager = self._get_manager()
            success, message, count = manager.update_hosts_file()
            return {
                "success": success,
                "message": message,
                "entries_added": count,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_certs(self) -> dict[str, Any]:
        """Sync certificates to Docker volumes.

        Returns:
            {success, message}
        """
        try:
            manager = self._get_manager()
            success, message = manager.sync_certs_to_docker()
            return {
                "success": success,
                "message": message,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_hosts_status(self) -> dict[str, Any]:
        """Get hosts file status for each domain.

        Returns:
            {domains: {domain: in_hosts_file, ...}}
        """
        try:
            manager = self._get_manager()
            status = manager.get_hosts_status()
            return {"domains": status}
        except Exception as e:
            return {"error": str(e)}

    def needs_regen(self) -> dict[str, Any]:
        """Check if certificates need regeneration.

        Returns:
            {needs_regen: bool}
        """
        try:
            manager = self._get_manager()
            needs = manager.needs_cert_regeneration()
            return {"needs_regen": needs}
        except Exception as e:
            return {"error": str(e)}
