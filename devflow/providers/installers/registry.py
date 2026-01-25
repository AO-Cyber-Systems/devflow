"""Tool registry containing metadata for all supported tools."""

from __future__ import annotations

from .base import ToolCategory, ToolInfo

# =============================================================================
# Code Editors (AI-Focused)
# =============================================================================

VSCODE = ToolInfo(
    id="vscode",
    name="Visual Studio Code",
    description="Popular code editor with extensive extension ecosystem",
    category=ToolCategory.CODE_EDITOR,
    website="https://code.visualstudio.com/",
    icon="Code2",
    binary="code",
    brew_cask="visual-studio-code",
    apt_package="code",  # Requires Microsoft repo
    snap_package="code",
    snap_classic=True,
    winget_id="Microsoft.VisualStudioCode",
    scoop_package="vscode",
    is_essential=True,
)

ZED = ToolInfo(
    id="zed",
    name="Zed",
    description="High-performance editor from the creators of Atom, written in Rust",
    category=ToolCategory.CODE_EDITOR,
    website="https://zed.dev/",
    icon="Zap",
    binary="zed",
    brew_cask="zed",
    official_url="https://zed.dev/download",
    # Windows support via official installer (DirectX 11 backend)
    supports_windows=True,
    supports_linux=True,
    supports_macos=True,
)

CURSOR = ToolInfo(
    id="cursor",
    name="Cursor",
    description="AI-first code editor built on VS Code with deep AI integration",
    category=ToolCategory.CODE_EDITOR,
    website="https://cursor.com/",
    icon="MousePointer2",
    binary="cursor",
    brew_cask="cursor",
    official_url="https://cursor.com/download",
    # Available as .exe, .dmg, .AppImage
    supports_windows=True,
    supports_linux=True,
    supports_macos=True,
)

WINDSURF = ToolInfo(
    id="windsurf",
    name="Windsurf",
    description="AI agent-powered IDE by Codeium with Cascade assistant",
    category=ToolCategory.CODE_EDITOR,
    website="https://windsurf.com/",
    icon="Wind",
    binary="windsurf",
    official_url="https://windsurf.com/download",
    supports_windows=True,
    supports_linux=True,
    supports_macos=True,
)

NEOVIM = ToolInfo(
    id="neovim",
    name="Neovim",
    description="Hyperextensible Vim-based text editor",
    category=ToolCategory.CODE_EDITOR,
    website="https://neovim.io/",
    icon="Terminal",
    binary="nvim",
    brew_package="neovim",
    apt_package="neovim",
    winget_id="Neovim.Neovim",
    scoop_package="neovim",
)

HELIX = ToolInfo(
    id="helix",
    name="Helix",
    description="Post-modern modal text editor with built-in LSP support",
    category=ToolCategory.CODE_EDITOR,
    website="https://helix-editor.com/",
    icon="Feather",
    binary="hx",
    brew_package="helix",
    apt_package="helix",
    winget_id="Helix.Helix",
)

# =============================================================================
# Runtime & Version Management
# =============================================================================

MISE = ToolInfo(
    id="mise",
    name="Mise",
    description="Polyglot tool version manager (replaces nvm, pyenv, rbenv, etc.)",
    category=ToolCategory.RUNTIME,
    website="https://mise.jdx.dev/",
    icon="Layers",
    binary="mise",
    brew_package="mise",
    winget_id="jdx.mise",
    official_url="https://mise.run",
    is_essential=True,
)

NODEJS = ToolInfo(
    id="nodejs",
    name="Node.js",
    description="JavaScript runtime built on Chrome's V8 engine",
    category=ToolCategory.RUNTIME,
    website="https://nodejs.org/",
    icon="Hexagon",
    binary="node",
    mise_package="node",
    managed_by_mise=True,
)

PYTHON = ToolInfo(
    id="python",
    name="Python",
    description="Versatile programming language for scripting and applications",
    category=ToolCategory.RUNTIME,
    website="https://python.org/",
    icon="FileCode",
    binary="python3",
    version_flag="--version",
    mise_package="python",
    managed_by_mise=True,
)

GO = ToolInfo(
    id="go",
    name="Go",
    description="Fast, statically typed language by Google",
    category=ToolCategory.RUNTIME,
    website="https://go.dev/",
    icon="FileCode",
    binary="go",
    mise_package="go",
    managed_by_mise=True,
)

RUST = ToolInfo(
    id="rust",
    name="Rust",
    description="Systems programming language focused on safety and performance",
    category=ToolCategory.RUNTIME,
    website="https://www.rust-lang.org/",
    icon="Cog",
    binary="rustc",
    mise_package="rust",
    managed_by_mise=True,
)

JAVA = ToolInfo(
    id="java",
    name="Java",
    description="Enterprise-grade programming language and platform",
    category=ToolCategory.RUNTIME,
    website="https://www.java.com/",
    icon="Coffee",
    binary="java",
    mise_package="java",
    managed_by_mise=True,
)

