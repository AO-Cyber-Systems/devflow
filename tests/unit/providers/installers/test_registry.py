"""Tests for tool registry."""

import pytest

from devflow.providers.installers.base import ToolCategory, ToolInfo
from devflow.providers.installers.registry import (
    ALL_TOOLS,
    ESSENTIAL_TOOLS,
    TOOLS_BY_CATEGORY,
    get_mise_managed_tools,
    get_tool_by_id,
    get_tools_by_category,
)


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_all_tools_not_empty(self) -> None:
        """Test that ALL_TOOLS contains tools."""
        assert len(ALL_TOOLS) > 0

    def test_essential_tools_not_empty(self) -> None:
        """Test that ESSENTIAL_TOOLS contains tools."""
        assert len(ESSENTIAL_TOOLS) > 0

    def test_essential_tools_subset_of_all(self) -> None:
        """Test that essential tools are a subset of all tools."""
        essential_ids = {t.id for t in ESSENTIAL_TOOLS}
        all_ids = {t.id for t in ALL_TOOLS}
        assert essential_ids.issubset(all_ids)

    def test_all_tools_have_required_fields(self) -> None:
        """Test that all tools have required fields populated."""
        for tool in ALL_TOOLS:
            assert tool.id, f"Tool missing id: {tool}"
            assert tool.name, f"Tool {tool.id} missing name"
            assert tool.description, f"Tool {tool.id} missing description"
            assert tool.category, f"Tool {tool.id} missing category"
            assert tool.website, f"Tool {tool.id} missing website"
            assert tool.icon, f"Tool {tool.id} missing icon"

    def test_tool_ids_are_unique(self) -> None:
        """Test that all tool IDs are unique."""
        ids = [t.id for t in ALL_TOOLS]
        assert len(ids) == len(set(ids)), "Duplicate tool IDs found"

    def test_tools_by_category_complete(self) -> None:
        """Test that TOOLS_BY_CATEGORY contains all categories."""
        for category in ToolCategory:
            assert category in TOOLS_BY_CATEGORY

    def test_all_tools_in_category_mapping(self) -> None:
        """Test that all tools appear in TOOLS_BY_CATEGORY."""
        category_tools = set()
        for tools in TOOLS_BY_CATEGORY.values():
            category_tools.update(t.id for t in tools)

        all_tool_ids = {t.id for t in ALL_TOOLS}
        assert category_tools == all_tool_ids


class TestGetToolById:
    """Tests for get_tool_by_id function."""

    def test_get_existing_tool(self) -> None:
        """Test getting an existing tool by ID."""
        tool = get_tool_by_id("git")
        assert tool is not None
        assert tool.id == "git"
        assert tool.name == "Git"

    def test_get_nonexistent_tool(self) -> None:
        """Test getting a non-existent tool returns None."""
        tool = get_tool_by_id("nonexistent-tool")
        assert tool is None

    def test_get_tool_case_sensitive(self) -> None:
        """Test that tool lookup is case-sensitive."""
        tool = get_tool_by_id("GIT")
        assert tool is None  # IDs should be lowercase


class TestGetToolsByCategory:
    """Tests for get_tools_by_category function."""

    def test_get_code_editors(self) -> None:
        """Test getting code editor tools."""
        tools = get_tools_by_category(ToolCategory.CODE_EDITOR)
        assert len(tools) > 0
        for tool in tools:
            assert tool.category == ToolCategory.CODE_EDITOR

    def test_get_runtimes(self) -> None:
        """Test getting runtime tools."""
        tools = get_tools_by_category(ToolCategory.RUNTIME)
        assert len(tools) > 0
        for tool in tools:
            assert tool.category == ToolCategory.RUNTIME

    def test_get_cli_utilities(self) -> None:
        """Test getting CLI utility tools."""
        tools = get_tools_by_category(ToolCategory.CLI_UTILITY)
        assert len(tools) > 0
        for tool in tools:
            assert tool.category == ToolCategory.CLI_UTILITY

    def test_empty_category_returns_empty_list(self) -> None:
        """Test that an empty category returns an empty list."""
        # All categories should have at least some tools in our registry
        # This tests the function behavior with the actual data
        for category in ToolCategory:
            tools = get_tools_by_category(category)
            assert isinstance(tools, list)


