"""Base preset class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class Preset(ABC):
    """Base class for project presets."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Preset name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Preset description."""
        pass

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get the preset configuration as a dictionary."""
        pass

    def get_yaml(self) -> str:
        """Get the preset configuration as YAML."""
        import yaml

        return yaml.dump(self.get_config(), default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, name: str) -> Optional["Preset"]:
        """Load a preset by name."""
        from devflow.presets.aocodex import AOCodexPreset
        from devflow.presets.aosentry import AOSentryPreset

        presets = {
            "aocodex": AOCodexPreset,
            "aosentry": AOSentryPreset,
        }

        preset_class = presets.get(name.lower())
        if preset_class:
            return preset_class()
        return None

    @classmethod
    def available_presets(cls) -> list[str]:
        """List available preset names."""
        return ["aocodex", "aosentry"]
