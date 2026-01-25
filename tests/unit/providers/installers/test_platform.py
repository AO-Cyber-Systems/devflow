"""Tests for platform detection utilities."""

from unittest.mock import MagicMock, patch

import pytest

from devflow.providers.installers.platform import (
    Architecture,
    LinuxDistro,
    OperatingSystem,
    PackageManager,
    PlatformInfo,
    _detect_architecture,
    _detect_linux_distro,
    _detect_os,
    _detect_package_managers,
    _detect_wsl,
    check_command_exists,
    detect_platform,
    get_command_path,
    get_command_version,
    refresh_platform_info,
)


class TestOperatingSystemDetection:
    """Tests for OS detection."""

    def test_detect_macos(self) -> None:
        """Test macOS detection."""
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.mac_ver", return_value=("14.0", ("", "", ""), "")):
                os_type, version = _detect_os()
                assert os_type == OperatingSystem.MACOS
                assert version == "14.0"

    def test_detect_linux(self) -> None:
        """Test Linux detection."""
        with patch("platform.system", return_value="Linux"):
            with patch("platform.release", return_value="5.15.0"):
                os_type, version = _detect_os()
                assert os_type == OperatingSystem.LINUX
                assert version == "5.15.0"

    def test_detect_windows(self) -> None:
        """Test Windows detection."""
        with patch("platform.system", return_value="Windows"):
            with patch("platform.win32_ver", return_value=("10", "", "", "")):
                os_type, version = _detect_os()
                assert os_type == OperatingSystem.WINDOWS
                assert version == "10"

    def test_detect_unknown(self) -> None:
        """Test unknown OS detection."""
        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.release", return_value="13.0"):
                os_type, version = _detect_os()
                assert os_type == OperatingSystem.UNKNOWN
                assert version == "13.0"


class TestWSLDetection:
    """Tests for WSL detection."""

    def test_not_wsl_on_non_linux(self) -> None:
        """Test WSL detection returns False on non-Linux."""
        with patch("platform.system", return_value="Darwin"):
            assert _detect_wsl() is False

    def test_wsl_detected_via_proc_version(self) -> None:
        """Test WSL detection via /proc/version."""
        with patch("platform.system", return_value="Linux"):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = "Linux version 5.15 microsoft-standard-WSL2"
            with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
                assert _detect_wsl() is True

    def test_wsl_detected_via_env(self) -> None:
        """Test WSL detection via environment variable."""
        with patch("platform.system", return_value="Linux"):
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
                with patch.dict("os.environ", {"WSL_DISTRO_NAME": "Ubuntu"}):
                    assert _detect_wsl() is True

    def test_not_wsl_on_native_linux(self) -> None:
        """Test WSL detection returns False on native Linux."""
        with patch("platform.system", return_value="Linux"):

            def mock_path_factory(path_str: str) -> MagicMock:
                mock = MagicMock()
                if path_str == "/proc/version":
                    mock.exists.return_value = True
                    mock.read_text.return_value = "Linux version 5.15.0-generic"
                elif path_str == "/proc/sys/fs/binfmt_misc/WSLInterop":
                    mock.exists.return_value = False
                else:
                    mock.exists.return_value = False
                return mock

            with patch("devflow.providers.installers.platform.Path", side_effect=mock_path_factory):
                with patch.dict("os.environ", {}, clear=True):
                    assert _detect_wsl() is False


