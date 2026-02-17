"""Component documentation manager for CRUD operations."""

import json
import logging
from datetime import datetime
from pathlib import Path

import yaml

from .models import ComponentCategory, ComponentDoc

logger = logging.getLogger(__name__)


class ComponentManager:
    """Manages UI component documentation storage and retrieval."""

    COMPONENTS_DIR = ".devflow/components"
    INDEX_FILE = "index.json"

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.components_dir = self.project_path / self.COMPONENTS_DIR
        self._ensure_dir()

    def _ensure_dir(self):
        """Ensure the components directory exists."""
        self.components_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.components_dir / self.INDEX_FILE
        if not index_file.exists():
            self._save_index([])

    def _load_index(self) -> list[str]:
        """Load the index of component names."""
        index_file = self.components_dir / self.INDEX_FILE
        if not index_file.exists():
            return []
        try:
            return json.loads(index_file.read_text())
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading component index: {e}")
            return []

    def _save_index(self, index: list[str]):
        """Save the index file."""
        index_file = self.components_dir / self.INDEX_FILE
        index_file.write_text(json.dumps(sorted(set(index)), indent=2))

    def _get_component_file(self, name: str) -> Path:
        """Get the file path for a component."""
        return self.components_dir / f"{name}.yml"

    def list_components(
        self,
        category: str | None = None,
        search: str | None = None,
    ) -> list[ComponentDoc]:
        """List all component documentation.

        Args:
            category: Filter by category
            search: Search in name and description

        Returns:
            List of ComponentDoc objects.
        """
        index = self._load_index()
        components = []

        for name in index:
            component = self.get_component(name)
            if component is None:
                continue

            # Apply filters
            if category and component.category.value != category:
                continue

            if search:
                search_lower = search.lower()
                if (
                    search_lower not in component.name.lower()
                    and search_lower not in component.description.lower()
                    and not any(search_lower in tag.lower() for tag in component.tags)
                ):
                    continue

            components.append(component)

        return components

    def get_component(self, name: str) -> ComponentDoc | None:
        """Get a component documentation by name.

        Args:
            name: Component name

        Returns:
            ComponentDoc or None if not found.
        """
        file_path = self._get_component_file(name)
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text()
            return ComponentDoc.from_yaml(content)
        except Exception as e:
            logger.error(f"Error loading component {name}: {e}")
            return None

    def create_component(
        self,
        name: str,
        category: str,
        description: str,
        props: list[dict] | None = None,
        slots: list[dict] | None = None,
        events: list[dict] | None = None,
        examples: list[dict] | None = None,
        ai_guidance: str | None = None,
        accessibility: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> ComponentDoc:
        """Create a new component documentation.

        Args:
            name: Component name
            category: Component category
            description: Component description
            props: List of prop definitions
            slots: List of slot definitions
            events: List of event definitions
            examples: List of examples
            ai_guidance: AI-specific guidance
            accessibility: Accessibility notes
            tags: Tags for searching

        Returns:
            Created ComponentDoc.
        """
        from .models import (
            PropDefinition,
            SlotDefinition,
            EventDefinition,
            ComponentExample,
        )

        component = ComponentDoc(
            name=name,
            category=ComponentCategory(category),
            description=description,
            props=[PropDefinition.from_dict(p) for p in (props or [])],
            slots=[SlotDefinition.from_dict(s) for s in (slots or [])],
            events=[EventDefinition.from_dict(e) for e in (events or [])],
            examples=[ComponentExample.from_dict(ex) for ex in (examples or [])],
            ai_guidance=ai_guidance,
            accessibility=accessibility or [],
            tags=tags or [],
        )

        # Save to file
        file_path = self._get_component_file(name)
        file_path.write_text(component.to_yaml())

        # Update index
        index = self._load_index()
        if name not in index:
            index.append(name)
            self._save_index(index)

        return component

    def update_component(
        self,
        name: str,
        category: str | None = None,
        description: str | None = None,
        props: list[dict] | None = None,
        slots: list[dict] | None = None,
        events: list[dict] | None = None,
        examples: list[dict] | None = None,
        ai_guidance: str | None = None,
        accessibility: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> ComponentDoc | None:
        """Update an existing component documentation.

        Args:
            name: Component name
            category: New category (optional)
            description: New description (optional)
            props: New props (optional)
            slots: New slots (optional)
            events: New events (optional)
            examples: New examples (optional)
            ai_guidance: New AI guidance (optional)
            accessibility: New accessibility notes (optional)
            tags: New tags (optional)

        Returns:
            Updated ComponentDoc or None if not found.
        """
        from .models import (
            PropDefinition,
            SlotDefinition,
            EventDefinition,
            ComponentExample,
        )

        component = self.get_component(name)
        if component is None:
            return None

        # Update fields
        if category is not None:
            component.category = ComponentCategory(category)
        if description is not None:
            component.description = description
        if props is not None:
            component.props = [PropDefinition.from_dict(p) for p in props]
        if slots is not None:
            component.slots = [SlotDefinition.from_dict(s) for s in slots]
        if events is not None:
            component.events = [EventDefinition.from_dict(e) for e in events]
        if examples is not None:
            component.examples = [ComponentExample.from_dict(ex) for ex in examples]
        if ai_guidance is not None:
            component.ai_guidance = ai_guidance
        if accessibility is not None:
            component.accessibility = accessibility
        if tags is not None:
            component.tags = tags

        component.updated_at = datetime.now()

        # Save to file
        file_path = self._get_component_file(name)
        file_path.write_text(component.to_yaml())

        return component

    def delete_component(self, name: str) -> bool:
        """Delete a component documentation.

        Args:
            name: Component name

        Returns:
            True if deleted, False if not found.
        """
        file_path = self._get_component_file(name)
        if not file_path.exists():
            return False

        file_path.unlink()

        # Update index
        index = self._load_index()
        if name in index:
            index.remove(name)
            self._save_index(index)

        return True

    def get_ai_context(
        self,
        component_names: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> str:
        """Get aggregated AI context from component documentation.

        Args:
            component_names: Specific components to include (None for all)
            categories: Filter by categories (None for all)

        Returns:
            AI-friendly context string.
        """
        if component_names:
            components = [
                c for name in component_names
                if (c := self.get_component(name)) is not None
            ]
        else:
            components = self.list_components()

        if categories:
            components = [c for c in components if c.category.value in categories]

        if not components:
            return ""

        parts = ["# UI Component Library\n"]
        parts.append("The following components are available for building UIs:\n")

        for component in components:
            parts.append(component.to_ai_context())
            parts.append("\n---\n")

        return "\n".join(parts)

    def get_categories(self) -> list[dict]:
        """Get all categories with counts.

        Returns:
            List of category info dicts.
        """
        components = self.list_components()
        category_counts: dict[ComponentCategory, int] = {}

        for component in components:
            category_counts[component.category] = category_counts.get(
                component.category, 0
            ) + 1

        return [
            {
                "id": cat.value,
                "name": cat.display_name,
                "icon": cat.icon,
                "count": category_counts.get(cat, 0),
            }
            for cat in ComponentCategory
            if category_counts.get(cat, 0) > 0
        ]
