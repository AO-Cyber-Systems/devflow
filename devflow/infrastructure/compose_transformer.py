"""Docker Compose transformer for shared infrastructure integration."""

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from devflow.core.config import InfrastructureConfig


@dataclass
class ValidationError:
    """Validation error in compose file."""

    file: str
    message: str
    line: Optional[int] = None
    severity: str = "error"  # error, warning


@dataclass
class TransformResult:
    """Result of a compose file transformation."""

    success: bool
    message: str
    backup_path: Optional[str] = None
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[ValidationError] = field(default_factory=list)


class ComposeTransformer:
    """Transform docker-compose files to use shared infrastructure.

    This transformer modifies project docker-compose files to:
    1. Replace project-specific networks with the devflow-proxy network
    2. Remove embedded Traefik services (if present)
    3. Update network references in services
    4. Preserve backward compatibility via network aliases
    """

    BACKUP_SUFFIX = ".devflow-backup"
    TRAEFIK_IMAGE_PATTERNS = [
        r"traefik:.*",
        r"traefik/traefik:.*",
    ]

    def __init__(self, config: Optional[InfrastructureConfig] = None):
        """Initialize the transformer.

        Args:
            config: Infrastructure configuration. Uses defaults if not provided.
        """
        self.config = config or InfrastructureConfig()

    def transform(self, compose_path: Path, dry_run: bool = False) -> TransformResult:
        """Transform a compose file to use shared infrastructure.

        Args:
            compose_path: Path to the docker-compose.yml file
            dry_run: If True, don't modify files, just report what would change

        Returns:
            TransformResult with changes made or errors encountered
        """
        compose_path = Path(compose_path)

        if not compose_path.exists():
            return TransformResult(
                success=False,
                message=f"File not found: {compose_path}",
            )

        # Read and parse the compose file
        try:
            with open(compose_path) as f:
                compose_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return TransformResult(
                success=False,
                message=f"Failed to parse YAML: {e}",
            )

        if not compose_data:
            return TransformResult(
                success=False,
                message="Empty compose file",
            )

        changes = []
        warnings = []

        # Track original networks for reference
        original_networks = self._get_network_names(compose_data)

        # Transform networks section
        compose_data, network_changes = self._transform_networks(compose_data)
        changes.extend(network_changes)

        # Transform services section
        compose_data, service_changes, service_warnings = self._transform_services(
            compose_data, original_networks
        )
        changes.extend(service_changes)
        warnings.extend(service_warnings)

        # Detect and handle embedded Traefik
        traefik_service = self._find_traefik_service(compose_data)
        if traefik_service:
            compose_data, traefik_changes = self._remove_traefik_service(compose_data, traefik_service)
            changes.extend(traefik_changes)
            warnings.append(
                f"Removed embedded Traefik service '{traefik_service}'. "
                "Use 'devflow infra up' to start the shared Traefik instance."
            )

        if not changes:
            return TransformResult(
                success=True,
                message="No changes needed - compose file is already configured",
                changes=[],
            )

        if dry_run:
            return TransformResult(
                success=True,
                message=f"Dry run - {len(changes)} changes would be made",
                changes=changes,
                warnings=warnings,
            )

        # Create backup
        backup_path = self.backup(compose_path)

        # Write transformed file
        try:
            with open(compose_path, "w") as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except OSError as e:
            return TransformResult(
                success=False,
                message=f"Failed to write transformed file: {e}",
                backup_path=str(backup_path),
            )

        return TransformResult(
            success=True,
            message=f"Transformed {compose_path.name} with {len(changes)} changes",
            backup_path=str(backup_path),
            changes=changes,
            warnings=warnings,
        )

    def backup(self, compose_path: Path) -> Path:
        """Create a backup of the compose file.

        Args:
            compose_path: Path to the compose file

        Returns:
            Path to the backup file
        """
        compose_path = Path(compose_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = compose_path.parent / f"{compose_path.name}{self.BACKUP_SUFFIX}.{timestamp}"
        shutil.copy2(compose_path, backup_path)
        return backup_path

    def restore(self, compose_path: Path) -> bool:
        """Restore a compose file from the most recent backup.

        Args:
            compose_path: Path to the compose file

        Returns:
            True if restoration was successful
        """
        compose_path = Path(compose_path)
        backup_pattern = f"{compose_path.name}{self.BACKUP_SUFFIX}.*"

        # Find most recent backup
        backups = list(compose_path.parent.glob(backup_pattern))
        if not backups:
            return False

        # Sort by modification time and get the most recent
        most_recent = max(backups, key=lambda p: p.stat().st_mtime)
        shutil.copy2(most_recent, compose_path)
        return True

    def get_backups(self, compose_path: Path) -> list[Path]:
        """Get list of backup files for a compose file.

        Args:
            compose_path: Path to the compose file

        Returns:
            List of backup file paths, sorted by modification time (newest first)
        """
        compose_path = Path(compose_path)
        backup_pattern = f"{compose_path.name}{self.BACKUP_SUFFIX}.*"
        backups = list(compose_path.parent.glob(backup_pattern))
        return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)

    def validate(self, compose_path: Path) -> list[ValidationError]:
        """Validate a compose file after transformation.

        Args:
            compose_path: Path to the compose file

        Returns:
            List of validation errors/warnings
        """
        compose_path = Path(compose_path)
        errors = []

        if not compose_path.exists():
            errors.append(ValidationError(
                file=str(compose_path),
                message="File does not exist",
            ))
            return errors

        try:
            with open(compose_path) as f:
                compose_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(ValidationError(
                file=str(compose_path),
                message=f"Invalid YAML: {e}",
            ))
            return errors

        # Check networks section
        networks = compose_data.get("networks", {})
        if self.config.network_name not in networks:
            errors.append(ValidationError(
                file=str(compose_path),
                message=f"Missing network '{self.config.network_name}'",
                severity="warning",
            ))

        # Check services use the correct network
        services = compose_data.get("services", {})
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue

            service_networks = service_config.get("networks", [])
            if isinstance(service_networks, list):
                # Check if any legacy network is used
                for net in service_networks:
                    if net in self.config.legacy_networks and net != self.config.network_name:
                        errors.append(ValidationError(
                            file=str(compose_path),
                            message=f"Service '{service_name}' uses legacy network '{net}'",
                            severity="warning",
                        ))

        return errors

    def _get_network_names(self, compose_data: dict) -> set[str]:
        """Get all network names defined or referenced in the compose file.

        Args:
            compose_data: Parsed compose file data

        Returns:
            Set of network names
        """
        networks = set()

        # From networks section
        if "networks" in compose_data:
            networks.update(compose_data["networks"].keys())

        # From services
        for service_config in compose_data.get("services", {}).values():
            if isinstance(service_config, dict):
                service_networks = service_config.get("networks", [])
                if isinstance(service_networks, list):
                    networks.update(service_networks)
                elif isinstance(service_networks, dict):
                    networks.update(service_networks.keys())

        return networks

    def _transform_networks(self, compose_data: dict) -> tuple[dict, list[str]]:
        """Transform the networks section.

        Args:
            compose_data: Parsed compose file data

        Returns:
            Tuple of (modified compose_data, list of changes)
        """
        changes = []
        networks = compose_data.get("networks", {})

        # Identify networks to replace (project-specific external networks)
        networks_to_replace = set()
        for net_name, net_config in list(networks.items()):
            if net_config is None:
                net_config = {}

            # Replace external networks that match our aliases
            if net_name in self.config.legacy_networks:
                networks_to_replace.add(net_name)
                changes.append(f"Network '{net_name}' will be replaced with '{self.config.network_name}'")

        # Remove old networks and add the devflow network
        for net_name in networks_to_replace:
            del networks[net_name]

        # Add devflow-proxy network if any services need it
        if networks_to_replace or self.config.network_name not in networks:
            networks[self.config.network_name] = {
                "external": True,
                "name": self.config.network_name,
            }
            if self.config.network_name not in [c.split("'")[1] for c in changes if "will be replaced" in c]:
                changes.append(f"Added external network '{self.config.network_name}'")

        compose_data["networks"] = networks
        return compose_data, changes

    def _transform_services(
        self, compose_data: dict, original_networks: set[str]
    ) -> tuple[dict, list[str], list[str]]:
        """Transform service network references.

        Args:
            compose_data: Parsed compose file data
            original_networks: Set of original network names

        Returns:
            Tuple of (modified compose_data, list of changes, list of warnings)
        """
        changes = []
        warnings = []
        services = compose_data.get("services", {})

        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue

            service_networks = service_config.get("networks")
            if service_networks is None:
                continue

            if isinstance(service_networks, list):
                # Simple list format: networks: [proxy]
                new_networks = []
                modified = False

                for net in service_networks:
                    if net in self.config.legacy_networks and net != self.config.network_name:
                        new_networks.append(self.config.network_name)
                        modified = True
                    else:
                        new_networks.append(net)

                if modified:
                    # Remove duplicates while preserving order
                    seen = set()
                    service_config["networks"] = [
                        n for n in new_networks if not (n in seen or seen.add(n))
                    ]
                    changes.append(f"Updated networks for service '{service_name}'")

            elif isinstance(service_networks, dict):
                # Extended format: networks: proxy: aliases: [...]
                new_networks = {}
                modified = False

                for net, net_config in service_networks.items():
                    if net in self.config.legacy_networks and net != self.config.network_name:
                        # Preserve any aliases or other config
                        new_networks[self.config.network_name] = net_config
                        modified = True
                    else:
                        new_networks[net] = net_config

                if modified:
                    service_config["networks"] = new_networks
                    changes.append(f"Updated networks for service '{service_name}'")

        compose_data["services"] = services
        return compose_data, changes, warnings

    def _find_traefik_service(self, compose_data: dict) -> Optional[str]:
        """Find an embedded Traefik service in the compose file.

        Args:
            compose_data: Parsed compose file data

        Returns:
            Name of the Traefik service, or None if not found
        """
        services = compose_data.get("services", {})

        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue

            image = service_config.get("image", "")
            for pattern in self.TRAEFIK_IMAGE_PATTERNS:
                if re.match(pattern, image, re.IGNORECASE):
                    return service_name

        return None

    def _remove_traefik_service(
        self, compose_data: dict, service_name: str
    ) -> tuple[dict, list[str]]:
        """Remove an embedded Traefik service.

        Args:
            compose_data: Parsed compose file data
            service_name: Name of the Traefik service to remove

        Returns:
            Tuple of (modified compose_data, list of changes)
        """
        changes = []
        services = compose_data.get("services", {})

        if service_name in services:
            del services[service_name]
            changes.append(f"Removed embedded Traefik service '{service_name}'")

        compose_data["services"] = services
        return compose_data, changes

    def detect_domains(self, compose_path: Path) -> list[str]:
        """Detect domains configured in Traefik labels.

        Args:
            compose_path: Path to the compose file

        Returns:
            List of detected domains
        """
        compose_path = Path(compose_path)

        if not compose_path.exists():
            return []

        try:
            with open(compose_path) as f:
                compose_data = yaml.safe_load(f)
        except yaml.YAMLError:
            return []

        domains = set()
        services = compose_data.get("services", {})

        for service_config in services.values():
            if not isinstance(service_config, dict):
                continue

            labels = service_config.get("labels", [])
            if isinstance(labels, list):
                for label in labels:
                    domains.update(self._extract_domains_from_label(str(label)))
            elif isinstance(labels, dict):
                for key, value in labels.items():
                    domains.update(self._extract_domains_from_label(f"{key}={value}"))

        return sorted(domains)

    def _extract_domains_from_label(self, label: str) -> set[str]:
        """Extract domain names from a Traefik label.

        Args:
            label: The label string (e.g., traefik.http.routers.x.rule=Host(`foo.localhost`))

        Returns:
            Set of domain names found
        """
        domains = set()

        # Match Host(`domain`) or Host(`domain1`,`domain2`)
        host_pattern = r"Host\s*\(\s*`([^`]+)`(?:\s*,\s*`([^`]+)`)*\s*\)"
        matches = re.findall(host_pattern, label)

        for match in matches:
            if isinstance(match, tuple):
                for domain in match:
                    if domain:
                        domains.add(domain)
            else:
                domains.add(match)

        return domains
