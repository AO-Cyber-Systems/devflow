"""Template system for project scaffolding."""

from devflow.templates.models import (
    FileMapping,
    Hook,
    Template,
    TemplateCategory,
    TemplateMetadata,
    WizardField,
    WizardFieldOption,
    WizardFieldType,
    WizardStep,
)
from devflow.templates.loader import (
    get_builtin_templates_dir,
    get_local_templates_dir,
    list_template_sources,
    load_template,
    load_templates,
)
from devflow.templates.renderer import TemplateRenderer
from devflow.templates.validator import (
    TemplateValidationError,
    validate_template_manifest,
    validate_wizard_input,
)

__all__ = [
    # Models
    "Template",
    "TemplateMetadata",
    "TemplateCategory",
    "WizardStep",
    "WizardField",
    "WizardFieldType",
    "WizardFieldOption",
    "FileMapping",
    "Hook",
    # Loader
    "load_templates",
    "load_template",
    "list_template_sources",
    "get_builtin_templates_dir",
    "get_local_templates_dir",
    # Renderer
    "TemplateRenderer",
    # Validator
    "validate_template_manifest",
    "validate_wizard_input",
    "TemplateValidationError",
]
