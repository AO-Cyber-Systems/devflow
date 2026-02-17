"""Data models for the tool browser."""

from dataclasses import dataclass, field
from enum import Enum


class ToolSource(str, Enum):
    """Source of a browsable tool."""

    MISE = "mise"
    HOMEBREW = "homebrew"
    CASK = "cask"


class ToolBrowserCategory(str, Enum):
    """Categories for organizing tools."""

    LANGUAGES = "languages"
    DATABASES = "databases"
    CONTAINERS = "containers"
    CLOUD = "cloud"
    VERSION_CONTROL = "vcs"
    EDITORS = "editors"
    SHELL = "shell"
    BUILD_TOOLS = "build"
    SECURITY = "security"
    NETWORKING = "networking"
    MEDIA = "media"
    PRODUCTIVITY = "productivity"
    DEVOPS = "devops"
    APPLICATIONS = "applications"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """Human-readable category name."""
        names = {
            ToolBrowserCategory.LANGUAGES: "Languages & Runtimes",
            ToolBrowserCategory.DATABASES: "Databases",
            ToolBrowserCategory.CONTAINERS: "Containers & VMs",
            ToolBrowserCategory.CLOUD: "Cloud & Infrastructure",
            ToolBrowserCategory.VERSION_CONTROL: "Version Control",
            ToolBrowserCategory.EDITORS: "Editors & IDEs",
            ToolBrowserCategory.SHELL: "Shell & Terminal",
            ToolBrowserCategory.BUILD_TOOLS: "Build Tools",
            ToolBrowserCategory.SECURITY: "Security",
            ToolBrowserCategory.NETWORKING: "Networking",
            ToolBrowserCategory.MEDIA: "Media & Graphics",
            ToolBrowserCategory.PRODUCTIVITY: "Productivity",
            ToolBrowserCategory.DEVOPS: "DevOps",
            ToolBrowserCategory.APPLICATIONS: "Applications",
            ToolBrowserCategory.OTHER: "Other",
        }
        return names.get(self, self.value.title())

    @property
    def icon(self) -> str:
        """SF Symbol name for the category."""
        icons = {
            ToolBrowserCategory.LANGUAGES: "chevron.left.forwardslash.chevron.right",
            ToolBrowserCategory.DATABASES: "cylinder",
            ToolBrowserCategory.CONTAINERS: "shippingbox",
            ToolBrowserCategory.CLOUD: "cloud",
            ToolBrowserCategory.VERSION_CONTROL: "arrow.triangle.branch",
            ToolBrowserCategory.EDITORS: "pencil.and.outline",
            ToolBrowserCategory.SHELL: "terminal",
            ToolBrowserCategory.BUILD_TOOLS: "hammer",
            ToolBrowserCategory.SECURITY: "lock.shield",
            ToolBrowserCategory.NETWORKING: "network",
            ToolBrowserCategory.MEDIA: "photo",
            ToolBrowserCategory.PRODUCTIVITY: "bolt",
            ToolBrowserCategory.DEVOPS: "gearshape.2",
            ToolBrowserCategory.APPLICATIONS: "macwindow",
            ToolBrowserCategory.OTHER: "ellipsis.circle",
        }
        return icons.get(self, "questionmark.circle")


@dataclass
class BrowsableTool:
    """A tool that can be browsed and installed."""

    id: str  # Unique ID (e.g., "mise:node", "brew:git", "cask:docker")
    name: str  # Display name
    description: str  # Tool description
    source: ToolSource  # mise | homebrew | cask
    category: ToolBrowserCategory  # Derived from tool type/description
    install_command: str  # e.g., "mise use node@latest", "brew install git"

    # Optional metadata
    homepage: str | None = None
    version: str | None = None
    aliases: list[str] = field(default_factory=list)
    license: str | None = None

    # Install state (populated at runtime)
    is_installed: bool = False
    installed_version: str | None = None

    # Flags
    is_gui_app: bool = False
    is_runtime: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "category": self.category.value,
            "category_display": self.category.display_name,
            "category_icon": self.category.icon,
            "install_command": self.install_command,
            "homepage": self.homepage,
            "version": self.version,
            "aliases": self.aliases,
            "license": self.license,
            "is_installed": self.is_installed,
            "installed_version": self.installed_version,
            "is_gui_app": self.is_gui_app,
            "is_runtime": self.is_runtime,
        }


@dataclass
class SearchResult:
    """Result from searching tools."""

    tools: list[BrowsableTool]
    total: int
    has_more: bool
    offset: int
    limit: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tools": [t.to_dict() for t in self.tools],
            "total": self.total,
            "has_more": self.has_more,
            "offset": self.offset,
            "limit": self.limit,
        }


@dataclass
class CategoryInfo:
    """Information about a category."""

    id: str
    name: str
    icon: str
    count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "count": self.count,
        }


@dataclass
class SourceInfo:
    """Information about a tool source."""

    id: str
    name: str
    count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count,
        }
