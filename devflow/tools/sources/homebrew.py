"""Fetch tools from the Homebrew API."""

import asyncio
import json
import logging
from datetime import timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

from devflow.tools.cache import is_cache_valid, load_cache, save_cache
from devflow.tools.categorizer import ToolCategorizer
from devflow.tools.models import BrowsableTool, ToolBrowserCategory, ToolSource

logger = logging.getLogger(__name__)

# Homebrew API endpoints
FORMULAE_API_URL = "https://formulae.brew.sh/api/formula.json"
CASKS_API_URL = "https://formulae.brew.sh/api/cask.json"

# Cache settings
FORMULAE_CACHE_NAME = "homebrew_formulae"
CASKS_CACHE_NAME = "homebrew_casks"
HOMEBREW_CACHE_MAX_AGE = timedelta(days=7)

# Request timeout
REQUEST_TIMEOUT = 60


async def fetch_homebrew_formulae(force_refresh: bool = False) -> list[BrowsableTool]:
    """Fetch formulae from the Homebrew API.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        List of BrowsableTool objects from Homebrew formulae.
    """
    # Check cache first
    if not force_refresh and is_cache_valid(FORMULAE_CACHE_NAME, HOMEBREW_CACHE_MAX_AGE):
        cached = load_cache(FORMULAE_CACHE_NAME)
        if cached:
            logger.debug(f"Using cached Homebrew formulae ({len(cached)} tools)")
            return [_dict_to_tool(d) for d in cached]

    logger.info("Fetching Homebrew formulae...")

    try:
        # Run blocking HTTP request in thread pool
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _fetch_json, FORMULAE_API_URL)

        if data is None:
            return []

        tools = _parse_formulae(data)

        # Cache the results
        save_cache(FORMULAE_CACHE_NAME, [_tool_to_dict(t) for t in tools])

        logger.info(f"Fetched {len(tools)} Homebrew formulae")
        return tools

    except Exception as e:
        logger.error(f"Failed to fetch Homebrew formulae: {e}")
        return []


async def fetch_homebrew_casks(force_refresh: bool = False) -> list[BrowsableTool]:
    """Fetch casks from the Homebrew API.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        List of BrowsableTool objects from Homebrew casks.
    """
    # Check cache first
    if not force_refresh and is_cache_valid(CASKS_CACHE_NAME, HOMEBREW_CACHE_MAX_AGE):
        cached = load_cache(CASKS_CACHE_NAME)
        if cached:
            logger.debug(f"Using cached Homebrew casks ({len(cached)} tools)")
            return [_dict_to_tool(d) for d in cached]

    logger.info("Fetching Homebrew casks...")

    try:
        # Run blocking HTTP request in thread pool
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, _fetch_json, CASKS_API_URL)

        if data is None:
            return []

        tools = _parse_casks(data)

        # Cache the results
        save_cache(CASKS_CACHE_NAME, [_tool_to_dict(t) for t in tools])

        logger.info(f"Fetched {len(tools)} Homebrew casks")
        return tools

    except Exception as e:
        logger.error(f"Failed to fetch Homebrew casks: {e}")
        return []


def _fetch_json(url: str) -> list[dict] | None:
    """Fetch JSON from a URL (blocking)."""
    try:
        request = Request(url)
        request.add_header("User-Agent", "DevFlow/1.0")

        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode())
    except URLError as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {url}: {e}")
        return None


def _parse_formulae(data: list[dict]) -> list[BrowsableTool]:
    """Parse Homebrew formulae JSON into BrowsableTool objects.

    Formulae entries have structure like:
    {
        "name": "git",
        "full_name": "git",
        "desc": "Distributed revision control system",
        "homepage": "https://git-scm.com/",
        "license": "GPL-2.0-only",
        "versions": {"stable": "2.43.0", ...},
        "aliases": ["git-core"],
        ...
    }
    """
    tools = []

    for entry in data:
        name = entry.get("name", "")
        if not name:
            continue

        description = entry.get("desc", "") or ""
        homepage = entry.get("homepage")
        license_info = entry.get("license")

        # Get version
        versions = entry.get("versions", {})
        version = versions.get("stable") if isinstance(versions, dict) else None

        # Get aliases
        aliases = entry.get("aliases", []) or []

        # Categorize
        category = ToolCategorizer.categorize(name, description, is_cask=False)

        tool = BrowsableTool(
            id=f"brew:{name}",
            name=name,
            description=description or f"{name} (Homebrew)",
            source=ToolSource.HOMEBREW,
            category=category,
            install_command=f"brew install {name}",
            homepage=homepage,
            version=version,
            aliases=aliases,
            license=license_info,
            is_gui_app=False,
            is_runtime=False,
        )

        tools.append(tool)

    return tools


def _parse_casks(data: list[dict]) -> list[BrowsableTool]:
    """Parse Homebrew casks JSON into BrowsableTool objects.

    Cask entries have structure like:
    {
        "token": "docker",
        "name": ["Docker Desktop"],
        "desc": "App to build and share containerized applications",
        "homepage": "https://www.docker.com/products/docker-desktop",
        "version": "4.26.1,131620",
        ...
    }
    """
    tools = []

    for entry in data:
        token = entry.get("token", "")
        if not token:
            continue

        # Name can be a list
        name_list = entry.get("name", [])
        display_name = name_list[0] if name_list else token

        description = entry.get("desc", "") or ""
        homepage = entry.get("homepage")
        version = entry.get("version")

        # Clean up version (remove build numbers after comma)
        if version and "," in version:
            version = version.split(",")[0]

        # Categorize - casks are typically GUI apps
        category = ToolCategorizer.categorize(token, description, is_cask=True)

        tool = BrowsableTool(
            id=f"cask:{token}",
            name=display_name,
            description=description or f"{display_name} (Homebrew Cask)",
            source=ToolSource.CASK,
            category=category,
            install_command=f"brew install --cask {token}",
            homepage=homepage,
            version=version,
            aliases=[token] if token != display_name.lower() else [],
            is_gui_app=True,
            is_runtime=False,
        )

        tools.append(tool)

    return tools


def _tool_to_dict(tool: BrowsableTool) -> dict:
    """Convert tool to dictionary for caching."""
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "source": tool.source.value,
        "category": tool.category.value,
        "install_command": tool.install_command,
        "homepage": tool.homepage,
        "version": tool.version,
        "aliases": tool.aliases,
        "license": tool.license,
        "is_gui_app": tool.is_gui_app,
        "is_runtime": tool.is_runtime,
    }


def _dict_to_tool(d: dict) -> BrowsableTool:
    """Convert cached dictionary back to BrowsableTool."""
    return BrowsableTool(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        source=ToolSource(d["source"]),
        category=ToolBrowserCategory(d["category"]),
        install_command=d["install_command"],
        homepage=d.get("homepage"),
        version=d.get("version"),
        aliases=d.get("aliases", []),
        license=d.get("license"),
        is_gui_app=d.get("is_gui_app", False),
        is_runtime=d.get("is_runtime", False),
    )
