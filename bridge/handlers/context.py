"""Remote Docker context RPC handlers."""

from pathlib import Path
from typing import Any

from devflow.core.config import RemoteContextConfig, load_project_config


class ContextHandler:
    """Handler for remote context RPC methods."""

    def _get_remote_config(self) -> RemoteContextConfig | None:
        """Get remote context configuration from devflow.yml."""
        try:
            config = load_project_config()
            if config and config.remote:
                return config.remote
        except Exception:
            pass
        return None

    def list_contexts(self) -> dict[str, Any]:
        """List all available Docker contexts."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()
            contexts = manager.list_contexts()

            return {
                "contexts": [ctx.to_dict() for ctx in contexts],
                "total": len(contexts),
            }
        except Exception as e:
            return {"error": str(e)}

    def current_context(self) -> dict[str, Any]:
        """Get the current Docker context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()
            current = manager.current_context()

            if current:
                return {
                    "success": True,
                    "context": current.to_dict(),
                }
            return {"success": False, "error": "No current context found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_context(
        self,
        name: str,
        host: str,
        user: str = "root",
        ssh_port: int = 22,
        ssh_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a new remote Docker context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            config = RemoteContextConfig(
                enabled=True,
                name=name,
                host=host,
                user=user,
                ssh_port=ssh_port,
                ssh_key=Path(ssh_key) if ssh_key else None,
            )

            manager = DockerContextManager(config)
            success, message = manager.create_remote_context(name, config)

            return {
                "success": success,
                "message": message,
                "context_name": f"devflow-{name}" if success else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_context(self, name: str) -> dict[str, Any]:
        """Delete a Docker context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()
            success, message = manager.delete_context(name)

            return {"success": success, "message": message}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def use_context(self, name: str) -> dict[str, Any]:
        """Switch to a Docker context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()

            if name == "local":
                success, message = manager.use_local()
            else:
                success, message = manager.use_context(name)

            return {"success": success, "message": message}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_connection(self, context_name: str | None = None) -> dict[str, Any]:
        """Test connection to a Docker context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()
            success, message = manager.test_connection(context_name)

            return {
                "success": success,
                "message": message,
                "context": context_name or "current",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_remote(self) -> dict[str, Any]:
        """Check if the current context is a remote DevFlow context."""
        try:
            from devflow.providers.remote.context import DockerContextManager

            manager = DockerContextManager()
            is_remote = manager.is_remote()
            current = manager.current_context()

            return {
                "is_remote": is_remote,
                "context_name": current.name if current else None,
            }
        except Exception as e:
            return {"is_remote": False, "error": str(e)}

    # Tunnel operations

    def tunnel_status(self) -> dict[str, Any]:
        """Get the status of the SSH tunnel."""
        try:
            config = self._get_remote_config()

            if not config or not config.enabled:
                return {
                    "configured": False,
                    "message": "No remote context configured",
                }

            from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

            tunnel = SSHTunnelProvider(config)
            health = tunnel.health()

            return {
                "configured": True,
                "host": config.host,
                "user": config.user,
                "tunnels": [
                    {"local": t.local, "remote": t.remote, "description": t.description} for t in config.tunnels
                ],
                **health.to_dict(),
            }
        except Exception as e:
            return {"configured": False, "error": str(e)}

    def tunnel_start(self) -> dict[str, Any]:
        """Start the SSH tunnel."""
        try:
            config = self._get_remote_config()

            if not config or not config.enabled:
                return {
                    "success": False,
                    "message": "No remote context configured in devflow.yml",
                }

            from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

            tunnel = SSHTunnelProvider(config)

            if not tunnel.is_available():
                return {
                    "success": False,
                    "message": "SSH is not available on this system",
                }

            tunnel.start()
            health = tunnel.health()

            return {
                "success": True,
                "message": "Tunnel started",
                **health.to_dict(),
            }
        except RuntimeError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def tunnel_stop(self) -> dict[str, Any]:
        """Stop the SSH tunnel."""
        try:
            config = self._get_remote_config()

            if not config:
                return {
                    "success": False,
                    "message": "No remote context configured",
                }

            from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

            tunnel = SSHTunnelProvider(config)
            tunnel.stop()

            return {"success": True, "message": "Tunnel stopped"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def tunnel_restart(self) -> dict[str, Any]:
        """Restart the SSH tunnel."""
        try:
            config = self._get_remote_config()

            if not config or not config.enabled:
                return {
                    "success": False,
                    "message": "No remote context configured",
                }

            from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider

            tunnel = SSHTunnelProvider(config)
            tunnel.stop()
            tunnel.start()
            health = tunnel.health()

            return {
                "success": True,
                "message": "Tunnel restarted",
                **health.to_dict(),
            }
        except RuntimeError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
