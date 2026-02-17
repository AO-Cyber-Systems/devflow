"""Tests for tools handler."""

from unittest.mock import MagicMock, patch

import pytest

from bridge.handlers.tools import ToolsHandler


@pytest.fixture
def tools_handler() -> ToolsHandler:
    """Create a ToolsHandler for testing."""
    return ToolsHandler()


@pytest.fixture
def mock_browser():
    """Create a mock ToolBrowser."""
    return MagicMock()


class TestToolsHandlerSearch:
    """Tests for search method."""

    def test_search_basic(self, tools_handler: ToolsHandler) -> None:
        """Test basic search without filters."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "tools": [
                {"id": "mise:node", "name": "Node.js"},
                {"id": "mise:python", "name": "Python"},
            ],
            "total": 2,
            "limit": 50,
            "offset": 0,
        }

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                result = tools_handler.search(query="node")

                assert len(result["tools"]) == 2
                assert result["total"] == 2

    def test_search_with_sources_filter(self, tools_handler: ToolsHandler) -> None:
        """Test search with source filter."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"tools": [], "total": 0}

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                tools_handler.search(sources=["mise", "homebrew"])

                # Verify asyncio.run was called
                assert mock_run.called

    def test_search_with_categories_filter(self, tools_handler: ToolsHandler) -> None:
        """Test search with category filter."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"tools": [], "total": 0}

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                tools_handler.search(categories=["language_runtime", "database"])

                assert mock_run.called

    def test_search_with_pagination(self, tools_handler: ToolsHandler) -> None:
        """Test search with pagination."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "tools": [{"id": "mise:go", "name": "Go"}],
            "total": 100,
            "limit": 10,
            "offset": 20,
        }

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                result = tools_handler.search(limit=10, offset=20)

                assert result["limit"] == 10
                assert result["offset"] == 20

    def test_search_installed_only(self, tools_handler: ToolsHandler) -> None:
        """Test search with installed_only filter."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"tools": [], "total": 0}

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                tools_handler.search(installed_only=True)

                assert mock_run.called

    def test_search_exception(self, tools_handler: ToolsHandler) -> None:
        """Test search when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            mock_get_browser.side_effect = Exception("Browser init failed")

            result = tools_handler.search()

            assert "error" in result
            assert "Browser init failed" in result["error"]

    def test_search_unknown_source(self, tools_handler: ToolsHandler) -> None:
        """Test search with unknown source (should be filtered out)."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"tools": [], "total": 0}

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_result

                # Should not raise, just log warning
                result = tools_handler.search(sources=["unknown_source"])

                assert "error" not in result


class TestToolsHandlerGetCategories:
    """Tests for get_categories method."""

    def test_get_categories_success(self, tools_handler: ToolsHandler) -> None:
        """Test getting categories successfully."""
        mock_categories = [
            MagicMock(to_dict=lambda: {"id": "language_runtime", "name": "Language Runtime", "count": 10}),
            MagicMock(to_dict=lambda: {"id": "database", "name": "Database", "count": 5}),
        ]

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_categories

                result = tools_handler.get_categories()

                assert "categories" in result
                assert len(result["categories"]) == 2

    def test_get_categories_exception(self, tools_handler: ToolsHandler) -> None:
        """Test getting categories when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Failed to fetch categories")

                result = tools_handler.get_categories()

                assert "error" in result


class TestToolsHandlerGetSources:
    """Tests for get_sources method."""

    def test_get_sources_success(self, tools_handler: ToolsHandler) -> None:
        """Test getting sources successfully."""
        mock_sources = [
            MagicMock(to_dict=lambda: {"id": "mise", "name": "Mise", "count": 50}),
            MagicMock(to_dict=lambda: {"id": "homebrew", "name": "Homebrew", "count": 100}),
        ]

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_sources

                result = tools_handler.get_sources()

                assert "sources" in result
                assert len(result["sources"]) == 2

    def test_get_sources_exception(self, tools_handler: ToolsHandler) -> None:
        """Test getting sources when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Failed to fetch sources")

                result = tools_handler.get_sources()

                assert "error" in result


class TestToolsHandlerGetTool:
    """Tests for get_tool method."""

    def test_get_tool_success(self, tools_handler: ToolsHandler) -> None:
        """Test getting a tool successfully."""
        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {
            "id": "mise:node",
            "name": "Node.js",
            "description": "JavaScript runtime",
            "installed": True,
            "version": "20.10.0",
        }

        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = mock_tool

                result = tools_handler.get_tool("mise:node")

                assert "tool" in result
                assert result["tool"]["id"] == "mise:node"
                assert result["tool"]["installed"] is True

    def test_get_tool_not_found(self, tools_handler: ToolsHandler) -> None:
        """Test getting a tool that doesn't exist."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = None

                result = tools_handler.get_tool("nonexistent:tool")

                assert "error" in result
                assert "not found" in result["error"]

    def test_get_tool_exception(self, tools_handler: ToolsHandler) -> None:
        """Test getting a tool when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Failed to fetch tool")

                result = tools_handler.get_tool("mise:node")

                assert "error" in result


class TestToolsHandlerInstall:
    """Tests for install method."""

    def test_install_success(self, tools_handler: ToolsHandler) -> None:
        """Test installing a tool successfully."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {"success": True, "message": "Installed node@20.10.0"}

                result = tools_handler.install("mise:node")

                assert result["success"] is True

    def test_install_failure(self, tools_handler: ToolsHandler) -> None:
        """Test installing a tool that fails."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {"success": False, "error": "Permission denied"}

                result = tools_handler.install("mise:node")

                assert result["success"] is False

    def test_install_exception(self, tools_handler: ToolsHandler) -> None:
        """Test installing when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Install failed")

                result = tools_handler.install("mise:node")

                assert "error" in result