class TestLinuxDistroDetection:
    """Tests for Linux distribution detection."""

    def test_detect_ubuntu(self) -> None:
        """Test Ubuntu detection."""
        os_release_content = 'ID=ubuntu\nVERSION_ID="22.04"'
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = os_release_content

        with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
            distro, version = _detect_linux_distro()
            assert distro == LinuxDistro.UBUNTU
            assert version == "22.04"

    def test_detect_fedora(self) -> None:
        """Test Fedora detection."""
        os_release_content = "ID=fedora\nVERSION_ID=39"
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = os_release_content

        with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
            distro, version = _detect_linux_distro()
            assert distro == LinuxDistro.FEDORA
            assert version == "39"

    def test_detect_arch(self) -> None:
        """Test Arch Linux detection."""
        os_release_content = "ID=arch"
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = os_release_content

        with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
            distro, version = _detect_linux_distro()
            assert distro == LinuxDistro.ARCH
            assert version is None

    def test_detect_unknown_distro(self) -> None:
        """Test unknown distro detection."""
        os_release_content = "ID=gentoo"
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = os_release_content

        with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
            distro, version = _detect_linux_distro()
            assert distro == LinuxDistro.UNKNOWN

    def test_no_os_release_file(self) -> None:
        """Test when /etc/os-release doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False

        with patch("devflow.providers.installers.platform.Path", return_value=mock_path):
            distro, version = _detect_linux_distro()
            assert distro == LinuxDistro.UNKNOWN
            assert version is None


class TestArchitectureDetection:
    """Tests for CPU architecture detection."""

    def test_detect_x86_64(self) -> None:
        """Test x86_64 detection."""
        with patch("platform.machine", return_value="x86_64"):
            assert _detect_architecture() == Architecture.X86_64

    def test_detect_amd64(self) -> None:
        """Test AMD64 detection (alias for x86_64)."""
        with patch("platform.machine", return_value="AMD64"):
            assert _detect_architecture() == Architecture.X86_64

    def test_detect_arm64(self) -> None:
        """Test ARM64 detection."""
        with patch("platform.machine", return_value="arm64"):
            assert _detect_architecture() == Architecture.ARM64

    def test_detect_aarch64(self) -> None:
        """Test aarch64 detection (alias for arm64)."""
        with patch("platform.machine", return_value="aarch64"):
            assert _detect_architecture() == Architecture.ARM64

    def test_detect_armv7(self) -> None:
        """Test ARMv7 detection."""
        with patch("platform.machine", return_value="armv7l"):
            assert _detect_architecture() == Architecture.ARMV7

    def test_detect_unknown(self) -> None:
        """Test unknown architecture."""
        with patch("platform.machine", return_value="riscv64"):
            assert _detect_architecture() == Architecture.UNKNOWN


class TestPackageManagerDetection:
    """Tests for package manager detection."""

    def test_detect_brew(self) -> None:
        """Test Homebrew detection."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/opt/homebrew/bin/brew" if cmd == "brew" else None
            managers = _detect_package_managers()
            assert PackageManager.BREW in managers

    def test_detect_apt(self) -> None:
        """Test APT detection."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/apt" if cmd == "apt" else None
            managers = _detect_package_managers()
            assert PackageManager.APT in managers

    def test_detect_multiple(self) -> None:
        """Test multiple package manager detection."""

        def mock_which(cmd: str) -> str | None:
            binaries = {
                "apt": "/usr/bin/apt",
                "snap": "/usr/bin/snap",
                "npm": "/usr/bin/npm",
            }
            return binaries.get(cmd)

        with patch("shutil.which", side_effect=mock_which):
            managers = _detect_package_managers()
            assert PackageManager.APT in managers
            assert PackageManager.SNAP in managers
            assert PackageManager.NPM in managers


class TestPlatformInfo:
    """Tests for PlatformInfo dataclass."""

    def test_is_linux(self) -> None:
        """Test is_linux property."""
        info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.UBUNTU,
            distro_version="22.04",
            arch=Architecture.X86_64,
            is_wsl=False,
        )
        assert info.is_linux is True
        assert info.is_macos is False
        assert info.is_windows is False

    def test_is_macos(self) -> None:
        """Test is_macos property."""
        info = PlatformInfo(
            os=OperatingSystem.MACOS,
            os_version="14.0",
            distro=None,
            distro_version=None,
            arch=Architecture.ARM64,
            is_wsl=False,
        )
        assert info.is_macos is True
        assert info.is_linux is False
        assert info.is_apple_silicon is True

    def test_is_windows(self) -> None:
        """Test is_windows property."""
        info = PlatformInfo(
            os=OperatingSystem.WINDOWS,
            os_version="10",
            distro=None,
            distro_version=None,
            arch=Architecture.X86_64,
            is_wsl=False,
        )
        assert info.is_windows is True
        assert info.is_linux is False
        assert info.is_macos is False

    def test_is_debian_based(self) -> None:
        """Test is_debian_based property."""
        ubuntu_info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.UBUNTU,
            distro_version="22.04",
            arch=Architecture.X86_64,
            is_wsl=False,
        )
        assert ubuntu_info.is_debian_based is True

        fedora_info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.FEDORA,
            distro_version="39",
            arch=Architecture.X86_64,
            is_wsl=False,
        )
        assert fedora_info.is_debian_based is False

    def test_has_package_manager(self) -> None:
        """Test has_package_manager method."""
        info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.UBUNTU,
            distro_version="22.04",
            arch=Architecture.X86_64,
            is_wsl=False,
            package_managers=[PackageManager.APT, PackageManager.SNAP],
        )
        assert info.has_package_manager(PackageManager.APT) is True
        assert info.has_package_manager(PackageManager.SNAP) is True
        assert info.has_package_manager(PackageManager.BREW) is False

    def test_get_preferred_package_manager(self) -> None:
        """Test preferred package manager selection."""
        linux_info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.UBUNTU,
            distro_version="22.04",
            arch=Architecture.X86_64,
            is_wsl=False,
            package_managers=[PackageManager.APT, PackageManager.SNAP],
        )
        assert linux_info.get_preferred_package_manager() == PackageManager.APT

        macos_info = PlatformInfo(
            os=OperatingSystem.MACOS,
            os_version="14.0",
            distro=None,
            distro_version=None,
            arch=Architecture.ARM64,
            is_wsl=False,
            package_managers=[PackageManager.BREW],
        )
        assert macos_info.get_preferred_package_manager() == PackageManager.BREW


class TestCommandUtilities:
    """Tests for command utility functions."""

    def test_check_command_exists_true(self) -> None:
        """Test command exists check returns True."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert check_command_exists("git") is True

    def test_check_command_exists_false(self) -> None:
        """Test command exists check returns False."""
        with patch("shutil.which", return_value=None):
            assert check_command_exists("nonexistent") is False

    def test_get_command_path(self) -> None:
        """Test getting command path."""
        with patch("shutil.which", return_value="/usr/bin/python"):
            assert get_command_path("python") == "/usr/bin/python"

    def test_get_command_path_not_found(self) -> None:
        """Test getting path for non-existent command."""
        with patch("shutil.which", return_value=None):
            assert get_command_path("nonexistent") is None

    def test_get_command_version(self) -> None:
        """Test getting command version."""
        mock_result = MagicMock()
        mock_result.stdout = "git version 2.40.0\n"
        mock_result.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/git"):
            with patch("subprocess.run", return_value=mock_result):
                version = get_command_version("git")
                assert version == "git version 2.40.0"

    def test_get_command_version_not_installed(self) -> None:
        """Test getting version for non-installed command."""
        with patch("shutil.which", return_value=None):
            assert get_command_version("nonexistent") is None


