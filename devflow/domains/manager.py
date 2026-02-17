"""Domain manager for DevFlow."""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from devflow.core.paths import get_devflow_home, get_hosts_file

from .models import CertificateInfo, DomainRegistry, DomainsListResponse, DomainStatus, ManagedDomain

if TYPE_CHECKING:
    from devflow.providers.infrastructure import InfrastructureProvider


class DomainManager:
    """Central manager for domains, certificates, and DNS."""

    # Default domains that are always included
    DEFAULT_DOMAINS = ["*.localhost", "localhost"]

    def __init__(self, infra_provider: "InfrastructureProvider"):
        """Initialize the domain manager.

        Args:
            infra_provider: The infrastructure provider instance.
        """
        self.infra = infra_provider
        self.mkcert = infra_provider.mkcert
        self.registry_path = get_devflow_home() / "domains.json"
        self.certs_dir = infra_provider.certs_dir

    def _load_registry(self) -> DomainRegistry:
        """Load the domain registry from disk."""
        if not self.registry_path.exists():
            # Initialize with default domains
            registry = DomainRegistry()
            for domain in self.DEFAULT_DOMAINS:
                registry.add_domain(ManagedDomain.create(domain, source="default"))
            return registry

        try:
            with open(self.registry_path) as f:
                data = json.load(f)
            return DomainRegistry.from_dict(data)
        except (json.JSONDecodeError, OSError):
            # Return default registry on error
            registry = DomainRegistry()
            for domain in self.DEFAULT_DOMAINS:
                registry.add_domain(ManagedDomain.create(domain, source="default"))
            return registry

    def _save_registry(self, registry: DomainRegistry) -> bool:
        """Save the domain registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.registry_path, "w") as f:
                json.dump(registry.to_dict(), f, indent=2)
            return True
        except OSError:
            return False

    # -------------------------------------------------------------------------
    # Domain CRUD
    # -------------------------------------------------------------------------

    def list_domains(self) -> DomainsListResponse:
        """Get all managed domains with their status.

        Returns:
            DomainsListResponse with domains, cert info, and hosts entries.
        """
        registry = self._load_registry()
        cert_info = self.get_cert_info()
        hosts_entries = self._get_hosts_entries()

        # Build domain status list
        statuses = []
        for managed in registry.domains:
            # Check if domain is covered by certificate
            in_cert = self._is_domain_in_cert(managed.domain, cert_info.domains)

            # Check if domain is in hosts file (non-wildcards only)
            in_hosts = False
            if not managed.is_wildcard:
                in_hosts = any(managed.domain in entry for entry in hosts_entries)

            statuses.append(
                DomainStatus(
                    domain=managed.domain,
                    in_certificate=in_cert,
                    in_hosts_file=in_hosts,
                    is_wildcard=managed.is_wildcard,
                    source=managed.source,
                )
            )

        return DomainsListResponse(
            domains=statuses,
            cert_info=cert_info,
            hosts_entries=hosts_entries,
        )

    def add_domain(self, domain: str, source: str = "user") -> tuple[bool, str, bool]:
        """Add a domain to the registry.

        Args:
            domain: The domain to add.
            source: Source of the domain ("user", "project:{name}", "default").

        Returns:
            Tuple of (success, message, needs_cert_regen).
        """
        # Validate domain format
        domain = domain.strip().lower()
        if not domain:
            return False, "Domain cannot be empty", False

        if not self._is_valid_domain(domain):
            return False, f"Invalid domain format: {domain}", False

        registry = self._load_registry()

        if registry.has_domain(domain):
            return False, f"Domain '{domain}' already exists", False

        # Add domain
        managed = ManagedDomain.create(domain, source)
        registry.add_domain(managed)

        if not self._save_registry(registry):
            return False, "Failed to save registry", False

        # Check if cert needs regeneration
        cert_info = self.get_cert_info()
        needs_regen = not self._is_domain_in_cert(domain, cert_info.domains)

        return True, f"Domain '{domain}' added", needs_regen

    def remove_domain(self, domain: str) -> tuple[bool, str, bool]:
        """Remove a domain from the registry.

        Args:
            domain: The domain to remove.

        Returns:
            Tuple of (success, message, needs_cert_regen).
        """
        domain = domain.strip().lower()

        registry = self._load_registry()
        managed = registry.get_domain(domain)

        if not managed:
            return False, f"Domain '{domain}' not found", False

        # Don't allow removing default domains
        if managed.source == "default":
            return False, f"Cannot remove default domain '{domain}'", False

        registry.remove_domain(domain)

        if not self._save_registry(registry):
            return False, "Failed to save registry", False

        # Cert should be regenerated to remove the domain
        return True, f"Domain '{domain}' removed", True

    def get_domains_for_project(self, project_name: str) -> list[str]:
        """Get domains associated with a specific project.

        Args:
            project_name: The project name.

        Returns:
            List of domain names for the project.
        """
        registry = self._load_registry()
        source_prefix = f"project:{project_name}"
        return [d.domain for d in registry.domains if d.source.startswith(source_prefix)]

    # -------------------------------------------------------------------------
    # Certificate Management
    # -------------------------------------------------------------------------

    def get_cert_info(self) -> CertificateInfo:
        """Get information about the current certificate.

        Returns:
            CertificateInfo with certificate details.
        """
        cert_path = self.certs_dir / "cert.pem"

        if not cert_path.exists():
            return CertificateInfo.empty(str(self.certs_dir))

        domains = self.mkcert.get_cert_domains(str(cert_path))
        expires_at = self.mkcert.get_cert_expiry(str(cert_path))
        issuer = self.mkcert.get_cert_issuer(str(cert_path))

        return CertificateInfo(
            valid=bool(domains),
            path=str(self.certs_dir),
            domains=domains,
            expires_at=expires_at,
            issuer=issuer,
        )

    def regenerate_certs(self) -> tuple[bool, str, int]:
        """Regenerate certificates with all registered domains.

        Returns:
            Tuple of (success, message, domains_count).
        """
        registry = self._load_registry()
        domains = registry.get_all_domain_names()

        if not domains:
            return False, "No domains registered", 0

        result = self.infra.regenerate_certificates(domains=domains)

        if result.success:
            # Update registry with last cert update time
            registry.last_cert_update = datetime.now().isoformat()
            self._save_registry(registry)

            # Sync to Docker volumes
            self.sync_certs_to_docker()

        return result.success, result.message, len(domains)

    def sync_certs_to_docker(self) -> tuple[bool, str]:
        """Sync certificates to Docker volumes.

        Returns:
            Tuple of (success, message).
        """
        result = self.infra.sync_certs_to_docker()
        return result.success, result.message

    # -------------------------------------------------------------------------
    # DNS / Hosts Management
    # -------------------------------------------------------------------------

    def get_hosts_status(self) -> dict[str, bool]:
        """Get hosts file status for each non-wildcard domain.

        Returns:
            Dictionary mapping domain names to whether they're in /etc/hosts.
        """
        registry = self._load_registry()
        hosts_entries = self._get_hosts_entries()

        status = {}
        for managed in registry.domains:
            if not managed.is_wildcard:
                status[managed.domain] = any(managed.domain in entry for entry in hosts_entries)

        return status

    def update_hosts_file(self) -> tuple[bool, str, int]:
        """Add missing non-wildcard domains to /etc/hosts.

        Returns:
            Tuple of (success, message, entries_added).
        """
        registry = self._load_registry()
        hosts_entries = self._get_hosts_entries()

        # Find domains that need to be added
        domains_to_add = []
        for managed in registry.domains:
            if not managed.is_wildcard:
                if not any(managed.domain in entry for entry in hosts_entries):
                    domains_to_add.append(managed.domain)

        if not domains_to_add:
            return True, "All domains already in hosts file", 0

        result = self.infra.add_hosts_entries(domains_to_add)

        if result.success:
            return True, result.message, len(domains_to_add)
        return False, result.message, 0

    def _get_hosts_entries(self) -> list[str]:
        """Get devflow-managed entries from hosts file."""
        return self.infra.get_hosts_entries()

    # -------------------------------------------------------------------------
    # Validation Helpers
    # -------------------------------------------------------------------------

    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format."""
        import re

        # Allow wildcards like *.example.com
        if domain.startswith("*."):
            domain = domain[2:]  # Remove wildcard prefix for validation

        # Basic domain validation regex
        pattern = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$"
        return bool(re.match(pattern, domain))

    def _is_domain_in_cert(self, domain: str, cert_domains: list[str]) -> bool:
        """Check if a domain is covered by the certificate.

        Handles wildcard matching (e.g., *.localhost covers foo.localhost).
        """
        if domain in cert_domains:
            return True

        # Check if covered by wildcard
        if not domain.startswith("*."):
            for cert_domain in cert_domains:
                if cert_domain.startswith("*."):
                    suffix = cert_domain[1:]  # e.g., ".localhost"
                    if domain.endswith(suffix) and domain.count(".") == 1:
                        return True

        return False

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_registry_path(self) -> Path:
        """Get the path to the domain registry file."""
        return self.registry_path

    def needs_cert_regeneration(self) -> bool:
        """Check if certificates need to be regenerated.

        Returns True if registered domains don't match certificate domains.
        """
        registry = self._load_registry()
        cert_info = self.get_cert_info()

        if not cert_info.valid:
            return True

        registered = set(registry.get_all_domain_names())
        in_cert = set(cert_info.domains)

        return registered != in_cert
