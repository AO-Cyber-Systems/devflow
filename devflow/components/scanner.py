"""Component scanner for auto-detecting components in a project."""

import logging
import re
from pathlib import Path

from .models import ComponentCategory, ComponentDoc, PropDefinition

logger = logging.getLogger(__name__)


class ComponentScanner:
    """Scans a project for UI components and generates documentation scaffolds."""

    # Common component file patterns
    COMPONENT_PATTERNS = [
        # React/Next.js
        "**/*.tsx",
        "**/*.jsx",
        # Vue
        "**/*.vue",
        # Svelte
        "**/*.svelte",
        # Angular
        "**/*.component.ts",
        # Web Components
        "**/*-element.ts",
        "**/*-component.ts",
    ]

    # Directories to exclude
    EXCLUDE_DIRS = {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".svelte-kit",
        "coverage",
        "__pycache__",
        ".devflow",
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def scan(
        self,
        patterns: list[str] | None = None,
        exclude_dirs: set[str] | None = None,
    ) -> list[ComponentDoc]:
        """Scan the project for components.

        Args:
            patterns: Glob patterns to use (default: COMPONENT_PATTERNS)
            exclude_dirs: Directories to exclude (default: EXCLUDE_DIRS)

        Returns:
            List of detected ComponentDoc objects (scaffolds).
        """
        patterns = patterns or self.COMPONENT_PATTERNS
        exclude_dirs = exclude_dirs or self.EXCLUDE_DIRS

        components = []
        seen_names: set[str] = set()

        for pattern in patterns:
            for file_path in self.project_path.glob(pattern):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                # Parse the component
                try:
                    component = self._parse_component_file(file_path)
                    if component and component.name not in seen_names:
                        seen_names.add(component.name)
                        components.append(component)
                except Exception as e:
                    logger.warning(f"Failed to parse {file_path}: {e}")

        return components

    def _parse_component_file(self, file_path: Path) -> ComponentDoc | None:
        """Parse a component file and extract documentation scaffold.

        Args:
            file_path: Path to the component file

        Returns:
            ComponentDoc scaffold or None if not a component.
        """
        content = file_path.read_text()
        suffix = file_path.suffix.lower()

        if suffix in (".tsx", ".jsx"):
            return self._parse_react_component(file_path, content)
        elif suffix == ".vue":
            return self._parse_vue_component(file_path, content)
        elif suffix == ".svelte":
            return self._parse_svelte_component(file_path, content)
        elif suffix == ".ts":
            return self._parse_typescript_component(file_path, content)

        return None

    def _parse_react_component(
        self, file_path: Path, content: str
    ) -> ComponentDoc | None:
        """Parse a React component file."""
        # Try to find component name from export
        name_match = re.search(
            r"export\s+(?:default\s+)?(?:function|const)\s+(\w+)",
            content,
        )
        if not name_match:
            # Try class component
            name_match = re.search(
                r"class\s+(\w+)\s+extends\s+(?:React\.)?Component",
                content,
            )

        if not name_match:
            return None

        name = name_match.group(1)

        # Skip non-component names
        if name.startswith("use") or name[0].islower():
            return None

        # Extract props from interface/type
        props = self._extract_typescript_props(content, name)

        # Guess category from name
        category = self._guess_category(name, content)

        return ComponentDoc(
            name=name,
            category=category,
            description=f"{name} component",
            props=props,
            source_file=str(file_path.relative_to(self.project_path)),
        )

    def _parse_vue_component(self, file_path: Path, content: str) -> ComponentDoc | None:
        """Parse a Vue component file."""
        # Get component name from filename
        name = file_path.stem

        # Extract props from defineProps or props option
        props = self._extract_vue_props(content)

        # Guess category
        category = self._guess_category(name, content)

        return ComponentDoc(
            name=name,
            category=category,
            description=f"{name} component",
            props=props,
            source_file=str(file_path.relative_to(self.project_path)),
        )

    def _parse_svelte_component(
        self, file_path: Path, content: str
    ) -> ComponentDoc | None:
        """Parse a Svelte component file."""
        # Get component name from filename
        name = file_path.stem

        # Extract props from export let statements
        props = self._extract_svelte_props(content)

        # Guess category
        category = self._guess_category(name, content)

        return ComponentDoc(
            name=name,
            category=category,
            description=f"{name} component",
            props=props,
            source_file=str(file_path.relative_to(self.project_path)),
        )

    def _parse_typescript_component(
        self, file_path: Path, content: str
    ) -> ComponentDoc | None:
        """Parse a TypeScript component (Angular/Web Component)."""
        # Get component name from filename or decorator
        name = file_path.stem.replace(".component", "").replace("-", " ").title().replace(" ", "")

        # Check for @Component decorator (Angular)
        if "@Component" not in content:
            return None

        # Extract inputs from @Input() decorators
        props = []
        input_matches = re.finditer(
            r"@Input\(\)\s+(\w+)(?:\s*:\s*(\w+))?",
            content,
        )
        for match in input_matches:
            props.append(
                PropDefinition(
                    name=match.group(1),
                    type=match.group(2) or "any",
                )
            )

        # Guess category
        category = self._guess_category(name, content)

        return ComponentDoc(
            name=name,
            category=category,
            description=f"{name} component",
            props=props,
            source_file=str(file_path.relative_to(self.project_path)),
        )

    def _extract_typescript_props(
        self, content: str, component_name: str
    ) -> list[PropDefinition]:
        """Extract props from TypeScript interfaces."""
        props = []

        # Look for Props interface or type
        props_pattern = rf"(?:interface|type)\s+{component_name}Props\s*(?:=\s*)?\{{\s*([\s\S]*?)\}}"
        match = re.search(props_pattern, content)

        if not match:
            # Try generic Props
            match = re.search(r"(?:interface|type)\s+Props\s*(?:=\s*)?\{\s*([\s\S]*?)\}", content)

        if match:
            props_content = match.group(1)
            # Parse each prop line
            prop_lines = re.finditer(
                r"(\w+)(\?)?\s*:\s*([^;}\n]+)",
                props_content,
            )
            for prop_match in prop_lines:
                props.append(
                    PropDefinition(
                        name=prop_match.group(1),
                        type=prop_match.group(3).strip(),
                        required=prop_match.group(2) is None,
                    )
                )

        return props

    def _extract_vue_props(self, content: str) -> list[PropDefinition]:
        """Extract props from Vue component."""
        props = []

        # Try defineProps with type
        define_props_match = re.search(
            r"defineProps<\{([\s\S]*?)\}>",
            content,
        )
        if define_props_match:
            props_content = define_props_match.group(1)
            prop_lines = re.finditer(
                r"(\w+)(\?)?\s*:\s*([^;}\n]+)",
                props_content,
            )
            for match in prop_lines:
                props.append(
                    PropDefinition(
                        name=match.group(1),
                        type=match.group(3).strip(),
                        required=match.group(2) is None,
                    )
                )

        # Try options API props
        if not props:
            options_match = re.search(
                r"props\s*:\s*\{([\s\S]*?)\}",
                content,
            )
            if options_match:
                prop_lines = re.finditer(
                    r"(\w+)\s*:\s*\{[^}]*type\s*:\s*(\w+)",
                    options_match.group(1),
                )
                for match in prop_lines:
                    props.append(
                        PropDefinition(
                            name=match.group(1),
                            type=match.group(2),
                        )
                    )

        return props

    def _extract_svelte_props(self, content: str) -> list[PropDefinition]:
        """Extract props from Svelte component."""
        props = []

        # Find export let statements
        export_matches = re.finditer(
            r"export\s+let\s+(\w+)(?:\s*:\s*(\w+))?(?:\s*=\s*([^;]+))?",
            content,
        )
        for match in export_matches:
            props.append(
                PropDefinition(
                    name=match.group(1),
                    type=match.group(2) or "any",
                    default=match.group(3).strip() if match.group(3) else None,
                )
            )

        return props

    def _guess_category(self, name: str, content: str) -> ComponentCategory:
        """Guess the component category from name and content."""
        name_lower = name.lower()
        content_lower = content.lower()

        # Form controls
        form_keywords = ["input", "button", "select", "checkbox", "radio", "form", "field"]
        if any(kw in name_lower for kw in form_keywords):
            return ComponentCategory.FORM

        # Layout
        layout_keywords = ["layout", "container", "grid", "flex", "stack", "box", "wrapper"]
        if any(kw in name_lower for kw in layout_keywords):
            return ComponentCategory.LAYOUT

        # Navigation
        nav_keywords = ["nav", "menu", "sidebar", "header", "footer", "breadcrumb", "tab"]
        if any(kw in name_lower for kw in nav_keywords):
            return ComponentCategory.NAVIGATION

        # Feedback
        feedback_keywords = ["alert", "toast", "notification", "message", "spinner", "loading"]
        if any(kw in name_lower for kw in feedback_keywords):
            return ComponentCategory.FEEDBACK

        # Data display
        data_keywords = ["table", "list", "card", "badge", "tag", "avatar", "tooltip"]
        if any(kw in name_lower for kw in data_keywords):
            return ComponentCategory.DATA_DISPLAY

        # Overlay
        overlay_keywords = ["modal", "dialog", "drawer", "popup", "dropdown", "popover"]
        if any(kw in name_lower for kw in overlay_keywords):
            return ComponentCategory.OVERLAY

        # Typography
        text_keywords = ["text", "heading", "title", "paragraph", "link", "label"]
        if any(kw in name_lower for kw in text_keywords):
            return ComponentCategory.TYPOGRAPHY

        return ComponentCategory.OTHER
