"""Data models for domain management."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ManagedDomain:
    """A domain managed by DevFlow."""

    domain: str  # e.g., "*.localhost", "myapp.dev"
    is_wildcard: bool  # True if starts with "*."
    source: str  # "user" | "project:{name}" | "default"
    added_at: str  # ISO timestamp

    @classmethod
    def create(cls, domain: str, source: str = "user") -> "ManagedDomain":
        """Create a new managed domain."""
        return cls(
            domain=domain,
            is_wildcard=domain.startswith("*."),
            source=source,
            added_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "is_wildcard": self.is_wildcard,
            "source": self.source,
            "added_at": self.added_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ManagedDomain":
        """Create from dictionary."""
        return cls(
            domain=data["domain"],
            is_wildcard=data.get("is_wildcard", data["domain"].startswith("*.")),
            source=data.get("source", "user"),
            added_at=data.get("added_at", datetime.now().isoformat()),
        )


@dataclass
class DomainRegistry:
    """Registry of all managed domains."""

    domains: list[ManagedDomain] = field(default_factory=list)
    last_cert_update: str | None = None  # ISO timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "domains": [d.to_dict() for d in self.domains],
            "last_cert_update": self.last_cert_update,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DomainRegistry":
        """Create from dictionary."""
        return cls(
            domains=[ManagedDomain.from_dict(d) for d in data.get("domains", [])],
            last_cert_update=data.get("last_cert_update"),
        )

    def get_domain(self, domain: str) -> ManagedDomain | None:
        """Get a domain by name."""
        for d in self.domains:
            if d.domain == domain:
                return d
        return None

    def has_domain(self, domain: str) -> bool:
        """Check if a domain is registered."""
        return any(d.domain == domain for d in self.domains)

    def add_domain(self, domain: ManagedDomain) -> bool:
        """Add a domain to the registry.

        Returns False if domain already exists.
        """
        if self.has_domain(domain.domain):
            return False
        self.domains.append(domain)
        return True

    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from the registry.

        Returns False if domain not found.
        """
        original_count = len(self.domains)
        self.domains = [d for d in self.domains if d.domain != domain]
        return len(self.domains) < original_count

    def get_all_domain_names(self) -> list[str]:
        """Get list of all domain names."""
        return [d.domain for d in self.domains]


@dataclass
class CertificateInfo:
    """Information about the current SSL certificate."""

    valid: bool
    path: str
    domains: list[str]  # Domains in the cert
    expires_at: str | None  # ISO timestamp
    issuer: str | None  # "mkcert ..."

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "path": self.path,
            "domains": self.domains,
            "expires_at": self.expires_at,
            "issuer": self.issuer,
        }

    @classmethod
    def empty(cls, path: str = "") -> "CertificateInfo":
        """Create empty certificate info."""
        return cls(
            valid=False,
            path=path,
            domains=[],
            expires_at=None,
            issuer=None,
        )


@dataclass
class DomainStatus:
    """Status of a single domain."""

    domain: str
    in_certificate: bool  # Is this domain covered by the cert?
    in_hosts_file: bool  # Is there a hosts entry? (non-wildcards only)
    is_wildcard: bool
    source: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "in_certificate": self.in_certificate,
            "in_hosts_file": self.in_hosts_file,
            "is_wildcard": self.is_wildcard,
            "source": self.source,
        }


@dataclass
class DomainsListResponse:
    """Response for domains.list RPC call."""

    domains: list[DomainStatus]
    cert_info: CertificateInfo
    hosts_entries: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "domains": [d.to_dict() for d in self.domains],
            "cert_info": self.cert_info.to_dict(),
            "hosts_entries": self.hosts_entries,
        }
