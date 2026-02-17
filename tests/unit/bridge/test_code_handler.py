"""Tests for the code handler."""

import pytest
import tempfile
from pathlib import Path

from bridge.handlers.code import CodeHandler


class TestCodeHandler:
    """Tests for CodeHandler."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return CodeHandler()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create a simple Python project
            (project_path / "src").mkdir()

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

            yield project_path

    def test_get_supported_languages(self, handler):
        """Test getting supported languages."""
        result = handler.get_supported_languages()

        assert result["success"]
        assert "python" in result["languages"]
        assert ".py" in result["extensions"]

    def test_get_entity_types(self, handler):
        """Test getting entity types."""
        result = handler.get_entity_types()

        assert result["success"]
        type_ids = [t["id"] for t in result["types"]]
        assert "function" in type_ids
        assert "class" in type_ids
        assert "method" in type_ids

    def test_get_relationship_types(self, handler):
        """Test getting relationship types."""
        result = handler.get_relationship_types()

        assert result["success"]
        type_ids = [t["id"] for t in result["types"]]
        assert "calls" in type_ids
        assert "extends" in type_ids

    def test_scan_project(self, handler, temp_project):
        """Test scanning a project."""
        result = handler.scan_project(str(temp_project))

        assert result["success"]
        assert result["result"]["files_scanned"] > 0
        assert result["result"]["entity_count"] > 0

    def test_scan_file(self, handler, temp_project):
        """Test scanning a single file."""
        result = handler.scan_file(
            str(temp_project / "src" / "main.py"),
            str(temp_project),
        )

        assert result["success"]
        assert result["count"] > 0

        # Should find main function and App class
        entity_names = [e["name"] for e in result["entities"]]
        assert "main" in entity_names
        assert "App" in entity_names

    def test_find_function(self, handler, temp_project):
        """Test finding functions by name."""
        # First scan the project
        handler.scan_project(str(temp_project))

        result = handler.find_function("main", str(temp_project))

        assert result["success"]
        assert result["count"] > 0
        assert any(f["name"] == "main" for f in result["functions"])

    def test_find_class(self, handler, temp_project):
        """Test finding classes by name."""
        # First scan the project
        handler.scan_project(str(temp_project))

        result = handler.find_class("App", str(temp_project))

        assert result["success"]
        assert result["count"] > 0
        assert any(c["name"] == "App" for c in result["classes"])

    def test_get_code_stats(self, handler, temp_project):
        """Test getting code statistics."""
        # First scan the project
        handler.scan_project(str(temp_project))

        result = handler.get_code_stats(str(temp_project))

        assert result["success"]
        stats = result["stats"]
        assert stats["entities"]["total"] > 0
        assert "python" in stats["entities"]["by_language"]

    def test_get_scan_status(self, handler, temp_project):
        """Test getting scan status."""
        result = handler.get_scan_status(str(temp_project))

        # Initially not indexed
        assert result["success"]
        assert not result["status"]["indexed"]

        # After scanning
        handler.scan_project(str(temp_project))
        result = handler.get_scan_status(str(temp_project))

        # Status should be available via manager
        assert result["success"]

    def test_search_code(self, handler, temp_project):
        """Test code search."""
        # First scan the project
        handler.scan_project(str(temp_project))

        result = handler.search_code(
            query="main",
            project_path=str(temp_project),
            limit=10,
        )

        assert result["success"]
        assert len(result["results"]) > 0

    def test_error_handling(self, handler):
        """Test error handling for invalid paths."""
        result = handler.scan_project("/nonexistent/path")

        # Should handle errors gracefully
        assert not result["success"]
        assert "error" in result
