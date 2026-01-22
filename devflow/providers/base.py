"""Abstract provider interface."""

import shutil
import subprocess
from abc import ABC, abstractmethod


class Provider(ABC):
    """Base class for external tool providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'github', 'docker')."""
        pass

    @property
    @abstractmethod
    def binary(self) -> str:
        """Binary name to execute (e.g., 'gh', 'docker')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is installed and accessible."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if the tool is authenticated/configured."""
        pass

    def get_version(self) -> str | None:
        """Get the tool version."""
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [self.binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n")[0]
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def get_path(self) -> str | None:
        """Get the path to the binary."""
        return shutil.which(self.binary)

    def doctor(self) -> dict:
        """Run diagnostics and return status."""
        return {
            "name": self.name,
            "binary": self.binary,
            "available": self.is_available(),
            "authenticated": self.is_authenticated(),
            "version": self.get_version(),
            "path": self.get_path(),
        }

    def run(
        self,
        args: list[str],
        capture_output: bool = True,
        check: bool = True,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess:
        """
        Run a command with this provider's binary.

        Args:
            args: Command arguments (without the binary name)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit code
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess instance
        """
        cmd = [self.binary] + args
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout,
        )
