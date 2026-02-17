"""Templates RPC handler - project scaffolding and template management."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from devflow.core.config import load_global_config, save_global_config
from devflow.templates import (
    TemplateRenderer,
    load_template,
    load_templates,
    validate_wizard_input,
)
from devflow.templates.git_importer import (
    import_template_from_git,
    remove_imported_template,
)
from devflow.templates.loader import (
    get_builtin_templates_dir,
    get_local_templates_dir,
    list_template_sources,
)
from devflow.templates.validator import validate_all_wizard_inputs

logger = logging.getLogger(__name__)


class TemplatesHandler:
    """Handler for template-related RPC methods."""

    def __init__(self) -> None:
        # Cache for tool detection (lazily initialized)
        self._tool_detector = None

    def list_templates(
        self,
        category: str | None = None,
        search: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """List available templates.

        Args:
            category: Filter by category (web, mobile, desktop, fullstack, api)
            search: Search in name, description, tags
            source: Filter by source (builtin, local, git)

        Returns:
            Dict with templates list and total count.
        """
        try:
            templates = load_templates(category=category, search=search, source=source)
            return {
                "templates": [t.to_summary_dict() for t in templates],
                "total": len(templates),
            }
        except Exception as e:
            logger.exception(f"Error listing templates: {e}")
            return {"error": str(e)}

    def get_template(self, template_id: str) -> dict[str, Any]:
        """Get full template details including wizard steps.

        Args:
            template_id: Template identifier

        Returns:
            Full template data or error.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        return {
            "template": {
                **template.to_summary_dict(),
                "wizard_steps": [s.to_dict() for s in template.wizard_steps],
                "files": [f.to_dict() for f in template.files],
                "hooks": [h.to_dict() for h in template.hooks],
            }
        }

    def get_wizard_steps(self, template_id: str) -> dict[str, Any]:
        """Get wizard steps for a template.

        Args:
            template_id: Template identifier

        Returns:
            List of wizard steps with their fields.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        return {
            "steps": [s.to_dict() for s in template.wizard_steps],
            "step_count": len(template.wizard_steps),
        }

    def validate_wizard_input(
        self,
        template_id: str,
        step_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate wizard input for a specific step.

        Args:
            template_id: Template identifier
            step_id: Wizard step identifier
            values: User-provided values

        Returns:
            Validation result with any errors.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        errors = validate_wizard_input(template, step_id, values)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def validate_all_inputs(
        self,
        template_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate all wizard inputs across all steps.

        Args:
            template_id: Template identifier
            values: All user-provided values

        Returns:
            Validation result with errors by step.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        all_errors = validate_all_wizard_inputs(template, values)

        return {
            "valid": len(all_errors) == 0,
            "errors_by_step": all_errors,
        }

    def check_required_tools(self, template_id: str) -> dict[str, Any]:
        """Check if required and recommended tools are installed.

        Args:
            template_id: Template identifier

        Returns:
            Tool status information.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        # Import here to avoid circular imports
        from devflow.providers.installers import (
            ToolDetector,
            detect_platform,
            get_tool_by_id,
        )

        if self._tool_detector is None:
            platform_info = detect_platform()
            self._tool_detector = ToolDetector(platform_info)

        required_status = []
        for tool_id in template.required_tools:
            tool = get_tool_by_id(tool_id)
            if tool:
                status = self._tool_detector.detect_tool(tool)
                required_status.append({
                    "tool_id": tool.id,
                    "name": tool.name,
                    "installed": status.status.value == "installed",
                    "version": status.version,
                })
            else:
                required_status.append({
                    "tool_id": tool_id,
                    "name": tool_id,
                    "installed": False,
                    "error": "Unknown tool",
                })

        recommended_status = []
        for tool_id in template.recommended_tools:
            tool = get_tool_by_id(tool_id)
            if tool:
                status = self._tool_detector.detect_tool(tool)
                recommended_status.append({
                    "tool_id": tool.id,
                    "name": tool.name,
                    "installed": status.status.value == "installed",
                    "version": status.version,
                })
            else:
                recommended_status.append({
                    "tool_id": tool_id,
                    "name": tool_id,
                    "installed": False,
                    "error": "Unknown tool",
                })

        all_required_installed = all(t["installed"] for t in required_status)

        return {
            "all_required_installed": all_required_installed,
            "required": required_status,
            "recommended": recommended_status,
        }

    def create_project(
        self,
        template_id: str,
        wizard_values: dict[str, Any],
        *,
        run_hooks: bool = True,
    ) -> dict[str, Any]:
        """Create a new project from a template.

        Args:
            template_id: Template identifier
            wizard_values: Wizard form values
            run_hooks: Whether to run post-creation hooks

        Returns:
            Result with project path and any errors.
        """
        template = load_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        # Validate all inputs first
        all_errors = validate_all_wizard_inputs(template, wizard_values)
        if all_errors:
            return {
                "success": False,
                "error": "Validation failed",
                "validation_errors": all_errors,
            }

        # Get project path from wizard values
        project_path_str = wizard_values.get("project_path")
        project_name = wizard_values.get("project_name")

        if not project_path_str:
            return {"error": "project_path is required"}
        if not project_name:
            return {"error": "project_name is required"}

        project_path = Path(project_path_str).expanduser() / project_name

        # Check if path already exists
        if project_path.exists():
            return {"error": f"Directory already exists: {project_path}"}

        try:
            # Create renderer and render template
            renderer = TemplateRenderer(template)
            render_result = renderer.render(project_path, wizard_values)

            if not render_result.success:
                return {
                    "success": False,
                    "error": "Failed to render template",
                    "render_errors": render_result.errors,
                }

            result: dict[str, Any] = {
                "success": True,
                "path": str(project_path),
                "files_created": render_result.files_created,
                "file_count": len(render_result.files_created),
            }

            # Run hooks if requested
            if run_hooks and template.hooks:
                hook_results = renderer.run_hooks(project_path, wizard_values)
                result["hooks"] = [hr.to_dict() for hr in hook_results]
                result["hooks_success"] = all(hr.success for hr in hook_results)

            # Generate next steps
            result["next_steps"] = self._generate_next_steps(template, project_path)

            logger.info(f"Created project from template {template_id} at {project_path}")
            return result

        except Exception as e:
            logger.exception(f"Error creating project: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _generate_next_steps(self, template, project_path: Path) -> list[str]:
        """Generate helpful next steps after project creation."""
        steps = [f"cd {project_path}"]

        # Add template-specific next steps based on tools/category
        if "nodejs" in template.required_tools:
            steps.append("npm install")
            steps.append("npm run dev")
        elif "python" in template.required_tools:
            steps.append("python -m venv .venv")
            steps.append("source .venv/bin/activate")
            steps.append("pip install -r requirements.txt")

        return steps

    def import_template(
        self,
        git_url: str,
        branch: str | None = None,
        subdirectory: str | None = None,
    ) -> dict[str, Any]:
        """Import a template from a Git repository.

        Args:
            git_url: Git repository URL
            branch: Optional branch or tag
            subdirectory: Optional subdirectory containing template

        Returns:
            Import result with template info or errors.
        """
        result = import_template_from_git(
            git_url,
            branch=branch,
            subdirectory=subdirectory,
        )
        return result.to_dict()

    def remove_template(self, template_id: str) -> dict[str, Any]:
        """Remove a locally imported template.

        Args:
            template_id: Template identifier

        Returns:
            Success status.
        """
        # Only allow removing local templates
        template = load_template(template_id)
        if template and template.source.value == "builtin":
            return {"error": "Cannot remove built-in templates"}

        return remove_imported_template(template_id)

    def get_template_sources(self) -> dict[str, Any]:
        """Get information about template source directories.

        Returns:
            List of template sources with paths.
        """
        return {
            "sources": list_template_sources(),
            "builtin_path": str(get_builtin_templates_dir()),
            "local_path": str(get_local_templates_dir()),
        }

    def get_categories(self) -> dict[str, Any]:
        """Get available template categories with counts.

        Returns:
            Categories with template counts.
        """
        from devflow.templates.models import TemplateCategory

        templates = load_templates()
        counts: dict[str, int] = {}

        for template in templates:
            cat = template.metadata.category.value
            counts[cat] = counts.get(cat, 0) + 1

        categories = []
        for cat in TemplateCategory:
            categories.append({
                "id": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "count": counts.get(cat.value, 0),
            })

        return {
            "categories": categories,
            "total_templates": len(templates),
        }
