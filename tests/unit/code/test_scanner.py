"""Tests for the code scanner."""

import pytest
import tempfile
from pathlib import Path

from devflow.code.scanner import CodeScanner, ScanConfig, ScanResult


class TestScanConfig:
    """Tests for ScanConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = ScanConfig()
        assert config.max_file_size > 0
        assert config.max_files > 0
        assert len(config.include_patterns) > 0

    def test_ignore_patterns(self):
        """Test ignore pattern generation."""
        config = ScanConfig()
        patterns = config.get_ignore_patterns()
        assert ".git" in patterns
        assert "node_modules" in patterns
        assert "__pycache__" in patterns

    def test_custom_ignore_patterns(self):
        """Test custom ignore patterns."""
        config = ScanConfig(ignore_patterns=["custom_dir", "*.custom"])
        patterns = config.get_ignore_patterns()
        assert "custom_dir" in patterns
        assert "*.custom" in patterns

    def test_exclude_tests(self):
        """Test excluding test files."""
        config = ScanConfig(include_tests=False)
        patterns = config.get_ignore_patterns()
        assert "test_*" in patterns or any("test" in p for p in patterns)


class TestCodeScanner:
    """Tests for CodeScanner."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create a simple Python project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "node_modules").mkdir()  # Should be ignored

            # Create source files
            (project_path / "src" / "__init__.py").write_text('"""Main package."""')

            (project_path / "src" / "main.py").write_text('''
"""Main module."""

def main():
    """Entry point."""
    print("Hello")

class App:
    """Application class."""

    def run(self):
        """Run the app."""
        main()
''')

            (project_path / "src" / "utils.py").write_text('''
"""Utility functions."""

def helper(x: int) -> int:
    """Helper function."""
    return x * 2

def another_helper():
    result = helper(10)
    return result
''')

            # Create test file
            (project_path / "tests" / "test_main.py").write_text('''
"""Tests for main module."""

def test_main():
    pass
''')

            # Create file that should be ignored
            (project_path / "node_modules" / "pkg.js").write_text("// ignored")

            yield project_path

    def test_scanner_initialization(self, temp_project):
        """Test scanner initialization."""
        scanner = CodeScanner(temp_project)
        # Use resolve() to handle symlinks (e.g., /var -> /private/var on macOS)
        assert scanner.project_path == temp_project.resolve()
        assert scanner.config is not None

    def test_supported_languages(self, temp_project):
        """Test getting supported languages."""
        scanner = CodeScanner(temp_project)
        languages = scanner.get_supported_languages()
        assert "python" in languages

    def test_supported_extensions(self, temp_project):
        """Test getting supported extensions."""
        scanner = CodeScanner(temp_project)
        extensions = scanner.get_supported_extensions()
        assert ".py" in extensions

    def test_scan_project(self, temp_project):
        """Test scanning a project."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        assert isinstance(result, ScanResult)
        # Use resolve() to handle symlinks (e.g., /var -> /private/var on macOS)
        assert result.project_path == str(temp_project.resolve())
        assert result.files_scanned > 0
        assert len(result.entities) > 0
        assert result.scan_time_ms >= 0

    def test_scan_finds_functions(self, temp_project):
        """Test that scan finds functions."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        func_names = [e.name for e in result.entities if e.entity_type.value == "function"]
        assert "main" in func_names
        assert "helper" in func_names
        assert "another_helper" in func_names

    def test_scan_finds_classes(self, temp_project):
        """Test that scan finds classes."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        class_names = [e.name for e in result.entities if e.entity_type.value == "class"]
        assert "App" in class_names

    def test_scan_finds_methods(self, temp_project):
        """Test that scan finds methods."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        method_names = [e.name for e in result.entities if e.entity_type.value == "method"]
        assert "run" in method_names

    def test_scan_ignores_node_modules(self, temp_project):
        """Test that node_modules is ignored."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        files = [e.file_path for e in result.entities]
        assert not any("node_modules" in f for f in files)

    def test_scan_with_language_filter(self, temp_project):
        """Test scanning with language filter."""
        config = ScanConfig(languages=["python"])
        scanner = CodeScanner(temp_project, config)
        result = scanner.scan()

        # All entities should be Python
        for entity in result.entities:
            assert entity.language == "python"

    def test_scan_with_exclude_patterns(self, temp_project):
        """Test scanning with exclude patterns."""
        config = ScanConfig(exclude_patterns=["tests/*", "*/tests/*"])
        scanner = CodeScanner(temp_project, config)
        result = scanner.scan()

        files = [e.file_path for e in result.entities]
        assert not any("tests/test_main.py" in f for f in files)

    def test_scan_single_file(self, temp_project):
        """Test scanning a single file."""
        scanner = CodeScanner(temp_project)
        entities = scanner.scan_file("src/main.py")

        assert len(entities) > 0
        assert any(e.name == "main" for e in entities)
        assert any(e.name == "App" for e in entities)

    def test_scan_result_to_dict(self, temp_project):
        """Test ScanResult serialization."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()
        data = result.to_dict()

        assert "project_path" in data
        assert "entity_count" in data
        assert "files_scanned" in data
        assert "languages" in data
        assert data["entity_count"] == len(result.entities)

    def test_scan_language_stats(self, temp_project):
        """Test language statistics in scan result."""
        scanner = CodeScanner(temp_project)
        result = scanner.scan()

        assert "python" in result.languages
        assert result.languages["python"] > 0

    def test_progress_callback(self, temp_project):
        """Test progress callback."""
        scanner = CodeScanner(temp_project)

        progress_calls = []

        def callback(file_path, current, total):
            progress_calls.append((file_path, current, total))

        scanner.set_progress_callback(callback)
        scanner.scan()

        # Should have received progress updates
        assert len(progress_calls) > 0

        # Progress should be monotonically increasing
        for i in range(1, len(progress_calls)):
            assert progress_calls[i][1] >= progress_calls[i - 1][1]

    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = CodeScanner(tmpdir)
            result = scanner.scan()

            assert result.files_scanned == 0
            assert len(result.entities) == 0

    def test_scan_with_max_files(self, temp_project):
        """Test scanning with max files limit."""
        config = ScanConfig(max_files=1)
        scanner = CodeScanner(temp_project, config)
        result = scanner.scan()

        assert result.files_scanned <= 1

    def test_scan_large_file_skip(self, temp_project):
        """Test that large files are skipped."""
        # Create a large file (over max size)
        large_file = temp_project / "src" / "large.py"
        large_content = "x = 1\n" * 200000  # ~1.2MB
        large_file.write_text(large_content)

        config = ScanConfig(max_file_size=1024 * 100)  # 100KB limit
        scanner = CodeScanner(temp_project, config)
        result = scanner.scan()

        # Large file should not be in results
        files = [e.file_path for e in result.entities]
        assert not any("large.py" in f for f in files)