class TestGetMiseManagedTools:
    """Tests for get_mise_managed_tools function."""

    def test_mise_managed_tools_not_empty(self) -> None:
        """Test that there are Mise-managed tools."""
        tools = get_mise_managed_tools()
        assert len(tools) > 0

    def test_all_mise_tools_have_mise_package(self) -> None:
        """Test that all Mise-managed tools have a mise_package."""
        tools = get_mise_managed_tools()
        for tool in tools:
            assert tool.managed_by_mise is True
            assert tool.mise_package is not None, f"Tool {tool.id} marked as managed_by_mise but has no mise_package"

    def test_mise_tools_are_runtimes(self) -> None:
        """Test that Mise-managed tools are primarily runtimes."""
        tools = get_mise_managed_tools()
        # At least some should be runtimes
        runtime_tools = [t for t in tools if t.category == ToolCategory.RUNTIME]
        assert len(runtime_tools) > 0


class TestSpecificTools:
    """Tests for specific tools in the registry."""

    def test_git_tool(self) -> None:
        """Test Git tool definition."""
        git = get_tool_by_id("git")
        assert git is not None
        assert git.binary == "git"
        assert git.category == ToolCategory.VERSION_CONTROL
        assert git.is_essential is True
        assert git.apt_package == "git"
        assert git.brew_package == "git"

    def test_vscode_tool(self) -> None:
        """Test VS Code tool definition."""
        vscode = get_tool_by_id("vscode")
        assert vscode is not None
        assert vscode.binary == "code"
        assert vscode.category == ToolCategory.CODE_EDITOR
        assert vscode.brew_cask == "visual-studio-code"
        assert vscode.winget_id is not None

    def test_docker_tool(self) -> None:
        """Test Docker tool definition."""
        docker = get_tool_by_id("docker")
        assert docker is not None
        assert docker.binary == "docker"
        assert docker.category == ToolCategory.CONTAINER
        assert docker.is_essential is True

    def test_nodejs_tool(self) -> None:
        """Test Node.js tool definition."""
        node = get_tool_by_id("nodejs")
        assert node is not None
        assert node.binary == "node"
        assert node.category == ToolCategory.RUNTIME
        assert node.managed_by_mise is True
        assert node.mise_package == "node"

    def test_python_tool(self) -> None:
        """Test Python tool definition."""
        python = get_tool_by_id("python")
        assert python is not None
        assert python.binary == "python3"
        assert python.category == ToolCategory.RUNTIME
        assert python.managed_by_mise is True
        assert python.mise_package == "python"

    def test_gh_tool(self) -> None:
        """Test GitHub CLI tool definition."""
        gh = get_tool_by_id("gh")
        assert gh is not None
        assert gh.binary == "gh"
        assert gh.category == ToolCategory.VERSION_CONTROL
        assert gh.is_essential is True

    def test_ripgrep_tool(self) -> None:
        """Test ripgrep tool definition."""
        rg = get_tool_by_id("ripgrep")
        assert rg is not None
        assert rg.binary == "rg"
        assert rg.category == ToolCategory.CLI_UTILITY
        assert rg.apt_package == "ripgrep"
        assert rg.brew_package == "ripgrep"


class TestToolInfo:
    """Tests for ToolInfo dataclass."""

    def test_tool_info_creation(self) -> None:
        """Test creating a ToolInfo instance."""
        tool = ToolInfo(
            id="test-tool",
            name="Test Tool",
            description="A test tool",
            category=ToolCategory.CLI_UTILITY,
            website="https://example.com",
            icon="terminal",
            binary="test",
        )
        assert tool.id == "test-tool"
        assert tool.name == "Test Tool"
        assert tool.is_essential is False  # default
        assert tool.managed_by_mise is False  # default

    def test_tool_info_with_packages(self) -> None:
        """Test ToolInfo with package definitions."""
        tool = ToolInfo(
            id="test-tool",
            name="Test Tool",
            description="A test tool",
            category=ToolCategory.CLI_UTILITY,
            website="https://example.com",
            icon="terminal",
            binary="test",
            brew_package="test",
            apt_package="test",
            winget_id="Test.Tool",
        )
        assert tool.brew_package == "test"
        assert tool.apt_package == "test"
        assert tool.winget_id == "Test.Tool"
        assert tool.brew_cask is None  # not set

    def test_tool_info_mise_managed(self) -> None:
        """Test ToolInfo for Mise-managed tool."""
        tool = ToolInfo(
            id="test-runtime",
            name="Test Runtime",
            description="A test runtime",
            category=ToolCategory.RUNTIME,
            website="https://example.com",
            icon="cpu",
            binary="test",
            managed_by_mise=True,
            mise_package="test",
        )
        assert tool.managed_by_mise is True
        assert tool.mise_package == "test"