class TestToolsHandlerDetectInstalled:
    """Tests for detect_installed method."""

    def test_detect_installed_success(self, tools_handler: ToolsHandler) -> None:
        """Test detecting installed tools successfully."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {
                    "mise:node": True,
                    "mise:python": True,
                    "mise:ruby": False,
                }

                result = tools_handler.detect_installed(["mise:node", "mise:python", "mise:ruby"])

                assert "installed" in result
                assert result["installed"]["mise:node"] is True
                assert result["installed"]["mise:ruby"] is False

    def test_detect_installed_empty(self, tools_handler: ToolsHandler) -> None:
        """Test detecting with empty list."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {}

                result = tools_handler.detect_installed([])

                assert result["installed"] == {}

    def test_detect_installed_exception(self, tools_handler: ToolsHandler) -> None:
        """Test detecting when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Detection failed")

                result = tools_handler.detect_installed(["mise:node"])

                assert "error" in result


class TestToolsHandlerRefreshCache:
    """Tests for refresh_cache method."""

    def test_refresh_cache_success(self, tools_handler: ToolsHandler) -> None:
        """Test refreshing cache successfully."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {
                    "success": True,
                    "tools_count": 150,
                    "sources_refreshed": ["mise", "homebrew"],
                }

                result = tools_handler.refresh_cache()

                assert result["success"] is True
                assert result["tools_count"] == 150

    def test_refresh_cache_force(self, tools_handler: ToolsHandler) -> None:
        """Test force refreshing cache."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_browser = MagicMock()
                mock_get_browser.return_value = mock_browser
                mock_run.return_value = {"success": True}

                tools_handler.refresh_cache(force=True)

                assert mock_run.called

    def test_refresh_cache_exception(self, tools_handler: ToolsHandler) -> None:
        """Test refreshing cache when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            with patch("asyncio.run") as mock_run:
                mock_run.side_effect = Exception("Refresh failed")

                result = tools_handler.refresh_cache()

                assert "error" in result


class TestToolsHandlerGetCacheStatus:
    """Tests for get_cache_status method."""

    def test_get_cache_status_success(self, tools_handler: ToolsHandler) -> None:
        """Test getting cache status successfully."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            mock_browser = MagicMock()
            mock_browser.get_cache_status.return_value = {
                "cached": True,
                "tools_count": 150,
                "last_updated": "2024-01-15T10:30:00Z",
                "cache_path": "/path/to/cache",
            }
            mock_get_browser.return_value = mock_browser

            result = tools_handler.get_cache_status()

            assert result["cached"] is True
            assert result["tools_count"] == 150

    def test_get_cache_status_exception(self, tools_handler: ToolsHandler) -> None:
        """Test getting cache status when an exception occurs."""
        with patch.object(tools_handler, "_get_browser") as mock_get_browser:
            mock_get_browser.side_effect = Exception("Cache error")

            result = tools_handler.get_cache_status()

            assert "error" in result


class TestToolsHandlerGetBrowser:
    """Tests for _get_browser method."""

    def test_get_browser_creates_once(self, tools_handler: ToolsHandler) -> None:
        """Test that browser is created only once (cached)."""
        with patch("bridge.handlers.tools.ToolBrowser") as mock_browser_class:
            mock_instance = MagicMock()
            mock_browser_class.return_value = mock_instance

            # Call twice
            browser1 = tools_handler._get_browser()
            browser2 = tools_handler._get_browser()

            # Should only create once
            assert mock_browser_class.call_count == 1
            assert browser1 is browser2
