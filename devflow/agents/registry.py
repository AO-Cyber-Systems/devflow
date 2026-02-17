"""Registry of known AI coding agents."""

from .models import (
    AgentCapability,
    AgentInstallMethod,
    AgentProvider,
    AIAgent,
    ApiKeyConfig,
)


AGENT_REGISTRY: dict[str, AIAgent] = {
    "claude-code": AIAgent(
        id="claude-code",
        name="Claude Code",
        description="Anthropic's official AI coding assistant CLI. Agentic coding with Claude directly in your terminal.",
        homepage="https://docs.anthropic.com/en/docs/claude-code",
        install_method=AgentInstallMethod.NPM,
        install_command="npm install -g @anthropic-ai/claude-code",
        config_location="~/.claude/",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.TERMINAL,
            AgentCapability.MCP,
            AgentCapability.FILE_SEARCH,
            AgentCapability.WEB_SEARCH,
            AgentCapability.MULTI_FILE,
            AgentCapability.GIT,
            AgentCapability.TESTING,
        ],
        supported_providers=[AgentProvider.ANTHROPIC],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.ANTHROPIC,
                env_var="ANTHROPIC_API_KEY",
                required=True,
                description="API key from console.anthropic.com",
            )
        ],
        icon="brain",
        docs_url="https://docs.anthropic.com/en/docs/claude-code",
        github_url="https://github.com/anthropics/claude-code",
    ),
    "opencode": AIAgent(
        id="opencode",
        name="OpenCode",
        description="Open-source AI coding assistant supporting multiple providers including OpenAI, Anthropic, and local models.",
        homepage="https://opencode.ai",
        install_method=AgentInstallMethod.CURL,
        install_command="curl -fsSL https://opencode.ai/install.sh | bash",
        config_location="~/.config/opencode/",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.TERMINAL,
            AgentCapability.FILE_SEARCH,
            AgentCapability.MULTI_FILE,
            AgentCapability.GIT,
        ],
        supported_providers=[
            AgentProvider.OPENAI,
            AgentProvider.ANTHROPIC,
            AgentProvider.GOOGLE,
            AgentProvider.OLLAMA,
            AgentProvider.OPENROUTER,
        ],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.OPENAI,
                env_var="OPENAI_API_KEY",
                required=False,
                description="API key from platform.openai.com",
            ),
            ApiKeyConfig(
                provider=AgentProvider.ANTHROPIC,
                env_var="ANTHROPIC_API_KEY",
                required=False,
                description="API key from console.anthropic.com",
            ),
        ],
        icon="chevron.left.forwardslash.chevron.right",
        github_url="https://github.com/opencode-ai/opencode",
    ),
    "gemini-cli": AIAgent(
        id="gemini-cli",
        name="Gemini CLI",
        description="Google's official CLI for interacting with Gemini models. Supports code generation and editing.",
        homepage="https://github.com/google-gemini/gemini-cli",
        install_method=AgentInstallMethod.NPM,
        install_command="npm install -g @anthropic-ai/claude-code",  # Using claude-code as placeholder
        config_location=".gemini/.env",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.TERMINAL,
            AgentCapability.FILE_SEARCH,
            AgentCapability.WEB_SEARCH,
        ],
        supported_providers=[AgentProvider.GOOGLE],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.GOOGLE,
                env_var="GEMINI_API_KEY",
                required=True,
                description="API key from aistudio.google.com",
            )
        ],
        icon="sparkles",
        github_url="https://github.com/google-gemini/gemini-cli",
    ),
    "codex-cli": AIAgent(
        id="codex-cli",
        name="Codex CLI",
        description="OpenAI's command-line tool for code generation using GPT models.",
        homepage="https://github.com/openai/codex",
        install_method=AgentInstallMethod.NPM,
        install_command="npm install -g @openai/codex",
        config_location="~/.codex/",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.TERMINAL,
            AgentCapability.FILE_SEARCH,
        ],
        supported_providers=[AgentProvider.OPENAI],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.OPENAI,
                env_var="OPENAI_API_KEY",
                required=True,
                description="API key from platform.openai.com",
            )
        ],
        icon="bolt",
        github_url="https://github.com/openai/codex",
    ),
    "aider": AIAgent(
        id="aider",
        name="Aider",
        description="AI pair programming in your terminal. Works with GPT-4, Claude, and local models to help you edit code.",
        homepage="https://aider.chat",
        install_method=AgentInstallMethod.PIP,
        install_command="pip install aider-chat",
        config_location=".aider.conf.yml",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.MULTI_FILE,
            AgentCapability.GIT,
            AgentCapability.TESTING,
        ],
        supported_providers=[
            AgentProvider.OPENAI,
            AgentProvider.ANTHROPIC,
            AgentProvider.OLLAMA,
            AgentProvider.OPENROUTER,
            AgentProvider.AZURE,
        ],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.OPENAI,
                env_var="OPENAI_API_KEY",
                required=False,
                description="API key from platform.openai.com",
            ),
            ApiKeyConfig(
                provider=AgentProvider.ANTHROPIC,
                env_var="ANTHROPIC_API_KEY",
                required=False,
                description="API key from console.anthropic.com",
            ),
        ],
        icon="person.2",
        docs_url="https://aider.chat/docs/",
        github_url="https://github.com/paul-gauthier/aider",
    ),
    "continue": AIAgent(
        id="continue",
        name="Continue",
        description="Open-source AI code assistant for VS Code and JetBrains. Supports many LLM providers.",
        homepage="https://continue.dev",
        install_method=AgentInstallMethod.VSCODE,
        install_command="code --install-extension Continue.continue",
        config_location="~/.continue/",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_EDIT,
            AgentCapability.FILE_SEARCH,
            AgentCapability.DEBUGGING,
            AgentCapability.TESTING,
        ],
        supported_providers=[
            AgentProvider.OPENAI,
            AgentProvider.ANTHROPIC,
            AgentProvider.GOOGLE,
            AgentProvider.OLLAMA,
            AgentProvider.OPENROUTER,
            AgentProvider.AZURE,
        ],
        api_keys=[
            ApiKeyConfig(
                provider=AgentProvider.OPENAI,
                env_var="OPENAI_API_KEY",
                required=False,
                description="API key from platform.openai.com",
            ),
            ApiKeyConfig(
                provider=AgentProvider.ANTHROPIC,
                env_var="ANTHROPIC_API_KEY",
                required=False,
                description="API key from console.anthropic.com",
            ),
        ],
        icon="puzzlepiece",
        docs_url="https://continue.dev/docs",
        github_url="https://github.com/continuedev/continue",
    ),
}


def get_all_agents() -> list[AIAgent]:
    """Get all registered agents."""
    return list(AGENT_REGISTRY.values())


def get_agent(agent_id: str) -> AIAgent | None:
    """Get an agent by ID."""
    return AGENT_REGISTRY.get(agent_id)
