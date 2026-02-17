"""AI Agent browser and installer module."""

from .models import (
    AgentCapability,
    AgentInstallMethod,
    AgentProvider,
    AIAgent,
    ApiKeyConfig,
)
from .registry import AGENT_REGISTRY, get_all_agents, get_agent
from .browser import AgentBrowser
from .installer import AgentInstaller

__all__ = [
    "AgentCapability",
    "AgentInstallMethod",
    "AgentProvider",
    "AIAgent",
    "ApiKeyConfig",
    "AGENT_REGISTRY",
    "get_all_agents",
    "get_agent",
    "AgentBrowser",
    "AgentInstaller",
]
