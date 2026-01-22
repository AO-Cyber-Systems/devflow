"""Tests for config commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from devflow.commands.config import app, _parse_value, _get_nested_value, _set_nested_value


runner = CliRunner()


class TestParseValue:
    """Tests for _parse_value helper function."""

    def test_parse_true(self) -> None:
        """Test parsing boolean true."""
        assert _parse_value("true") is True
        assert _parse_value("True") is True
        assert _parse_value("TRUE") is True

    def test_parse_false(self) -> None:
        """Test parsing boolean false."""
        assert _parse_value("false") is False
        assert _parse_value("False") is False
        assert _parse_value("FALSE") is False

    def test_parse_integer(self) -> None:
        """Test parsing integer."""
        assert _parse_value("42") == 42
        assert _parse_value("0") == 0
        assert _parse_value("-10") == -10

    def test_parse_float(self) -> None:
        """Test parsing float."""
        assert _parse_value("3.14") == 3.14
        assert _parse_value("-2.5") == -2.5

    def test_parse_json_array(self) -> None:
        """Test parsing JSON array."""
        result = _parse_value('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_json_object(self) -> None:
        """Test parsing JSON object."""
        result = _parse_value('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_string(self) -> None:
        """Test parsing plain string."""
        assert _parse_value("hello") == "hello"
        assert _parse_value("my-value") == "my-value"
        assert _parse_value("/path/to/file") == "/path/to/file"

    def test_parse_invalid_json_as_string(self) -> None:
        """Test that invalid JSON is returned as string."""
        assert _parse_value("[invalid") == "[invalid"
        assert _parse_value("{not: json}") == "{not: json}"


class TestNestedValueFunctions:
    """Tests for nested value helper functions."""

    def test_get_nested_value_simple(self) -> None:
        """Test getting simple nested value."""
        data = {"a": {"b": {"c": "value"}}}
        assert _get_nested_value(data, ["a", "b", "c"]) == "value"

    def test_get_nested_value_missing(self) -> None:
        """Test getting missing nested value."""
        data = {"a": {"b": "value"}}
        assert _get_nested_value(data, ["a", "c"]) is None
        assert _get_nested_value(data, ["x", "y", "z"]) is None

    def test_get_nested_value_non_dict(self) -> None:
        """Test getting nested value when path traverses non-dict."""
        data = {"a": "not_a_dict"}
        assert _get_nested_value(data, ["a", "b"]) is None

    def test_set_nested_value_simple(self) -> None:
        """Test setting simple nested value."""
        data = {"a": {"b": {}}}
        _set_nested_value(data, ["a", "b", "c"], "new_value")
        assert data["a"]["b"]["c"] == "new_value"

    def test_set_nested_value_creates_intermediates(self) -> None:
        """Test setting nested value creates intermediate dicts."""
        data = {}
        _set_nested_value(data, ["a", "b", "c"], "value")
        assert data == {"a": {"b": {"c": "value"}}}

    def test_set_nested_value_overwrites(self) -> None:
        """Test setting nested value overwrites existing."""
        data = {"a": {"b": "old"}}
        _set_nested_value(data, ["a", "b"], "new")
        assert data["a"]["b"] == "new"


class TestConfigShowCommand:
    """Tests for config show command."""

    def test_show_no_config(self, tmp_path: Path) -> None:
        """Test show fails without config file."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = runner.invoke(app, ["show"])
            assert result.exit_code == 1
            assert "devflow.yml" in result.output
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.load_project_config")
    def test_show_with_config(
        self,
        mock_load_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test show displays config."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: "1"
project:
  name: test
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_load_config.return_value = MagicMock()

            result = runner.invoke(app, ["show"])
            assert result.exit_code == 0
        finally:
            os.chdir(original_dir)


class TestConfigValidateCommand:
    """Tests for config validate command."""

    def test_validate_no_config(self, tmp_path: Path) -> None:
        """Test validate fails without config file."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = runner.invoke(app, ["validate"])
            assert result.exit_code == 1
            assert "devflow.yml" in result.output
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_validate_with_errors(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test validate shows errors."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            (tmp_path / "devflow.yml").write_text("version: '1'")
            mock_validate.return_value = ["Missing required field: project.name"]

            result = runner.invoke(app, ["validate"])
            assert result.exit_code == 1
            assert "errors" in result.output.lower()
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_validate_success(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test validate succeeds."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            (tmp_path / "devflow.yml").write_text("version: '1'")
            mock_validate.return_value = []

            result = runner.invoke(app, ["validate"])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()
        finally:
            os.chdir(original_dir)


class TestConfigEnvCommand:
    """Tests for config env command."""

    @patch("devflow.core.config.get_current_env")
    def test_env_show_current(self, mock_get_env: MagicMock) -> None:
        """Test showing current environment."""
        mock_get_env.return_value = "local"

        result = runner.invoke(app, ["env"])
        assert "local" in result.output

    @patch("devflow.core.config.set_current_env")
    def test_env_switch(self, mock_set_env: MagicMock) -> None:
        """Test switching environment."""
        result = runner.invoke(app, ["env", "staging"])

        mock_set_env.assert_called_once_with("staging")
        assert "staging" in result.output


class TestConfigSetCommand:
    """Tests for config set command."""

    def test_set_no_config(self, tmp_path: Path) -> None:
        """Test set fails without config file."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = runner.invoke(app, ["set", "project.name", "test", "--json"])
            output = json.loads(result.output)
            assert output["success"] is False
            assert "devflow.yml" in output["error"]
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_string_value(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setting string value."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
project:
  name: old_name
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "project.name", "new_name", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert output["old_value"] == "old_name"
            assert output["new_value"] == "new_name"
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_boolean_value(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setting boolean value."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
infrastructure:
  enabled: false
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "infrastructure.enabled", "true", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert output["new_value"] is True
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_integer_value(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setting integer value."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
settings:
  timeout: 30
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "settings.timeout", "60", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert output["new_value"] == 60
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_creates_nested_keys(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setting value creates nested keys."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "database.migrations.directory", "migrations", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert output["new_value"] == "migrations"
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_json_array(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setting JSON array value."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "settings.tags", '["tag1", "tag2"]', "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert output["new_value"] == ["tag1", "tag2"]
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_validation_failure(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test set fails when validation fails."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
project:
  name: test
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = ["Invalid configuration: missing required field"]

            result = runner.invoke(app, ["set", "project.name", "", "--json"])
            output = json.loads(result.output)

            assert output["success"] is False
            assert "validation" in output["error"].lower()
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.validate_config")
    def test_set_non_json_output(
        self,
        mock_validate: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test set with human-readable output."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            config_content = """version: '1'
project:
  name: old_name
"""
            (tmp_path / "devflow.yml").write_text(config_content)
            mock_validate.return_value = []

            result = runner.invoke(app, ["set", "project.name", "new_name"])

            assert result.exit_code == 0
            assert "Updated" in result.output
            assert "old_name" in result.output
            assert "new_name" in result.output
        finally:
            os.chdir(original_dir)
