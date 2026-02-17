"""RPC method handlers for the bridge server."""

from .agents import AgentsHandler
from .ai import AIHandler
from .code import CodeHandler
from .components import ComponentsHandler
from .config import ConfigHandler
from .context import ContextHandler
from .database import DatabaseHandler
from .deploy import DeployHandler
from .dev import DevHandler
from .docs import DocsHandler
from .domains import DomainsHandler
from .infra import InfraHandler
from .logs import LogsHandler
from .projects import ProjectsHandler
from .secrets import SecretsHandler
from .setup import SetupHandler
from .system import SystemHandler
from .templates import TemplatesHandler
from .tools import ToolsHandler

__all__ = [
    "AgentsHandler",
    "AIHandler",
    "CodeHandler",
    "ComponentsHandler",
    "ConfigHandler",
    "ContextHandler",
    "DatabaseHandler",
    "DeployHandler",
    "DevHandler",
    "DocsHandler",
    "DomainsHandler",
    "InfraHandler",
    "LogsHandler",
    "ProjectsHandler",
    "SecretsHandler",
    "SetupHandler",
    "SystemHandler",
    "TemplatesHandler",
    "ToolsHandler",
]
