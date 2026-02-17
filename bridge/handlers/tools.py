"""RPC handler for tool browsing."""

import asyncio
import logging
from typing import Any

from devflow.tools.browser import ToolBrowser
from devflow.tools.models import ToolBrowserCategory, ToolSource

logger = logging.getLogger(__name__)


class ToolsHandler:
    """Handler for browsing and installing dev tools."""

    def __init__(self):
        self._browser: ToolBrowser | None = None

    def _get_browser(self) -> ToolBrowser:
        """Get or create the tool browser instance."""
        if self._browser is None:
            self._browser = ToolBrowser()
        return self._browser

    def search(
        self,
        query: str = "",
        sources: list[str] | None = None,
        categories: list[str] | None = None,
        installed_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search tools with filters.

        Args:
            query: Search query (matches name, description, aliases)
            sources: Filter by sources (mise, homebrew, cask)
            categories: Filter by category IDs
            installed_only: Only show installed tools
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            Dictionary with tools list and pagination info.
        """
        try:
            browser = self._get_browser()

            # Convert string sources to ToolSource enum
            source_enums = None
            if sources:
                source_enums = []
                for s in sources:
                    try:
                        source_enums.append(ToolSource(s))
                    except ValueError:
                        logger.warning(f"Unknown source: {s}")

            # Convert string categories to ToolBrowserCategory enum
            category_enums = None
            if categories:
                category_enums = []
                for c in categories:
                    try:
                        category_enums.append(ToolBrowserCategory(c))
                    except ValueError:
                        logger.warning(f"Unknown category: {c}")

            result = asyncio.run(
                browser.search(
                    query=query,
                    sources=source_enums,
                    categories=category_enums,
                    installed_only=installed_only,
                    limit=limit,
                    offset=offset,
                )
            )

            return result.to_dict()

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e)}

    def get_categories(self) -> dict[str, Any]:
        """Get all categories with tool counts.

        Returns:
            Dictionary with categories list.
        """
        try:
            browser = self._get_browser()
            categories = asyncio.run(browser.get_categories())
            return {"categories": [c.to_dict() for c in categories]}
        except Exception as e:
            logger.error(f"Get categories failed: {e}")
            return {"error": str(e)}

    def get_sources(self) -> dict[str, Any]:
        """Get available sources with counts.

        Returns:
            Dictionary with sources list.
        """
        try:
            browser = self._get_browser()
            sources = asyncio.run(browser.get_sources())
            return {"sources": [s.to_dict() for s in sources]}
        except Exception as e:
            logger.error(f"Get sources failed: {e}")
            return {"error": str(e)}

    def get_tool(self, tool_id: str) -> dict[str, Any]:
        """Get a single tool by ID.

        Args:
            tool_id: Tool ID (e.g., "mise:node", "brew:git", "cask:docker")

        Returns:
            Tool details or error.
        """
        try:
            browser = self._get_browser()
            tool = asyncio.run(browser.get_tool(tool_id))

            if tool is None:
                return {"error": f"Tool not found: {tool_id}"}

            return {"tool": tool.to_dict()}
        except Exception as e:
            logger.error(f"Get tool failed: {e}")
            return {"error": str(e)}

    def install(self, tool_id: str) -> dict[str, Any]:
        """Install a tool.

        Args:
            tool_id: Tool ID to install.

        Returns:
            Installation result.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(browser.install(tool_id))
            return result
        except Exception as e:
            logger.error(f"Install failed: {e}")
            return {"error": str(e)}

    def detect_installed(self, tool_ids: list[str]) -> dict[str, Any]:
        """Batch check installation status.

        Args:
            tool_ids: List of tool IDs to check.

        Returns:
            Dictionary mapping tool_id to installed status.
        """
        try:
            browser = self._get_browser()
            results = asyncio.run(browser.detect_installed(tool_ids))
            return {"installed": results}
        except Exception as e:
            logger.error(f"Detect installed failed: {e}")
            return {"error": str(e)}

    def refresh_cache(self, force: bool = False) -> dict[str, Any]:
        """Refresh the tool cache.

        Args:
            force: If True, bypass cache and fetch fresh data.

        Returns:
            Refresh result with tool counts.
        """
        try:
            browser = self._get_browser()
            result = asyncio.run(browser.refresh(force=force))
            return result
        except Exception as e:
            logger.error(f"Refresh cache failed: {e}")
            return {"error": str(e)}

    def get_cache_status(self) -> dict[str, Any]:
        """Get cache status information.

        Returns:
            Cache status info.
        """
        try:
            browser = self._get_browser()
            return browser.get_cache_status()
        except Exception as e:
            logger.error(f"Get cache status failed: {e}")
            return {"error": str(e)}
