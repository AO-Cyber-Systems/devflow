"""1Password CLI (op) provider."""

import json
import shutil
import subprocess
from typing import Any, Optional

from devflow.providers.base import Provider


class OnePasswordProvider(Provider):
    """Wrapper for 1Password CLI (op)."""

    @property
    def name(self) -> str:
        return "1password"

    @property
    def binary(self) -> str:
        return "op"

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                [self.binary, "account", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def list_vaults(self) -> list[dict]:
        """List available vaults."""
        try:
            result = self.run(["vault", "list", "--format", "json"])
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return []

    def list_items(self, vault: str) -> list[dict]:
        """List items in a vault."""
        try:
            result = self.run(["item", "list", "--vault", vault, "--format", "json"])
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return []

    def get_item(self, item_name: str, vault: Optional[str] = None) -> Optional[dict]:
        """Get an item by name."""
        args = ["item", "get", item_name, "--format", "json"]
        if vault:
            args.extend(["--vault", vault])

        try:
            result = self.run(args)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return None

    def read_field(self, item_name: str, field: str, vault: Optional[str] = None) -> Optional[str]:
        """Read a specific field from an item."""
        # Use op read for direct field access
        reference = f"op://{vault}/{item_name}/{field}" if vault else f"op://{item_name}/{field}"

        try:
            result = self.run(["read", reference])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def inject(self, template: str) -> str:
        """Inject 1Password references into a template string."""
        try:
            result = subprocess.run(
                [self.binary, "inject"],
                input=template,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            return template
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return template
