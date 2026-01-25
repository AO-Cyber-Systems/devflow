# WSL2 Setup Wizard Manual Test Plan

## Prerequisites
- Windows 10/11 with WSL2 enabled
- At least one WSL2 distribution installed (e.g., Ubuntu)
- Optional: WSL1 distribution for testing warnings
- Optional: Multiple distributions for testing selection

## Test Environment Setup

```powershell
# List your WSL distributions
wsl --list --verbose

# Expected output shows VERSION column (1 or 2)
# NAME            STATE           VERSION
# Ubuntu          Running         2
# Debian          Stopped         2
```

---

## Test Cases

### TC-01: Basic Detection
**Steps:**
1. Launch DevFlow app
2. Click "Get Started" on welcome screen
3. Wait for detection to complete

**Expected:**
- WSL2 option appears in backend selection
- Shows "X distribution(s) available"

---

### TC-02: Distro Selection Dropdown
**Steps:**
1. Select "WSL2 Service" backend option
2. Observe the distro dropdown

**Expected:**
- All WSL distributions appear
- Each shows status: (WSL1) if version 1, (Stopped) if not running
- DevFlow installation status shown if already installed

---

### TC-03: Distro Status Display
**Steps:**
1. Select a distribution from dropdown
2. Observe the status grid below

**Expected:**
- Shows WSL2 or WSL1 status with colored indicator
- Shows Running or Stopped status
- Shows Python version or "Not found"
- Shows DevFlow status

---

### TC-04: Validation - Running Distro with Python
**Steps:**
1. Ensure target distro is running: `wsl -d Ubuntu`
2. Ensure Python 3.10+ is installed in distro
3. Select the distro and click Continue

**Expected:**
- Validation passes
- Shows "All checks passed. Ready to install DevFlow in Ubuntu."

---

### TC-05: Validation - Stopped Distro
**Steps:**
1. Stop your distro: `wsl --terminate Ubuntu`
2. Select that distro and click Continue

**Expected:**
- Validation shows "Distribution Not Running" error
- "Start Ubuntu" button appears
- Clicking start button starts distro and re-validates

---

### TC-06: Validation - WSL1 Distro
**Steps:**
1. If you have a WSL1 distro, select it
2. Click Continue

**Expected:**
- Validation shows "WSL1 Distribution" error
- Shows resolution: "Upgrade to WSL2 by running: wsl --set-version <distro> 2"

---

### TC-07: Validation - No Python
**Steps:**
1. Use a distro without Python (or temporarily: `sudo apt remove python3`)
2. Select that distro and click Continue

**Expected:**
- Validation shows "Python Not Installed" error
- Shows resolution command

---

### TC-08: Validation - Python Too Old
**Steps:**
1. Use a distro with Python < 3.10 (rare on modern distros)
2. Select that distro and click Continue

**Expected:**
- Validation shows "Python Version Too Old" error
- Shows current version and required version

---

### TC-09: Validation - Port Conflict
**Steps:**
1. In PowerShell, start a listener: `nc -l 9876` or use netcat
2. Select a valid distro and click Continue

**Expected:**
- Validation shows "Port In Use" error
- Port input appears to select alternative
- Changing port and clicking "Re-check" validates with new port

---

### TC-10: Installation Log Viewer
**Steps:**
1. Complete validation successfully
2. Click "Install"
3. During installation, click "Show Installation Output"

**Expected:**
- Log panel expands showing real-time installation output
- Color-coded entries (info, success, error)
- Auto-scrolls to latest entry
- Can collapse with "Hide Installation Output"

---

### TC-11: Full Installation Flow
**Steps:**
1. Select a clean distro without DevFlow
2. Complete validation
3. Click Install
4. Wait for completion

**Expected:**
- Installation progresses with status messages
- Connection test succeeds
- "Setup Complete" screen appears
- App functions normally after clicking "Start Using DevFlow"

---

### TC-12: Re-installation / Existing Installation
**Steps:**
1. Run setup on a distro that already has DevFlow
2. Observe the distro dropdown

**Expected:**
- Shows "DevFlow installed" or version number
- Installation still works (upgrades/reinstalls)

---

## Test Results Template

| Test Case | Pass/Fail | Notes | Date | Tester |
|-----------|-----------|-------|------|--------|
| TC-01 | | | | |
| TC-02 | | | | |
| TC-03 | | | | |
| TC-04 | | | | |
| TC-05 | | | | |
| TC-06 | | | | |
| TC-07 | | | | |
| TC-08 | | | | |
| TC-09 | | | | |
| TC-10 | | | | |
| TC-11 | | | | |
| TC-12 | | | | |

---

## Edge Cases to Note

1. **Unicode distro names**: Some users have distros with special characters
2. **Slow WSL startup**: First WSL command after boot can take 10+ seconds
3. **Network issues in WSL**: DNS resolution failures are common
4. **Disk space**: WSL vhdx files can grow large
5. **Multiple default distros**: `wsl --set-default` affects behavior
