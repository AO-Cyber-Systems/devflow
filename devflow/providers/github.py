"""GitHub CLI (gh) and GitHub App provider."""

import shutil
import subprocess
import time
from typing import TYPE_CHECKING, Any

import jwt
import requests

from devflow.providers.base import Provider

if TYPE_CHECKING:
    from devflow.core.config import GitHubAppConfig


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


class GitHubAppProvider:
    """GitHub App authentication provider for API-based operations.

    This provider authenticates using a GitHub App's private key and installation ID,
    providing better security and auditability compared to Personal Access Tokens.

    The authentication flow:
    1. Generate a JWT signed with the App's private key
    2. Exchange the JWT for an installation access token
    3. Use the token for GitHub API calls (valid for 1 hour)
    """

    GITHUB_API_BASE = "https://api.github.com"
    JWT_EXPIRATION_SECONDS = 600  # 10 minutes (GitHub max)
    TOKEN_EXPIRATION_BUFFER = 300  # Refresh token 5 minutes before expiry

    def __init__(self, app_config: "GitHubAppConfig") -> None:
        """Initialize with GitHub App configuration.

        Args:
            app_config: GitHubAppConfig containing app_id, installation_id, and private_key.
                        Values may be raw or op:// references (resolved before passing here).
        """
        self.app_id = app_config.app_id
        self.installation_id = app_config.installation_id
        self.private_key = app_config.private_key
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @property
    def name(self) -> str:
        return "github-app"

    def _generate_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication.

        Returns:
            JWT token string for authenticating as the GitHub App.
        """
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock drift tolerance)
            "exp": now + self.JWT_EXPIRATION_SECONDS,
            "iss": self.app_id,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def _get_installation_token(self) -> str:
        """Get or refresh the installation access token.

        Returns:
            Installation access token for API calls.

        Raises:
            RuntimeError: If token exchange fails.
        """
        # Return cached token if still valid
        if self._access_token and time.time() < self._token_expires_at - self.TOKEN_EXPIRATION_BUFFER:
            return self._access_token

        # Generate JWT and exchange for installation token
        jwt_token = self._generate_jwt()
        url = f"{self.GITHUB_API_BASE}/app/installations/{self.installation_id}/access_tokens"

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        )

        if response.status_code != 201:
            raise RuntimeError(f"Failed to get installation token: {response.status_code} {response.text}")

        data = response.json()
        self._access_token = data["token"]
        # Parse expiration time (ISO 8601 format)
        from datetime import datetime

        expires_at_str = data.get("expires_at", "")
        if expires_at_str:
            # Handle Z suffix for UTC
            if expires_at_str.endswith("Z"):
                expires_at_str = expires_at_str[:-1] + "+00:00"
            expires_at = datetime.fromisoformat(expires_at_str)
            self._token_expires_at = expires_at.timestamp()
        else:
            # Default to 1 hour if not specified
            self._token_expires_at = time.time() + 3600

        return str(self._access_token)

    def _api_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        token = self._get_installation_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def is_authenticated(self) -> bool:
        """Check if we can authenticate with GitHub App credentials."""
        try:
            self._get_installation_token()
            return True
        except (RuntimeError, requests.RequestException, jwt.PyJWTError):
            return False

    def get_authenticated_app(self) -> dict[str, Any] | None:
        """Get information about the authenticated GitHub App."""
        try:
            jwt_token = self._generate_jwt()
            response = requests.get(
                f"{self.GITHUB_API_BASE}/app",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30,
            )
            if response.status_code == 200:
                return dict(response.json())
            return None
        except (requests.RequestException, jwt.PyJWTError):
            return None

    def get_public_key(self, repo: str) -> tuple[str, str] | None:
        """Get the repository's public key for encrypting secrets.

        Args:
            repo: Repository in "owner/repo" format.

        Returns:
            Tuple of (key_id, public_key) or None if failed.
        """
        try:
            response = requests.get(
                f"{self.GITHUB_API_BASE}/repos/{repo}/actions/secrets/public-key",
                headers=self._api_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return (data["key_id"], data["key"])
            return None
        except requests.RequestException:
            return None

    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt a secret value using the repository's public key.

        Uses libsodium sealed box encryption as required by GitHub.

        Args:
            public_key: Base64-encoded public key from GitHub.
            secret_value: Plain text secret to encrypt.

        Returns:
            Base64-encoded encrypted value.
        """
        from base64 import b64decode, b64encode

        from nacl.public import PublicKey, SealedBox

        # Decode the public key
        public_key_bytes = b64decode(public_key)
        public_key_obj = PublicKey(public_key_bytes)

        # Create sealed box and encrypt
        sealed_box = SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))

        return b64encode(encrypted).decode("utf-8")

    def list_secrets(self, repo: str) -> list[str]:
        """List secrets for a repository.

        Args:
            repo: Repository in "owner/repo" format.

        Returns:
            List of secret names.
        """
        try:
            response = requests.get(
                f"{self.GITHUB_API_BASE}/repos/{repo}/actions/secrets",
                headers=self._api_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return [secret["name"] for secret in data.get("secrets", [])]
            return []
        except requests.RequestException:
            return []

    def set_secret(self, repo: str, name: str, value: str) -> bool:
        """Set a secret for a repository.

        Args:
            repo: Repository in "owner/repo" format.
            name: Secret name.
            value: Secret value (will be encrypted before sending).

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get public key for encryption
            key_info = self.get_public_key(repo)
            if not key_info:
                return False

            key_id, public_key = key_info

            # Encrypt the secret
            encrypted_value = self._encrypt_secret(public_key, value)

            # Set the secret
            response = requests.put(
                f"{self.GITHUB_API_BASE}/repos/{repo}/actions/secrets/{name}",
                headers=self._api_headers(),
                json={
                    "encrypted_value": encrypted_value,
                    "key_id": key_id,
                },
                timeout=30,
            )
            # 201 = created, 204 = updated
            return response.status_code in (201, 204)
        except requests.RequestException:
            return False

    def delete_secret(self, repo: str, name: str) -> bool:
        """Delete a secret from a repository.

        Args:
            repo: Repository in "owner/repo" format.
            name: Secret name.

        Returns:
            True if successful, False otherwise.
        """
        try:
            response = requests.delete(
                f"{self.GITHUB_API_BASE}/repos/{repo}/actions/secrets/{name}",
                headers=self._api_headers(),
                timeout=30,
            )
            return bool(response.status_code == 204)
        except requests.RequestException:
            return False


def resolve_github_app_config(
    app_config: "GitHubAppConfig",
    vault: str | None = None,
) -> "GitHubAppConfig":
    """Resolve op:// references in GitHub App configuration.

    Args:
        app_config: GitHubAppConfig that may contain op:// references.
        vault: Optional 1Password vault name for resolving references.

    Returns:
        New GitHubAppConfig with all references resolved.

    Raises:
        ValueError: If a reference cannot be resolved.
    """
    from devflow.core.config import GitHubAppConfig
    from devflow.providers.onepassword import OnePasswordProvider

    op = OnePasswordProvider()

    def resolve_value(value: str, field_name: str) -> str:
        """Resolve a single value, handling op:// references."""
        if not value.startswith("op://"):
            return value

        if not op.is_authenticated():
            raise ValueError(f"Cannot resolve {field_name}: 1Password not authenticated")

        # Use op inject for full reference resolution
        resolved = op.inject(value)
        if resolved == value:
            # Injection returned original value, meaning it failed
            raise ValueError(f"Cannot resolve {field_name}: Failed to read from 1Password")

        return resolved

    return GitHubAppConfig(
        app_id=resolve_value(app_config.app_id, "app_id"),
        installation_id=resolve_value(app_config.installation_id, "installation_id"),
        private_key=resolve_value(app_config.private_key, "private_key"),
    )
