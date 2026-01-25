"""Platform detection utilities for cross-platform installation support."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path


class OperatingSystem(str, Enum):
    """Supported operating systems."""

    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class LinuxDistro(str, Enum):
    """Supported Linux distributions."""

    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    FEDORA = "fedora"
    CENTOS = "centos"
    RHEL = "rhel"
    ARCH = "arch"
    MANJARO = "manjaro"
    OPENSUSE = "opensuse"
    UNKNOWN = "unknown"


class PackageManager(str, Enum):
    """Available package managers."""

    BREW = "brew"
    APT = "apt"
    DNF = "dnf"
    YUM = "yum"
    PACMAN = "pacman"
    ZYPPER = "zypper"
    SNAP = "snap"
    FLATPAK = "flatpak"
    WINGET = "winget"
    SCOOP = "scoop"
    CHOCO = "choco"
    MISE = "mise"
    NPM = "npm"
    PIPX = "pipx"


class Architecture(str, Enum):
    """CPU architectures."""

    X86_64 = "x86_64"
    ARM64 = "arm64"
    ARMV7 = "armv7"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Information about the current platform."""

    os: OperatingSystem
    os_version: str
    distro: LinuxDistro | None
    distro_version: str | None
    arch: Architecture
    is_wsl: bool
    package_managers: list[PackageManager] = field(default_factory=list)

    @property
    def is_linux(self) -> bool:
        return self.os == OperatingSystem.LINUX

    @property
    def is_macos(self) -> bool:
        return self.os == OperatingSystem.MACOS

    @property
    def is_windows(self) -> bool:
        return self.os == OperatingSystem.WINDOWS

    @property
    def is_apple_silicon(self) -> bool:
        return self.is_macos and self.arch == Architecture.ARM64

    @property
    def is_debian_based(self) -> bool:
        return self.distro in (LinuxDistro.UBUNTU, LinuxDistro.DEBIAN)

    @property
    def is_rhel_based(self) -> bool:
        return self.distro in (LinuxDistro.FEDORA, LinuxDistro.CENTOS, LinuxDistro.RHEL)

    @property
    def is_arch_based(self) -> bool:
        return self.distro in (LinuxDistro.ARCH, LinuxDistro.MANJARO)

    def has_package_manager(self, pm: PackageManager) -> bool:
        return pm in self.package_managers

    def get_preferred_package_manager(self) -> PackageManager | None:
        """Get the preferred package manager for this platform."""
        preference_order = {
            OperatingSystem.MACOS: [PackageManager.BREW],
            OperatingSystem.LINUX: [
                PackageManager.APT,
                PackageManager.DNF,
                PackageManager.PACMAN,
                PackageManager.ZYPPER,
            ],
            OperatingSystem.WINDOWS: [PackageManager.WINGET, PackageManager.SCOOP, PackageManager.CHOCO],
        }

        for pm in preference_order.get(self.os, []):
            if pm in self.package_managers:
                return pm
        return None


def _detect_os() -> tuple[OperatingSystem, str]:
    """Detect the current operating system."""
    system = platform.system().lower()
    version = platform.release()

    if system == "darwin":
        return OperatingSystem.MACOS, platform.mac_ver()[0] or version
    elif system == "linux":
        return OperatingSystem.LINUX, version
    elif system == "windows":
        return OperatingSystem.WINDOWS, platform.win32_ver()[0] or version
    else:
        return OperatingSystem.UNKNOWN, version


def _detect_wsl() -> bool:
    """Detect if running in Windows Subsystem for Linux."""
    if platform.system().lower() != "linux":
        return False

    # Check for WSL-specific indicators
    try:
        # Check /proc/version for Microsoft
        version_path = Path("/proc/version")
        if version_path.exists():
            content = version_path.read_text().lower()
            if "microsoft" in content or "wsl" in content:
                return True

        # Check for WSL environment variable
        if os.environ.get("WSL_DISTRO_NAME"):
            return True

        # Check for WSL interop
        if Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
            return True

    except (OSError, PermissionError):
        pass

    return False


def _detect_linux_distro() -> tuple[LinuxDistro, str | None]:
    """Detect the Linux distribution."""
    distro = LinuxDistro.UNKNOWN
    version = None

    # Try /etc/os-release first (standard on modern distros)
    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            content = os_release.read_text()
            info = {}
            for line in content.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    info[key] = value.strip('"')

            distro_id = info.get("ID", "").lower()
            version = info.get("VERSION_ID")

            distro_map = {
                "ubuntu": LinuxDistro.UBUNTU,
                "debian": LinuxDistro.DEBIAN,
                "fedora": LinuxDistro.FEDORA,
                "centos": LinuxDistro.CENTOS,
                "rhel": LinuxDistro.RHEL,
                "arch": LinuxDistro.ARCH,
                "manjaro": LinuxDistro.MANJARO,
                "opensuse": LinuxDistro.OPENSUSE,
                "opensuse-leap": LinuxDistro.OPENSUSE,
                "opensuse-tumbleweed": LinuxDistro.OPENSUSE,
            }
            distro = distro_map.get(distro_id, LinuxDistro.UNKNOWN)

        except (OSError, ValueError):
            pass

    return distro, version


def _detect_architecture() -> Architecture:
    """Detect the CPU architecture."""
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        return Architecture.X86_64
    elif machine in ("arm64", "aarch64"):
        return Architecture.ARM64
    elif machine.startswith("armv7"):
        return Architecture.ARMV7
    else:
        return Architecture.UNKNOWN


def _detect_package_managers() -> list[PackageManager]:
    """Detect available package managers."""
    managers = []

    # Map binary names to package managers
    pm_binaries = {
        "brew": PackageManager.BREW,
        "apt": PackageManager.APT,
        "apt-get": PackageManager.APT,
        "dnf": PackageManager.DNF,
        "yum": PackageManager.YUM,
        "pacman": PackageManager.PACMAN,
        "zypper": PackageManager.ZYPPER,
        "snap": PackageManager.SNAP,
        "flatpak": PackageManager.FLATPAK,
        "winget": PackageManager.WINGET,
        "scoop": PackageManager.SCOOP,
        "choco": PackageManager.CHOCO,
        "mise": PackageManager.MISE,
        "npm": PackageManager.NPM,
        "pipx": PackageManager.PIPX,
    }

    for binary, pm in pm_binaries.items():
        if shutil.which(binary):
            if pm not in managers:
                managers.append(pm)

    return managers


@lru_cache(maxsize=1)
def detect_platform() -> PlatformInfo:
    """Detect and cache platform information."""
    os_type, os_version = _detect_os()
    arch = _detect_architecture()
    is_wsl = _detect_wsl()

    distro = None
    distro_version = None
    if os_type == OperatingSystem.LINUX:
        distro, distro_version = _detect_linux_distro()

    package_managers = _detect_package_managers()

    return PlatformInfo(
        os=os_type,
        os_version=os_version,
        distro=distro,
        distro_version=distro_version,
        arch=arch,
        is_wsl=is_wsl,
        package_managers=package_managers,
    )


def refresh_platform_info() -> PlatformInfo:
    """Clear cache and re-detect platform information."""
    detect_platform.cache_clear()
    return detect_platform()


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def get_command_version(command: str, version_flag: str = "--version") -> str | None:
    """Get the version of a command."""
    if not check_command_exists(command):
        return None

    try:
        result = subprocess.run(
            [command, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip() or result.stderr.strip()
        # Return first line of version output
        return output.split("\n")[0] if output else None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None


def get_command_path(command: str) -> str | None:
    """Get the full path to a command."""
    return shutil.which(command)
