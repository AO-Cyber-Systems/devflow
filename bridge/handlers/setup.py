"""Setup RPC handlers - prerequisites installation and tool management."""

from __future__ import annotations

import asyncio
from typing import Any

from devflow.providers.installers import (
    ALL_TOOLS,
    ESSENTIAL_TOOLS,
    TOOLS_BY_CATEGORY,
    InstallStatus,
    PackageManager,
    PlatformInfo,
    ToolCategory,
    ToolDetector,
    ToolInfo,
    detect_platform,
    get_available_installers,
    get_installer,
    get_mise_managed_tools,
    get_tool_by_id,
    get_tools_by_category,
    install_tool,
)


class SetupHandler:
    """Handler for setup and prerequisites RPC methods."""

    def __init__(self) -> None:
        self._platform_info: PlatformInfo | None = None
        self._tool_detector: ToolDetector | None = None

    def _get_platform_info(self) -> PlatformInfo:
        """Get cached platform info."""
        if self._platform_info is None:
            self._platform_info = detect_platform()
        return self._platform_info

    def _get_detector(self) -> ToolDetector:
        """Get cached tool detector."""
        if self._tool_detector is None:
            self._tool_detector = ToolDetector(self._get_platform_info())
        return self._tool_detector

    def get_platform_info(self) -> dict[str, Any]:
        """Get current platform information."""
        info = self._get_platform_info()
        return {
            "os": info.os.value,
            "distro": info.distro.value if info.distro else None,
            "architecture": info.arch.value,
            "is_wsl": info.is_wsl,
            "package_managers": [pm.value for pm in info.package_managers],
            "is_macos": info.is_macos,
            "is_linux": info.is_linux,
            "is_windows": info.is_windows,
        }

    def get_categories(self) -> dict[str, Any]:
        """Get all tool categories with their tools."""
        categories = {}
        for category in ToolCategory:
            tools = get_tools_by_category(category)
            if tools:
                categories[category.value] = {
                    "name": category.value.replace("_", " ").title(),
                    "tool_count": len(tools),
                    "tool_ids": [t.id for t in tools],
                }
        return categories

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all available tools with their basic info."""
        return [self._tool_to_dict(tool) for tool in ALL_TOOLS]

    def get_essential_tools(self) -> list[dict[str, Any]]:
        """Get essential tools list."""
        return [self._tool_to_dict(tool) for tool in ESSENTIAL_TOOLS]

    def get_tools_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get tools for a specific category."""
        try:
            cat = ToolCategory(category)
            tools = get_tools_by_category(cat)
            return [self._tool_to_dict(tool) for tool in tools]
        except ValueError:
            return []

    def get_mise_managed_tools(self) -> list[dict[str, Any]]:
        """Get tools that are managed by Mise."""
        tools = get_mise_managed_tools()
        return [self._tool_to_dict(tool) for tool in tools]

    def get_tool(self, tool_id: str) -> dict[str, Any] | None:
        """Get a specific tool by ID."""
        tool = get_tool_by_id(tool_id)
        if tool:
            return self._tool_to_dict(tool)
        return None

    def detect_tool(self, tool_id: str) -> dict[str, Any]:
        """Detect installation status of a specific tool."""
        tool = get_tool_by_id(tool_id)
        if not tool:
            return {"error": f"Unknown tool: {tool_id}"}

        detector = self._get_detector()
        status = detector.detect_tool(tool)

        return {
            "tool_id": tool.id,
            "name": tool.name,
            "status": status.status.value,
            "version": status.version,
            "path": status.path,
            "install_methods": [m.value for m in status.install_methods],
        }

    def detect_all_tools(self) -> list[dict[str, Any]]:
        """Detect installation status of all tools."""
        detector = self._get_detector()
        results = []

        for tool in ALL_TOOLS:
            status = detector.detect_tool(tool)
            results.append({
                "tool_id": tool.id,
                "name": tool.name,
                "category": tool.category.value,
                "status": status.status.value,
                "version": status.version,
                "install_methods": [m.value for m in status.install_methods],
            })

        return results

    def detect_essential_tools(self) -> list[dict[str, Any]]:
        """Detect installation status of essential tools."""
        detector = self._get_detector()
        results = []

        for tool in ESSENTIAL_TOOLS:
            status = detector.detect_tool(tool)
            results.append({
                "tool_id": tool.id,
                "name": tool.name,
                "category": tool.category.value,
                "status": status.status.value,
                "version": status.version,
                "install_methods": [m.value for m in status.install_methods],
            })

        return results

    def get_install_methods(self, tool_id: str) -> dict[str, Any]:
        """Get available installation methods for a tool."""
        tool = get_tool_by_id(tool_id)
        if not tool:
            return {"error": f"Unknown tool: {tool_id}"}

        detector = self._get_detector()
        status = detector.detect_tool(tool)

        methods = []
        for pm in status.install_methods:
            method_info = {
                "method": pm.value,
                "available": True,
                "package": self._get_package_name(tool, pm),
            }

            # Add specific info for each method
            if pm == PackageManager.BREW:
                method_info["is_cask"] = tool.brew_cask
            elif pm == PackageManager.SNAP:
                method_info["classic"] = tool.snap_classic
            elif pm == PackageManager.MISE:
                method_info["managed_by_mise"] = True

            methods.append(method_info)

        return {
            "tool_id": tool.id,
            "name": tool.name,
            "methods": methods,
            "recommended": methods[0]["method"] if methods else None,
        }

    def install(self, tool_id: str, method: str | None = None) -> dict[str, Any]:
        """Install a tool using the specified or best available method."""
        tool = get_tool_by_id(tool_id)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_id}"}

        preferred_method = None
        if method:
            try:
                preferred_method = PackageManager(method)
            except ValueError:
                return {"success": False, "error": f"Unknown installation method: {method}"}

        # Run the async install in a sync context
        try:
            result = asyncio.run(
                install_tool(
                    tool=tool,
                    platform_info=self._get_platform_info(),
                    preferred_method=preferred_method,
                )
            )
            return {
                "success": result.success,
                "message": result.message,
                "version": result.version,
                "error_details": result.error_details,
                "requires_restart": result.requires_restart,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def install_multiple(self, tool_ids: list[str]) -> dict[str, Any]:
        """Install multiple tools."""
        results = []
        for tool_id in tool_ids:
            result = self.install(tool_id)
            results.append({
                "tool_id": tool_id,
                **result,
            })

        success_count = sum(1 for r in results if r.get("success"))
        return {
            "total": len(tool_ids),
            "success_count": success_count,
            "failed_count": len(tool_ids) - success_count,
            "results": results,
        }

    def check_mise_available(self) -> dict[str, Any]:
        """Check if Mise is installed and available."""
        from devflow.providers.installers.mise import MiseInstaller

        mise = MiseInstaller(self._get_platform_info())

        try:
            available = asyncio.run(mise.is_available())
            version = None
            if available:
                version = asyncio.run(mise.get_mise_version())

            return {
                "available": available,
                "version": version,
                "install_hint": "curl https://mise.run | sh" if not available else None,
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }

    def get_mise_installed_tools(self) -> dict[str, Any]:
        """Get all tools installed via Mise."""
        from devflow.providers.installers.mise import MiseInstaller

        mise = MiseInstaller(self._get_platform_info())

        try:
            if not asyncio.run(mise.is_available()):
                return {"error": "Mise is not installed"}

            tools = asyncio.run(mise.list_installed())
            return {
                "success": True,
                "tools": tools,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_available_installers(self) -> list[dict[str, Any]]:
        """Get all available installers for the current platform."""
        installers = get_available_installers(self._get_platform_info())
        return [
            {
                "package_manager": i.package_manager.value,
                "name": i.package_manager.name.replace("_", " ").title(),
            }
            for i in installers
        ]

    def refresh_platform_info(self) -> dict[str, Any]:
        """Refresh cached platform info."""
        self._platform_info = None
        self._tool_detector = None
        return self.get_platform_info()

    def get_prerequisites_summary(self) -> dict[str, Any]:
        """Get a summary of all prerequisites status."""
        detector = self._get_detector()

        summary = {
            "total": len(ALL_TOOLS),
            "installed": 0,
            "not_installed": 0,
            "outdated": 0,
            "by_category": {},
        }

        for tool in ALL_TOOLS:
            status = detector.detect_tool(tool)

            if status.status == InstallStatus.INSTALLED:
                summary["installed"] += 1
            elif status.status == InstallStatus.NOT_INSTALLED:
                summary["not_installed"] += 1
            elif status.status == InstallStatus.OUTDATED:
                summary["outdated"] += 1

            cat = tool.category.value
            if cat not in summary["by_category"]:
                summary["by_category"][cat] = {
                    "total": 0,
                    "installed": 0,
                }
            summary["by_category"][cat]["total"] += 1
            if status.status in (InstallStatus.INSTALLED, InstallStatus.OUTDATED):
                summary["by_category"][cat]["installed"] += 1

        return summary

    def _tool_to_dict(self, tool: ToolInfo) -> dict[str, Any]:
        """Convert a ToolInfo to a dictionary."""
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "category": tool.category.value,
            "command": tool.binary,
            "website": tool.website,
            "essential": tool.is_essential,
            "mise_managed": tool.managed_by_mise,
            "install_methods": {
                "brew_package": tool.brew_package,
                "brew_cask": tool.brew_cask,
                "apt_package": tool.apt_package,
                "snap_package": tool.snap_package,
                "snap_classic": tool.snap_classic,
                "winget_id": tool.winget_id,
                "scoop_package": tool.scoop_package,
                "mise_package": tool.mise_package,
                "npm_package": tool.npm_package,
            },
        }

    def _get_package_name(self, tool: ToolInfo, method: PackageManager) -> str | None:
        """Get the package name for a specific installation method."""
        method_to_attr = {
            PackageManager.BREW: "brew_cask" if tool.brew_cask else "brew_package",
            PackageManager.APT: "apt_package",
            PackageManager.SNAP: "snap_package",
            PackageManager.WINGET: "winget_id",
            PackageManager.SCOOP: "scoop_package",
            PackageManager.MISE: "mise_package",
            PackageManager.NPM: "npm_package",
        }

        attr = method_to_attr.get(method)
        if attr:
            return getattr(tool, attr, None)
        return None
