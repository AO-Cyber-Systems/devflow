"""GitHub CLI (gh) provider."""

import shutil
import subprocess
from typing import Any

from devflow.providers.base import Provider


class GitHubProvider(Provider):
    """Wrapper for GitHub CLI (gh)."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def binary(self) -> str:
        return "gh"

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                [self.binary, "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_current_user(self) -> str | None:
        """Get the currently authenticated user."""
        if not self.is_authenticated():
            return None

        try:
            result = self.run(["api", "user", "-q", ".login"])
            return str(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None

    def list_secrets(self, repo: str) -> list[str]:
        """List secrets for a repository."""
        try:
            result = self.run(["secret", "list", "-R", repo])
            # Parse output - each line is "NAME\tUpdated YYYY-MM-DD"
            lines = result.stdout.strip().split("\n")
            return [line.split("\t")[0] for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    def set_secret(self, repo: str, name: str, value: str) -> bool:
        """Set a secret for a repository."""
        try:
            # Use stdin to avoid exposing secret in command line
            result = subprocess.run(
                [self.binary, "secret", "set", name, "-R", repo],
                input=value,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def delete_secret(self, repo: str, name: str) -> bool:
        """Delete a secret from a repository."""
        try:
            self.run(["secret", "delete", name, "-R", repo])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_workflow_runs(self, repo: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent workflow runs."""
        try:
            result = self.run(
                [
                    "run",
                    "list",
                    "-R",
                    repo,
                    "-L",
                    str(limit),
                    "--json",
                    "databaseId,conclusion,status,name,headBranch,createdAt",
                ]
            )
            import json

            data: list[dict[str, Any]] = json.loads(result.stdout)
            return data
        except subprocess.CalledProcessError:
            return []
