"""
Base parser interface for language-specific code parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models import CodeEntity


class BaseParser(ABC):
    """Abstract base class for language-specific parsers."""

    # Languages this parser supports
    SUPPORTED_LANGUAGES: list[str] = []

    # File extensions this parser handles
    SUPPORTED_EXTENSIONS: list[str] = []

    def __init__(self):
        """Initialize the parser."""
        pass

    @abstractmethod
    def parse_file(self, file_path: str | Path) -> list[CodeEntity]:
        """
        Parse a source file and extract code entities.

        Args:
            file_path: Path to the source file

        Returns:
            List of CodeEntity objects extracted from the file
        """
        pass

    @abstractmethod
    def parse_source(
        self,
        source: str,
        file_path: str = "<string>",
        language: str | None = None,
    ) -> list[CodeEntity]:
        """
        Parse source code string and extract code entities.

        Args:
            source: Source code string
            file_path: Virtual file path for entity IDs
            language: Language of the source code

        Returns:
            List of CodeEntity objects extracted from the source
        """
        pass

    def can_parse(self, file_path: str | Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if this parser can handle the file
        """
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def detect_language(self, file_path: str | Path) -> str | None:
        """
        Detect the language of a file based on extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if not detected
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        extension_map: dict[str, str] = {
            ".py": "python",
            ".pyi": "python",
            ".pyw": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".hpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".scala": "scala",
            ".lua": "lua",
            ".r": "r",
            ".R": "r",
            ".jl": "julia",
            ".ex": "elixir",
            ".exs": "elixir",
            ".erl": "erlang",
            ".hs": "haskell",
            ".ml": "ocaml",
            ".mli": "ocaml",
            ".clj": "clojure",
            ".cljs": "clojure",
        }

        return extension_map.get(suffix)

    def get_qualified_name(
        self,
        name: str,
        file_path: str | Path,
        parent: str | None = None,
    ) -> str:
        """
        Generate a qualified name for an entity.

        Args:
            name: Entity name
            file_path: File path (used to derive module name)
            parent: Parent entity name (e.g., class name for methods)

        Returns:
            Fully qualified name
        """
        path = Path(file_path)

        # Convert file path to module-like name
        stem = path.stem
        if stem == "__init__":
            stem = path.parent.name

        # Add parent if present
        if parent:
            # If parent is already qualified (contains a dot), use it directly
            if "." in parent:
                return f"{parent}.{name}"
            else:
                return f"{stem}.{parent}.{name}"

        return f"{stem}.{name}"

    def extract_docstring(self, node: Any) -> str | None:
        """
        Extract docstring from an AST node.

        Override in subclasses for language-specific extraction.

        Args:
            node: AST node

        Returns:
            Docstring text or None
        """
        return None

    def calculate_complexity(self, node: Any) -> int:
        """
        Calculate cyclomatic complexity of a node.

        Override in subclasses for language-specific calculation.

        Args:
            node: AST node

        Returns:
            Complexity score
        """
        return 1
