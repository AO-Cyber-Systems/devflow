"""Import templates from Git repositories."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

from devflow.templates.loader import get_local_templates_dir
from devflow.templates.models import Template, TemplateSource
from devflow.templates.validator import validate_template_manifest

logger = logging.getLogger(__name__)


class GitImportError(Exception):
    """Error during Git template import."""

    pass


def import_template_from_git(
    git_url: str,
    *,
    branch: str | None = None,
    subdirectory: str | None = None,
) -> ImportResult:
    """Import a template from a Git repository.

    Args:
        git_url: Git repository URL (HTTPS or SSH)
        branch: Optional branch/tag to checkout
        subdirectory: Optional subdirectory within repo containing template

    Returns:
        ImportResult with template info or errors.
    """
    result = ImportResult()

    # Create temp directory for cloning
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        try:
            # Clone the repository
            clone_cmd = ["git", "clone", "--depth", "1"]
            if branch:
                clone_cmd.extend(["--branch", branch])
            clone_cmd.extend([git_url, str(tmp_path / "repo")])

            logger.info(f"Cloning {git_url}...")
            clone_result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if clone_result.returncode != 0:
                result.errors.append(f"Git clone failed: {clone_result.stderr}")
                return result

            # Determine template root
            template_root = tmp_path / "repo"
            if subdirectory:
                template_root = template_root / subdirectory

            if not template_root.exists():
                result.errors.append(f"Directory not found: {subdirectory}")
                return result

            # Find template.yml
            manifest_path = template_root / "template.yml"
            if not manifest_path.exists():
                manifest_path = template_root / "template.yaml"
            if not manifest_path.exists():
                result.errors.append("No template.yml found in repository")
                return result

            # Parse and validate manifest
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            validation_errors = validate_template_manifest(manifest_data)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Get template name
            template_name = manifest_data.get("metadata", {}).get("name")
            if not template_name:
                result.errors.append("Template name not found in manifest")
                return result

            # Check if template already exists
            local_dir = get_local_templates_dir()
            target_path = local_dir / template_name

            if target_path.exists():
                result.errors.append(
                    f"Template '{template_name}' already exists at {target_path}"
                )
                result.existing_template = template_name
                return result

            # Copy template to local templates directory
            local_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(template_root, target_path)

            # Load the imported template
            template = Template.from_dict(
                manifest_data,
                source=TemplateSource.GIT,
                source_path=target_path,
            )

            result.success = True
            result.template = template
            result.template_id = template_name
            result.installed_path = str(target_path)

            logger.info(f"Successfully imported template: {template_name}")

        except subprocess.TimeoutExpired:
            result.errors.append("Git clone timed out")
        except yaml.YAMLError as e:
            result.errors.append(f"Invalid YAML in template.yml: {e}")
        except Exception as e:
            logger.exception(f"Error importing template: {e}")
            result.errors.append(str(e))

    return result


def remove_imported_template(template_id: str) -> dict[str, Any]:
    """Remove a locally imported template.

    Args:
        template_id: Template identifier

    Returns:
        Dict with success status and any errors.
    """
    local_dir = get_local_templates_dir()
    template_path = local_dir / template_id

    if not template_path.exists():
        return {
            "success": False,
            "error": f"Template '{template_id}' not found in local templates",
        }

    # Check if it's actually in the local templates dir
    try:
        template_path.relative_to(local_dir)
    except ValueError:
        return {
            "success": False,
            "error": "Cannot remove templates outside local directory",
        }

    try:
        shutil.rmtree(template_path)
        logger.info(f"Removed template: {template_id}")
        return {
            "success": True,
            "template_id": template_id,
        }
    except Exception as e:
        logger.error(f"Failed to remove template {template_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def update_imported_template(
    template_id: str,
    git_url: str | None = None,
    branch: str | None = None,
) -> ImportResult:
    """Update an imported template by re-importing from Git.

    Args:
        template_id: Template identifier
        git_url: Git URL (if not provided, attempts to use stored URL)
        branch: Optional branch/tag

    Returns:
        ImportResult with updated template info.
    """
    local_dir = get_local_templates_dir()
    template_path = local_dir / template_id

    if not template_path.exists():
        result = ImportResult()
        result.errors.append(f"Template '{template_id}' not found")
        return result

    # If git_url not provided, we can't update
    if not git_url:
        result = ImportResult()
        result.errors.append("Git URL required for update")
        return result

    # Remove existing template
    remove_result = remove_imported_template(template_id)
    if not remove_result.get("success"):
        result = ImportResult()
        result.errors.append(f"Failed to remove existing template: {remove_result.get('error')}")
        return result

    # Re-import
    return import_template_from_git(git_url, branch=branch)


class ImportResult:
    """Result of a template import operation."""

    def __init__(self):
        self.success: bool = False
        self.template: Template | None = None
        self.template_id: str | None = None
        self.installed_path: str | None = None
        self.existing_template: str | None = None
        self.errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": self.success,
            "errors": self.errors,
        }

        if self.success and self.template:
            result["template_id"] = self.template_id
            result["template"] = self.template.to_summary_dict()
            result["installed_path"] = self.installed_path

        if self.existing_template:
            result["existing_template"] = self.existing_template

        return result
