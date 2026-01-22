"""Tests for ComposeTransformer."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from devflow.core.config import InfrastructureConfig
from devflow.infrastructure.compose_transformer import ComposeTransformer, TransformResult


class TestComposeTransformer:
    """Tests for ComposeTransformer class."""

    def test_default_config(self) -> None:
        """Test transformer with default config."""
        transformer = ComposeTransformer()
        assert transformer.config.network_name == "devflow-proxy"

    def test_custom_config(self) -> None:
        """Test transformer with custom config."""
        config = InfrastructureConfig(network_name="custom-network")
        transformer = ComposeTransformer(config)
        assert transformer.config.network_name == "custom-network"

    def test_transform_nonexistent_file(self, tmp_path: Path) -> None:
        """Test transformation of non-existent file."""
        transformer = ComposeTransformer()
        result = transformer.transform(tmp_path / "nonexistent.yml")

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_transform_empty_file(self, tmp_path: Path) -> None:
        """Test transformation of empty file."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("")

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is False
        assert "empty" in result.message.lower()

    def test_transform_invalid_yaml(self, tmp_path: Path) -> None:
        """Test transformation of invalid YAML file."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("invalid: yaml: content:")

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is False
        assert "yaml" in result.message.lower()

    def test_transform_no_changes_needed(self, tmp_path: Path) -> None:
        """Test transformation when file is already configured."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "networks": ["devflow-proxy"],
                }
            },
            "networks": {
                "devflow-proxy": {
                    "external": True,
                    "name": "devflow-proxy",
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file, dry_run=True)

        assert result.success is True
        assert "no changes" in result.message.lower()

    def test_transform_network_replacement(self, tmp_path: Path) -> None:
        """Test network replacement from proxy to devflow-proxy."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "networks": ["proxy"],
                }
            },
            "networks": {
                "proxy": {
                    "external": True,
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file, dry_run=True)

        assert result.success is True
        assert len(result.changes) > 0
        assert any("proxy" in change.lower() for change in result.changes)

    def test_transform_service_network_update(self, tmp_path: Path) -> None:
        """Test service network references are updated."""
        compose_content = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "networks": ["proxy", "internal"],
                },
                "api": {
                    "image": "myapi:latest",
                    "networks": ["proxy"],
                },
            },
            "networks": {
                "proxy": {"external": True},
                "internal": {},
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is True

        # Read back the file and verify
        with open(compose_file) as f:
            updated = yaml.safe_load(f)

        assert "devflow-proxy" in updated["services"]["web"]["networks"]
        assert "devflow-proxy" in updated["services"]["api"]["networks"]
        assert "internal" in updated["services"]["web"]["networks"]

    def test_transform_removes_traefik_service(self, tmp_path: Path) -> None:
        """Test that embedded Traefik service is removed."""
        compose_content = {
            "version": "3.8",
            "services": {
                "traefik": {
                    "image": "traefik:v3.0",
                    "ports": ["80:80", "443:443"],
                },
                "app": {
                    "image": "myapp:latest",
                    "networks": ["proxy"],
                },
            },
            "networks": {
                "proxy": {"external": True},
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is True
        assert any("traefik" in change.lower() for change in result.changes)
        assert len(result.warnings) > 0  # Should warn about removed Traefik

        # Verify Traefik was removed
        with open(compose_file) as f:
            updated = yaml.safe_load(f)

        assert "traefik" not in updated["services"]
        assert "app" in updated["services"]

    def test_transform_creates_backup(self, tmp_path: Path) -> None:
        """Test that backup is created before transformation."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "networks": ["proxy"],
                }
            },
            "networks": {
                "proxy": {"external": True},
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is True
        assert result.backup_path is not None
        assert Path(result.backup_path).exists()

    def test_backup_and_restore(self, tmp_path: Path) -> None:
        """Test backup creation and restoration."""
        original_content = "version: '3.8'\nservices:\n  app:\n    image: test\n"
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(original_content)

        transformer = ComposeTransformer()

        # Create backup
        backup_path = transformer.backup(compose_file)
        assert backup_path.exists()

        # Modify original
        compose_file.write_text("modified: content\n")

        # Restore
        success = transformer.restore(compose_file)
        assert success is True
        assert compose_file.read_text() == original_content

    def test_restore_no_backup(self, tmp_path: Path) -> None:
        """Test restore when no backup exists."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\n")

        transformer = ComposeTransformer()
        success = transformer.restore(compose_file)

        assert success is False

    def test_get_backups(self, tmp_path: Path) -> None:
        """Test getting list of backup files."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\n")

        transformer = ComposeTransformer()

        # Create a backup
        backup1 = transformer.backup(compose_file)

        # Create another backup with a different timestamp by manually creating it
        # (The backup filename includes timestamp, so we need different seconds)
        backup2 = tmp_path / f"{compose_file.name}.devflow-backup.20991231_235959"
        backup2.write_text("version: '3.8'\n")

        backups = transformer.get_backups(compose_file)

        assert len(backups) == 2
        # Should be sorted newest first (by mtime, not filename)
        assert backup2 in backups
        assert backup1 in backups

    def test_validate_correct_file(self, tmp_path: Path) -> None:
        """Test validation of correctly configured file."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "networks": ["devflow-proxy"],
                }
            },
            "networks": {
                "devflow-proxy": {
                    "external": True,
                    "name": "devflow-proxy",
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        errors = transformer.validate(compose_file)

        assert len(errors) == 0

    def test_validate_missing_network(self, tmp_path: Path) -> None:
        """Test validation catches missing network."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        errors = transformer.validate(compose_file)

        assert len(errors) > 0
        assert any("network" in e.message.lower() for e in errors)


