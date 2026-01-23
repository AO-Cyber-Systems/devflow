"""Configuration RPC handlers."""

from pathlib import Path
from typing import Any

import yaml

from devflow.core.config import DevflowConfig, GlobalConfig, load_project_config, load_global_config


class ConfigHandler:
    """Handler for configuration RPC methods."""

    def get_global(self) -> dict[str, Any]:
        """Get global configuration."""
        try:
            config = load_global_config()
            return config.model_dump()
        except FileNotFoundError:
            return {"error": "Global config not found", "initialized": False}
        except Exception as e:
            return {"error": str(e)}

    def get_project(self, path: str) -> dict[str, Any]:
        """Get project configuration."""
        try:
            project_path = Path(path)
            if not project_path.exists():
                return {"error": f"Project path does not exist: {path}"}

            config = load_project_config(project_path)
            return config.model_dump()
        except FileNotFoundError:
            return {"error": "devflow.yml not found in project", "has_config": False}
        except Exception as e:
            return {"error": str(e)}

    def set_global(self, key: str, value: Any) -> dict[str, Any]:
        """Update a global configuration value."""
        try:
            config_path = Path.home() / ".devflow" / "config.yml"

            if not config_path.exists():
                return {"error": "Global config not found"}

            # Load current config
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            # Navigate to nested key and update
            keys = key.split(".")
            current = data
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            old_value = current.get(keys[-1])
            current[keys[-1]] = value

            # Save updated config
            with open(config_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return {"success": True, "key": key, "old_value": old_value, "new_value": value}
        except Exception as e:
            return {"error": str(e)}

    def set_project(self, path: str, config: dict[str, Any]) -> dict[str, Any]:
        """Update project configuration."""
        try:
            project_path = Path(path)
            config_path = project_path / "devflow.yml"

            if not config_path.exists():
                return {"error": "devflow.yml not found in project"}

            # Validate config by parsing it
            DevflowConfig.model_validate(config)

            # Save updated config
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            return {"success": True, "path": str(config_path)}
        except Exception as e:
            return {"error": str(e)}

    def validate(self, path: str | None = None) -> dict[str, Any]:
        """Validate configuration."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Validate global config
            try:
                global_config = load_global_config()
                if not global_config.setup_completed:
                    warnings.append("Setup not completed - run 'devflow install'")
            except FileNotFoundError:
                errors.append("Global config not found")
            except Exception as e:
                errors.append(f"Global config error: {e}")

            # Validate project config if path provided
            if path:
                try:
                    project_path = Path(path)
                    config = load_project_config(project_path)

                    # Check for common issues
                    if not config.project.name:
                        errors.append("Project name is required")

                    if config.database:
                        if not config.database.environments:
                            warnings.append("No database environments configured")

                    if config.deployment:
                        if not config.deployment.services:
                            warnings.append("No deployment services configured")

                except FileNotFoundError:
                    errors.append(f"devflow.yml not found at {path}")
                except Exception as e:
                    errors.append(f"Project config error: {e}")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }
        except Exception as e:
            return {"valid": False, "errors": [str(e)], "warnings": []}

    def get_raw(self, path: str) -> dict[str, Any]:
        """Get raw YAML content for editing."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"error": f"File not found: {path}"}

            with open(file_path) as f:
                content = f.read()

            return {"success": True, "content": content, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)}

    def set_raw(self, path: str, content: str) -> dict[str, Any]:
        """Save raw YAML content after editing."""
        try:
            file_path = Path(path)

            # Validate YAML syntax
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                return {"error": f"Invalid YAML: {e}"}

            # Backup original
            if file_path.exists():
                backup_path = file_path.with_suffix(".yml.bak")
                backup_path.write_text(file_path.read_text())

            # Write new content
            file_path.write_text(content)

            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)}
