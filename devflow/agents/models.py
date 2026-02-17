"""Data models for AI agents."""

from dataclasses import dataclass, field
from enum import Enum


class AgentInstallMethod(str, Enum):
    """Installation method for an AI agent."""

    NPM = "npm"
    CURL = "curl"
    PIP = "pip"
    BREW = "brew"
    MANUAL = "manual"
    VSCODE = "vscode"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            AgentInstallMethod.NPM: "npm (Node.js)",
            AgentInstallMethod.CURL: "curl script",
            AgentInstallMethod.PIP: "pip (Python)",
            AgentInstallMethod.BREW: "Homebrew",
            AgentInstallMethod.MANUAL: "Manual",
            AgentInstallMethod.VSCODE: "VS Code Extension",
        }
        return names.get(self, self.value)


class AgentCapability(str, Enum):
    """Capabilities that an AI agent can have."""

    CODE_GENERATION = "code_generation"
    CODE_EDIT = "code_edit"
    TERMINAL = "terminal"
    MCP = "mcp"
    FILE_SEARCH = "file_search"
    WEB_SEARCH = "web_search"
    MULTI_FILE = "multi_file"
    GIT = "git"
    TESTING = "testing"
    DEBUGGING = "debugging"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            AgentCapability.CODE_GENERATION: "Code Generation",
            AgentCapability.CODE_EDIT: "Code Editing",
            AgentCapability.TERMINAL: "Terminal Access",
            AgentCapability.MCP: "MCP Support",
            AgentCapability.FILE_SEARCH: "File Search",
            AgentCapability.WEB_SEARCH: "Web Search",
            AgentCapability.MULTI_FILE: "Multi-file Editing",
            AgentCapability.GIT: "Git Integration",
            AgentCapability.TESTING: "Test Generation",
            AgentCapability.DEBUGGING: "Debugging",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def icon(self) -> str:
        """SF Symbol icon."""
        icons = {
            AgentCapability.CODE_GENERATION: "doc.text",
            AgentCapability.CODE_EDIT: "pencil",
            AgentCapability.TERMINAL: "terminal",
            AgentCapability.MCP: "link",
            AgentCapability.FILE_SEARCH: "doc.text.magnifyingglass",
            AgentCapability.WEB_SEARCH: "globe",
            AgentCapability.MULTI_FILE: "doc.on.doc",
            AgentCapability.GIT: "arrow.triangle.branch",
            AgentCapability.TESTING: "checkmark.circle",
            AgentCapability.DEBUGGING: "ladybug",
        }
        return icons.get(self, "questionmark.circle")


class AgentProvider(str, Enum):
    """AI providers supported by agents."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            AgentProvider.ANTHROPIC: "Anthropic (Claude)",
            AgentProvider.OPENAI: "OpenAI",
            AgentProvider.GOOGLE: "Google (Gemini)",
            AgentProvider.OLLAMA: "Ollama (Local)",
            AgentProvider.OPENROUTER: "OpenRouter",
            AgentProvider.AZURE: "Azure OpenAI",
            AgentProvider.AWS_BEDROCK: "AWS Bedrock",
        }
        return names.get(self, self.value.title())

    @property
    def api_key_env_var(self) -> str:
        """Environment variable for the API key."""
        env_vars = {
            AgentProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            AgentProvider.OPENAI: "OPENAI_API_KEY",
            AgentProvider.GOOGLE: "GEMINI_API_KEY",
            AgentProvider.OLLAMA: "",  # No API key needed
            AgentProvider.OPENROUTER: "OPENROUTER_API_KEY",
            AgentProvider.AZURE: "AZURE_OPENAI_API_KEY",
            AgentProvider.AWS_BEDROCK: "AWS_ACCESS_KEY_ID",
        }
        return env_vars.get(self, "")


@dataclass
class ApiKeyConfig:
    """Configuration for an API key."""

    provider: AgentProvider
    env_var: str
    required: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider": self.provider.value,
            "provider_display": self.provider.display_name,
            "env_var": self.env_var,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class AIAgent:
    """An AI coding assistant that can be installed and configured."""

    id: str
    name: str
    description: str
    homepage: str
    install_method: AgentInstallMethod
    install_command: str
    config_location: str
    capabilities: list[AgentCapability]
    supported_providers: list[AgentProvider]
    api_keys: list[ApiKeyConfig]

    # Runtime state
    is_installed: bool = False
    is_configured: bool = False
    installed_version: str | None = None

    # Optional metadata
    icon: str = "cpu"
    version: str | None = None
    aliases: list[str] = field(default_factory=list)
    docs_url: str | None = None
    github_url: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "homepage": self.homepage,
            "install_method": self.install_method.value,
            "install_method_display": self.install_method.display_name,
            "install_command": self.install_command,
            "config_location": self.config_location,
            "capabilities": [c.value for c in self.capabilities],
            "capabilities_display": [
                {"id": c.value, "name": c.display_name, "icon": c.icon}
                for c in self.capabilities
            ],
            "supported_providers": [p.value for p in self.supported_providers],
            "supported_providers_display": [
                {"id": p.value, "name": p.display_name}
                for p in self.supported_providers
            ],
            "api_keys": [k.to_dict() for k in self.api_keys],
            "is_installed": self.is_installed,
            "is_configured": self.is_configured,
            "installed_version": self.installed_version,
            "icon": self.icon,
            "version": self.version,
            "aliases": self.aliases,
            "docs_url": self.docs_url,
            "github_url": self.github_url,
        }