class TestDetectPlatform:
    """Tests for the main detect_platform function."""

    def test_detect_platform_caches_result(self) -> None:
        """Test that platform detection results are cached."""
        # Clear any existing cache
        detect_platform.cache_clear()

        with patch("devflow.providers.installers.platform._detect_os") as mock_os:
            with patch("devflow.providers.installers.platform._detect_architecture") as mock_arch:
                with patch("devflow.providers.installers.platform._detect_wsl") as mock_wsl:
                    with patch("devflow.providers.installers.platform._detect_package_managers") as mock_pm:
                        mock_os.return_value = (OperatingSystem.LINUX, "5.15")
                        mock_arch.return_value = Architecture.X86_64
                        mock_wsl.return_value = False
                        mock_pm.return_value = [PackageManager.APT]

                        # First call
                        result1 = detect_platform()
                        # Second call should use cache
                        result2 = detect_platform()

                        assert result1 is result2
                        # _detect_os should only be called once due to caching
                        assert mock_os.call_count == 1

        # Clear cache after test
        detect_platform.cache_clear()

    def test_refresh_platform_info_clears_cache(self) -> None:
        """Test that refresh_platform_info clears the cache."""
        detect_platform.cache_clear()

        with patch("devflow.providers.installers.platform._detect_os") as mock_os:
            with patch("devflow.providers.installers.platform._detect_architecture") as mock_arch:
                with patch("devflow.providers.installers.platform._detect_wsl") as mock_wsl:
                    with patch("devflow.providers.installers.platform._detect_package_managers") as mock_pm:
                        mock_os.return_value = (OperatingSystem.LINUX, "5.15")
                        mock_arch.return_value = Architecture.X86_64
                        mock_wsl.return_value = False
                        mock_pm.return_value = [PackageManager.APT]

                        detect_platform()
                        refresh_platform_info()
                        detect_platform()

                        # Should be called twice (initial + after refresh)
                        assert mock_os.call_count == 2

        detect_platform.cache_clear()