DENO = ToolInfo(
    id="deno",
    name="Deno",
    description="Secure runtime for JavaScript and TypeScript",
    category=ToolCategory.RUNTIME,
    website="https://deno.land/",
    icon="FileCode",
    binary="deno",
    mise_package="deno",
    managed_by_mise=True,
)

BUN = ToolInfo(
    id="bun",
    name="Bun",
    description="Fast all-in-one JavaScript runtime and toolkit",
    category=ToolCategory.RUNTIME,
    website="https://bun.sh/",
    icon="Rabbit",
    binary="bun",
    mise_package="bun",
    managed_by_mise=True,
)

# =============================================================================
# Container Tools
# =============================================================================

DOCKER = ToolInfo(
    id="docker",
    name="Docker",
    description="Container platform for building and running applications",
    category=ToolCategory.CONTAINER,
    website="https://www.docker.com/",
    icon="Container",
    binary="docker",
    brew_cask="docker",
    winget_id="Docker.DockerDesktop",
    official_url="https://docs.docker.com/get-docker/",
    is_essential=True,
)

# =============================================================================
# Version Control
# =============================================================================

GIT = ToolInfo(
    id="git",
    name="Git",
    description="Distributed version control system",
    category=ToolCategory.VERSION_CONTROL,
    website="https://git-scm.com/",
    icon="GitBranch",
    binary="git",
    brew_package="git",
    apt_package="git",
    winget_id="Git.Git",
    is_essential=True,
)

GH = ToolInfo(
    id="gh",
    name="GitHub CLI",
    description="GitHub's official command line tool",
    category=ToolCategory.VERSION_CONTROL,
    website="https://cli.github.com/",
    icon="Github",
    binary="gh",
    brew_package="gh",
    apt_package="gh",  # Requires GitHub repo
    winget_id="GitHub.cli",
    scoop_package="gh",
    is_essential=True,
)

# =============================================================================
# Database Tools
# =============================================================================

PSQL = ToolInfo(
    id="psql",
    name="PostgreSQL Client",
    description="Command-line client for PostgreSQL databases",
    category=ToolCategory.DATABASE,
    website="https://www.postgresql.org/",
    icon="Database",
    binary="psql",
    brew_package="postgresql",
    apt_package="postgresql-client",
    winget_id="PostgreSQL.PostgreSQL",
)

SUPABASE = ToolInfo(
    id="supabase",
    name="Supabase CLI",
    description="CLI for local Supabase development and migrations",
    category=ToolCategory.DATABASE,
    website="https://supabase.com/",
    icon="Database",
    binary="supabase",
    brew_package="supabase/tap/supabase",
    npm_package="supabase",
    scoop_package="supabase",
    depends_on=["docker"],
)

# =============================================================================
# Secrets & Security
# =============================================================================

OP = ToolInfo(
    id="op",
    name="1Password CLI",
    description="Command-line interface for 1Password secrets management",
    category=ToolCategory.SECRETS,
    website="https://developer.1password.com/docs/cli/",
    icon="Key",
    binary="op",
    brew_cask="1password-cli",
    winget_id="AgileBits.1Password.CLI",
    official_url="https://1password.com/downloads/command-line",
)

# =============================================================================
# Infrastructure
# =============================================================================

MKCERT = ToolInfo(
    id="mkcert",
    name="mkcert",
    description="Tool for creating locally-trusted development certificates",
    category=ToolCategory.INFRASTRUCTURE,
    website="https://github.com/FiloSottile/mkcert",
    icon="ShieldCheck",
    binary="mkcert",
    brew_package="mkcert",
    apt_package="mkcert",
    scoop_package="mkcert",
)

CLAUDE = ToolInfo(
    id="claude",
    name="Claude Code",
    description="AI coding assistant by Anthropic",
    category=ToolCategory.CLI_UTILITY,
    website="https://claude.ai/code",
    icon="Bot",
    binary="claude",
    official_url="https://claude.ai/code",
    # Native installers recommended, npm deprecated
    is_essential=True,
)

# =============================================================================
# CLI Utilities (Modern Replacements)
# =============================================================================

RIPGREP = ToolInfo(
    id="ripgrep",
    name="ripgrep",
    description="Fast search tool (replaces grep)",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/BurntSushi/ripgrep",
    icon="Search",
    binary="rg",
    brew_package="ripgrep",
    apt_package="ripgrep",
    winget_id="BurntSushi.ripgrep.MSVC",
    mise_package="cargo:ripgrep",
)

FD = ToolInfo(
    id="fd",
    name="fd",
    description="Fast and user-friendly find alternative",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/sharkdp/fd",
    icon="FolderSearch",
    binary="fd",
    brew_package="fd",
    apt_package="fd-find",
    winget_id="sharkdp.fd",
    mise_package="cargo:fd-find",
)

