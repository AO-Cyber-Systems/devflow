"""DevFlow service mode for daemon/remote operation.

This package provides a TCP-based JSON-RPC server that enables:
- Windows Tauri apps to communicate with Python backend running in WSL2
- Remote/headless operation of DevFlow
- Service-mode operation with systemd

The service exposes the same handlers as the stdio bridge but over TCP,
enabling cross-platform communication.
"""

from devflow.service.server import DevFlowServer

__all__ = ["DevFlowServer"]
