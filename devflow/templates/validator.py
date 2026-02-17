"""Template and wizard input validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from devflow.templates.models import (
    Template,
    TemplateCategory,
    WizardField,
    WizardFieldType,
    WizardStep,
)


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Template validation failed: {', '.join(errors)}")


def validate_template_manifest(data: dict[str, Any]) -> list[str]:
    """Validate a template manifest dictionary.

    Args:
        data: Parsed YAML data

    Returns:
        List of validation errors (empty if valid).
    """
    errors: list[str] = []

    # Check version
    version = data.get("version")
    if version not in ("1", 1):
        errors.append(f"Unsupported template version: {version}")

    # Check metadata
    metadata = data.get("metadata")
    if not metadata:
        errors.append("Missing 'metadata' section")
    else:
        if not metadata.get("name"):
            errors.append("Missing 'metadata.name'")
        elif not _is_valid_template_name(metadata["name"]):
            errors.append(
                f"Invalid template name '{metadata['name']}': "
                "must be lowercase alphanumeric with hyphens"
            )

        if not metadata.get("display_name"):
            errors.append("Missing 'metadata.display_name'")

        if cat := metadata.get("category"):
            try:
                TemplateCategory(cat)
            except ValueError:
                valid = [c.value for c in TemplateCategory]
                errors.append(f"Invalid category '{cat}'. Must be one of: {valid}")

    # Validate wizard
    if wizard := data.get("wizard"):
        wizard_errors = _validate_wizard(wizard)
        errors.extend(wizard_errors)

    # Validate files
    if files := data.get("files"):
        for i, file_mapping in enumerate(files):
            if not file_mapping.get("source"):
                errors.append(f"files[{i}]: missing 'source'")
            if not file_mapping.get("destination"):
                errors.append(f"files[{i}]: missing 'destination'")

    # Validate hooks
    if hooks := data.get("hooks"):
        for i, hook in enumerate(hooks):
            if not hook.get("name"):
                errors.append(f"hooks[{i}]: missing 'name'")
            if not hook.get("command"):
                errors.append(f"hooks[{i}]: missing 'command'")

    return errors


def _is_valid_template_name(name: str) -> bool:
    """Check if template name is valid."""
    return bool(re.match(r"^[a-z][a-z0-9-]*$", name))


def _validate_wizard(wizard: dict[str, Any]) -> list[str]:
    """Validate wizard configuration."""
    errors: list[str] = []

    steps = wizard.get("steps", [])
    if not steps:
        return errors  # Empty wizard is valid

    seen_step_ids: set[str] = set()
    seen_field_ids: set[str] = set()

    for i, step in enumerate(steps):
        step_id = step.get("id")
        if not step_id:
            errors.append(f"wizard.steps[{i}]: missing 'id'")
        elif step_id in seen_step_ids:
            errors.append(f"wizard.steps[{i}]: duplicate step id '{step_id}'")
        else:
            seen_step_ids.add(step_id)

        if not step.get("title"):
            errors.append(f"wizard.steps[{i}]: missing 'title'")

        for j, field in enumerate(step.get("fields", [])):
            field_id = field.get("id")
            if not field_id:
                errors.append(f"wizard.steps[{i}].fields[{j}]: missing 'id'")
            elif field_id in seen_field_ids:
                errors.append(
                    f"wizard.steps[{i}].fields[{j}]: duplicate field id '{field_id}'"
                )
            else:
                seen_field_ids.add(field_id)

            if not field.get("label"):
                errors.append(f"wizard.steps[{i}].fields[{j}]: missing 'label'")

            field_type = field.get("type", "text")
            try:
                WizardFieldType(field_type)
            except ValueError:
                valid = [t.value for t in WizardFieldType]
                errors.append(
                    f"wizard.steps[{i}].fields[{j}]: invalid type '{field_type}'. "
                    f"Must be one of: {valid}"
                )

            # Select fields need options
            if field_type in ("select", "multiselect"):
                options = field.get("options", [])
                if not options:
                    errors.append(
                        f"wizard.steps[{i}].fields[{j}]: "
                        f"'{field_type}' field requires 'options'"
                    )
                for k, opt in enumerate(options):
                    if not opt.get("value"):
                        errors.append(
                            f"wizard.steps[{i}].fields[{j}].options[{k}]: "
                            "missing 'value'"
                        )
                    if not opt.get("label"):
                        errors.append(
                            f"wizard.steps[{i}].fields[{j}].options[{k}]: "
                            "missing 'label'"
                        )

    return errors


def validate_wizard_input(
    template: Template,
    step_id: str,
    values: dict[str, Any],
) -> dict[str, list[str]]:
    """Validate wizard input values for a step.

    Args:
        template: Template being used
        step_id: ID of the wizard step
        values: User-provided values

    Returns:
        Dict mapping field_id to list of errors (empty dict if valid).
    """
    errors: dict[str, list[str]] = {}

    # Find the step
    step = None
    for s in template.wizard_steps:
        if s.id == step_id:
            step = s
            break

    if not step:
        return {"_step": [f"Unknown step: {step_id}"]}

    for field in step.fields:
        # Check if field should be shown
        if field.show_when and not _evaluate_condition(field.show_when, values):
            continue

        field_errors = _validate_field(field, values.get(field.id))
        if field_errors:
            errors[field.id] = field_errors

    return errors


def _evaluate_condition(condition: dict[str, Any], values: dict[str, Any]) -> bool:
    """Evaluate a show_when condition.

    Supports simple equality checks:
    {"field_id": "value"} - show when field_id equals value
    {"field_id": ["value1", "value2"]} - show when field_id is in list
    """
    for field_id, expected in condition.items():
        actual = values.get(field_id)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def _validate_field(field: WizardField, value: Any) -> list[str]:
    """Validate a single field value."""
    errors: list[str] = []

    # Check required
    if field.required and (value is None or value == ""):
        errors.append(f"{field.label} is required")
        return errors  # Skip other validations if empty and required

    # Skip validation if empty and not required
    if value is None or value == "":
        return errors

    # Type-specific validation
    if field.type == WizardFieldType.TEXT:
        if not isinstance(value, str):
            errors.append(f"{field.label} must be text")
        elif field.validation:
            if not re.match(field.validation, value):
                msg = field.validation_message or f"{field.label} has invalid format"
                errors.append(msg)

    elif field.type == WizardFieldType.NUMBER:
        if not isinstance(value, (int, float)):
            try:
                float(value)
            except (TypeError, ValueError):
                errors.append(f"{field.label} must be a number")

    elif field.type == WizardFieldType.SELECT:
        valid_values = [opt.value for opt in field.options]
        if value not in valid_values:
            errors.append(f"{field.label} must be one of: {valid_values}")

    elif field.type == WizardFieldType.MULTISELECT:
        if not isinstance(value, list):
            errors.append(f"{field.label} must be a list")
        else:
            valid_values = [opt.value for opt in field.options]
            for v in value:
                if v not in valid_values:
                    errors.append(f"{field.label}: invalid option '{v}'")

    elif field.type == WizardFieldType.CHECKBOX:
        # Accept bool or string "true"/"false"
        if isinstance(value, bool):
            pass  # Valid
        elif isinstance(value, str) and value.lower() in ("true", "false"):
            pass  # Valid string representation
        else:
            errors.append(f"{field.label} must be true or false")

    elif field.type == WizardFieldType.DIRECTORY:
        if not isinstance(value, str):
            errors.append(f"{field.label} must be a path")
        else:
            path = Path(value).expanduser()
            parent = path.parent
            if not parent.exists():
                errors.append(f"Parent directory does not exist: {parent}")

    return errors


def validate_all_wizard_inputs(
    template: Template,
    all_values: dict[str, Any],
) -> dict[str, dict[str, list[str]]]:
    """Validate all wizard inputs across all steps.

    Args:
        template: Template being used
        all_values: All user-provided values

    Returns:
        Dict mapping step_id to field errors dict.
    """
    all_errors: dict[str, dict[str, list[str]]] = {}

    for step in template.wizard_steps:
        step_errors = validate_wizard_input(template, step.id, all_values)
        if step_errors:
            all_errors[step.id] = step_errors

    return all_errors
