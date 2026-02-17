"""Agent browser for listing and searching AI agents."""

import asyncio
import logging
from dataclasses import dataclass

from .models import AIAgent
from .registry import get_all_agents, get_agent
from .installer import AgentInstaller

logger = logging.getLogger(__name__)


@dataclass
class AgentSearchResult:
    """Result from searching agents."""

    agents: list[AIAgent]
    total: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "agents": [a.to_dict() for a in self.agents],
            "total": self.total,
        }


class AgentBrowser:
    """Browser for discovering and managing AI coding agents."""

    def __init__(self):
        self._installer = AgentInstaller()
        self._agents_cache: list[AIAgent] | None = None

    async def list_agents(
        self,
        installed_only: bool = False,
        search: str = "",
    ) -> AgentSearchResult:
        """List all available agents.

        Args:
            installed_only: Only show installed agents
            search: Filter by search query

        Returns:
            AgentSearchResult with matching agents.
        """
        agents = await self._get_agents_with_status()

        # Filter by search
        if search:
            search_lower = search.lower()
            agents = [
                a
                for a in agents
                if search_lower in a.name.lower()
                or search_lower in a.description.lower()
                or any(search_lower in alias.lower() for alias in a.aliases)
            ]

        # Filter by installed status
        if installed_only:
            agents = [a for a in agents if a.is_installed]

        return AgentSearchResult(agents=agents, total=len(agents))

    async def get_agent(self, agent_id: str) -> AIAgent | None:
        """Get a single agent by ID with installation status.

        Args:
            agent_id: The agent ID (e.g., "claude-code", "aider")

        Returns:
            Agent with installation status, or None if not found.
        """
        agent = get_agent(agent_id)
        if not agent:
            return None

        # Check installation status
        is_installed, version = await self._installer.detect_installed(agent)
        agent.is_installed = is_installed
        agent.installed_version = version

        # Check API key configuration
        api_key_status = self._installer.check_api_key_configured(agent)
        agent.is_configured = any(api_key_status.values())

        return agent

    async def install(self, agent_id: str) -> dict:
        """Install an agent.

        Args:
            agent_id: The agent ID to install

        Returns:
            Installation result dictionary.
        """
        agent = get_agent(agent_id)
        if not agent:
            return {
                "success": False,
                "error": f"Agent not found: {agent_id}",
            }

        result = await self._installer.install(agent)

        # Clear cache to refresh status
        self._agents_cache = None

        return result

    async def detect_installed(self, agent_ids: list[str]) -> dict[str, bool]:
        """Batch check installation status for multiple agents.

        Args:
            agent_ids: List of agent IDs to check

        Returns:
            Dictionary mapping agent_id to installed status.
        """
        results = {}

        async def check_one(agent_id: str):
            agent = get_agent(agent_id)
            if agent:
                is_installed, _ = await self._installer.detect_installed(agent)
                results[agent_id] = is_installed
            else:
                results[agent_id] = False

        # Check all agents concurrently
        await asyncio.gather(*[check_one(aid) for aid in agent_ids])

        return results

    async def configure_api_key(
        self, agent_id: str, provider: str, api_key: str
    ) -> dict:
        """Configure an API key for an agent.

        Args:
            agent_id: The agent ID
            provider: The provider ID (e.g., "anthropic", "openai")
            api_key: The API key value

        Returns:
            Configuration result dictionary.
        """
        agent = get_agent(agent_id)
        if not agent:
            return {
                "success": False,
                "error": f"Agent not found: {agent_id}",
            }

        return await self._installer.configure_api_key(agent, provider, api_key)

    async def check_api_key_status(self, agent_id: str) -> dict:
        """Check API key configuration status for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            Dictionary with provider configuration status.
        """
        agent = get_agent(agent_id)
        if not agent:
            return {
                "error": f"Agent not found: {agent_id}",
            }

        status = self._installer.check_api_key_configured(agent)
        return {
            "agent_id": agent_id,
            "providers": status,
        }

    async def _get_agents_with_status(self) -> list[AIAgent]:
        """Get all agents with installation status."""
        if self._agents_cache is not None:
            return self._agents_cache

        agents = get_all_agents()

        # Check installation status for all agents concurrently
        async def update_status(agent: AIAgent):
            is_installed, version = await self._installer.detect_installed(agent)
            agent.is_installed = is_installed
            agent.installed_version = version

            # Check API key configuration
            api_key_status = self._installer.check_api_key_configured(agent)
            agent.is_configured = any(api_key_status.values())

        await asyncio.gather(*[update_status(a) for a in agents])

        self._agents_cache = agents
        return agents

    def clear_cache(self):
        """Clear the agents cache."""
        self._agents_cache = None
