# Cross-Platform Test Plan

This document outlines the comprehensive test strategy for validating DevFlow's cross-platform architecture across Linux, macOS, and Windows (WSL2).

## Test Categories

| Category | Scope | Automation | CI/CD |
|----------|-------|------------|-------|
| Unit Tests | Platform detection, path handling | Fully automated | Yes |
| Integration Tests | TCP server, bridge communication | Fully automated | Yes |
| Component Tests | Provider cross-platform behavior | Fully automated | Yes |
| E2E Tests | Full workflow on each platform | Semi-automated | Partial |
| Manual Tests | UI, installation, edge cases | Manual | No |

---

## 1. Unit Tests

### 1.1 Platform Detection (`tests/unit/core/test_platform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| PD-001 | Detect native Linux | Returns `Platform.LINUX` |
| PD-002 | Detect WSL2 via "microsoft" in kernel | Returns `Platform.WSL2` |
| PD-003 | Detect WSL2 via "wsl" in kernel | Returns `Platform.WSL2` |
| PD-004 | Detect macOS | Returns `Platform.MACOS` |
| PD-005 | Detect Windows | Returns `Platform.WINDOWS` |
| PD-006 | Unsupported platform raises error | Raises `RuntimeError` |
| PD-007 | `is_wsl()` false on native Linux | Returns `False` |
| PD-008 | `is_wsl()` true on WSL2 | Returns `True` |
| PD-009 | `is_wsl()` false on Windows | Returns `False` |
| PD-010 | `is_wsl2()` true on WSL2 | Returns `True` |
| PD-011 | `is_wsl2()` false on native Linux | Returns `False` |
| PD-012 | `is_windows()` true on Windows | Returns `True` |
| PD-013 | `is_windows()` false on Linux | Returns `False` |
| PD-014 | `is_macos()` true on macOS | Returns `True` |
| PD-015 | `is_macos()` false on Linux | Returns `False` |
| PD-016 | `is_linux()` true on native Linux | Returns `True` |
| PD-017 | `is_linux()` false on WSL2 | Returns `False` |
| PD-018 | `is_unix_like()` true on Linux | Returns `True` |
| PD-019 | `is_unix_like()` true on macOS | Returns `True` |
| PD-020 | `is_unix_like()` true on WSL2 | Returns `True` |
| PD-021 | `is_unix_like()` false on Windows | Returns `False` |
| PD-022 | Platform enum has correct values | Verify enum string values |
| PD-023 | Platform enum has 4 members | LINUX, MACOS, WINDOWS, WSL2 |
| PD-024 | `CURRENT_PLATFORM` is valid | Is instance of `Platform` |
| PD-025 | `CURRENT_PLATFORM` matches detection | Equals `detect_platform()` |

### 1.2 Path Handling (`tests/unit/core/test_paths.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| PH-001 | Docker socket on Linux | `/var/run/docker.sock` |
| PH-002 | Docker socket on WSL2 | `/var/run/docker.sock` |
| PH-003 | Docker socket on Windows | `//./pipe/docker_engine` |
| PH-004 | Docker socket on macOS (Docker Desktop) | `~/.docker/run/docker.sock` |
| PH-005 | Docker socket on macOS (fallback) | `/var/run/docker.sock` |
| PH-006 | Hosts file on Linux | `/etc/hosts` |
| PH-007 | Hosts file on macOS | `/etc/hosts` |
| PH-008 | Hosts file on WSL2 | `/etc/hosts` |
| PH-009 | Hosts file on Windows | `C:/Windows/System32/drivers/etc/hosts` |
| PH-010 | DevFlow home on Linux | `~/.devflow` |
| PH-011 | DevFlow home on macOS | `~/.devflow` |
| PH-012 | DevFlow home on WSL2 | `~/.devflow` |
| PH-013 | DevFlow home on Windows (APPDATA) | `%APPDATA%/devflow` |
| PH-014 | DevFlow home on Windows (fallback) | `%USERPROFILE%/.devflow` |
| PH-015 | SSH dir on Linux | `~/.ssh` |
| PH-016 | SSH dir on macOS | `~/.ssh` |
| PH-017 | SSH dir on Windows | `%USERPROFILE%/.ssh` |
| PH-018 | Cert dir on Linux | `~/.local/share/mkcert` |
| PH-019 | Cert dir on macOS | `~/Library/Application Support/mkcert` |
| PH-020 | Cert dir on Windows | `%LOCALAPPDATA%/mkcert` |
| PH-021 | Socket mount on Linux | `/var/run/docker.sock:/var/run/docker.sock` |
| PH-022 | Socket mount on Windows | `//./pipe/docker_engine:/var/run/docker.sock` |
| PH-023 | Expand tilde in path | Replaces `~` with home dir |
| PH-024 | Expand env var in path | Replaces `$VAR` with value |
| PH-025 | Normal path is normalized | Returns absolute path |
| PH-026 | `get_docker_socket()` convenience | Returns string |
| PH-027 | `get_hosts_file()` convenience | Returns Path |
| PH-028 | `get_devflow_home()` convenience | Returns Path |
| PH-029 | `get_ssh_dir()` convenience | Returns Path |

---

## 2. Integration Tests

### 2.1 TCP Bridge Server (`tests/integration/test_tcp_bridge.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| TCP-001 | Server starts and stops cleanly | `is_running` true, valid address |
| TCP-002 | Ping handler returns pong | `{"pong": true}` |
| TCP-003 | Echo handler returns message | `{"message": "..."}` |
| TCP-004 | Add handler returns sum | `{"result": 8}` for 5+3 |
| TCP-005 | Unknown method returns -32601 | Method not found error |
| TCP-006 | Handler error returns -32000 | Error message included |
| TCP-007 | Invalid JSON returns -32700 | Parse error |
| TCP-008 | Invalid JSON-RPC version returns -32600 | Invalid request error |
| TCP-009 | Multiple sequential requests | All responses correct |
| TCP-010 | Register method directly | Handler callable works |

### 2.2 TCP Client Connection (`tests/integration/test_tcp_client.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| TCC-001 | Connect to running server | Connection established |
| TCC-002 | Disconnect cleanly | No errors |
| TCC-003 | Reconnect after disconnect | Connection re-established |
| TCC-004 | Connect to invalid host | Returns connection error |
| TCC-005 | Call method on connected client | Returns result |
| TCC-006 | Call method on disconnected client | Returns not connected error |
| TCC-007 | Concurrent calls | All responses received |
| TCC-008 | Large payload handling | Data transmitted correctly |
| TCC-009 | Connection timeout | Proper timeout error |
| TCC-010 | Server disconnect during call | Graceful error handling |

### 2.3 Bridge Mode Selection (`tests/integration/test_bridge_modes.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| BM-001 | Subprocess mode on Linux | Uses stdio communication |
| BM-002 | Subprocess mode on macOS | Uses stdio communication |
| BM-003 | TCP mode on Windows | Uses TCP communication |
| BM-004 | Mode detection auto-select | Correct mode per platform |
| BM-005 | Switch from subprocess to TCP | Mode changes correctly |
| BM-006 | TCP config persistence | Host/port retained |

---

## 3. Component Tests

### 3.1 Docker Provider (`tests/unit/providers/test_docker_crossplatform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| DP-001 | `get_socket_path()` returns platform path | Correct for current platform |
| DP-002 | `get_socket_mount()` returns mount string | Source:target format |
| DP-003 | Socket path on mocked Linux | `/var/run/docker.sock` |
| DP-004 | Socket path on mocked Windows | `//./pipe/docker_engine` |
| DP-005 | Socket mount on mocked macOS | Correct Docker Desktop path |

### 3.2 SSH Provider (`tests/unit/providers/test_ssh_crossplatform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| SP-001 | `get_ssh_dir()` returns platform path | Correct for current platform |
| SP-002 | `get_ssh_key_path()` with default | Returns `~/.ssh/id_rsa` equivalent |
| SP-003 | `get_ssh_key_path()` with custom name | Returns `~/.ssh/{name}` equivalent |
| SP-004 | `get_known_hosts_path()` | Returns `~/.ssh/known_hosts` equivalent |
| SP-005 | `get_ssh_config_path()` | Returns `~/.ssh/config` equivalent |

### 3.3 1Password Provider (`tests/unit/providers/test_onepassword_crossplatform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| OP-001 | Binary name on Linux | `op` |
| OP-002 | Binary name on macOS | `op` |
| OP-003 | Binary name on Windows | `op.exe` |
| OP-004 | Binary name on WSL2 | `op` |

### 3.4 Mkcert Provider (`tests/unit/providers/test_mkcert_crossplatform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| MK-001 | Binary name on Linux | `mkcert` |
| MK-002 | Binary name on Windows | `mkcert.exe` |
| MK-003 | `is_available()` checks both names on Windows | True if either found |
| MK-004 | `get_default_cert_dir()` on Linux | `~/.local/share/mkcert` |
| MK-005 | `get_default_cert_dir()` on macOS | `~/Library/Application Support/mkcert` |
| MK-006 | `get_default_cert_dir()` on Windows | `%LOCALAPPDATA%/mkcert` |

### 3.5 Infrastructure Provider (`tests/unit/providers/test_infrastructure_crossplatform.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| IP-001 | Docker socket mount in Traefik | Uses `get_docker_socket()` |
| IP-002 | Hosts file path in DNS setup | Uses `get_hosts_file()` |
| IP-003 | DevFlow home for data storage | Uses `get_devflow_home()` |

---

## 4. End-to-End Tests

### 4.1 CLI Workflows (`tests/e2e/test_cli_workflows.py`)

| Test ID | Test Case | Platform | Expected Result |
|---------|-----------|----------|-----------------|
| E2E-001 | `devflow --version` | All | Shows version |
| E2E-002 | `devflow doctor` | All | Runs diagnostics |
| E2E-003 | `devflow init` | All | Creates config file |
| E2E-004 | `devflow dev setup` | Linux/macOS | Sets up environment |
| E2E-005 | `devflow dev start` | Linux/macOS | Starts containers |
| E2E-006 | `devflow dev stop` | Linux/macOS | Stops containers |

### 4.2 Windows CLI Wrapper (`tests/e2e/test_windows_wsl2.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| WIN-001 | WSL2 availability check | Detects WSL2 installation |
| WIN-002 | Find Ubuntu distribution | Locates distro |
| WIN-003 | DevFlow installed in WSL2 | `devflow --version` works |
| WIN-004 | CLI delegates to WSL2 | Command runs in WSL2 |
| WIN-005 | Exit codes propagate | WSL2 exit code returned |
| WIN-006 | Stdin/stdout pass through | Interactive commands work |

### 4.3 Service Mode (`tests/e2e/test_service_mode.py`)

| Test ID | Test Case | Expected Result |
|---------|-----------|-----------------|
| SVC-001 | Service starts on port | Binds to specified port |
| SVC-002 | Service handles multiple clients | Concurrent connections |
| SVC-003 | Service graceful shutdown | SIGTERM handled |
| SVC-004 | Service auto-restart (systemd) | Restarts after crash |
| SVC-005 | All handlers registered | All methods available |

---

## 5. Manual Test Procedures

### 5.1 Windows Installation

**Prerequisites**: Windows 10/11 with admin access

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open PowerShell as Admin | Admin prompt opens |
| 2 | Run `wsl --install -d Ubuntu` | WSL2 installs |
| 3 | Restart computer | System reboots |
| 4 | Complete Ubuntu setup | User created |
| 5 | Open Ubuntu terminal | WSL2 terminal opens |
| 6 | Run `pip install devflow` | DevFlow installs |
| 7 | Run `devflow --version` | Version displayed |
| 8 | Run `devflow doctor` | Shows system status |

### 5.2 Windows UI Connection

**Prerequisites**: DevFlow installed in WSL2

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start service in WSL2: `devflow-service` | Server listening message |
| 2 | Install DevFlow UI on Windows | App installed |
| 3 | Launch DevFlow UI | Window opens |
| 4 | Check connection status | Connected to WSL2 |
| 5 | Run a command from UI | Command executes |
| 6 | Stop service in WSL2 | Connection lost indicator |
| 7 | Restart service | UI reconnects |

### 5.3 macOS Installation

**Prerequisites**: macOS 10.15+ with Homebrew

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open Terminal | Terminal opens |
| 2 | Run `pip install devflow` | DevFlow installs |
| 3 | Run `devflow --version` | Version displayed |
| 4 | Run `devflow doctor` | Shows system status |
| 5 | Check Docker socket detection | Uses correct socket path |
| 6 | Launch DevFlow UI | Window opens |
| 7 | Verify subprocess bridge | Connected via stdio |

### 5.4 Linux Installation

**Prerequisites**: Ubuntu 20.04+ or equivalent

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open Terminal | Terminal opens |
| 2 | Run `pip install devflow` | DevFlow installs |
| 3 | Run `devflow --version` | Version displayed |
| 4 | Run `devflow doctor` | Shows system status |
| 5 | Launch DevFlow UI | Window opens |
| 6 | Verify subprocess bridge | Connected via stdio |

### 5.5 Docker Desktop Integration (macOS/Windows)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Install Docker Desktop | Docker installed |
| 2 | Enable WSL2 backend (Windows) | WSL integration enabled |
| 3 | Run `docker ps` in terminal | Shows containers |
| 4 | Run `devflow dev setup` | Uses Docker correctly |
| 5 | Run `devflow dev start` | Containers start |
| 6 | Verify in Docker Desktop | Containers visible |

---

## 6. Test Matrix

### 6.1 Platform Coverage

| Test Category | Linux | macOS | Windows/WSL2 |
|---------------|-------|-------|--------------|
| Platform Detection | ✅ | ✅ | ✅ |
| Path Handling | ✅ | ✅ | ✅ |
| TCP Bridge | ✅ | ✅ | ✅ |
| Docker Provider | ✅ | ✅ | ✅ |
| SSH Provider | ✅ | ✅ | ✅ |
| 1Password Provider | ✅ | ✅ | ✅ |
| Mkcert Provider | ✅ | ✅ | ✅ |
| CLI Workflows | ✅ | ✅ | ✅ |
| UI Connection | ✅ | ✅ | ✅ |

### 6.2 CI/CD Matrix

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.10', '3.11', '3.12']
```

---

## 7. Test Fixtures

### 7.1 Platform Mocking

```python
# tests/conftest.py
import pytest
from unittest.mock import patch, MagicMock
from devflow.core.platform import Platform

@pytest.fixture
def mock_linux():
    """Mock Linux platform."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.LINUX):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            yield

@pytest.fixture
def mock_macos():
    """Mock macOS platform."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.MACOS):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            yield

@pytest.fixture
def mock_windows():
    """Mock Windows platform."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.WINDOWS):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            yield

@pytest.fixture
def mock_wsl2():
    """Mock WSL2 platform."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.WSL2):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            yield
```

### 7.2 TCP Server Fixture

```python
# tests/conftest.py
import pytest_asyncio
from devflow.service.server import DevFlowServer

@pytest_asyncio.fixture
async def tcp_server():
    """Create a test TCP server on random port."""
    server = DevFlowServer(host="127.0.0.1", port=0)
    await server.start_background()
    yield server
    server.stop()

@pytest_asyncio.fixture
async def tcp_client(tcp_server):
    """Create a connected TCP client."""
    import asyncio
    host, port = tcp_server.get_address()
    reader, writer = await asyncio.open_connection(host, port)
    yield (reader, writer)
    writer.close()
    await writer.wait_closed()
```

---

## 8. Running Tests

### 8.1 All Unit Tests

```bash
pytest tests/unit/ -v
```

### 8.2 All Integration Tests

```bash
pytest tests/integration/ -v
```

### 8.3 Platform-Specific Tests

```bash
# Run only cross-platform tests
pytest tests/unit/core/test_platform.py tests/unit/core/test_paths.py -v

# Run TCP bridge tests
pytest tests/integration/test_tcp_bridge.py -v
```

### 8.4 Full Test Suite with Coverage

```bash
pytest tests/ --cov=devflow --cov-report=html -v
```

### 8.5 E2E Tests (Requires Docker)

```bash
pytest tests/e2e/ -v --timeout=120
```

---

## 9. Acceptance Criteria

### 9.1 Unit Tests
- [ ] All 71+ unit tests pass
- [ ] Code coverage > 80% for platform/paths modules
- [ ] No platform-specific test failures

### 9.2 Integration Tests
- [ ] TCP server starts/stops cleanly
- [ ] All JSON-RPC methods work correctly
- [ ] Error handling produces correct codes

### 9.3 E2E Tests
- [ ] CLI works on Linux
- [ ] CLI works on macOS
- [ ] CLI works on Windows via WSL2
- [ ] UI connects on all platforms

### 9.4 Manual Tests
- [ ] Windows installation guide works
- [ ] Docker Desktop integration works
- [ ] Service mode is stable

---

## 10. Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Windows native not supported | Must use WSL2 | Install WSL2 |
| macOS Docker socket varies | May need config | Try multiple paths |
| WSL2 network isolation | Port forwarding needed | Use localhost |
| Async fixture warnings | pytest-asyncio config | Use `@pytest_asyncio.fixture` |