BAT = ToolInfo(
    id="bat",
    name="bat",
    description="Cat clone with syntax highlighting",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/sharkdp/bat",
    icon="FileText",
    binary="bat",
    brew_package="bat",
    apt_package="bat",
    winget_id="sharkdp.bat",
    mise_package="cargo:bat",
)

EZA = ToolInfo(
    id="eza",
    name="eza",
    description="Modern replacement for ls",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/eza-community/eza",
    icon="List",
    binary="eza",
    brew_package="eza",
    apt_package="eza",
    mise_package="cargo:eza",
)

FZF = ToolInfo(
    id="fzf",
    name="fzf",
    description="Command-line fuzzy finder",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/junegunn/fzf",
    icon="Filter",
    binary="fzf",
    brew_package="fzf",
    apt_package="fzf",
    winget_id="junegunn.fzf",
)

JQ = ToolInfo(
    id="jq",
    name="jq",
    description="Lightweight command-line JSON processor",
    category=ToolCategory.CLI_UTILITY,
    website="https://stedolan.github.io/jq/",
    icon="Braces",
    binary="jq",
    brew_package="jq",
    apt_package="jq",
    winget_id="jqlang.jq",
    scoop_package="jq",
)

YQ = ToolInfo(
    id="yq",
    name="yq",
    description="YAML processor (like jq for YAML)",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/mikefarah/yq",
    icon="FileCode",
    binary="yq",
    brew_package="yq",
    snap_package="yq",
    winget_id="MikeFarah.yq",
)

ZOXIDE = ToolInfo(
    id="zoxide",
    name="zoxide",
    description="Smarter cd command with directory jumping",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/ajeetdsouza/zoxide",
    icon="Compass",
    binary="zoxide",
    brew_package="zoxide",
    apt_package="zoxide",
    winget_id="ajeetdsouza.zoxide",
    mise_package="cargo:zoxide",
)

DELTA = ToolInfo(
    id="delta",
    name="delta",
    description="Syntax-highlighting pager for git and diff output",
    category=ToolCategory.CLI_UTILITY,
    website="https://github.com/dandavison/delta",
    icon="GitCompare",
    binary="delta",
    brew_package="git-delta",
    apt_package="git-delta",
    winget_id="dandavison.delta",
    mise_package="cargo:git-delta",
)

STARSHIP = ToolInfo(
    id="starship",
    name="Starship",
    description="Fast, customizable cross-shell prompt",
    category=ToolCategory.SHELL,
    website="https://starship.rs/",
    icon="Star",
    binary="starship",
    brew_package="starship",
    winget_id="Starship.Starship",
    scoop_package="starship",
    mise_package="cargo:starship",
)

HTTPIE = ToolInfo(
    id="httpie",
    name="HTTPie",
    description="Modern, user-friendly command-line HTTP client",
    category=ToolCategory.CLI_UTILITY,
    website="https://httpie.io/",
    icon="Globe",
    binary="http",
    brew_package="httpie",
    apt_package="httpie",
    mise_package="pipx:httpie",
)

# =============================================================================
# Tool Collections
# =============================================================================

# All tools in registry
ALL_TOOLS: list[ToolInfo] = [
    # Code Editors (AI-Focused)
    VSCODE,
    ZED,
    CURSOR,
    WINDSURF,
    NEOVIM,
    HELIX,
    # Runtimes
    MISE,
    NODEJS,
    PYTHON,
    GO,
    RUST,
    JAVA,
    DENO,
    BUN,
    # Containers
    DOCKER,
    # Version Control
    GIT,
    GH,
    # Database
    PSQL,
    SUPABASE,
    # Secrets
    OP,
    # Infrastructure
    MKCERT,
    CLAUDE,
    # CLI Utilities
    RIPGREP,
    FD,
    BAT,
    EZA,
    FZF,
    JQ,
    YQ,
    ZOXIDE,
    DELTA,
    STARSHIP,
    HTTPIE,
]

# Essential tools for DevFlow
ESSENTIAL_TOOLS: list[ToolInfo] = [t for t in ALL_TOOLS if t.is_essential]

# Tools by category
TOOLS_BY_CATEGORY: dict[ToolCategory, list[ToolInfo]] = {}
for tool in ALL_TOOLS:
    if tool.category not in TOOLS_BY_CATEGORY:
        TOOLS_BY_CATEGORY[tool.category] = []
    TOOLS_BY_CATEGORY[tool.category].append(tool)


def get_tool_by_id(tool_id: str) -> ToolInfo | None:
    """Get a tool by its ID."""
    for tool in ALL_TOOLS:
        if tool.id == tool_id:
            return tool
    return None


def get_tools_by_category(category: ToolCategory) -> list[ToolInfo]:
    """Get all tools in a category."""
    return TOOLS_BY_CATEGORY.get(category, [])


def get_mise_managed_tools() -> list[ToolInfo]:
    """Get tools that should be managed by Mise."""
    return [t for t in ALL_TOOLS if t.managed_by_mise]
