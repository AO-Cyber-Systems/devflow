"""Data models for UI component documentation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ComponentCategory(str, Enum):
    """Category of UI component."""

    FORM = "form"
    LAYOUT = "layout"
    NAVIGATION = "navigation"
    FEEDBACK = "feedback"
    DATA_DISPLAY = "data_display"
    DATA_ENTRY = "data_entry"
    OVERLAY = "overlay"
    MEDIA = "media"
    TYPOGRAPHY = "typography"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            ComponentCategory.FORM: "Form Controls",
            ComponentCategory.LAYOUT: "Layout",
            ComponentCategory.NAVIGATION: "Navigation",
            ComponentCategory.FEEDBACK: "Feedback",
            ComponentCategory.DATA_DISPLAY: "Data Display",
            ComponentCategory.DATA_ENTRY: "Data Entry",
            ComponentCategory.OVERLAY: "Overlay",
            ComponentCategory.MEDIA: "Media",
            ComponentCategory.TYPOGRAPHY: "Typography",
            ComponentCategory.OTHER: "Other",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def icon(self) -> str:
        """SF Symbol icon."""
        icons = {
            ComponentCategory.FORM: "rectangle.and.pencil.and.ellipsis",
            ComponentCategory.LAYOUT: "square.grid.2x2",
            ComponentCategory.NAVIGATION: "arrow.triangle.turn.up.right.diamond",
            ComponentCategory.FEEDBACK: "exclamationmark.bubble",
            ComponentCategory.DATA_DISPLAY: "tablecells",
            ComponentCategory.DATA_ENTRY: "keyboard",
            ComponentCategory.OVERLAY: "rectangle.on.rectangle",
            ComponentCategory.MEDIA: "photo.on.rectangle",
            ComponentCategory.TYPOGRAPHY: "textformat",
            ComponentCategory.OTHER: "ellipsis.circle",
        }
        return icons.get(self, "square")


@dataclass
class PropDefinition:
    """Definition of a component prop/property."""

    name: str
    type: str
    description: str = ""
    default: str | None = None
    required: bool = False
    options: list[str] = field(default_factory=list)  # For enum-like props

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default": self.default,
            "required": self.required,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PropDefinition":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            description=data.get("description", ""),
            default=data.get("default"),
            required=data.get("required", False),
            options=data.get("options", []),
        )


@dataclass
class SlotDefinition:
    """Definition of a component slot."""

    name: str
    description: str = ""
    default_content: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "default_content": self.default_content,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SlotDefinition":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            default_content=data.get("default_content"),
        )


@dataclass
class EventDefinition:
    """Definition of a component event."""

    name: str
    description: str = ""
    payload_type: str | None = None
    payload_description: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "payload_type": self.payload_type,
            "payload_description": self.payload_description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EventDefinition":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            payload_type=data.get("payload_type"),
            payload_description=data.get("payload_description"),
        )


@dataclass
class ComponentExample:
    """An example usage of a component."""

    title: str
    code: str
    description: str = ""
    language: str = "html"  # html, jsx, vue, svelte, etc.

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "code": self.code,
            "description": self.description,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentExample":
        """Create from dictionary."""
        return cls(
            title=data["title"],
            code=data["code"],
            description=data.get("description", ""),
            language=data.get("language", "html"),
        )


@dataclass
class ComponentDoc:
    """Documentation for a UI component."""

    name: str
    category: ComponentCategory
    description: str

    props: list[PropDefinition] = field(default_factory=list)
    slots: list[SlotDefinition] = field(default_factory=list)
    events: list[EventDefinition] = field(default_factory=list)
    examples: list[ComponentExample] = field(default_factory=list)

    # AI-specific guidance
    ai_guidance: str | None = None

    # Accessibility notes
    accessibility: list[str] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    source_file: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "category": self.category.value,
            "category_display": self.category.display_name,
            "category_icon": self.category.icon,
            "description": self.description,
            "props": [p.to_dict() for p in self.props],
            "slots": [s.to_dict() for s in self.slots],
            "events": [e.to_dict() for e in self.events],
            "examples": [ex.to_dict() for ex in self.examples],
            "ai_guidance": self.ai_guidance,
            "accessibility": self.accessibility,
            "tags": self.tags,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentDoc":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            category=ComponentCategory(data["category"]),
            description=data["description"],
            props=[PropDefinition.from_dict(p) for p in data.get("props", [])],
            slots=[SlotDefinition.from_dict(s) for s in data.get("slots", [])],
            events=[EventDefinition.from_dict(e) for e in data.get("events", [])],
            examples=[ComponentExample.from_dict(ex) for ex in data.get("examples", [])],
            ai_guidance=data.get("ai_guidance"),
            accessibility=data.get("accessibility", []),
            tags=data.get("tags", []),
            source_file=data.get("source_file"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )

    def to_ai_context(self) -> str:
        """Generate AI-friendly context string from this component doc."""
        parts = []

        # Component header
        parts.append(f"## {self.name}")
        parts.append(f"Category: {self.category.display_name}")
        parts.append(f"Description: {self.description}")

        # AI guidance
        if self.ai_guidance:
            parts.append(f"\n### AI Guidance\n{self.ai_guidance}")

        # Props
        if self.props:
            parts.append("\n### Props")
            for prop in self.props:
                required = " (required)" if prop.required else ""
                default = f" = {prop.default}" if prop.default else ""
                parts.append(f"- `{prop.name}`: {prop.type}{required}{default}")
                if prop.description:
                    parts.append(f"  {prop.description}")
                if prop.options:
                    parts.append(f"  Options: {', '.join(prop.options)}")

        # Slots
        if self.slots:
            parts.append("\n### Slots")
            for slot in self.slots:
                parts.append(f"- `{slot.name}`: {slot.description}")

        # Events
        if self.events:
            parts.append("\n### Events")
            for event in self.events:
                parts.append(f"- `{event.name}`: {event.description}")
                if event.payload_type:
                    parts.append(f"  Payload: {event.payload_type}")

        # Examples
        if self.examples:
            parts.append("\n### Examples")
            for example in self.examples:
                parts.append(f"\n**{example.title}**")
                if example.description:
                    parts.append(example.description)
                parts.append(f"```{example.language}")
                parts.append(example.code)
                parts.append("```")

        # Accessibility
        if self.accessibility:
            parts.append("\n### Accessibility")
            for note in self.accessibility:
                parts.append(f"- {note}")

        return "\n".join(parts)

    def to_yaml(self) -> str:
        """Convert to YAML format for storage."""
        import yaml

        data = {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
        }

        if self.ai_guidance:
            data["ai_guidance"] = self.ai_guidance

        if self.props:
            data["props"] = [p.to_dict() for p in self.props]

        if self.slots:
            data["slots"] = [s.to_dict() for s in self.slots]

        if self.events:
            data["events"] = [e.to_dict() for e in self.events]

        if self.examples:
            data["examples"] = [ex.to_dict() for ex in self.examples]

        if self.accessibility:
            data["accessibility"] = self.accessibility

        if self.tags:
            data["tags"] = self.tags

        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "ComponentDoc":
        """Create from YAML content."""
        import yaml

        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)
