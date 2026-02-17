"""System doctor - checks and installs required Python packages."""

import importlib
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PackageStatus(str, Enum):
    """Status of a required package."""
    OK = "ok"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"


@dataclass
class PackageCheck:
    """Result of checking a package."""
    name: str
    import_name: str
    status: PackageStatus
    version: str | None = None
    required_for: str = ""
    install_cmd: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "import_name": self.import_name,
            "status": self.status.value,
            "version": self.version,
            "required_for": self.required_for,
            "install_cmd": self.install_cmd,
            "error": self.error,
        }


# Required packages with their pip names and import names
REQUIRED_PACKAGES: list[dict[str, str]] = [
    {
        "pip_name": "fastembed",
        "import_name": "fastembed",
        "required_for": "Semantic search and embeddings",
        "optional": False,
    },
    {
        "pip_name": "tree-sitter-language-pack",
        "import_name": "tree_sitter_language_pack",
        "required_for": "Code parsing and analysis",
        "optional": False,
    },
    {
        "pip_name": "httpx",
        "import_name": "httpx",
        "required_for": "HTTP requests and web crawling",
        "optional": False,
    },
    {
        "pip_name": "beautifulsoup4",
        "import_name": "bs4",
        "required_for": "HTML parsing for web import",
        "optional": False,
    },
    {
        "pip_name": "pymupdf",
        "import_name": "fitz",
        "required_for": "PDF document parsing",
        "optional": True,
    },
    {
        "pip_name": "psycopg2-binary",
        "import_name": "psycopg2",
        "required_for": "PostgreSQL database support",
        "optional": True,
    },
    {
        "pip_name": "tree-sitter",
        "import_name": "tree_sitter",
        "required_for": "Code parsing foundation",
        "optional": False,
    },
    {
        "pip_name": "pyyaml",
        "import_name": "yaml",
        "required_for": "YAML configuration parsing",
        "optional": False,
    },
    {
        "pip_name": "qdrant-client",
        "import_name": "qdrant_client",
        "required_for": "Vector database for semantic search",
        "optional": True,
    },
]


def get_package_version(import_name: str) -> str | None:
    """Get the version of an installed package."""
    try:
        module = importlib.import_module(import_name)
        # Try common version attributes
        for attr in ["__version__", "VERSION", "version"]:
            if hasattr(module, attr):
                ver = getattr(module, attr)
                if isinstance(ver, str):
                    return ver
                if hasattr(ver, "__str__"):
                    return str(ver)
        return "installed"
    except Exception:
        return None


def check_package(pip_name: str, import_name: str, required_for: str = "") -> PackageCheck:
    """Check if a package is installed and working."""
    try:
        importlib.import_module(import_name)
        version = get_package_version(import_name)
        return PackageCheck(
            name=pip_name,
            import_name=import_name,
            status=PackageStatus.OK,
            version=version,
            required_for=required_for,
            install_cmd=f"pip install {pip_name}",
        )
    except ImportError as e:
        return PackageCheck(
            name=pip_name,
            import_name=import_name,
            status=PackageStatus.MISSING,
            required_for=required_for,
            install_cmd=f"pip install {pip_name}",
            error=str(e),
        )
    except Exception as e:
        return PackageCheck(
            name=pip_name,
            import_name=import_name,
            status=PackageStatus.ERROR,
            required_for=required_for,
            install_cmd=f"pip install {pip_name}",
            error=str(e),
        )


def check_all_packages(include_optional: bool = True) -> list[PackageCheck]:
    """Check all required packages."""
    results = []
    for pkg in REQUIRED_PACKAGES:
        if not include_optional and pkg.get("optional", False):
            continue
        check = check_package(
            pkg["pip_name"],
            pkg["import_name"],
            pkg.get("required_for", ""),
        )
        results.append(check)
    return results


def install_package(pip_name: str) -> dict[str, Any]:
    """Install a package using pip."""
    try:
        # Use the same Python that's running this script
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            # Verify installation
            pkg_info = next((p for p in REQUIRED_PACKAGES if p["pip_name"] == pip_name), None)
            if pkg_info:
                # Clear cached imports and re-check
                import_name = pkg_info["import_name"]
                if import_name in sys.modules:
                    del sys.modules[import_name]
                try:
                    importlib.import_module(import_name)
                    version = get_package_version(import_name)
                    return {
                        "success": True,
                        "package": pip_name,
                        "version": version,
                        "output": result.stdout,
                    }
                except ImportError as e:
                    return {
                        "success": False,
                        "package": pip_name,
                        "error": f"Installed but import failed: {e}",
                        "output": result.stdout,
                    }
            return {
                "success": True,
                "package": pip_name,
                "output": result.stdout,
            }
        else:
            return {
                "success": False,
                "package": pip_name,
                "error": result.stderr or "Installation failed",
                "output": result.stdout,
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "package": pip_name,
            "error": "Installation timed out after 5 minutes",
        }
    except Exception as e:
        return {
            "success": False,
            "package": pip_name,
            "error": str(e),
        }


def install_all_missing(include_optional: bool = False) -> dict[str, Any]:
    """Install all missing packages."""
    checks = check_all_packages(include_optional=include_optional)
    missing = [c for c in checks if c.status == PackageStatus.MISSING]

    if not missing:
        return {
            "success": True,
            "installed": [],
            "already_installed": len(checks),
            "message": "All packages already installed",
        }

    results = []
    for check in missing:
        result = install_package(check.name)
        results.append(result)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    return {
        "success": len(failed) == 0,
        "installed": [r["package"] for r in successful],
        "failed": [{"package": r["package"], "error": r.get("error")} for r in failed],
        "total_missing": len(missing),
        "total_installed": len(successful),
    }


def run_doctor(include_optional: bool = True) -> dict[str, Any]:
    """Run full doctor check on packages."""
    checks = check_all_packages(include_optional=include_optional)

    ok_count = sum(1 for c in checks if c.status == PackageStatus.OK)
    missing_count = sum(1 for c in checks if c.status == PackageStatus.MISSING)
    error_count = sum(1 for c in checks if c.status == PackageStatus.ERROR)

    # Determine overall status
    if missing_count > 0 or error_count > 0:
        # Check if any required (non-optional) packages are missing
        required_missing = [
            c for c in checks
            if c.status in (PackageStatus.MISSING, PackageStatus.ERROR)
            and not any(
                p.get("optional", False)
                for p in REQUIRED_PACKAGES
                if p["pip_name"] == c.name
            )
        ]
        overall_status = "error" if required_missing else "warning"
    else:
        overall_status = "healthy"

    return {
        "overall_status": overall_status,
        "packages": [c.to_dict() for c in checks],
        "summary": {
            "total": len(checks),
            "ok": ok_count,
            "missing": missing_count,
            "error": error_count,
        },
        "can_auto_fix": missing_count > 0,
    }
