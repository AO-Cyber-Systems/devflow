"""Git utilities for devflow."""

import subprocess

from devflow.core.config import DevflowConfig


def configure_git_user(config: DevflowConfig) -> dict[str, str]:
    """Configure local git settings from devflow config.

    Returns dict with status and message.
    """
    if not config.git.user.name and not config.git.user.email:
        return {"status": "skipped", "message": "No git user config specified"}

    configured = []
    if config.git.user.name:
        subprocess.run(
            ["git", "config", "--local", "user.name", config.git.user.name],
            capture_output=True,
        )
        configured.append(f"name={config.git.user.name}")

    if config.git.user.email:
        subprocess.run(
            ["git", "config", "--local", "user.email", config.git.user.email],
            capture_output=True,
        )
        configured.append(f"email={config.git.user.email}")

    return {"status": "ok", "message": f"Git configured: {', '.join(configured)}"}


def get_co_author_line(config: DevflowConfig) -> str | None:
    """Get co-author line for commits if enabled.

    Returns None if co-author is disabled.
    """
    if not config.git.co_author.enabled:
        return None

    name = config.git.co_author.name
    email = config.git.co_author.email
    return f"Co-Authored-By: {name} <{email}>"