class TestDomainDetection:
    """Tests for domain detection from Traefik labels."""

    def test_detect_domains_host_rule(self, tmp_path: Path) -> None:
        """Test detection of domains from Host() rules."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "labels": [
                        "traefik.http.routers.app.rule=Host(`app.localhost`)",
                    ],
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        domains = transformer.detect_domains(compose_file)

        assert "app.localhost" in domains

    def test_detect_domains_multiple_hosts(self, tmp_path: Path) -> None:
        """Test detection of multiple domains."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "labels": [
                        "traefik.http.routers.app.rule=Host(`app.localhost`,`www.app.localhost`)",
                    ],
                },
                "api": {
                    "image": "myapi:latest",
                    "labels": {
                        "traefik.http.routers.api.rule": "Host(`api.localhost`)",
                    },
                },
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        domains = transformer.detect_domains(compose_file)

        assert "app.localhost" in domains
        assert "www.app.localhost" in domains
        assert "api.localhost" in domains

    def test_detect_domains_no_labels(self, tmp_path: Path) -> None:
        """Test detection when no labels exist."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        domains = transformer.detect_domains(compose_file)

        assert domains == []

    def test_detect_domains_nonexistent_file(self, tmp_path: Path) -> None:
        """Test detection on non-existent file."""
        transformer = ComposeTransformer()
        domains = transformer.detect_domains(tmp_path / "nonexistent.yml")

        assert domains == []


class TestNetworkTransformation:
    """Tests for network transformation logic."""

    def test_transform_aosentry_proxy_network(self, tmp_path: Path) -> None:
        """Test transformation of aosentry-proxy network."""
        compose_content = {
            "version": "3.8",
            "services": {
                "proxy": {
                    "image": "aosentry-proxy:latest",
                    "networks": ["aosentry-proxy"],
                }
            },
            "networks": {
                "aosentry-proxy": {
                    "external": True,
                }
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        # Use config with aosentry-proxy as an alias
        config = InfrastructureConfig(
            legacy_networks=["proxy", "aosentry-proxy"],
        )
        transformer = ComposeTransformer(config)
        result = transformer.transform(compose_file)

        assert result.success is True

        with open(compose_file) as f:
            updated = yaml.safe_load(f)

        assert "devflow-proxy" in updated["networks"]
        assert "aosentry-proxy" not in updated["networks"]
        assert "devflow-proxy" in updated["services"]["proxy"]["networks"]

    def test_transform_dict_style_networks(self, tmp_path: Path) -> None:
        """Test transformation of dict-style network definitions in services."""
        compose_content = {
            "version": "3.8",
            "services": {
                "app": {
                    "image": "myapp:latest",
                    "networks": {
                        "proxy": {
                            "aliases": ["myapp"],
                        },
                    },
                }
            },
            "networks": {
                "proxy": {"external": True},
            },
        }

        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text(yaml.dump(compose_content))

        transformer = ComposeTransformer()
        result = transformer.transform(compose_file)

        assert result.success is True

        with open(compose_file) as f:
            updated = yaml.safe_load(f)

        # Should preserve the aliases config under new network name
        assert "devflow-proxy" in updated["services"]["app"]["networks"]
        network_config = updated["services"]["app"]["networks"]["devflow-proxy"]
        assert network_config["aliases"] == ["myapp"]
