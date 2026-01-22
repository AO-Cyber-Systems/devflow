"""Tests for mkcert provider."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from devflow.providers.mkcert import MkcertProvider


class TestMkcertProvider:
    """Tests for mkcert CLI provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = MkcertProvider()
        assert provider.name == "mkcert"
        assert provider.binary == "mkcert"

    def test_is_available(self) -> None:
        """Test availability check."""
        provider = MkcertProvider()
        result = provider.is_available()
        assert isinstance(result, bool)

    @patch("shutil.which")
    def test_is_available_when_installed(self, mock_which: MagicMock) -> None:
        """Test availability when mkcert is installed."""
        mock_which.return_value = "/usr/local/bin/mkcert"
        provider = MkcertProvider()
        assert provider.is_available() is True

    @patch("shutil.which")
    def test_is_available_when_not_installed(self, mock_which: MagicMock) -> None:
        """Test availability when mkcert is not installed."""
        mock_which.return_value = None
        provider = MkcertProvider()
        assert provider.is_available() is False

    @patch("subprocess.run")
    def test_get_ca_root_success(self, mock_run: MagicMock) -> None:
        """Test successful CA root retrieval."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/home/user/.local/share/mkcert\n",
        )

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.get_ca_root()

        assert result == "/home/user/.local/share/mkcert"

    @patch("subprocess.run")
    def test_get_ca_root_failure(self, mock_run: MagicMock) -> None:
        """Test CA root retrieval failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.get_ca_root()

        assert result is None

    def test_get_ca_root_not_available(self) -> None:
        """Test CA root when mkcert not available."""
        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=False):
            result = provider.get_ca_root()
        assert result is None

    @patch("subprocess.run")
    def test_is_ca_installed_success(self, mock_run: MagicMock) -> None:
        """Test CA installation check when installed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/tmp/mkcert_test\n",
        )

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            with patch("pathlib.Path.exists", return_value=True):
                result = provider.is_ca_installed()

        assert result is True

    @patch("subprocess.run")
    def test_is_ca_installed_no_rootca(self, mock_run: MagicMock) -> None:
        """Test CA installation check when rootCA.pem doesn't exist."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/tmp/mkcert_test\n",
        )

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            with patch("pathlib.Path.exists", return_value=False):
                result = provider.is_ca_installed()

        assert result is False

    def test_is_ca_installed_not_available(self) -> None:
        """Test CA installation check when mkcert not available."""
        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=False):
            result = provider.is_ca_installed()
        assert result is False

    @patch("subprocess.run")
    def test_install_ca_success(self, mock_run: MagicMock) -> None:
        """Test successful CA installation."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            success, message = provider.install_ca()

        assert success is True
        assert "successfully" in message.lower()

    @patch("subprocess.run")
    def test_install_ca_failure(self, mock_run: MagicMock) -> None:
        """Test CA installation failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Permission denied",
        )

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            success, message = provider.install_ca()

        assert success is False
        assert "Permission denied" in message

    def test_install_ca_not_available(self) -> None:
        """Test CA installation when mkcert not available."""
        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=False):
            success, message = provider.install_ca()

        assert success is False
        assert "not installed" in message.lower()

    @patch("subprocess.run")
    def test_generate_cert_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test successful certificate generation."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "is_ca_installed", return_value=True):
                success, message = provider.generate_cert(
                    domains=["*.localhost", "localhost"],
                    output_dir=str(tmp_path),
                )

        assert success is True
        assert "generated" in message.lower()

    @patch("subprocess.run")
    def test_generate_cert_failure(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test certificate generation failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Failed to generate",
        )

        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "is_ca_installed", return_value=True):
                success, message = provider.generate_cert(
                    domains=["*.localhost"],
                    output_dir=str(tmp_path),
                )

        assert success is False
        assert "Failed" in message

    def test_generate_cert_not_available(self, tmp_path: Path) -> None:
        """Test cert generation when mkcert not available."""
        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=False):
            success, message = provider.generate_cert(
                domains=["*.localhost"],
                output_dir=str(tmp_path),
            )

        assert success is False
        assert "not installed" in message.lower()

    def test_generate_cert_ca_not_installed(self, tmp_path: Path) -> None:
        """Test cert generation when CA not installed."""
        provider = MkcertProvider()
        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "is_ca_installed", return_value=False):
                success, message = provider.generate_cert(
                    domains=["*.localhost"],
                    output_dir=str(tmp_path),
                )

        assert success is False
        assert "CA" in message

    def test_cert_exists_true(self, tmp_path: Path) -> None:
        """Test cert existence check when files exist."""
        # Create mock cert files
        (tmp_path / "cert.pem").write_text("cert content")
        (tmp_path / "key.pem").write_text("key content")

        provider = MkcertProvider()
        result = provider.cert_exists(str(tmp_path))

        assert result is True

    def test_cert_exists_false(self, tmp_path: Path) -> None:
        """Test cert existence check when files don't exist."""
        provider = MkcertProvider()
        result = provider.cert_exists(str(tmp_path))

        assert result is False

    def test_cert_exists_partial(self, tmp_path: Path) -> None:
        """Test cert existence check when only cert exists."""
        (tmp_path / "cert.pem").write_text("cert content")

        provider = MkcertProvider()
        result = provider.cert_exists(str(tmp_path))

        assert result is False

    def test_doctor_output(self) -> None:
        """Test doctor output includes mkcert-specific fields."""
        provider = MkcertProvider()
        with patch.object(provider, "is_ca_installed", return_value=True):
            with patch.object(provider, "get_ca_root", return_value="/path/to/ca"):
                status = provider.doctor()

        assert "name" in status
        assert "binary" in status
        assert "available" in status
        assert "ca_installed" in status
        assert "ca_root" in status
        assert status["name"] == "mkcert"
        assert status["binary"] == "mkcert"
