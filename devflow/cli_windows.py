"""Windows CLI wrapper that delegates to WSL2.

On Windows, DevFlow requires WSL2 for Docker and other Linux-native
dependencies. This wrapper transparently delegates CLI commands to
the DevFlow installation in WSL2.

Usage:
    This module is used automatically when `devflow` is invoked on Windows.
    Commands are passed through to WSL2's `devflow` CLI.
"""

import subprocess
import sys


def check_wsl_available() -> bool:
    """Check if WSL is available on this system.

    Returns:
        True if WSL is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["wsl", "--status"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_wsl_distros() -> list[str]:
    """Get list of available WSL distributions.

    Returns:
        List of distribution names.
    """
    try:
        result = subprocess.run(
            ["wsl", "--list", "--quiet"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse the output, filtering empty lines
            distros = [line.strip() for line in result.stdout.split("\n") if line.strip()]
            # Remove null characters that Windows sometimes adds
            distros = [d.replace("\x00", "") for d in distros]
            return distros
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def get_default_distro() -> str | None:
    """Get the default WSL distribution.

    Returns:
        Name of the default distribution, or None if not found.
    """
    distros = get_wsl_distros()
    if distros:
        return distros[0]
    return None


def find_devflow_distro() -> str | None:
    """Find a WSL distribution with DevFlow installed.

    Checks common distributions in order of preference:
    1. Ubuntu (most common)
    2. Debian
    3. Default distribution

    Returns:
        Distribution name with DevFlow installed, or None.
    """
    preferred_distros = ["Ubuntu", "Ubuntu-22.04", "Ubuntu-20.04", "Debian"]
    available = get_wsl_distros()

    # Check preferred distros first
    for distro in preferred_distros:
        if distro in available:
            if check_devflow_installed(distro):
                return distro

    # Check default distro
    default = get_default_distro()
    if default and check_devflow_installed(default):
        return default

    # Check any distro
    for distro in available:
        if check_devflow_installed(distro):
            return distro

    return None


def check_devflow_installed(distro: str) -> bool:
    """Check if DevFlow is installed in a WSL distribution.

    Args:
        distro: Name of the WSL distribution.

    Returns:
        True if devflow is installed, False otherwise.
    """
    try:
        result = subprocess.run(
            ["wsl", "-d", distro, "--", "which", "devflow"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_in_wsl(args: list[str], distro: str | None = None) -> int:
    """Run devflow command in WSL2.

    Args:
        args: Command-line arguments to pass to devflow.
        distro: WSL distribution name. If None, auto-detects.

    Returns:
        Exit code from the command.
    """
    # Find a suitable distro if not specified
    if distro is None:
        distro = find_devflow_distro()
        if distro is None:
            print("Error: Could not find a WSL2 distribution with DevFlow installed.")
            print()
            print("To install DevFlow in WSL2:")
            print("  1. Open a WSL terminal (Ubuntu recommended)")
            print("  2. Run: pip install devflow")
            print()
            print("To install WSL2 with Ubuntu:")
            print("  wsl --install -d Ubuntu")
            return 1

    # Build the WSL command
    wsl_command = ["wsl", "-d", distro, "--", "devflow"] + args

    try:
        # Run interactively, passing through stdin/stdout/stderr
        result = subprocess.run(
            wsl_command,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: WSL2 is not installed.")
        print()
        print("Please install WSL2:")
        print("  wsl --install -d Ubuntu")
        print()
        print("Then restart your computer and install DevFlow in WSL2:")
        print("  pip install devflow")
        return 1
    except KeyboardInterrupt:
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> None:
    """Windows entry point for DevFlow CLI.

    This function is called when `devflow` is run on Windows.
    It delegates all commands to the WSL2 installation.
    """
    # Check if WSL is available
    if not check_wsl_available():
        print("Error: WSL2 is not available on this system.")
        print()
        print("Please install WSL2:")
        print("  wsl --install -d Ubuntu")
        print()
        print("After installation, restart your computer and install DevFlow in WSL2:")
        print("  pip install devflow")
        sys.exit(1)

    # Run the command in WSL
    exit_code = run_in_wsl(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
