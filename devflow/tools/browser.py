"""Tool browser - aggregates and searches tools from multiple sources."""

import asyncio
import logging
import re
import shutil
from collections import defaultdict
from datetime import datetime

from devflow.tools.cache import clear_cache, get_cache_info
from devflow.tools.models import (
    BrowsableTool,
    CategoryInfo,
    SearchResult,
    SourceInfo,
    ToolBrowserCategory,
    ToolSource,
)
from devflow.tools.sources.homebrew import fetch_homebrew_casks, fetch_homebrew_formulae
from devflow.tools.sources.mise import fetch_mise_registry

logger = logging.getLogger(__name__)


class ToolBrowser:
    """Aggregates tools from multiple sources with caching and search."""

    def __init__(self):
        self._mise_tools: list[BrowsableTool] = []
        self._brew_tools: list[BrowsableTool] = []
        self._cask_tools: list[BrowsableTool] = []
        self._all_tools: list[BrowsableTool] = []
        self._tools_by_id: dict[str, BrowsableTool] = {}
        self._last_refresh: datetime | None = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if tools have been loaded."""
        return self._is_loaded

    @property
    def total_count(self) -> int:
        """Total number of tools across all sources."""
        return len(self._all_tools)

    async def refresh(self, force: bool = False) -> dict:
        """Refresh tool data from all sources.

        Args:
            force: If True, bypass cache and fetch fresh data.

        Returns:
            Dictionary with refresh results.
        """
        logger.info(f"Refreshing tool browser (force={force})")

        # Clear cache if forcing refresh
        if force:
            clear_cache()

        # Fetch from all sources in parallel
        mise_task = asyncio.create_task(fetch_mise_registry(force))
        brew_task = asyncio.create_task(fetch_homebrew_formulae(force))
        cask_task = asyncio.create_task(fetch_homebrew_casks(force))

        self._mise_tools = await mise_task
        self._brew_tools = await brew_task
        self._cask_tools = await cask_task

        # Combine all tools
        self._all_tools = self._mise_tools + self._brew_tools + self._cask_tools

        # Build lookup index
        self._tools_by_id = {t.id: t for t in self._all_tools}

        self._last_refresh = datetime.now()
        self._is_loaded = True

        logger.info(
            f"Tool browser loaded: {len(self._mise_tools)} mise, "
            f"{len(self._brew_tools)} brew, {len(self._cask_tools)} cask"
        )

        return {
            "success": True,
            "mise_count": len(self._mise_tools),
            "brew_count": len(self._brew_tools),
            "cask_count": len(self._cask_tools),
            "total": self.total_count,
        }

    async def ensure_loaded(self) -> None:
        """Ensure tools are loaded, fetching if necessary."""
        if not self._is_loaded:
            await self.refresh()

    async def search(
        self,
        query: str = "",
        sources: list[ToolSource] | None = None,
        categories: list[ToolBrowserCategory] | None = None,
        installed_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> SearchResult:
        """Search tools with filters.

        Args:
            query: Search query (matches name, description, aliases)
            sources: Filter by sources (None = all sources)
            categories: Filter by categories (None = all categories)
            installed_only: Only show installed tools
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            SearchResult with matching tools and pagination info.
        """
        await self.ensure_loaded()

        # Start with all tools
        results = self._all_tools

        # Filter by source
        if sources:
            source_set = set(sources)
            results = [t for t in results if t.source in source_set]

        # Filter by category
        if categories:
            category_set = set(categories)
            results = [t for t in results if t.category in category_set]

        # Filter by installed status
        if installed_only:
            results = [t for t in results if t.is_installed]

        # Search query
        if query:
            results = self._search_tools(results, query)

        # Get total before pagination
        total = len(results)

        # Sort by relevance (if query) or name
        if not query:
            results.sort(key=lambda t: t.name.lower())

        # Apply pagination
        paginated = results[offset : offset + limit]
        has_more = (offset + limit) < total

        return SearchResult(
            tools=paginated,
            total=total,
            has_more=has_more,
            offset=offset,
            limit=limit,
        )

    def _search_tools(
        self,
        tools: list[BrowsableTool],
        query: str,
    ) -> list[BrowsableTool]:
        """Search tools by query with relevance scoring.

        Scoring:
        - Exact name match: 100 points
        - Name starts with query: 50 points
        - Name contains query: 25 points
        - Alias match: 20 points
        - Description contains query word: 5 points per word
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return tools

        # Split query into words for multi-word search
        query_words = query_lower.split()

        scored: list[tuple[int, BrowsableTool]] = []

        for tool in tools:
            score = 0
            name_lower = tool.name.lower()

            # Exact name match
            if name_lower == query_lower:
                score += 100
            # Name starts with query
            elif name_lower.startswith(query_lower):
                score += 50
            # Name contains query
            elif query_lower in name_lower:
                score += 25

            # Check aliases
            for alias in tool.aliases:
                alias_lower = alias.lower()
                if alias_lower == query_lower:
                    score += 20
                elif query_lower in alias_lower:
                    score += 10

            # Check description for query words
            desc_lower = tool.description.lower()
            for word in query_words:
                if re.search(rf"\b{re.escape(word)}\b", desc_lower):
                    score += 5
                elif word in desc_lower:
                    score += 2

            if score > 0:
                scored.append((score, tool))

        # Sort by score (descending), then name
        scored.sort(key=lambda x: (-x[0], x[1].name.lower()))

        return [tool for _, tool in scored]

    async def get_categories(self) -> list[CategoryInfo]:
        """Get all categories with tool counts.

        Returns:
            List of CategoryInfo objects sorted by count (descending).
        """
        await self.ensure_loaded()

        counts: dict[ToolBrowserCategory, int] = defaultdict(int)

        for tool in self._all_tools:
            counts[tool.category] += 1

        categories = [
            CategoryInfo(
                id=cat.value,
                name=cat.display_name,
                icon=cat.icon,
                count=counts[cat],
            )
            for cat in ToolBrowserCategory
            if counts[cat] > 0
        ]

        # Sort by count descending
        categories.sort(key=lambda c: -c.count)

        return categories

    async def get_sources(self) -> list[SourceInfo]:
        """Get available sources with tool counts.

        Returns:
            List of SourceInfo objects.
        """
        await self.ensure_loaded()

        return [
            SourceInfo(id="mise", name="Mise", count=len(self._mise_tools)),
            SourceInfo(id="homebrew", name="Homebrew", count=len(self._brew_tools)),
            SourceInfo(id="cask", name="Cask", count=len(self._cask_tools)),
        ]

    async def get_tool(self, tool_id: str) -> BrowsableTool | None:
        """Get a single tool by ID.

        Args:
            tool_id: Tool ID (e.g., "mise:node", "brew:git", "cask:docker")

        Returns:
            BrowsableTool or None if not found.
        """
        await self.ensure_loaded()
        return self._tools_by_id.get(tool_id)

    async def detect_installed(self, tool_ids: list[str]) -> dict[str, bool]:
        """Batch check installation status for tools.

        Args:
            tool_ids: List of tool IDs to check.

        Returns:
            Dictionary mapping tool_id to installed status.
        """
        await self.ensure_loaded()

        results: dict[str, bool] = {}

        for tool_id in tool_ids:
            tool = self._tools_by_id.get(tool_id)
            if not tool:
                results[tool_id] = False
                continue

            # Check based on source
            is_installed = await self._check_installed(tool)
            results[tool_id] = is_installed

            # Update tool state
            tool.is_installed = is_installed

        return results

    async def _check_installed(self, tool: BrowsableTool) -> bool:
        """Check if a single tool is installed."""
        try:
            if tool.source == ToolSource.MISE:
                return await self._check_mise_installed(tool.name)
            elif tool.source == ToolSource.HOMEBREW:
                return await self._check_brew_installed(tool.name)
            elif tool.source == ToolSource.CASK:
                return await self._check_cask_installed(tool.id.replace("cask:", ""))
        except Exception as e:
            logger.debug(f"Error checking install status for {tool.id}: {e}")

        return False

    async def _check_mise_installed(self, name: str) -> bool:
        """Check if a mise tool is installed."""
        mise_path = shutil.which("mise")
        if not mise_path:
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                mise_path,
                "ls",
                name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
        except Exception:
            return False

    async def _check_brew_installed(self, name: str) -> bool:
        """Check if a Homebrew formula is installed."""
        brew_path = shutil.which("brew")
        if not brew_path:
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                brew_path,
                "list",
                "--formula",
                name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
        except Exception:
            return False

    async def _check_cask_installed(self, token: str) -> bool:
        """Check if a Homebrew cask is installed."""
        brew_path = shutil.which("brew")
        if not brew_path:
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                brew_path,
                "list",
                "--cask",
                token,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
        except Exception:
            return False

    async def install(self, tool_id: str) -> dict:
        """Install a tool.

        Args:
            tool_id: Tool ID to install.

        Returns:
            Dictionary with install result.
        """
        await self.ensure_loaded()

        tool = self._tools_by_id.get(tool_id)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_id}"}

        logger.info(f"Installing tool: {tool_id}")

        try:
            if tool.source == ToolSource.MISE:
                return await self._install_mise(tool)
            elif tool.source == ToolSource.HOMEBREW:
                return await self._install_brew(tool)
            elif tool.source == ToolSource.CASK:
                return await self._install_cask(tool)
            else:
                return {"success": False, "error": f"Unknown source: {tool.source}"}
        except Exception as e:
            logger.error(f"Failed to install {tool_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _install_mise(self, tool: BrowsableTool) -> dict:
        """Install a mise tool."""
        mise_path = shutil.which("mise")
        if not mise_path:
            return {"success": False, "error": "mise not found"}

        process = await asyncio.create_subprocess_exec(
            mise_path,
            "use",
            "-g",
            f"{tool.name}@latest",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300.0,  # 5 minutes
        )

        if process.returncode != 0:
            error = stderr.decode().strip() if stderr else "Unknown error"
            return {"success": False, "error": error}

        tool.is_installed = True
        return {
            "success": True,
            "message": f"Installed {tool.name}",
            "output": stdout.decode().strip(),
        }

    async def _install_brew(self, tool: BrowsableTool) -> dict:
        """Install a Homebrew formula."""
        brew_path = shutil.which("brew")
        if not brew_path:
            return {"success": False, "error": "brew not found"}

        process = await asyncio.create_subprocess_exec(
            brew_path,
            "install",
            tool.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=600.0,  # 10 minutes
        )

        if process.returncode != 0:
            error = stderr.decode().strip() if stderr else "Unknown error"
            return {"success": False, "error": error}

        tool.is_installed = True
        return {
            "success": True,
            "message": f"Installed {tool.name}",
            "output": stdout.decode().strip(),
        }

    async def _install_cask(self, tool: BrowsableTool) -> dict:
        """Install a Homebrew cask."""
        brew_path = shutil.which("brew")
        if not brew_path:
            return {"success": False, "error": "brew not found"}

        token = tool.id.replace("cask:", "")

        process = await asyncio.create_subprocess_exec(
            brew_path,
            "install",
            "--cask",
            token,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=600.0,  # 10 minutes
        )

        if process.returncode != 0:
            error = stderr.decode().strip() if stderr else "Unknown error"
            return {"success": False, "error": error}

        tool.is_installed = True
        return {
            "success": True,
            "message": f"Installed {tool.name}",
            "output": stdout.decode().strip(),
        }

    def get_cache_status(self) -> dict:
        """Get information about cache status.

        Returns:
            Dictionary with cache info.
        """
        return {
            "is_loaded": self._is_loaded,
            "total_tools": self.total_count,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "cache_files": get_cache_info(),
        }
