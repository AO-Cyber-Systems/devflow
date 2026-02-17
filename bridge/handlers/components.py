"""RPC handler for UI component documentation."""

import logging
from typing import Any

from devflow.components.manager import ComponentManager
from devflow.components.scanner import ComponentScanner

logger = logging.getLogger(__name__)


class ComponentsHandler:
    """Handler for managing UI component documentation."""

    def __init__(self):
        self._managers: dict[str, ComponentManager] = {}

    def _get_manager(self, project_path: str) -> ComponentManager:
        """Get or create a component manager for a project."""
        if project_path not in self._managers:
            self._managers[project_path] = ComponentManager(project_path)
        return self._managers[project_path]

    def list_components(
        self,
        project_path: str,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List component documentation.

        Args:
            project_path: Path to the project
            category: Filter by category
            search: Search in name and description

        Returns:
            Dictionary with components list.
        """
        try:
            manager = self._get_manager(project_path)
            components = manager.list_components(
                category=category,
                search=search,
            )
            return {
                "components": [c.to_dict() for c in components],
                "total": len(components),
            }
        except Exception as e:
            logger.error(f"List components failed: {e}")
            return {"error": str(e)}

    def get_component(
        self,
        project_path: str,
        name: str,
    ) -> dict[str, Any]:
        """Get a single component documentation.

        Args:
            project_path: Path to the project
            name: Component name

        Returns:
            Component details or error.
        """
        try:
            manager = self._get_manager(project_path)
            component = manager.get_component(name)

            if component is None:
                return {"error": f"Component not found: {name}"}

            return {"component": component.to_dict()}
        except Exception as e:
            logger.error(f"Get component failed: {e}")
            return {"error": str(e)}

    def create_component(
        self,
        project_path: str,
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
    ) -> dict[str, Any]:
        """Create a new component documentation.

        Args:
            project_path: Path to the project
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
            Created component details.
        """
        try:
            manager = self._get_manager(project_path)
            component = manager.create_component(
                name=name,
                category=category,
                description=description,
                props=props,
                slots=slots,
                events=events,
                examples=examples,
                ai_guidance=ai_guidance,
                accessibility=accessibility,
                tags=tags,
            )
            return {
                "success": True,
                "component": component.to_dict(),
            }
        except Exception as e:
            logger.error(f"Create component failed: {e}")
            return {"success": False, "error": str(e)}

    def update_component(
        self,
        project_path: str,
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
    ) -> dict[str, Any]:
        """Update an existing component documentation.

        Args:
            project_path: Path to the project
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
            Updated component details.
        """
        try:
            manager = self._get_manager(project_path)
            component = manager.update_component(
                name=name,
                category=category,
                description=description,
                props=props,
                slots=slots,
                events=events,
                examples=examples,
                ai_guidance=ai_guidance,
                accessibility=accessibility,
                tags=tags,
            )

            if component is None:
                return {"success": False, "error": f"Component not found: {name}"}

            return {
                "success": True,
                "component": component.to_dict(),
            }
        except Exception as e:
            logger.error(f"Update component failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_component(
        self,
        project_path: str,
        name: str,
    ) -> dict[str, Any]:
        """Delete a component documentation.

        Args:
            project_path: Path to the project
            name: Component name

        Returns:
            Deletion result.
        """
        try:
            manager = self._get_manager(project_path)
            deleted = manager.delete_component(name)

            if not deleted:
                return {"success": False, "error": f"Component not found: {name}"}

            return {"success": True, "message": "Component documentation deleted"}
        except Exception as e:
            logger.error(f"Delete component failed: {e}")
            return {"success": False, "error": str(e)}

    def scan_components(
        self,
        project_path: str,
        patterns: list[str] | None = None,
        save: bool = False,
    ) -> dict[str, Any]:
        """Scan the project for components and generate documentation scaffolds.

        Args:
            project_path: Path to the project
            patterns: Glob patterns to use (optional)
            save: Whether to save the detected components

        Returns:
            Detected components.
        """
        try:
            scanner = ComponentScanner(project_path)
            components = scanner.scan(patterns=patterns)

            if save:
                manager = self._get_manager(project_path)
                for component in components:
                    # Only create if doesn't exist
                    existing = manager.get_component(component.name)
                    if existing is None:
                        manager.create_component(
                            name=component.name,
                            category=component.category.value,
                            description=component.description,
                            props=[p.to_dict() for p in component.props],
                            tags=component.tags,
                        )

            return {
                "components": [c.to_dict() for c in components],
                "total": len(components),
                "saved": save,
            }
        except Exception as e:
            logger.error(f"Scan components failed: {e}")
            return {"error": str(e)}

    def get_ai_context(
        self,
        project_path: str,
        component_names: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get aggregated AI context from component documentation.

        Args:
            project_path: Path to the project
            component_names: Specific components to include (None for all)
            categories: Filter by categories (None for all)

        Returns:
            AI-friendly context string.
        """
        try:
            manager = self._get_manager(project_path)
            context = manager.get_ai_context(
                component_names=component_names,
                categories=categories,
            )
            return {
                "context": context,
                "length": len(context),
            }
        except Exception as e:
            logger.error(f"Get AI context failed: {e}")
            return {"error": str(e)}

    def get_categories(self, project_path: str) -> dict[str, Any]:
        """Get component categories with counts.

        Args:
            project_path: Path to the project

        Returns:
            List of categories with counts.
        """
        try:
            manager = self._get_manager(project_path)
            categories = manager.get_categories()
            return {"categories": categories}
        except Exception as e:
            logger.error(f"Get categories failed: {e}")
            return {"error": str(e)}

    def get_all_categories(self) -> dict[str, Any]:
        """Get all available categories.

        Returns:
            List of all category options.
        """
        from devflow.components.models import ComponentCategory

        return {
            "categories": [
                {
                    "id": c.value,
                    "name": c.display_name,
                    "icon": c.icon,
                }
                for c in ComponentCategory
            ]
        }
