"""Data models for the template system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TemplateCategory(str, Enum):
    """Template categories for organization."""

    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    FULLSTACK = "fullstack"
    API = "api"
    LIBRARY = "library"
    OTHER = "other"


class WizardFieldType(str, Enum):
    """Types of wizard input fields."""

    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    DIRECTORY = "directory"
    NUMBER = "number"


class TemplateSource(str, Enum):
    """Where a template was loaded from."""

    BUILTIN = "builtin"
    LOCAL = "local"
    GIT = "git"


@dataclass
class WizardFieldOption:
    """An option for select/multiselect fields."""

    value: str
    label: str
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardFieldOption:
        """Create from dictionary."""
        return cls(
            value=data["value"],
            label=data["label"],
            description=data.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {"value": self.value, "label": self.label}
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class WizardField:
    """A field in a wizard step."""

    id: str
    type: WizardFieldType
    label: str
    required: bool = False
    default: Any = None
    placeholder: str | None = None
    description: str | None = None
    validation: str | None = None  # Regex pattern
    validation_message: str | None = None
    options: list[WizardFieldOption] = field(default_factory=list)
    # Conditional visibility
    show_when: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardField:
        """Create from dictionary."""
        field_type = WizardFieldType(data.get("type", "text"))
        options = [
            WizardFieldOption.from_dict(opt)
            for opt in data.get("options", [])
        ]

        return cls(
            id=data["id"],
            type=field_type,
            label=data["label"],
            required=data.get("required", False),
            default=data.get("default"),
            placeholder=data.get("placeholder"),
            description=data.get("description"),
            validation=data.get("validation"),
            validation_message=data.get("validation_message"),
            options=options,
            show_when=data.get("show_when"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "required": self.required,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.placeholder:
            result["placeholder"] = self.placeholder
        if self.description:
            result["description"] = self.description
        if self.validation:
            result["validation"] = self.validation
        if self.validation_message:
            result["validation_message"] = self.validation_message
        if self.options:
            result["options"] = [opt.to_dict() for opt in self.options]
        if self.show_when:
            result["show_when"] = self.show_when
        return result


@dataclass
class WizardStep:
    """A step in the project creation wizard."""

    id: str
    title: str
    description: str | None = None
    fields: list[WizardField] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardStep:
        """Create from dictionary."""
        fields = [WizardField.from_dict(f) for f in data.get("fields", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            fields=fields,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "title": self.title,
            "fields": [f.to_dict() for f in self.fields],
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class FileMapping:
    """Mapping from source to destination file."""

    source: str
    destination: str
    template: bool = False  # If true, render with Jinja2
    recursive: bool = False  # If true, copy directory recursively
    condition: str | None = None  # Condition for including this file

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileMapping:
        """Create from dictionary."""
        return cls(
            source=data["source"],
            destination=data["destination"],
            template=data.get("template", False),
            recursive=data.get("recursive", False),
            condition=data.get("condition"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "source": self.source,
            "destination": self.destination,
        }
        if self.template:
            result["template"] = True
        if self.recursive:
            result["recursive"] = True
        if self.condition:
            result["condition"] = self.condition
        return result


@dataclass
class Hook:
    """Post-creation hook command."""

    name: str
    command: str
    working_dir: str | None = None  # Relative to project root
    condition: str | None = None
    continue_on_error: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hook:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            command=data["command"],
            working_dir=data.get("working_dir"),
            condition=data.get("condition"),
            continue_on_error=data.get("continue_on_error", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "command": self.command,
        }
        if self.working_dir:
            result["working_dir"] = self.working_dir
        if self.condition:
            result["condition"] = self.condition
        if self.continue_on_error:
            result["continue_on_error"] = True
        return result


@dataclass
class TemplateMetadata:
    """Template metadata from template.yml."""

    name: str  # Unique identifier (e.g., "nextjs-fullstack")
    display_name: str
    description: str
    category: TemplateCategory = TemplateCategory.OTHER
    icon: str | None = None  # Icon identifier
    author: str | None = None
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateMetadata:
        """Create from dictionary."""
        category = TemplateCategory.OTHER
        if cat_str := data.get("category"):
            try:
                category = TemplateCategory(cat_str)
            except ValueError:
                pass

        return cls(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            category=category,
            icon=data.get("icon"),
            author=data.get("author"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "icon": self.icon,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
        }


@dataclass
class Template:
    """Complete template definition."""

    metadata: TemplateMetadata
    required_tools: list[str] = field(default_factory=list)
    recommended_tools: list[str] = field(default_factory=list)
    wizard_steps: list[WizardStep] = field(default_factory=list)
    files: list[FileMapping] = field(default_factory=list)
    hooks: list[Hook] = field(default_factory=list)
    # Source tracking
    source: TemplateSource = TemplateSource.BUILTIN
    source_path: Path | None = None

    @property
    def id(self) -> str:
        """Get template ID (same as name)."""
        return self.metadata.name

    @classmethod
    def from_dict(cls, data: dict[str, Any], source: TemplateSource = TemplateSource.BUILTIN, source_path: Path | None = None) -> Template:
        """Create from dictionary (parsed YAML)."""
        metadata = TemplateMetadata.from_dict(data.get("metadata", {}))

        wizard_steps = []
        if wizard_data := data.get("wizard", {}):
            for step_data in wizard_data.get("steps", []):
                wizard_steps.append(WizardStep.from_dict(step_data))

        files = [FileMapping.from_dict(f) for f in data.get("files", [])]
        hooks = [Hook.from_dict(h) for h in data.get("hooks", [])]

        return cls(
            metadata=metadata,
            required_tools=data.get("required_tools", []),
            recommended_tools=data.get("recommended_tools", []),
            wizard_steps=wizard_steps,
            files=files,
            hooks=hooks,
            source=source,
            source_path=source_path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "version": "1",
            "metadata": self.metadata.to_dict(),
            "required_tools": self.required_tools,
            "recommended_tools": self.recommended_tools,
        }

        if self.wizard_steps:
            result["wizard"] = {
                "steps": [s.to_dict() for s in self.wizard_steps]
            }

        if self.files:
            result["files"] = [f.to_dict() for f in self.files]

        if self.hooks:
            result["hooks"] = [h.to_dict() for h in self.hooks]

        return result

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert to summary dictionary for listing."""
        return {
            "id": self.id,
            "name": self.metadata.name,
            "display_name": self.metadata.display_name,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "icon": self.metadata.icon,
            "author": self.metadata.author,
            "version": self.metadata.version,
            "tags": self.metadata.tags,
            "source": self.source.value,
            "required_tools": self.required_tools,
            "recommended_tools": self.recommended_tools,
            "wizard_step_count": len(self.wizard_steps),
        }
