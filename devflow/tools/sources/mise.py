"""Fetch tools from the Mise registry."""

import asyncio
import json
import logging
import shutil
from datetime import timedelta

from devflow.tools.cache import is_cache_valid, load_cache, save_cache
from devflow.tools.categorizer import ToolCategorizer
from devflow.tools.models import BrowsableTool, ToolBrowserCategory, ToolSource

logger = logging.getLogger(__name__)

# Cache mise registry for 24 hours
MISE_CACHE_NAME = "mise_registry"
MISE_CACHE_MAX_AGE = timedelta(hours=24)


async def fetch_mise_registry(force_refresh: bool = False) -> list[BrowsableTool]:
    """Fetch tools from the mise registry.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        List of BrowsableTool objects from mise.
    """
    # Check cache first
    if not force_refresh and is_cache_valid(MISE_CACHE_NAME, MISE_CACHE_MAX_AGE):
        cached = load_cache(MISE_CACHE_NAME)
        if cached:
            logger.debug(f"Using cached mise registry ({len(cached)} tools)")
            return [_dict_to_tool(d) for d in cached]

    # Check if mise is available
    mise_path = shutil.which("mise")
    if not mise_path:
        logger.warning("mise not found in PATH, returning empty registry")
        return []

    logger.info("Fetching mise registry...")

    try:
        process = await asyncio.create_subprocess_exec(
            mise_path,
            "registry",
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0,
        )

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            logger.error(f"mise registry failed: {error_msg}")
            return []

        registry_data = json.loads(stdout.decode())
        tools = _parse_mise_registry(registry_data)

        # Cache the results
        save_cache(MISE_CACHE_NAME, [_tool_to_dict(t) for t in tools])

        logger.info(f"Fetched {len(tools)} tools from mise registry")
        return tools

    except asyncio.TimeoutError:
        logger.error("mise registry command timed out")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse mise registry JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch mise registry: {e}")
        return []


def _parse_mise_registry(data: list[dict]) -> list[BrowsableTool]:
    """Parse mise registry JSON into BrowsableTool objects.

    The mise registry returns entries like:
    {
        "short": "node",
        "backends": ["core:node"],
        "description": "Node.js JavaScript runtime",
        "aliases": ["nodejs"]
    }
    """
    tools = []

    for entry in data:
        short = entry.get("short", "")
        if not short:
            continue

        description = entry.get("description", "")
        aliases = entry.get("aliases", [])

        # Determine if it's a runtime (has version management)
        backends = entry.get("backends", [])
        is_runtime = any(
            b.startswith("core:") or b.startswith("vfox:") or b.startswith("asdf:")
            for b in backends
        )

        # Categorize the tool
        category = ToolCategorizer.categorize(short, description)

        # Build install command
        install_command = f"mise use {short}@latest"

        tool = BrowsableTool(
            id=f"mise:{short}",
            name=short,
            description=description or f"{short} (mise)",
            source=ToolSource.MISE,
            category=category,
            install_command=install_command,
            aliases=aliases,
            is_runtime=is_runtime,
            is_gui_app=False,
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
