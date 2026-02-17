"""RPC handler for AI agent browsing and installation."""

import asyncio
import logging
from typing import Any

from devflow.agents.browser import AgentBrowser

logger = logging.getLogger(__name__)


class AgentsHandler:
    """Handler for browsing and installing AI coding agents."""

    def __init__(self):
        self._browser: AgentBrowser | None = None

    def _get_browser(self) -> AgentBrowser:
        """Get or create the agent browser instance."""
        if self._browser is None:
            self._browser = AgentBrowser()
        return self._browser

    def list_agents(
        self,
        installed_only: bool = False,
        search: str = "",
    ) -> dict[str, Any]:
        """List all available AI agents.

        Args:
            installed_only: Only show installed agents
            search: Filter by search query

        Returns:
            Dictionary with agents list and total count.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(
                browser.list_agents(
                    installed_only=installed_only,
                    search=search,
                )
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"List agents failed: {e}")
            return {"error": str(e)}

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Get a single agent by ID.

        Args:
            agent_id: Agent ID (e.g., "claude-code", "aider")

        Returns:
            Agent details or error.
        """
        try:
            browser = self._get_browser()
            agent = asyncio.run(browser.get_agent(agent_id))

            if agent is None:
                return {"error": f"Agent not found: {agent_id}"}

            return {"agent": agent.to_dict()}
        except Exception as e:
            logger.error(f"Get agent failed: {e}")
            return {"error": str(e)}

    def install(self, agent_id: str) -> dict[str, Any]:
        """Install an AI agent.

        Args:
            agent_id: Agent ID to install.

        Returns:
            Installation result.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(browser.install(agent_id))
            return result
        except Exception as e:
            logger.error(f"Install agent failed: {e}")
            return {"success": False, "error": str(e)}

    def detect_installed(self, agent_ids: list[str] | None = None) -> dict[str, Any]:
        """Batch check installation status for agents.

        Args:
            agent_ids: List of agent IDs to check. If None, checks all.

        Returns:
            Dictionary mapping agent_id to installed status.
        """
        try:
            browser = self._get_browser()

            if agent_ids is None:
                # Get all agent IDs
                result = asyncio.run(browser.list_agents())
                agent_ids = [a.id for a in result.agents]

            installed = asyncio.run(browser.detect_installed(agent_ids))
            return {"installed": installed}
        except Exception as e:
            logger.error(f"Detect installed failed: {e}")
            return {"error": str(e)}

    def configure_api_key(
        self, agent_id: str, provider: str, api_key: str
    ) -> dict[str, Any]:
        """Configure an API key for an agent.

        Args:
            agent_id: Agent ID
            provider: Provider ID (e.g., "anthropic", "openai")
            api_key: The API key value

        Returns:
            Configuration result.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(
                browser.configure_api_key(agent_id, provider, api_key)
            )
            return result
        except Exception as e:
            logger.error(f"Configure API key failed: {e}")
            return {"success": False, "error": str(e)}

    def check_api_key_status(self, agent_id: str) -> dict[str, Any]:
        """Check API key configuration status for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with provider configuration status.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(browser.check_api_key_status(agent_id))
            return result
        except Exception as e:
            logger.error(f"Check API key status failed: {e}")
            return {"error": str(e)}

    def refresh(self) -> dict[str, Any]:
        """Refresh the agents cache and re-detect installation status.

        Returns:
            Updated agents list.
        """
        try:
            browser = self._get_browser()
            browser.clear_cache()
            result = asyncio.run(browser.list_agents())
            return result.to_dict()
        except Exception as e:
            logger.error(f"Refresh agents failed: {e}")
            return {"error": str(e)}
