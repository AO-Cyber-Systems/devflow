"""Secrets RPC handlers."""

import re
import subprocess
from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubProvider, GitHubAppProvider, resolve_github_app_config
from devflow.providers.onepassword import OnePasswordProvider


class SecretsHandler:
    """Handler for secrets management RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()
        self._github = GitHubProvider()
        self._onepassword = OnePasswordProvider()

    def _get_github_provider(self, config) -> GitHubProvider | GitHubAppProvider:
        """Get the appropriate GitHub provider based on config.

        Args:
            config: DevflowConfig

        Returns:
            GitHubProvider (CLI) or GitHubAppProvider (App auth)
        """
        if config.secrets and config.secrets.github:
            if config.secrets.github.auth == "app" and config.secrets.github.app:
                try:
                    vault = config.secrets.vault if config.secrets else None
                    resolved_app_config = resolve_github_app_config(
                        config.secrets.github.app,
                        vault=vault,
                    )
                    return GitHubAppProvider(resolved_app_config)
                except Exception:
                    pass
        return self._github

    def _get_repo_name(self, project_path: Path) -> str | None:
        """Get GitHub repo name from git remote.

        Args:
            project_path: Path to the project

        Returns:
            Repo name in "owner/repo" format, or None
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None

            url = result.stdout.strip()

            # Handle SSH format: git@github.com:owner/repo.git
            ssh_match = re.match(r"git@github\.com:(.+?)(?:\.git)?$", url)
            if ssh_match:
                return ssh_match.group(1)

            # Handle HTTPS format: https://github.com/owner/repo.git
            https_match = re.match(r"https://github\.com/(.+?)(?:\.git)?$", url)
            if https_match:
                return https_match.group(1)

            return None
        except Exception:
            return None

    def list(self, path: str, environment: str | None = None, source: str | None = None) -> dict[str, Any]:
        """List secrets from configuration.

        Args:
            path: Project path
            environment: Optional environment filter
            source: Optional source filter (1password, github, docker)

        Returns:
            Dict with secrets list
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.secrets:
                return {"error": "No secrets configuration found"}

            secrets = []
            mapped_count = 0

            for mapping in config.secrets.mappings:
                secret_info = {
                    "name": mapping.name,
                    "source": "mapping",
                    "mapped_to": [],
                    "last_synced": None,
                }

                if mapping.op_item:
                    secret_info["mapped_to"].append(f"1password:{mapping.op_item}")
                if mapping.github_secret:
                    secret_info["mapped_to"].append(f"github:{mapping.github_secret}")
                if mapping.docker_secret:
                    secret_info["mapped_to"].append(f"docker:{mapping.docker_secret}")

                if secret_info["mapped_to"]:
                    mapped_count += 1

                # Apply source filter
                if source:
                    if source == "1password" and not mapping.op_item:
                        continue
                    if source == "github" and not mapping.github_secret:
                        continue
                    if source == "docker" and not mapping.docker_secret:
                        continue

                secrets.append(secret_info)

            return {
                "source": source or "all",
                "environment": environment or "all",
                "secrets": secrets,
                "mapped_count": mapped_count,
                "total_count": len(secrets),
            }
        except Exception as e:
            return {"error": str(e)}

    def sync(
        self,
        path: str,
        from_source: str,
        to_target: str,
        environment: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Sync secrets between sources.

        Args:
            path: Project path
            from_source: Source to read from (1password, env)
            to_target: Target to write to (github, docker)
            environment: Optional environment filter
            dry_run: If True, only show what would be synced

        Returns:
            Dict with sync results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            # Validate source
            if from_source == "1password":
                if not self._onepassword.is_authenticated():
                    return {
                        "success": False,
                        "error": "1Password CLI not authenticated. Run: op signin",
                    }
            elif from_source != "env":
                return {"success": False, "error": f"Unknown source: {from_source}"}

            # Validate target
            if to_target == "github":
                github_provider = self._get_github_provider(config)
                if isinstance(github_provider, GitHubProvider):
                    if not github_provider.is_authenticated():
                        return {
                            "success": False,
                            "error": "GitHub CLI not authenticated. Run: gh auth login",
                        }

                repo = self._get_repo_name(project_path)
                if not repo:
                    return {
                        "success": False,
                        "error": "Could not determine GitHub repository from git remote",
                    }
            elif to_target == "docker":
                if not self._docker.is_authenticated():
                    return {
                        "success": False,
                        "error": "Docker is not available or not running",
                    }
            else:
                return {"success": False, "error": f"Unknown target: {to_target}"}

            vault = config.secrets.vault
            results = []
            synced = 0
            failed = 0

            for mapping in config.secrets.mappings:
                # Check if mapping has source and target
                has_source = False
                has_target = False
                target_name = None

                if from_source == "1password" and mapping.op_item:
                    has_source = True
                elif from_source == "env":
                    has_source = True

                if to_target == "github" and mapping.github_secret:
                    has_target = True
                    target_name = mapping.github_secret
                elif to_target == "docker" and mapping.docker_secret:
                    has_target = True
                    target_name = mapping.docker_secret

                if not (has_source and has_target):
                    continue

                result = {
                    "secret": mapping.name,
                    "from_source": from_source,
                    "to_target": to_target,
                    "target_name": target_name,
                    "status": "would_sync" if dry_run else "pending",
                    "error": None,
                }

                if dry_run:
                    results.append(result)
                    continue

                # Read value from source
                value = None
                try:
                    if from_source == "1password" and mapping.op_item:
                        field = mapping.op_field or "password"
                        value = self._onepassword.read_field(mapping.op_item, field, vault)
                        if not value:
                            result["status"] = "failed"
                            result["error"] = f"Could not read from 1Password: {mapping.op_item}/{field}"
                            failed += 1
                            results.append(result)
                            continue
                    elif from_source == "env":
                        import os

                        env_name = mapping.name.upper().replace("-", "_")
                        value = os.environ.get(env_name)
                        if not value:
                            result["status"] = "failed"
                            result["error"] = f"Environment variable not set: {env_name}"
                            failed += 1
                            results.append(result)
                            continue
                except Exception as e:
                    result["status"] = "failed"
                    result["error"] = f"Read failed: {e}"
                    failed += 1
                    results.append(result)
                    continue

                # Write value to target
                try:
                    if to_target == "github":
                        github_provider = self._get_github_provider(config)
                        success = github_provider.set_secret(repo, mapping.github_secret, value)
                        if success:
                            result["status"] = "synced"
                            synced += 1
                        else:
                            result["status"] = "failed"
                            result["error"] = "Failed to set GitHub secret"
                            failed += 1

                    elif to_target == "docker":
                        # Docker secrets are immutable - remove first if exists
                        if self._docker.secret_exists(mapping.docker_secret):
                            self._docker.remove_secret(mapping.docker_secret)

                        success = self._docker.create_secret(mapping.docker_secret, value)
                        if success:
                            result["status"] = "synced"
                            synced += 1
                        else:
                            result["status"] = "failed"
                            result["error"] = "Failed to create Docker secret"
                            failed += 1

                except Exception as e:
                    result["status"] = "failed"
                    result["error"] = f"Write failed: {e}"
                    failed += 1

                results.append(result)

            return {
                "success": failed == 0,
                "synced": synced,
                "failed": failed,
                "dry_run": dry_run,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify(self, path: str, environment: str | None = None) -> dict[str, Any]:
        """Verify secrets are present in all targets.

        Args:
            path: Project path
            environment: Optional environment filter

        Returns:
            Dict with verification results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            vault = config.secrets.vault
            repo = self._get_repo_name(project_path)
            github_provider = self._get_github_provider(config)

            # Get existing secrets from each provider
            docker_secrets = []
            github_secrets = []

            if self._docker.is_authenticated():
                docker_secrets = [s.get("Name") for s in self._docker.list_secrets()]

            if repo:
                try:
                    github_secrets = github_provider.list_secrets(repo)
                except Exception:
                    pass

            results = []
            in_sync = 0
            out_of_sync = 0

            for mapping in config.secrets.mappings:
                result = {
                    "secret": mapping.name,
                    "checks": {},
                    "status": "in_sync",
                }

                # Check 1Password
                if mapping.op_item:
                    if self._onepassword.is_authenticated():
                        field = mapping.op_field or "password"
                        value = self._onepassword.read_field(mapping.op_item, field, vault)
                        result["checks"]["1password"] = bool(value)
                        if not value:
                            result["status"] = "out_of_sync"
                    else:
                        result["checks"]["1password"] = None  # Can't check

                # Check GitHub
                if mapping.github_secret:
                    if repo:
                        result["checks"]["github"] = mapping.github_secret in github_secrets
                        if not result["checks"]["github"]:
                            result["status"] = "out_of_sync"
                    else:
                        result["checks"]["github"] = None  # Can't check

                # Check Docker
                if mapping.docker_secret:
                    result["checks"]["docker"] = mapping.docker_secret in docker_secrets
                    if not result["checks"]["docker"]:
                        result["status"] = "out_of_sync"

                if result["status"] == "in_sync":
                    in_sync += 1
                else:
                    out_of_sync += 1

                results.append(result)

            return {
                "success": True,
                "in_sync": in_sync,
                "out_of_sync": out_of_sync,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export(self, path: str, environment: str, format: str = "env") -> dict[str, Any]:
        """Export secrets to file or env format.

        Reads values from 1Password and outputs in requested format.
        Only intended for local/development environments.

        Args:
            path: Project path
            environment: Target environment (should be 'local' for safety)
            format: Output format (env, json, yaml)

        Returns:
            Dict with exported content
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            # Safety check: only allow export for local environments
            if environment not in ("local", "development", "dev"):
                return {
                    "success": False,
                    "error": "Secret export is only allowed for local/development environments",
                }

            if not self._onepassword.is_authenticated():
                return {
                    "success": False,
                    "error": "1Password CLI not authenticated. Run: op signin",
                }

            vault = config.secrets.vault
            exported = 0
            failed = 0
            secrets_data = {}

            for mapping in config.secrets.mappings:
                if not mapping.op_item:
                    continue

                field = mapping.op_field or "password"
                value = self._onepassword.read_field(mapping.op_item, field, vault)

                if value:
                    env_name = mapping.name.upper().replace("-", "_")
                    secrets_data[env_name] = value
                    exported += 1
                else:
                    failed += 1

            # Format output
            content = ""
            if format == "env":
                lines = []
                for name, value in secrets_data.items():
                    # Escape special characters in value
                    escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{name}="{escaped_value}"')
                content = "\n".join(lines)

            elif format == "json":
                import json

                content = json.dumps(secrets_data, indent=2)

            elif format == "yaml":
                lines = ["# Secrets exported from 1Password"]
                for name, value in secrets_data.items():
                    # YAML string escaping
                    if any(c in value for c in [":", "#", "'", '"', "\n"]):
                        escaped_value = value.replace("'", "''")
                        lines.append(f"{name}: '{escaped_value}'")
                    else:
                        lines.append(f"{name}: {value}")
                content = "\n".join(lines)

            else:
                return {"success": False, "error": f"Unknown format: {format}"}

            return {
                "success": True,
                "exported": exported,
                "failed": failed,
                "content": content,
                "format": format,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def providers(self) -> dict[str, Any]:
        """Get available secret providers and their status.

        Returns:
            Dict with provider information
        """
        providers = []

        # 1Password
        op_available = self._onepassword.is_available()
        providers.append(
            {
                "name": "1password",
                "available": op_available,
                "authenticated": self._onepassword.is_authenticated() if op_available else False,
            }
        )

        # GitHub
        gh_available = self._github.is_available()
        providers.append(
            {
                "name": "github",
                "available": gh_available,
                "authenticated": self._github.is_authenticated() if gh_available else False,
            }
        )

        # Docker
        docker_available = self._docker.is_available()
        providers.append(
            {
                "name": "docker",
                "available": docker_available,
                "authenticated": docker_available,  # Docker secrets don't require separate auth
            }
        )

        # Environment variables (always available)
        providers.append(
            {
                "name": "env",
                "available": True,
                "authenticated": True,
            }
        )

        return {"providers": providers}
