"""1Password CLI (op) provider."""

import json
import shutil
import subprocess
from typing import Any

from devflow.core.platform import CURRENT_PLATFORM, Platform
from devflow.providers.base import Provider


class OnePasswordProvider(Provider):
    """Wrapper for 1Password CLI (op)."""

    @property
    def name(self) -> str:
        return "1password"

    @property
    def binary(self) -> str:
        # On Windows, the binary has a .exe extension
        if CURRENT_PLATFORM == Platform.WINDOWS:
            return "op.exe"
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

    def list_vaults(self) -> list[dict[str, Any]]:
        """List available vaults."""
        try:
            result = self.run(["vault", "list", "--format", "json"])
            data: list[dict[str, Any]] = json.loads(result.stdout)
            return data
        except subprocess.CalledProcessError:
            return []

    def list_items(self, vault: str) -> list[dict[str, Any]]:
        """List items in a vault."""
        try:
            result = self.run(["item", "list", "--vault", vault, "--format", "json"])
            data: list[dict[str, Any]] = json.loads(result.stdout)
            return data
        except subprocess.CalledProcessError:
            return []

    def get_item(self, item_name: str, vault: str | None = None) -> dict[str, Any] | None:
        """Get an item by name."""
        args = ["item", "get", item_name, "--format", "json"]
        if vault:
            args.extend(["--vault", vault])

        try:
            result = self.run(args)
            data: dict[str, Any] = json.loads(result.stdout)
            return data
        except subprocess.CalledProcessError:
            return None

    def read_field(self, item_name: str, field: str, vault: str | None = None) -> str | None:
        """Read a specific field from an item."""
        # Use op read for direct field access
        reference = f"op://{vault}/{item_name}/{field}" if vault else f"op://{item_name}/{field}"

        try:
            result = self.run(["read", reference])
            return str(result.stdout.strip())
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
