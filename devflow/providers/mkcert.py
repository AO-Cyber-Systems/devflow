"""Mkcert provider for local TLS certificate management."""

import re
import shutil
import subprocess
from pathlib import Path

from devflow.core.paths import PathHandler
from devflow.core.platform import CURRENT_PLATFORM, Platform
from devflow.providers.base import Provider


class MkcertProvider(Provider):
    """Wrapper for mkcert CLI for generating locally-trusted certificates."""

    @property
    def name(self) -> str:
        return "mkcert"

    @property
    def binary(self) -> str:
        # On Windows, the binary may have .exe extension
        if CURRENT_PLATFORM == Platform.WINDOWS:
            return "mkcert.exe"
        return "mkcert"

    def is_available(self) -> bool:
        """Check if mkcert is installed."""
        # Try with and without .exe on Windows
        if shutil.which(self.binary) is not None:
            return True
        # Fallback for Windows if .exe wasn't found explicitly
        if CURRENT_PLATFORM == Platform.WINDOWS:
            return shutil.which("mkcert") is not None
        return False

    def get_default_cert_dir(self) -> Path:
        """Get the default certificate directory for current platform.

        Returns:
            Path to the platform-appropriate certificate directory.
        """
        return PathHandler.get_cert_dir()

    def is_authenticated(self) -> bool:
        """Check if mkcert CA is installed in the system trust store."""
        return self.is_ca_installed()

    def is_ca_installed(self) -> bool:
        """Check if the mkcert CA is installed in the system trust store."""
        if not self.is_available():
            return False

        try:
            # mkcert -check returns 0 if CA is installed, non-zero otherwise
            # Note: Some versions don't have -check, so we verify by checking CAROOT
            caroot = self.get_ca_root()
            if not caroot:
                return False

            caroot_path = Path(caroot)
            rootca_pem = caroot_path / "rootCA.pem"
            return rootca_pem.exists()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def install_ca(self) -> tuple[bool, str]:
        """Install the mkcert CA into the system trust store.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_available():
            return False, "mkcert is not installed"

        try:
            result = self.run(["-install"], capture_output=True, check=False, timeout=60)
            if result.returncode == 0:
                return True, "CA installed successfully"
            return False, result.stderr.strip() or "Failed to install CA"
        except subprocess.TimeoutExpired:
            return False, "CA installation timed out"
        except subprocess.SubprocessError as e:
            return False, f"Failed to install CA: {e}"

    def generate_cert(
        self,
        domains: list[str],
        output_dir: str,
        cert_name: str = "cert",
        key_name: str = "key",
    ) -> tuple[bool, str]:
        """Generate a certificate for the specified domains.

        Args:
            domains: List of domains (e.g., ["*.localhost", "localhost"])
            output_dir: Directory to write certificate files to
            cert_name: Name for the certificate file (without extension)
            key_name: Name for the key file (without extension)

        Returns:
            Tuple of (success, message)
        """
        if not self.is_available():
            return False, "mkcert is not installed"

        if not self.is_ca_installed():
            return False, "mkcert CA is not installed. Run 'mkcert -install' first."

        output_path = Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)

        cert_file = output_path / f"{cert_name}.pem"
        key_file = output_path / f"{key_name}.pem"

        try:
            # mkcert -cert-file cert.pem -key-file key.pem domain1 domain2
            args = [
                "-cert-file",
                str(cert_file),
                "-key-file",
                str(key_file),
            ] + domains

            result = self.run(args, capture_output=True, check=False, timeout=30)
            if result.returncode == 0:
                return True, f"Certificates generated at {output_path}"
            return False, result.stderr.strip() or "Failed to generate certificates"
        except subprocess.TimeoutExpired:
            return False, "Certificate generation timed out"
        except subprocess.SubprocessError as e:
            return False, f"Failed to generate certificates: {e}"

    def get_ca_root(self) -> str | None:
        """Get the path to the mkcert CA root directory.

        Returns:
            Path to the CAROOT directory, or None if mkcert is not available
        """
        if not self.is_available():
            return None

        try:
            result = self.run(["-CAROOT"], capture_output=True, check=False, timeout=10)
            if result.returncode == 0:
                return str(result.stdout.strip())
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def get_version(self) -> str | None:
        """Get the mkcert version."""
        if not self.is_available():
            return None

        try:
            # mkcert doesn't have --version, but -version works
            result = subprocess.run(
                [self.binary, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def cert_exists(self, output_dir: str, cert_name: str = "cert", key_name: str = "key") -> bool:
        """Check if certificate files already exist.

        Args:
            output_dir: Directory where certificates should be
            cert_name: Name of the certificate file (without extension)
            key_name: Name of the key file (without extension)

        Returns:
            True if both cert and key files exist
        """
        output_path = Path(output_dir).expanduser()
        cert_file = output_path / f"{cert_name}.pem"
        key_file = output_path / f"{key_name}.pem"
        return cert_file.exists() and key_file.exists()

    def get_cert_domains(self, cert_path: str) -> list[str]:
        """Extract domains from an existing certificate using openssl.

        Args:
            cert_path: Path to the certificate file

        Returns:
            List of domains in the certificate, or empty list on failure
        """
        cert_file = Path(cert_path).expanduser()
        if not cert_file.exists():
            return []

        try:
            # Use openssl to extract SAN from certificate
            result = subprocess.run(
                ["openssl", "x509", "-in", str(cert_file), "-noout", "-text"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            # Parse DNS entries from Subject Alternative Name
            domains = []
            in_san = False
            for line in result.stdout.split("\n"):
                stripped = line.strip()
                if "Subject Alternative Name:" in stripped:
                    in_san = True
                    continue
                if in_san:
                    # Extract DNS:*.localhost, DNS:localhost format
                    dns_matches = re.findall(r"DNS:([^\s,]+)", stripped)
                    domains.extend(dns_matches)
                    break

            return domains
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return []

    def doctor(self) -> dict:
        """Run diagnostics and return status."""
        status = super().doctor()
        status["ca_installed"] = self.is_ca_installed()
        status["ca_root"] = self.get_ca_root()
        return status
