"""Agent installation logic."""

import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path

from .models import AgentInstallMethod, AIAgent

logger = logging.getLogger(__name__)


class AgentInstaller:
    """Handles installation and detection of AI agents."""

    async def detect_installed(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Check if an agent is installed and get its version.

        Returns:
            Tuple of (is_installed, installed_version)
        """
        try:
            return await asyncio.to_thread(self._detect_installed_sync, agent)
        except Exception as e:
            logger.error(f"Error detecting agent {agent.id}: {e}")
            return False, None

    def _detect_installed_sync(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Synchronous version of detect_installed."""
        method = agent.install_method

        if method == AgentInstallMethod.NPM:
            return self._detect_npm_package(agent)
        elif method == AgentInstallMethod.PIP:
            return self._detect_pip_package(agent)
        elif method == AgentInstallMethod.BREW:
            return self._detect_brew_package(agent)
        elif method == AgentInstallMethod.CURL:
            return self._detect_binary(agent)
        elif method == AgentInstallMethod.VSCODE:
            return self._detect_vscode_extension(agent)
        elif method == AgentInstallMethod.MANUAL:
            return self._detect_binary(agent)
        else:
            return False, None

    def _detect_npm_package(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Detect if an npm package is installed globally."""
        # Extract package name from install command
        # e.g., "npm install -g @anthropic-ai/claude-code" -> "@anthropic-ai/claude-code"
        parts = agent.install_command.split()
        if len(parts) < 4:
            return False, None

        package_name = parts[-1]

        try:
            result = subprocess.run(
                ["npm", "list", "-g", package_name, "--depth=0", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                deps = data.get("dependencies", {})
                if package_name in deps:
                    version = deps[package_name].get("version")
                    return True, version
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: check if command exists
        cmd_name = agent.id.replace("-", "")
        if agent.id == "claude-code":
            cmd_name = "claude"
        elif agent.id == "gemini-cli":
            cmd_name = "gemini"
        elif agent.id == "codex-cli":
            cmd_name = "codex"

        if shutil.which(cmd_name):
            return True, None

        return False, None

    def _detect_pip_package(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Detect if a pip package is installed."""
        # Extract package name from install command
        # e.g., "pip install aider-chat" -> "aider-chat"
        parts = agent.install_command.split()
        if len(parts) < 3:
            return False, None

        package_name = parts[-1]

        try:
            result = subprocess.run(
                ["pip", "show", package_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        return True, version
                return True, None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: check if command exists
        cmd_name = agent.id
        if agent.id == "aider":
            cmd_name = "aider"

        if shutil.which(cmd_name):
            return True, None

        return False, None

    def _detect_brew_package(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Detect if a Homebrew package is installed."""
        # Extract package name from install command
        parts = agent.install_command.split()
        if len(parts) < 3:
            return False, None

        package_name = parts[-1]

        try:
            result = subprocess.run(
                ["brew", "list", "--versions", package_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Output format: "package_name version"
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return True, parts[1]
                return True, None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, None

    def _detect_binary(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Detect if a binary is available in PATH."""
        cmd_name = agent.id.replace("-", "")
        if agent.id == "opencode":
            cmd_name = "opencode"

        if shutil.which(cmd_name):
            return True, None

        return False, None

    def _detect_vscode_extension(self, agent: AIAgent) -> tuple[bool, str | None]:
        """Detect if a VS Code extension is installed."""
        # Extract extension ID from command
        # e.g., "code --install-extension Continue.continue" -> "Continue.continue"
        parts = agent.install_command.split()
        if len(parts) < 3:
            return False, None

        extension_id = parts[-1].lower()

        try:
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                extensions = result.stdout.lower().split("\n")
                for ext in extensions:
                    if ext.strip() == extension_id:
                        return True, None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, None

    async def install(self, agent: AIAgent) -> dict:
        """Install an agent.

        Returns:
            Dictionary with success status, message, and output.
        """
        try:
            return await asyncio.to_thread(self._install_sync, agent)
        except Exception as e:
            logger.error(f"Error installing agent {agent.id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _install_sync(self, agent: AIAgent) -> dict:
        """Synchronous version of install."""
        method = agent.install_method
        command = agent.install_command

        logger.info(f"Installing agent {agent.id} using {method.value}: {command}")

        try:
            # Run the install command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**os.environ, "CI": "1"},  # Disable interactive prompts
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully installed {agent.name}",
                    "output": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "error": f"Installation failed: {result.stderr or result.stdout}",
                    "output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Installation timed out after 5 minutes",
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "error": f"Command not found: {e}",
            }

    def check_api_key_configured(
        self, agent: AIAgent, provider_id: str | None = None
    ) -> dict[str, bool]:
        """Check if API keys are configured for an agent.

        Args:
            agent: The agent to check
            provider_id: Optional specific provider to check

        Returns:
            Dictionary mapping provider ID to configured status.
        """
        result = {}

        for key_config in agent.api_keys:
            if provider_id and key_config.provider.value != provider_id:
                continue

            env_var = key_config.env_var
            is_configured = bool(os.environ.get(env_var))

            # Also check config file locations
            if not is_configured:
                is_configured = self._check_config_file(agent, key_config)

            result[key_config.provider.value] = is_configured

        return result

    def _check_config_file(self, agent: AIAgent, key_config) -> bool:
        """Check if API key is configured in the agent's config file."""
        config_path = Path(agent.config_location).expanduser()

        if not config_path.exists():
            return False

        # Check for .env files or config files that might contain the key
        env_files = [
            config_path / ".env",
            config_path / "config.json",
            config_path / "settings.json",
        ]

        for env_file in env_files:
            if env_file.exists():
                try:
                    content = env_file.read_text()
                    if key_config.env_var in content:
                        return True
                except Exception:
                    pass

        return False

    async def configure_api_key(
        self, agent: AIAgent, provider_id: str, api_key: str
    ) -> dict:
        """Configure an API key for an agent.

        This sets the API key in the agent's config location.

        Returns:
            Dictionary with success status and message.
        """
        try:
            config_path = Path(agent.config_location).expanduser()
            config_path.mkdir(parents=True, exist_ok=True)

            # Find the matching key config
            key_config = None
            for kc in agent.api_keys:
                if kc.provider.value == provider_id:
                    key_config = kc
                    break

            if not key_config:
                return {
                    "success": False,
                    "error": f"Provider {provider_id} not supported by {agent.name}",
                }

            # Write to .env file in config directory
            env_file = config_path / ".env"
            env_content = {}

            # Read existing env file if it exists
            if env_file.exists():
                for line in env_file.read_text().split("\n"):
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

            # Update with new key
            env_content[key_config.env_var] = api_key

            # Write back
            lines = [f"{k}={v}" for k, v in env_content.items()]
            env_file.write_text("\n".join(lines) + "\n")

            return {
                "success": True,
                "message": f"Configured {key_config.provider.display_name} API key for {agent.name}",
            }

        except Exception as e:
            logger.error(f"Error configuring API key for {agent.id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
