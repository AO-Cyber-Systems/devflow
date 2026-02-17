"""
Code scanner for discovering and parsing source files.

Provides file discovery with glob patterns, language detection,
and dispatching to language-specific parsers.
"""

import fnmatch
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from .models import CodeEntity
from .parsers.base import BaseParser
from .parsers.python_parser import PythonParser
from .parsers.treesitter_parser import TreeSitterParser

logger = logging.getLogger(__name__)


# Default patterns to ignore
DEFAULT_IGNORE_PATTERNS = [
    # Version control
    ".git",
    ".svn",
    ".hg",
    # Dependencies
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # Build outputs
    "build",
    "dist",
    "target",
    "out",
    ".next",
    ".nuxt",
    # IDE/Editor
    ".idea",
    ".vscode",
    "*.egg-info",
    # Test/coverage
    "coverage",
    ".coverage",
    "htmlcov",
    # Other
    ".devflow",
    ".tox",
    "*.min.js",
    "*.bundle.js",
    "*.map",
]


@dataclass
class ScanResult:
    """Result of a code scan operation."""

    project_path: str
    entities: list[CodeEntity]
    files_scanned: int
    files_failed: int
    parse_errors: list[str]
    scan_time_ms: float
    languages: dict[str, int]
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "project_path": self.project_path,
            "entity_count": len(self.entities),
            "files_scanned": self.files_scanned,
            "files_failed": self.files_failed,
            "parse_errors": self.parse_errors[:10],  # Limit errors
            "scan_time_ms": self.scan_time_ms,
            "languages": self.languages,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ScanConfig:
    """Configuration for code scanning."""

    # Languages to scan (empty = all supported)
    languages: list[str] = field(default_factory=list)

    # File patterns to include
    include_patterns: list[str] = field(
        default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.go", "**/*.rs"]
    )

    # Patterns to exclude
    exclude_patterns: list[str] = field(default_factory=list)

    # Additional ignore patterns
    ignore_patterns: list[str] = field(default_factory=list)

    # Maximum file size to parse (bytes)
    max_file_size: int = 1024 * 1024  # 1MB

    # Maximum number of files to scan
    max_files: int = 10000

    # Whether to follow symlinks
    follow_symlinks: bool = False

    # Whether to include test files
    include_tests: bool = True

    def get_ignore_patterns(self) -> list[str]:
        """Get all ignore patterns."""
        patterns = list(DEFAULT_IGNORE_PATTERNS)
        patterns.extend(self.ignore_patterns)
        if not self.include_tests:
            patterns.extend(["test_*", "*_test.py", "tests", "__tests__", "*.test.ts", "*.test.js"])
        return patterns


class CodeScanner:
    """Scanner for discovering and parsing source code files."""

    def __init__(
        self,
        project_path: str | Path,
        config: ScanConfig | None = None,
    ):
        """
        Initialize the code scanner.

        Args:
            project_path: Root directory to scan
            config: Scan configuration options
        """
        self.project_path = Path(project_path).resolve()
        self.config = config or ScanConfig()

        # Initialize parsers
        self._python_parser = PythonParser()
        self._treesitter_parser = TreeSitterParser()

        # Progress callback
        self._progress_callback: Callable[[str, int, int], None] | None = None

    def set_progress_callback(
        self, callback: Callable[[str, int, int], None] | None
    ) -> None:
        """
        Set a callback for progress updates.

        Args:
            callback: Function(file_path, current, total) called during scanning
        """
        self._progress_callback = callback

    def scan(self) -> ScanResult:
        """
        Scan the project for code entities.

        Returns:
            ScanResult with all discovered entities
        """
        start_time = datetime.now()
        entities: list[CodeEntity] = []
        files_scanned = 0
        files_failed = 0
        parse_errors: list[str] = []
        languages: dict[str, int] = {}

        # Discover files
        files = self._discover_files()
        total_files = len(files)

        logger.info(f"Scanning {total_files} files in {self.project_path}")

        for i, file_path in enumerate(files):
            if self._progress_callback:
                self._progress_callback(str(file_path), i + 1, total_files)

            try:
                file_entities = self._parse_file(file_path)

                if file_entities:
                    entities.extend(file_entities)
                    files_scanned += 1

                    # Track language stats
                    lang = file_entities[0].language
                    languages[lang] = languages.get(lang, 0) + 1

            except Exception as e:
                files_failed += 1
                error_msg = f"{file_path}: {str(e)}"
                parse_errors.append(error_msg)
                logger.debug(f"Error parsing {file_path}: {e}")

        end_time = datetime.now()
        scan_time_ms = (end_time - start_time).total_seconds() * 1000

        logger.info(
            f"Scan complete: {files_scanned} files, {len(entities)} entities, "
            f"{files_failed} failures in {scan_time_ms:.0f}ms"
        )

        return ScanResult(
            project_path=str(self.project_path),
            entities=entities,
            files_scanned=files_scanned,
            files_failed=files_failed,
            parse_errors=parse_errors,
            scan_time_ms=scan_time_ms,
            languages=languages,
            started_at=start_time,
            completed_at=end_time,
        )

    def scan_file(self, file_path: str | Path) -> list[CodeEntity]:
        """
        Scan a single file.

        Args:
            file_path: Path to the file

        Returns:
            List of code entities from the file
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_path / path

        return self._parse_file(path)

    def _discover_files(self) -> list[Path]:
        """Discover all files to scan."""
        files: list[Path] = []
        ignore_patterns = self.config.get_ignore_patterns()

        def should_ignore(path: Path) -> bool:
            """Check if a path should be ignored."""
            name = path.name
            rel_path = str(path.relative_to(self.project_path))

            for pattern in ignore_patterns:
                if fnmatch.fnmatch(name, pattern):
                    return True
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            return False

        def should_include(path: Path) -> bool:
            """Check if a file matches include patterns."""
            if not self.config.include_patterns:
                return True

            rel_path = str(path.relative_to(self.project_path))
            for pattern in self.config.include_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
                if fnmatch.fnmatch(path.name, pattern):
                    return True
            return False

        def should_exclude(path: Path) -> bool:
            """Check if a file matches exclude patterns."""
            if not self.config.exclude_patterns:
                return False

            rel_path = str(path.relative_to(self.project_path))
            for pattern in self.config.exclude_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
                if fnmatch.fnmatch(path.name, pattern):
                    return True
            return False

        try:
            for root, dirs, filenames in os.walk(
                self.project_path,
                followlinks=self.config.follow_symlinks,
            ):
                root_path = Path(root)

                # Filter directories in-place to skip ignored ones
                dirs[:] = [
                    d for d in dirs
                    if not should_ignore(root_path / d)
                ]

                for filename in filenames:
                    if len(files) >= self.config.max_files:
                        logger.warning(f"Reached max files limit: {self.config.max_files}")
                        return files

                    file_path = root_path / filename

                    # Skip ignored files
                    if should_ignore(file_path):
                        continue

                    # Check include/exclude patterns
                    if not should_include(file_path):
                        continue

                    if should_exclude(file_path):
                        continue

                    # Check file size
                    try:
                        if file_path.stat().st_size > self.config.max_file_size:
                            logger.debug(f"Skipping large file: {file_path}")
                            continue
                    except OSError:
                        continue

                    # Check if we can parse this file
                    if self._can_parse(file_path):
                        files.append(file_path)

        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")

        return files

    def _can_parse(self, file_path: Path) -> bool:
        """Check if we can parse a file."""
        # Check language filter
        if self.config.languages:
            lang = self._detect_language(file_path)
            if lang not in self.config.languages:
                return False

        # Check parser availability
        if self._python_parser.can_parse(file_path):
            return True
        if self._treesitter_parser.can_parse(file_path):
            return True

        return False

    def _detect_language(self, file_path: Path) -> str | None:
        """Detect the language of a file."""
        return (
            self._python_parser.detect_language(file_path)
            or self._treesitter_parser.detect_language(file_path)
        )

    def _parse_file(self, file_path: Path) -> list[CodeEntity]:
        """Parse a file with the appropriate parser."""
        # Prefer Python parser for .py files
        if self._python_parser.can_parse(file_path):
            return self._python_parser.parse_file(file_path)

        # Use tree-sitter for other languages
        if self._treesitter_parser.can_parse(file_path):
            return self._treesitter_parser.parse_file(file_path)

        logger.debug(f"No parser available for: {file_path}")
        return []

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        languages = set(self._python_parser.SUPPORTED_LANGUAGES)
        languages.update(self._treesitter_parser.SUPPORTED_LANGUAGES)
        return sorted(languages)

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        extensions = set(self._python_parser.SUPPORTED_EXTENSIONS)
        extensions.update(self._treesitter_parser.SUPPORTED_EXTENSIONS)
        return sorted(extensions)
