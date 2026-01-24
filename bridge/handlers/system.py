"""System RPC handlers - doctor, info, and utilities."""

import platform
import sys
from pathlib import Path
from typing import Any

from devflow import __version__ as devflow_version
from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubProvider
from devflow.providers.mkcert import MkcertProvider
from devflow.providers.onepassword import OnePasswordProvider


class SystemHandler:
    """Handler for system-related RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()
        self._github = GitHubProvider()
        self._mkcert = MkcertProvider()
        self._onepassword = OnePasswordProvider()

    def ping(self) -> dict[str, Any]:
        """Simple ping for connection testing."""
        return {"pong": True, "version": devflow_version}

    def version(self) -> dict[str, Any]:
        """Get DevFlow version information."""
        return {
            "devflow": devflow_version,
            "python": platform.python_version(),
            "platform": platform.system(),
        }

    def info(self) -> dict[str, Any]:
        """Get system information."""
        home_dir = Path.home()
        config_dir = home_dir / ".devflow"

        docker_version = None
        try:
            docker_version = self._docker.get_version()
        except Exception:
            pass

        return {
            "platform": platform.system(),
            "os_version": platform.version(),
            "devflow_version": devflow_version,
            "python_version": platform.python_version(),
            "docker_version": docker_version,
            "home_dir": str(home_dir),
            "config_dir": str(config_dir),
        }

    def doctor(self, path: str | None = None) -> dict[str, Any]:
        """Run system doctor checks."""
        checks: list[dict[str, Any]] = []
        overall_status = "healthy"

        # Check Docker
        docker_check = self._check_provider(self._docker, "Docker", "tool", "Install Docker Desktop or Docker Engine")
        checks.append(docker_check)
        if docker_check["status"] == "error":
            overall_status = "error"
        elif docker_check["status"] == "warning" and overall_status == "healthy":
            overall_status = "warning"

        # Check GitHub CLI
        github_check = self._check_provider(
            self._github, "GitHub CLI", "tool", "Install GitHub CLI: https://cli.github.com/"
        )
        checks.append(github_check)

        # Check mkcert
        mkcert_check = self._check_provider(
            self._mkcert, "mkcert", "tool", "Install mkcert: https://github.com/FiloSottile/mkcert"
        )
        checks.append(mkcert_check)

        # Check 1Password CLI
        op_check = self._check_provider(
            self._onepassword,
            "1Password CLI",
            "tool",
            "Install 1Password CLI: https://1password.com/downloads/command-line/",
        )
        checks.append(op_check)

        # Check config directory
        config_dir = Path.home() / ".devflow"
        config_check = {
            "name": "Config Directory",
            "category": "config",
            "status": "ok" if config_dir.exists() else "warning",
            "message": str(config_dir) if config_dir.exists() else "Not initialized",
            "fix_hint": "Run 'devflow install' to initialize" if not config_dir.exists() else None,
        }
        checks.append(config_check)

        # Check global config
        global_config = config_dir / "config.yml"
        config_file_check = {
            "name": "Global Config",
            "category": "config",
            "status": "ok" if global_config.exists() else "warning",
            "message": "Found" if global_config.exists() else "Not found",
            "fix_hint": "Run 'devflow install' to create" if not global_config.exists() else None,
        }
        checks.append(config_file_check)

        return {"overall_status": overall_status, "checks": checks}

    def _check_provider(self, provider: Any, name: str, category: str, fix_hint: str) -> dict[str, Any]:
        """Check a provider's status."""
        try:
            available = provider.is_available()
            authenticated = provider.is_authenticated() if available else False
            version = provider.get_version() if available else None

            if not available:
                return {
                    "name": name,
                    "category": category,
                    "status": "error" if name == "Docker" else "warning",
                    "message": "Not installed",
                    "fix_hint": fix_hint,
                }

            if not authenticated:
                return {
                    "name": name,
                    "category": category,
                    "status": "warning",
                    "message": f"Installed (v{version}) but not authenticated",
                    "fix_hint": f"Run authentication for {name}",
                }

            return {
                "name": name,
                "category": category,
                "status": "ok",
                "message": f"v{version}" if version else "Available",
                "details": {"version": version, "authenticated": authenticated},
            }

        except Exception as e:
            return {
                "name": name,
                "category": category,
                "status": "error",
                "message": f"Check failed: {e}",
                "fix_hint": fix_hint,
            }

    def provider_status(self, provider: str) -> dict[str, Any]:
        """Get status of a specific provider."""
        providers = {
            "docker": self._docker,
            "github": self._github,
            "mkcert": self._mkcert,
            "onepassword": self._onepassword,
        }

        if provider not in providers:
            return {"error": f"Unknown provider: {provider}"}

        p = providers[provider]
        return p.doctor()

    def all_providers(self) -> dict[str, Any]:
        """Get status of all providers."""
        return {
            "docker": self._docker.doctor(),
            "github": self._github.doctor(),
            "mkcert": self._mkcert.doctor(),
            "onepassword": self._onepassword.doctor(),
        }

    def check_updates(self) -> dict[str, Any]:
        """Check for DevFlow updates."""
        # Placeholder - would check PyPI or GitHub releases
        return {
            "current_version": devflow_version,
            "latest_version": devflow_version,
            "update_available": False,
        }
