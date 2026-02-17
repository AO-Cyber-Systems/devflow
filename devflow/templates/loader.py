"""Template loading from various sources."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from devflow.core.paths import get_devflow_home
from devflow.templates.models import (
    Template,
    TemplateCategory,
    TemplateSource,
)

logger = logging.getLogger(__name__)


def get_builtin_templates_dir() -> Path:
    """Get the directory containing built-in templates."""
    return Path(__file__).parent / "builtin"


def get_local_templates_dir() -> Path:
    """Get the user's local templates directory."""
    return get_devflow_home() / "templates"


def list_template_sources() -> list[dict[str, Any]]:
    """List all template source directories.

    Returns:
        List of dicts with 'source', 'path', and 'exists' keys.
    """
    sources = [
        {
            "source": TemplateSource.BUILTIN.value,
            "path": str(get_builtin_templates_dir()),
            "exists": get_builtin_templates_dir().exists(),
        },
        {
            "source": TemplateSource.LOCAL.value,
            "path": str(get_local_templates_dir()),
            "exists": get_local_templates_dir().exists(),
        },
    ]
    return sources


def _load_template_from_dir(
    template_dir: Path,
    source: TemplateSource,
) -> Template | None:
    """Load a single template from a directory.

    Args:
        template_dir: Directory containing template.yml
        source: Source type (builtin, local, git)

    Returns:
        Template if valid, None otherwise.
    """
    manifest_path = template_dir / "template.yml"
    if not manifest_path.exists():
        # Try template.yaml as alternative
        manifest_path = template_dir / "template.yaml"
        if not manifest_path.exists():
            logger.debug(f"No template manifest found in {template_dir}")
            return None

    try:
        with open(manifest_path) as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty template manifest: {manifest_path}")
            return None

        template = Template.from_dict(data, source=source, source_path=template_dir)
        logger.debug(f"Loaded template: {template.id} from {template_dir}")
        return template

    except yaml.YAMLError as e:
        logger.error(f"YAML error in {manifest_path}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Missing required field in {manifest_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading template from {template_dir}: {e}")
        return None


def _load_templates_from_source(
    source_dir: Path,
    source: TemplateSource,
) -> list[Template]:
    """Load all templates from a source directory.

    Args:
        source_dir: Directory containing template subdirectories
        source: Source type

    Returns:
        List of loaded templates.
    """
    templates = []

    if not source_dir.exists():
        return templates

    for item in source_dir.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue

        template = _load_template_from_dir(item, source)
        if template:
            templates.append(template)

    return templates


def load_templates(
    category: TemplateCategory | str | None = None,
    search: str | None = None,
    source: TemplateSource | str | None = None,
) -> list[Template]:
    """Load all available templates.

    Args:
        category: Filter by category
        search: Search in name, display_name, description, tags
        source: Filter by source (builtin, local, git)

    Returns:
        List of templates matching filters.
    """
    all_templates: list[Template] = []

    # Convert string to enum if needed
    if isinstance(category, str):
        try:
            category = TemplateCategory(category)
        except ValueError:
            category = None

    if isinstance(source, str):
        try:
            source = TemplateSource(source)
        except ValueError:
            source = None

    # Load from builtin
    if source is None or source == TemplateSource.BUILTIN:
        builtin_templates = _load_templates_from_source(
            get_builtin_templates_dir(),
            TemplateSource.BUILTIN,
        )
        all_templates.extend(builtin_templates)

    # Load from local
    if source is None or source == TemplateSource.LOCAL:
        local_templates = _load_templates_from_source(
            get_local_templates_dir(),
            TemplateSource.LOCAL,
        )
        all_templates.extend(local_templates)

    # Apply filters
    if category:
        all_templates = [
            t for t in all_templates
            if t.metadata.category == category
        ]

    if search:
        search_lower = search.lower()
        all_templates = [
            t for t in all_templates
            if _matches_search(t, search_lower)
        ]

    # Sort by display name
    all_templates.sort(key=lambda t: t.metadata.display_name.lower())

    return all_templates


def _matches_search(template: Template, search_lower: str) -> bool:
    """Check if template matches search query."""
    # Check name
    if search_lower in template.metadata.name.lower():
        return True
    # Check display name
    if search_lower in template.metadata.display_name.lower():
        return True
    # Check description
    if search_lower in template.metadata.description.lower():
        return True
    # Check tags
    for tag in template.metadata.tags:
        if search_lower in tag.lower():
            return True
    return False


def load_template(template_id: str) -> Template | None:
    """Load a specific template by ID.

    Args:
        template_id: Template identifier (metadata.name)

    Returns:
        Template if found, None otherwise.
    """
    # Check builtin first
    builtin_path = get_builtin_templates_dir() / template_id
    if builtin_path.exists():
        return _load_template_from_dir(builtin_path, TemplateSource.BUILTIN)

    # Check local
    local_path = get_local_templates_dir() / template_id
    if local_path.exists():
        return _load_template_from_dir(local_path, TemplateSource.LOCAL)

    # Not found - search all templates
    all_templates = load_templates()
    for template in all_templates:
        if template.id == template_id:
            return template

    return None


def get_template_path(template: Template) -> Path | None:
    """Get the filesystem path to a template's directory.

    Args:
        template: Template instance

    Returns:
        Path to template directory, or None if not available.
    """
    if template.source_path:
        return template.source_path

    # Try to find it
    if template.source == TemplateSource.BUILTIN:
        path = get_builtin_templates_dir() / template.id
        if path.exists():
            return path

    if template.source == TemplateSource.LOCAL:
        path = get_local_templates_dir() / template.id
        if path.exists():
            return path

    return None
