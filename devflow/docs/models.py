"""Data models for dev documentation."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocType(str, Enum):
    """Type of documentation."""

    API = "api"
    ARCHITECTURE = "architecture"
    COMPONENT = "component"
    GUIDE = "guide"
    REFERENCE = "reference"
    TUTORIAL = "tutorial"
    CUSTOM = "custom"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            DocType.API: "API Documentation",
            DocType.ARCHITECTURE: "Architecture",
            DocType.COMPONENT: "Component Docs",
            DocType.GUIDE: "Guide",
            DocType.REFERENCE: "Reference",
            DocType.TUTORIAL: "Tutorial",
            DocType.CUSTOM: "Custom",
        }
        return names.get(self, self.value.title())

    @property
    def icon(self) -> str:
        """SF Symbol icon."""
        icons = {
            DocType.API: "network",
            DocType.ARCHITECTURE: "building.2",
            DocType.COMPONENT: "square.stack.3d.up",
            DocType.GUIDE: "book",
            DocType.REFERENCE: "doc.text.magnifyingglass",
            DocType.TUTORIAL: "graduationcap",
            DocType.CUSTOM: "doc.text",
        }
        return icons.get(self, "doc")


class DocFormat(str, Enum):
    """Format of the documentation content."""

    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    OPENAPI = "openapi"
    ASYNCAPI = "asyncapi"
    PLAINTEXT = "plaintext"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            DocFormat.MARKDOWN: "Markdown",
            DocFormat.JSON: "JSON",
            DocFormat.YAML: "YAML",
            DocFormat.OPENAPI: "OpenAPI",
            DocFormat.ASYNCAPI: "AsyncAPI",
            DocFormat.PLAINTEXT: "Plain Text",
        }
        return names.get(self, self.value.upper())

    @property
    def file_extension(self) -> str:
        """File extension for this format."""
        extensions = {
            DocFormat.MARKDOWN: ".md",
            DocFormat.JSON: ".json",
            DocFormat.YAML: ".yaml",
            DocFormat.OPENAPI: ".json",
            DocFormat.ASYNCAPI: ".yaml",
            DocFormat.PLAINTEXT: ".txt",
        }
        return extensions.get(self, ".txt")


@dataclass
class Documentation:
    """A documentation document."""

    id: str
    title: str
    doc_type: DocType
    format: DocFormat
    content: str
    project_id: str | None = None  # None for global docs

    # Metadata
    description: str = ""
    tags: list[str] = field(default_factory=list)
    ai_context: str | None = None  # Special hints for AI consumption
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # File info (if imported from file)
    source_file: str | None = None

    @classmethod
    def create(
        cls,
        title: str,
        doc_type: DocType,
        format: DocFormat,
        content: str,
        project_id: str | None = None,
        **kwargs,
    ) -> "Documentation":
        """Create a new documentation with a generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            doc_type=doc_type,
            format=format,
            content=content,
            project_id=project_id,
            **kwargs,
        )

    def to_dict(self, include_content: bool = True) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "doc_type": self.doc_type.value,
            "doc_type_display": self.doc_type.display_name,
            "doc_type_icon": self.doc_type.icon,
            "format": self.format.value,
            "format_display": self.format.display_name,
            "project_id": self.project_id,
            "description": self.description,
            "tags": self.tags,
            "ai_context": self.ai_context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_file": self.source_file,
        }
        if include_content:
            result["content"] = self.content
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Documentation":
        """Create from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            doc_type=DocType(data["doc_type"]),
            format=DocFormat(data["format"]),
            content=data.get("content", ""),
            project_id=data.get("project_id"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            ai_context=data.get("ai_context"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
            source_file=data.get("source_file"),
        )

    def to_ai_context(self) -> str:
        """Generate AI-friendly context string from this documentation."""
        parts = []

        # Add header
        parts.append(f"# {self.title}")
        parts.append(f"Type: {self.doc_type.display_name}")

        if self.description:
            parts.append(f"Description: {self.description}")

        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")

        # Add AI context hint if present
        if self.ai_context:
            parts.append(f"\n## AI Context\n{self.ai_context}")

        # Add content
        parts.append(f"\n## Content\n{self.content}")

        return "\n".join(parts)
