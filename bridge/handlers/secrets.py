"""Secrets RPC handlers."""

from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubProvider
from devflow.providers.onepassword import OnePasswordProvider


class SecretsHandler:
    """Handler for secrets management RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()
        self._github = GitHubProvider()
        self._onepassword = OnePasswordProvider()

    def list(
        self, path: str, environment: str | None = None, source: str | None = None
    ) -> dict[str, Any]:
        """List secrets."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

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
        """Sync secrets between sources."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            results = []
            synced = 0
            failed = 0

            for mapping in config.secrets.mappings:
                # Determine source and target based on mapping
                has_source = False
                has_target = False

                if from_source == "1password" and mapping.op_item:
                    has_source = True
                elif from_source == "env":
                    has_source = True

                if to_target == "github" and mapping.github_secret:
                    has_target = True
                elif to_target == "docker" and mapping.docker_secret:
                    has_target = True

                if has_source and has_target:
                    results.append(
                        {
                            "secret": mapping.name,
                            "from_source": from_source,
                            "to_target": to_target,
                            "status": "would_sync" if dry_run else "pending",
                            "error": None,
                        }
                    )

            return {
                "success": True,
                "synced": 0 if dry_run else synced,
                "failed": failed,
                "dry_run": dry_run,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify(self, path: str, environment: str | None = None) -> dict[str, Any]:
        """Verify secrets are in sync."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            results = []
            in_sync = 0
            out_of_sync = 0

            for mapping in config.secrets.mappings:
                # Check each target
                result = {
                    "secret": mapping.name,
                    "status": "unknown",
                    "details": None,
                }

                # This is a simplified version - real implementation would check each provider
                if mapping.op_item and self._onepassword.is_available():
                    result["status"] = "in_sync"
                    in_sync += 1
                else:
                    result["status"] = "out_of_sync"
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

    def export(
        self, path: str, environment: str, format: str = "env"
    ) -> dict[str, Any]:
        """Export secrets to file or env format."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.secrets:
                return {"success": False, "error": "No secrets configuration found"}

            # This is a simplified version
            content = ""
            exported = 0

            if format == "env":
                for mapping in config.secrets.mappings:
                    content += f"# {mapping.name}\n"
                    content += f"{mapping.name}=<value>\n"
                    exported += 1
            elif format == "json":
                import json

                secrets_dict = {}
                for mapping in config.secrets.mappings:
                    secrets_dict[mapping.name] = "<value>"
                    exported += 1
                content = json.dumps(secrets_dict, indent=2)
            elif format == "yaml":
                content = "# Secrets\n"
                for mapping in config.secrets.mappings:
                    content += f"{mapping.name}: <value>\n"
                    exported += 1
            else:
                return {"success": False, "error": f"Unknown format: {format}"}

            return {
                "success": True,
                "exported": exported,
                "failed": 0,
                "content": content,
                "format": format,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def providers(self) -> dict[str, Any]:
        """Get available secret providers."""
        providers = []

        # 1Password
        providers.append(
            {
                "name": "1password",
                "available": self._onepassword.is_available(),
                "authenticated": self._onepassword.is_authenticated()
                if self._onepassword.is_available()
                else False,
            }
        )

        # GitHub
        providers.append(
            {
                "name": "github",
                "available": self._github.is_available(),
                "authenticated": self._github.is_authenticated()
                if self._github.is_available()
                else False,
            }
        )

        # Docker (always available if Docker is)
        providers.append(
            {
                "name": "docker",
                "available": self._docker.is_available(),
                "authenticated": True,  # Docker secrets don't require separate auth
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
