"""Jinja2 template rendering engine."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from devflow.templates.models import FileMapping, Hook, Template
from devflow.templates.loader import get_template_path

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renders templates to create new projects."""

    def __init__(self, template: Template):
        """Initialize renderer with a template.

        Args:
            template: Template to render
        """
        self.template = template
        self.template_path = get_template_path(template)

        if not self.template_path:
            raise ValueError(f"Template path not found for: {template.id}")

        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_path)),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self._setup_filters()

    def _setup_filters(self) -> None:
        """Add custom Jinja2 filters."""
        self.jinja_env.filters["pascalcase"] = self._pascal_case
        self.jinja_env.filters["camelcase"] = self._camel_case
        self.jinja_env.filters["snakecase"] = self._snake_case
        self.jinja_env.filters["kebabcase"] = self._kebab_case

    @staticmethod
    def _pascal_case(value: str) -> str:
        """Convert to PascalCase."""
        words = value.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in words)

    @staticmethod
    def _camel_case(value: str) -> str:
        """Convert to camelCase."""
        pascal = TemplateRenderer._pascal_case(value)
        return pascal[0].lower() + pascal[1:] if pascal else ""

    @staticmethod
    def _snake_case(value: str) -> str:
        """Convert to snake_case."""
        return value.replace("-", "_").lower()

    @staticmethod
    def _kebab_case(value: str) -> str:
        """Convert to kebab-case."""
        return value.replace("_", "-").lower()

    def render(
        self,
        destination: Path,
        values: dict[str, Any],
        *,
        dry_run: bool = False,
    ) -> RenderResult:
        """Render the template to a destination directory.

        Args:
            destination: Target directory for the project
            values: Wizard values for template rendering
            dry_run: If True, don't write files, just return what would be done

        Returns:
            RenderResult with created files and any errors.
        """
        result = RenderResult()

        # Add standard context values
        context = {
            **values,
            "project_name": values.get("project_name", destination.name),
            "project_path": str(destination),
        }

        # Create destination if not dry run
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)

        # Process each file mapping
        for file_mapping in self.template.files:
            try:
                # Check condition
                if file_mapping.condition:
                    if not self._evaluate_condition(file_mapping.condition, context):
                        logger.debug(f"Skipping {file_mapping.source} (condition not met)")
                        continue

                files_created = self._process_file_mapping(
                    file_mapping,
                    destination,
                    context,
                    dry_run=dry_run,
                )
                result.files_created.extend(files_created)

            except Exception as e:
                logger.error(f"Error processing {file_mapping.source}: {e}")
                result.errors.append(f"Failed to process {file_mapping.source}: {e}")

        return result

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a file condition.

        Supports simple conditions like:
        - "database != 'none'"
        - "use_docker"
        - "not use_docker"
        """
        try:
            # Create a safe evaluation environment
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return True  # Default to including the file

    def _process_file_mapping(
        self,
        mapping: FileMapping,
        destination: Path,
        context: dict[str, Any],
        dry_run: bool,
    ) -> list[str]:
        """Process a single file mapping.

        Returns list of created file paths (relative to destination).
        """
        source_path = self.template_path / mapping.source
        dest_path = destination / self._render_path(mapping.destination, context)
        created: list[str] = []

        if mapping.recursive:
            # Copy directory recursively
            created.extend(
                self._copy_directory(
                    source_path,
                    dest_path,
                    context,
                    is_template=mapping.template,
                    dry_run=dry_run,
                )
            )
        elif source_path.is_dir():
            # Non-recursive directory copy (just top-level files)
            for item in source_path.iterdir():
                if item.is_file():
                    file_dest = dest_path / item.name
                    self._copy_file(
                        item,
                        file_dest,
                        context,
                        is_template=mapping.template,
                        dry_run=dry_run,
                    )
                    created.append(str(file_dest.relative_to(destination)))
        else:
            # Single file
            self._copy_file(
                source_path,
                dest_path,
                context,
                is_template=mapping.template,
                dry_run=dry_run,
            )
            created.append(str(dest_path.relative_to(destination)))

        return created

    def _render_path(self, path: str, context: dict[str, Any]) -> str:
        """Render Jinja2 expressions in a path."""
        if "{{" in path:
            template = self.jinja_env.from_string(path)
            return template.render(context)
        return path

    def _copy_directory(
        self,
        source: Path,
        destination: Path,
        context: dict[str, Any],
        is_template: bool,
        dry_run: bool,
    ) -> list[str]:
        """Recursively copy a directory, optionally rendering templates."""
        created: list[str] = []

        if not source.exists():
            logger.warning(f"Source directory not found: {source}")
            return created

        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)

        for item in source.rglob("*"):
            if item.is_dir():
                continue

            # Skip hidden files and __pycache__
            if any(part.startswith(".") or part == "__pycache__" for part in item.parts):
                continue

            rel_path = item.relative_to(source)
            dest_file = destination / self._render_path(str(rel_path), context)

            # Determine if this file should be rendered as template
            render = is_template or item.suffix == ".j2"

            self._copy_file(
                item,
                dest_file,
                context,
                is_template=render,
                dry_run=dry_run,
            )
            created.append(str(dest_file.relative_to(destination.parent)))

        return created

    def _copy_file(
        self,
        source: Path,
        destination: Path,
        context: dict[str, Any],
        is_template: bool,
        dry_run: bool,
    ) -> None:
        """Copy a single file, optionally rendering as template."""
        if dry_run:
            logger.info(f"Would create: {destination}")
            return

        # Create parent directories
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Remove .j2 extension from destination if present
        if destination.suffix == ".j2":
            destination = destination.with_suffix("")

        if is_template or source.suffix == ".j2":
            # Render template
            try:
                rel_source = source.relative_to(self.template_path)
                template = self.jinja_env.get_template(str(rel_source))
                content = template.render(context)
                destination.write_text(content)
                logger.debug(f"Rendered template: {destination}")
            except Exception as e:
                logger.error(f"Failed to render template {source}: {e}")
                raise
        else:
            # Copy as-is
            shutil.copy2(source, destination)
            logger.debug(f"Copied file: {destination}")

    def run_hooks(
        self,
        destination: Path,
        values: dict[str, Any],
        *,
        on_progress: HookProgressCallback | None = None,
    ) -> list[HookResult]:
        """Run post-creation hooks.

        Args:
            destination: Project directory
            values: Wizard values
            on_progress: Optional callback for progress updates

        Returns:
            List of hook results.
        """
        results: list[HookResult] = []
        context = {**values, "project_path": str(destination)}

        for i, hook in enumerate(self.template.hooks):
            # Check condition
            if hook.condition:
                if not self._evaluate_condition(hook.condition, context):
                    logger.debug(f"Skipping hook '{hook.name}' (condition not met)")
                    continue

            if on_progress:
                on_progress(i, len(self.template.hooks), hook.name, "running")

            result = self._run_hook(hook, destination, context)
            results.append(result)

            if on_progress:
                status = "completed" if result.success else "failed"
                on_progress(i, len(self.template.hooks), hook.name, status)

            # Stop on error unless continue_on_error is set
            if not result.success and not hook.continue_on_error:
                logger.error(f"Hook '{hook.name}' failed, stopping")
                break

        return results

    def _run_hook(
        self,
        hook: Hook,
        destination: Path,
        context: dict[str, Any],
    ) -> HookResult:
        """Run a single hook command."""
        # Determine working directory
        if hook.working_dir:
            cwd = destination / hook.working_dir
        else:
            cwd = destination

        # Render command with context
        command = hook.command
        if "{{" in command:
            template = self.jinja_env.from_string(command)
            command = template.render(context)

        logger.info(f"Running hook '{hook.name}': {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**os.environ, **{k: str(v) for k, v in context.items() if isinstance(v, (str, int, float, bool))}},
            )

            return HookResult(
                name=hook.name,
                command=command,
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            return HookResult(
                name=hook.name,
                command=command,
                success=False,
                exit_code=-1,
                stderr="Hook timed out after 5 minutes",
            )
        except Exception as e:
            return HookResult(
                name=hook.name,
                command=command,
                success=False,
                exit_code=-1,
                stderr=str(e),
            )


# Type alias for hook progress callback
HookProgressCallback = Any  # Callable[[int, int, str, str], None]


class RenderResult:
    """Result of template rendering."""

    def __init__(self):
        self.files_created: list[str] = []
        self.errors: list[str] = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "files_created": self.files_created,
            "file_count": len(self.files_created),
            "errors": self.errors,
        }


class HookResult:
    """Result of running a hook."""

    def __init__(
        self,
        name: str,
        command: str,
        success: bool,
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
    ):
        self.name = name
        self.command = command
        self.success = success
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }
