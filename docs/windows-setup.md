# DevFlow on Windows

DevFlow on Windows uses WSL2 (Windows Subsystem for Linux) for optimal Docker compatibility and performance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WINDOWS HOST                                 │
│  ┌───────────────┐                                                  │
│  │  Tauri App    │─────TCP/JSON-RPC────┐                           │
│  │  (WebView2)   │                      │                           │
│  └───────────────┘                      ▼                           │
│                           ┌─────────────────┐                       │
│                           │   WSL2 Bridge   │                       │
│                           │  (localhost:X)  │                       │
│                           └────────┬────────┘                       │
│  ┌─────────────────────────────────┼────────────────────────────┐  │
│  │              WSL2 Linux         │                             │  │
│  │  ┌──────────────────────────────┼───────────────────────────┐│  │
│  │  │  Python Service (systemd)    ▼                            ││  │
│  │  │  ┌─────────────────────────────────────────────────────┐ ││  │
│  │  │  │  DevFlow Core                                        │ ││  │
│  │  │  │  ├── Providers (Docker, SSH, 1Password, etc.)       │ ││  │
│  │  │  │  ├── Database Migrations                             │ ││  │
│  │  │  │  └── Infrastructure Management                       │ ││  │
│  │  │  └─────────────────────────────────────────────────────┘ ││  │
│  │  └──────────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Windows 10 version 2004+** or **Windows 11**
2. **WSL2** enabled with Ubuntu distribution
3. **Docker Desktop** with WSL2 backend (recommended) or Docker installed in WSL2

## Installation

### Step 1: Install WSL2

Open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu
```

After installation, restart your computer and complete Ubuntu setup when prompted.

### Step 2: Configure Docker

#### Option A: Docker Desktop (Recommended)

1. Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Open Docker Desktop settings
3. Go to **Resources** > **WSL Integration**
4. Enable integration with your Ubuntu distribution
5. Click **Apply & Restart**

#### Option B: Docker in WSL2

Install Docker directly in WSL2:

```bash
# In WSL2 terminal
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out and back in for group changes to take effect.

### Step 3: Install DevFlow in WSL2

```bash
# In WSL2 terminal
pip install devflow
```

Or install from source:

```bash
git clone https://github.com/your-org/devflow.git
cd devflow
pip install -e ".[dev]"
```

### Step 4: Start DevFlow Service

DevFlow runs as a service in WSL2 that the Windows UI connects to:

```bash
# In WSL2 terminal
devflow-service --host 0.0.0.0 --port 9876
```

For persistent service operation, install as a systemd service:

```bash
# Copy service file
sudo cp /path/to/devflow/devflow/service/devflow.service /etc/systemd/system/

# Enable and start
sudo systemctl enable devflow
sudo systemctl start devflow

# Check status
sudo systemctl status devflow
```

### Step 5: Install DevFlow UI (Windows)

Download and install the DevFlow UI from the [releases page](https://github.com/your-org/devflow/releases).

The UI will automatically detect WSL2 and connect to the service running on `localhost:9876`.

## Using the CLI from Windows

### Option 1: Run in WSL2 Terminal

Open a WSL2 terminal and use DevFlow directly:

```bash
devflow dev up
devflow db migrate
devflow deploy staging
```

### Option 2: Use Windows CLI Wrapper

If you installed the Windows CLI wrapper, you can run from PowerShell:

```powershell
devflow dev up
devflow db migrate
```

The wrapper automatically delegates commands to WSL2.

## Troubleshooting

### WSL2 Not Installed

If you see "WSL2 is not installed":

```powershell
# Check WSL status
wsl --status

# Install if needed
wsl --install
```

### Docker Not Accessible

If Docker commands fail in WSL2:

1. **Docker Desktop users**: Ensure WSL integration is enabled in Docker Desktop settings
2. **Native Docker users**: Check the Docker service is running:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

### Service Connection Failed

If the UI cannot connect to the WSL2 service:

1. Check the service is running:
   ```bash
   wsl -d Ubuntu -- systemctl status devflow
   ```

2. Verify the port is accessible:
   ```bash
   # In WSL2
   netstat -tlnp | grep 9876
   ```

3. Check Windows Firewall isn't blocking the connection

### Slow File Operations

WSL2 file system performance is best when working with files inside the Linux filesystem (`/home/...`) rather than Windows mounted paths (`/mnt/c/...`).

For best performance:
- Clone repositories inside WSL2's Linux filesystem
- Store project files in `/home/username/projects/`

### Network Issues

WSL2 uses a virtual network adapter. If you have connectivity issues:

```powershell
# Reset WSL network
wsl --shutdown
# Wait a few seconds, then restart WSL
wsl
```

## Configuration

### Service Port

To change the default service port, edit the systemd service or start manually:

```bash
devflow-service --host 0.0.0.0 --port 8765
```

Update the UI settings to use the new port.

### Logging

Service logs are available via journald:

```bash
journalctl -u devflow -f
```

Or when running manually, logs go to stdout.

## Uninstalling

### Remove DevFlow from WSL2

```bash
pip uninstall devflow
sudo systemctl disable devflow
sudo rm /etc/systemd/system/devflow.service
```

### Remove Windows UI

Uninstall from Windows Settings > Apps.
