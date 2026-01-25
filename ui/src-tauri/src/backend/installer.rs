//! Backend installation commands - pure Rust, no Python bridge needed.

use serde::{Deserialize, Serialize};
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::Command;

use super::detection::{check_wsl_distro_status, is_distro_running, is_wsl2_distro};

/// Result of an installation operation.
#[derive(Debug)]
pub struct InstallResult {
    pub success: bool,
    pub message: String,
    pub version: Option<String>,
}

/// Issues that can prevent WSL installation.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WslInstallIssue {
    /// Distribution is running WSL1, not WSL2
    DistroNotWsl2,
    /// Distribution is not running
    DistroNotRunning,
    /// Python is not installed
    PythonNotInstalled,
    /// Python version is too old
    PythonVersionTooOld {
        version: String,
        required: String,
    },
    /// Cannot reach package servers
    NoNetworkAccess,
    /// Insufficient disk space
    InsufficientDiskSpace {
        available_mb: u64,
        required_mb: u64,
    },
    /// pipx is not available and cannot be installed
    PipxNotAvailable,
    /// Port is already in use
    PortInUse {
        port: u16,
    },
}

/// Result of pre-installation validation for WSL.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WslInstallValidation {
    /// Distribution name
    pub distro: String,
    /// Whether installation can proceed
    pub can_install: bool,
    /// Blocking issues that must be resolved
    pub issues: Vec<WslInstallIssue>,
    /// Non-blocking warnings
    pub warnings: Vec<String>,
}

impl InstallResult {
    pub fn ok(message: impl Into<String>) -> Self {
        Self {
            success: true,
            message: message.into(),
            version: None,
        }
    }

    pub fn ok_with_version(message: impl Into<String>, version: String) -> Self {
        Self {
            success: true,
            message: message.into(),
            version: Some(version),
        }
    }

    pub fn err(message: impl Into<String>) -> Self {
        Self {
            success: false,
            message: message.into(),
            version: None,
        }
    }
}

/// Install the devflow Python package locally.
///
/// Runs `pip install devflow` or `pip install git+https://...` for dev.
pub fn install_devflow_local(python_path: Option<&PathBuf>) -> InstallResult {
    let python = python_path
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "python".to_string()
            } else {
                "python3".to_string()
            }
        });

    log::info!("Installing devflow package using: {}", python);

    // Try pip install devflow first
    let output = Command::new(&python)
        .args(["-m", "pip", "install", "--upgrade", "devflow"])
        .output();

    match output {
        Ok(o) if o.status.success() => {
            // Get installed version
            let version = get_devflow_version(python_path);
            InstallResult::ok_with_version(
                "DevFlow package installed successfully",
                version.unwrap_or_else(|| "unknown".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            // Try from GitHub if PyPI fails
            log::warn!("PyPI install failed, trying GitHub: {}", stderr);
            install_devflow_from_github(python_path)
        }
        Err(e) => InstallResult::err(format!("Failed to run pip: {}", e)),
    }
}

/// Install devflow from GitHub (for development or when PyPI is unavailable).
fn install_devflow_from_github(python_path: Option<&PathBuf>) -> InstallResult {
    let python = python_path
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "python".to_string()
            } else {
                "python3".to_string()
            }
        });

    let output = Command::new(&python)
        .args([
            "-m",
            "pip",
            "install",
            "--upgrade",
            "git+https://github.com/AO-Cyber-Systems/devflow.git",
        ])
        .output();

    match output {
        Ok(o) if o.status.success() => {
            let version = get_devflow_version(python_path);
            InstallResult::ok_with_version(
                "DevFlow package installed from GitHub",
                version.unwrap_or_else(|| "dev".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to install from GitHub: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run pip: {}", e)),
    }
}

/// Get the installed devflow version.
fn get_devflow_version(python_path: Option<&PathBuf>) -> Option<String> {
    let python = python_path
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "python".to_string()
            } else {
                "python3".to_string()
            }
        });

    Command::new(&python)
        .args(["-c", "import devflow; print(devflow.__version__)"])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
}

/// Pull the DevFlow Docker image.
pub fn pull_docker_image() -> InstallResult {
    pull_docker_image_with_progress(|_| {})
}

/// Pull the DevFlow Docker image with progress callback.
pub fn pull_docker_image_with_progress<F>(on_progress: F) -> InstallResult
where
    F: Fn(&str),
{
    const IMAGE: &str = "ghcr.io/ao-cyber-systems/devflow:latest";

    log::info!("Pulling Docker image: {}", IMAGE);
    on_progress(&format!("Pulling image: {}", IMAGE));

    // Use docker pull with --progress=plain for better output
    let output = Command::new("docker")
        .args(["pull", "--progress=plain", IMAGE])
        .output();

    match output {
        Ok(o) if o.status.success() => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            // Report the output
            for line in stdout.lines() {
                if !line.trim().is_empty() {
                    on_progress(line.trim());
                }
            }
            InstallResult::ok("Docker image pulled successfully")
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            on_progress(&format!("Error: {}", stderr.trim()));
            InstallResult::err(format!("Failed to pull image: {}", stderr))
        }
        Err(e) => {
            on_progress(&format!("Error: Failed to run docker: {}", e));
            InstallResult::err(format!("Failed to run docker: {}", e))
        }
    }
}

/// Start the DevFlow Docker container.
pub fn start_docker_container(container_name: &str, port: u16) -> InstallResult {
    const IMAGE: &str = "ghcr.io/ao-cyber-systems/devflow:latest";

    log::info!(
        "Starting Docker container: {} on port {}",
        container_name,
        port
    );

    // First, check if container already exists
    let inspect = Command::new("docker")
        .args(["inspect", container_name])
        .output();

    if inspect.map(|o| o.status.success()).unwrap_or(false) {
        // Container exists, try to start it
        let start = Command::new("docker")
            .args(["start", container_name])
            .output();

        return match start {
            Ok(o) if o.status.success() => InstallResult::ok("Container started"),
            _ => {
                // Remove and recreate
                let _ = Command::new("docker")
                    .args(["rm", "-f", container_name])
                    .output();
                create_docker_container(container_name, port, IMAGE)
            }
        };
    }

    // Container doesn't exist, create it
    create_docker_container(container_name, port, IMAGE)
}

/// Create and start a new Docker container.
fn create_docker_container(container_name: &str, port: u16, image: &str) -> InstallResult {
    // Get home directory for volume mount
    let home = dirs::home_dir();
    let devflow_dir = home.as_ref().map(|h| h.join(".devflow"));

    // Ensure .devflow directory exists
    if let Some(ref dir) = devflow_dir {
        let _ = std::fs::create_dir_all(dir);
    }

    let mut args = vec![
        "run".to_string(),
        "-d".to_string(),
        "--name".to_string(),
        container_name.to_string(),
        "-p".to_string(),
        format!("{}:9876", port),
        "--restart".to_string(),
        "unless-stopped".to_string(),
    ];

    // Add volume mount if possible
    if let Some(ref dir) = devflow_dir {
        args.push("-v".to_string());
        args.push(format!("{}:/root/.devflow", dir.display()));
    }

    args.push(image.to_string());

    let output = Command::new("docker")
        .args(&args)
        .output();

    match output {
        Ok(o) if o.status.success() => {
            InstallResult::ok(format!("Container '{}' started on port {}", container_name, port))
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to start container: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run docker: {}", e)),
    }
}

/// Stop a Docker container.
pub fn stop_docker_container(container_name: &str) -> InstallResult {
    log::info!("Stopping Docker container: {}", container_name);

    let output = Command::new("docker")
        .args(["stop", container_name])
        .output();

    match output {
        Ok(o) if o.status.success() => InstallResult::ok("Container stopped"),
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to stop container: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run docker: {}", e)),
    }
}

/// Remove a Docker container.
pub fn remove_docker_container(container_name: &str) -> InstallResult {
    log::info!("Removing Docker container: {}", container_name);

    let output = Command::new("docker")
        .args(["rm", "-f", container_name])
        .output();

    match output {
        Ok(o) if o.status.success() => InstallResult::ok("Container removed"),
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to remove container: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run docker: {}", e)),
    }
}

/// Check if a port is available on the local machine.
pub fn is_port_available(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

/// Parse a Python version string and check if it meets minimum requirements.
fn check_python_version_meets_minimum(version: &str, min_major: u32, min_minor: u32) -> bool {
    let parts: Vec<&str> = version.split('.').collect();
    if parts.len() < 2 {
        return false;
    }

    let major: u32 = match parts[0].parse() {
        Ok(v) => v,
        Err(_) => return false,
    };
    let minor: u32 = match parts[1].parse() {
        Ok(v) => v,
        Err(_) => return false,
    };

    if major > min_major {
        return true;
    }
    if major == min_major && minor >= min_minor {
        return true;
    }
    false
}

/// Run a bash command in WSL2.
///
/// Uses `wsl -d <distro> -e bash -lc "command"` which:
/// - `-d <distro>`: Targets specific distribution
/// - `-e bash`: Executes bash directly (not through default shell)
/// - `-l`: Login shell (sources profile for PATH)
/// - `-c`: Run command string
#[cfg(windows)]
fn run_wsl_command(distro: &str, command: &str) -> std::io::Result<std::process::Output> {
    Command::new("wsl")
        .args(["-d", distro, "-e", "bash", "-lc", command])
        .output()
}

/// Check network access in WSL distro by testing connection to pypi.org.
#[cfg(windows)]
fn check_wsl_network_access(distro: &str) -> bool {
    let check_cmd = "curl -s --connect-timeout 5 -o /dev/null -w '%{http_code}' https://pypi.org 2>/dev/null || echo 'FAIL'";

    if let Ok(output) = run_wsl_command(distro, check_cmd) {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            // Accept any HTTP response (200, 301, etc.) as success
            return result != "FAIL" && result.len() == 3 && result.chars().all(|c| c.is_ascii_digit());
        }
    }
    false
}

#[cfg(not(windows))]
fn check_wsl_network_access(_distro: &str) -> bool {
    false
}

/// Check available disk space in WSL distro.
#[cfg(windows)]
fn check_wsl_disk_space(distro: &str) -> Option<u64> {
    // Get available space in MB using df
    let check_cmd = "df -m / 2>/dev/null | tail -1 | awk '{print $4}'";

    if let Ok(output) = run_wsl_command(distro, check_cmd) {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            return result.parse().ok();
        }
    }
    None
}

#[cfg(not(windows))]
fn check_wsl_disk_space(_distro: &str) -> Option<u64> {
    None
}

/// Check if pipx is available or can be installed in WSL distro.
#[cfg(windows)]
fn check_wsl_pipx_availability(distro: &str) -> bool {
    // Check if pipx is already installed
    let check_cmd = "command -v pipx >/dev/null 2>&1 && echo 'yes' || echo 'no'";

    if let Ok(output) = run_wsl_command(distro, check_cmd) {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if result == "yes" {
                return true;
            }
        }
    }

    // Check if apt is available (we can install pipx via apt)
    let apt_check = "command -v apt-get >/dev/null 2>&1 && echo 'yes' || echo 'no'";
    if let Ok(output) = run_wsl_command(distro, apt_check) {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            return result == "yes";
        }
    }

    false
}

#[cfg(not(windows))]
fn check_wsl_pipx_availability(_distro: &str) -> bool {
    false
}

/// Validate WSL installation prerequisites.
///
/// Checks:
/// 1. Is distro WSL2 (not WSL1)?
/// 2. Is distro running?
/// 3. Is Python installed? Version >= 3.10?
/// 4. Is pipx available or can be installed?
/// 5. Is port available?
/// 6. Basic network connectivity test
#[cfg(windows)]
pub fn validate_wsl_installation(distro: &str, port: u16) -> WslInstallValidation {
    let mut issues = Vec::new();
    let mut warnings = Vec::new();

    // Check 1: Is distro WSL2?
    if !is_wsl2_distro(distro) {
        issues.push(WslInstallIssue::DistroNotWsl2);
    }

    // Check 2: Is distro running?
    let running = is_distro_running(distro);
    if !running {
        issues.push(WslInstallIssue::DistroNotRunning);
        // If not running, we can't check the rest
        return WslInstallValidation {
            distro: distro.to_string(),
            can_install: false,
            issues,
            warnings,
        };
    }

    // Get detailed status (includes Python check)
    let status = check_wsl_distro_status(distro);

    // Check 3: Python availability and version
    if !status.python_available {
        issues.push(WslInstallIssue::PythonNotInstalled);
    } else if let Some(ref version) = status.python_version {
        // Require Python 3.10+
        if !check_python_version_meets_minimum(version, 3, 10) {
            issues.push(WslInstallIssue::PythonVersionTooOld {
                version: version.clone(),
                required: "3.10".to_string(),
            });
        }
    }

    // Check 4: pipx availability
    if !check_wsl_pipx_availability(distro) {
        issues.push(WslInstallIssue::PipxNotAvailable);
    }

    // Check 5: Port availability (on Windows side)
    if !is_port_available(port) {
        issues.push(WslInstallIssue::PortInUse { port });
    }

    // Check 6: Network access
    if !check_wsl_network_access(distro) {
        issues.push(WslInstallIssue::NoNetworkAccess);
    }

    // Check 7: Disk space (warning only, not blocking)
    const REQUIRED_MB: u64 = 500; // 500MB minimum
    if let Some(available_mb) = check_wsl_disk_space(distro) {
        if available_mb < REQUIRED_MB {
            issues.push(WslInstallIssue::InsufficientDiskSpace {
                available_mb,
                required_mb: REQUIRED_MB,
            });
        } else if available_mb < REQUIRED_MB * 2 {
            warnings.push(format!(
                "Low disk space: {}MB available ({}MB recommended)",
                available_mb,
                REQUIRED_MB * 2
            ));
        }
    }

    // Add warning if devflow is already installed
    if status.devflow_installed {
        if let Some(ref version) = status.devflow_version {
            warnings.push(format!("DevFlow {} is already installed", version));
        } else {
            warnings.push("DevFlow is already installed".to_string());
        }
    }

    WslInstallValidation {
        distro: distro.to_string(),
        can_install: issues.is_empty(),
        issues,
        warnings,
    }
}

#[cfg(not(windows))]
pub fn validate_wsl_installation(distro: &str, _port: u16) -> WslInstallValidation {
    WslInstallValidation {
        distro: distro.to_string(),
        can_install: false,
        issues: vec![],
        warnings: vec!["WSL is only available on Windows".to_string()],
    }
}

/// Install devflow in a WSL2 distribution.
///
/// Uses pipx for installation (PEP 668 compliant). Falls back to a venv if pipx
/// is unavailable. This avoids the "externally-managed-environment" error on
/// modern Debian/Ubuntu systems.
#[cfg(windows)]
pub fn install_devflow_wsl(distro: &str) -> InstallResult {
    install_devflow_wsl_with_progress(distro, |_| {})
}

/// Install devflow in a WSL2 distribution with progress callback.
#[cfg(windows)]
pub fn install_devflow_wsl_with_progress<F>(distro: &str, on_progress: F) -> InstallResult
where
    F: Fn(&str),
{
    log::info!("Installing devflow in WSL2 distro: {}", distro);
    on_progress(&format!("Installing DevFlow in WSL2 distro: {}", distro));

    // Check if pipx is available
    on_progress("Checking for pipx...");
    let pipx_check = run_wsl_command(distro, "command -v pipx");
    let has_pipx = pipx_check.map(|o| o.status.success()).unwrap_or(false);

    if has_pipx {
        // Use pipx (preferred for CLI applications)
        on_progress("Found pipx, using it to install devflow...");
        log::info!("Using pipx to install devflow");
        return install_devflow_wsl_pipx_with_progress(distro, on_progress);
    }

    // Try to install pipx
    on_progress("pipx not found, installing it...");
    log::info!("pipx not found, attempting to install it");

    on_progress("Running: sudo apt-get update...");
    let pipx_install = run_wsl_command(
        distro,
        "sudo apt-get update && sudo apt-get install -y pipx && pipx ensurepath",
    );

    if let Ok(ref output) = pipx_install {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines().take(10) {
            if !line.trim().is_empty() {
                on_progress(line.trim());
            }
        }
    }

    if pipx_install.map(|o| o.status.success()).unwrap_or(false) {
        on_progress("pipx installed successfully");
        return install_devflow_wsl_pipx_with_progress(distro, on_progress);
    }

    // Fall back to venv if pipx installation failed
    on_progress("pipx installation failed, falling back to virtual environment...");
    log::info!("pipx installation failed, falling back to venv");
    install_devflow_wsl_venv_with_progress(distro, on_progress)
}

#[cfg(not(windows))]
pub fn install_devflow_wsl_with_progress<F>(_distro: &str, _on_progress: F) -> InstallResult
where
    F: Fn(&str),
{
    InstallResult::err("WSL2 is only available on Windows")
}

/// Install devflow using pipx in WSL2 with progress.
#[cfg(windows)]
fn install_devflow_wsl_pipx_with_progress<F>(distro: &str, on_progress: F) -> InstallResult
where
    F: Fn(&str),
{
    on_progress("Installing devflow via pipx...");

    // Install devflow with pipx
    let output = run_wsl_command(
        distro,
        "pipx install devflow --force 2>&1 || ~/.local/bin/pipx install devflow --force 2>&1",
    );

    match output {
        Ok(o) if o.status.success() => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            for line in stdout.lines() {
                if !line.trim().is_empty() {
                    on_progress(line.trim());
                }
            }
            let version = get_wsl_devflow_version(distro);
            on_progress(&format!("DevFlow {} installed successfully", version.as_deref().unwrap_or("unknown")));
            InstallResult::ok_with_version(
                format!("DevFlow installed in WSL2 ({}) via pipx", distro),
                version.unwrap_or_else(|| "unknown".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            let stdout = String::from_utf8_lossy(&o.stdout);
            on_progress(&format!("pipx install from PyPI failed: {}", stderr.trim()));

            // Try installing from GitHub
            on_progress("Trying to install from GitHub...");
            let github_output = run_wsl_command(
                distro,
                "pipx install git+https://github.com/AO-Cyber-Systems/devflow.git --force 2>&1 || \
                 ~/.local/bin/pipx install git+https://github.com/AO-Cyber-Systems/devflow.git --force 2>&1",
            );

            match github_output {
                Ok(o) if o.status.success() => {
                    let stdout = String::from_utf8_lossy(&o.stdout);
                    for line in stdout.lines() {
                        if !line.trim().is_empty() {
                            on_progress(line.trim());
                        }
                    }
                    let version = get_wsl_devflow_version(distro);
                    on_progress(&format!("DevFlow {} installed from GitHub", version.as_deref().unwrap_or("dev")));
                    InstallResult::ok_with_version(
                        format!("DevFlow installed in WSL2 ({}) via pipx from GitHub", distro),
                        version.unwrap_or_else(|| "dev".to_string()),
                    )
                }
                Ok(o) => {
                    let stderr = String::from_utf8_lossy(&o.stderr);
                    on_progress(&format!("Error: {}", stderr.trim()));
                    InstallResult::err(format!("Failed to install via pipx: {}", stderr))
                }
                Err(e) => {
                    on_progress(&format!("Error: Failed to run pipx: {}", e));
                    InstallResult::err(format!("Failed to run pipx: {}", e))
                }
            }
        }
        Err(e) => {
            on_progress(&format!("Error: Failed to run wsl: {}", e));
            InstallResult::err(format!("Failed to run wsl: {}", e))
        }
    }
}

/// Install devflow in a virtual environment in WSL2 with progress.
#[cfg(windows)]
fn install_devflow_wsl_venv_with_progress<F>(distro: &str, on_progress: F) -> InstallResult
where
    F: Fn(&str),
{
    let venv_path = "$HOME/.local/share/devflow-venv";
    on_progress(&format!("Creating virtual environment at {}", venv_path));

    // Ensure python3-venv is installed and create venv
    on_progress("Installing python3-venv...");
    let setup_cmd = format!(
        "sudo apt-get update && sudo apt-get install -y python3-venv && \
         python3 -m venv {venv} && \
         {venv}/bin/pip install --upgrade pip && \
         {venv}/bin/pip install devflow",
        venv = venv_path
    );

    let output = run_wsl_command(distro, &setup_cmd);

    match output {
        Ok(o) if o.status.success() => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            for line in stdout.lines().take(20) {
                if !line.trim().is_empty() && !line.contains("Reading package lists") {
                    on_progress(line.trim());
                }
            }

            // Create a symlink to make devflow accessible
            on_progress("Creating symlink...");
            let link_cmd = format!(
                "mkdir -p $HOME/.local/bin && ln -sf {}/bin/devflow $HOME/.local/bin/devflow",
                venv_path
            );
            let _ = run_wsl_command(distro, &link_cmd);

            let version = get_wsl_devflow_version(distro);
            on_progress(&format!("DevFlow {} installed in virtual environment", version.as_deref().unwrap_or("unknown")));
            InstallResult::ok_with_version(
                format!("DevFlow installed in WSL2 ({}) via venv", distro),
                version.unwrap_or_else(|| "unknown".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            on_progress(&format!("Error: {}", stderr.trim()));
            InstallResult::err(format!("Failed to install in venv: {}", stderr))
        }
        Err(e) => {
            on_progress(&format!("Error: Failed to run wsl: {}", e));
            InstallResult::err(format!("Failed to run wsl: {}", e))
        }
    }
}

/// Install devflow using pipx in WSL2.
#[cfg(windows)]
fn install_devflow_wsl_pipx(distro: &str) -> InstallResult {
    // Install devflow with pipx, using full path to pipx in case PATH isn't set
    // The `|| true` ensures we continue even if the package isn't found on PyPI yet
    let output = run_wsl_command(
        distro,
        "pipx install devflow --force 2>/dev/null || ~/.local/bin/pipx install devflow --force",
    );

    match output {
        Ok(o) if o.status.success() => {
            // Get version
            let version = get_wsl_devflow_version(distro);
            InstallResult::ok_with_version(
                format!("DevFlow installed in WSL2 ({}) via pipx", distro),
                version.unwrap_or_else(|| "unknown".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            // Try installing from GitHub if PyPI fails
            log::warn!("pipx install from PyPI failed, trying GitHub: {}", stderr);
            let github_output = run_wsl_command(
                distro,
                "pipx install git+https://github.com/AO-Cyber-Systems/devflow.git --force 2>/dev/null || \
                 ~/.local/bin/pipx install git+https://github.com/AO-Cyber-Systems/devflow.git --force",
            );

            match github_output {
                Ok(o) if o.status.success() => {
                    let version = get_wsl_devflow_version(distro);
                    InstallResult::ok_with_version(
                        format!("DevFlow installed in WSL2 ({}) via pipx from GitHub", distro),
                        version.unwrap_or_else(|| "dev".to_string()),
                    )
                }
                Ok(o) => {
                    let stderr = String::from_utf8_lossy(&o.stderr);
                    InstallResult::err(format!("Failed to install via pipx: {}", stderr))
                }
                Err(e) => InstallResult::err(format!("Failed to run pipx: {}", e)),
            }
        }
        Err(e) => InstallResult::err(format!("Failed to run wsl: {}", e)),
    }
}

/// Install devflow in a virtual environment in WSL2.
#[cfg(windows)]
fn install_devflow_wsl_venv(distro: &str) -> InstallResult {
    // Use expanded path since ~ might not expand in all contexts
    let venv_path = "$HOME/.local/share/devflow-venv";

    // Ensure python3-venv is installed and create venv
    let setup_cmd = format!(
        "sudo apt-get update && sudo apt-get install -y python3-venv && \
         python3 -m venv {venv} && \
         {venv}/bin/pip install --upgrade pip && \
         {venv}/bin/pip install devflow",
        venv = venv_path
    );

    let output = run_wsl_command(distro, &setup_cmd);

    match output {
        Ok(o) if o.status.success() => {
            // Create a symlink to make devflow accessible
            let link_cmd = format!(
                "mkdir -p $HOME/.local/bin && ln -sf {}/bin/devflow $HOME/.local/bin/devflow",
                venv_path
            );
            let _ = run_wsl_command(distro, &link_cmd);

            let version = get_wsl_devflow_version(distro);
            InstallResult::ok_with_version(
                format!("DevFlow installed in WSL2 ({}) via venv", distro),
                version.unwrap_or_else(|| "unknown".to_string()),
            )
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to install in venv: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run wsl: {}", e)),
    }
}

/// Get devflow version from WSL2.
#[cfg(windows)]
fn get_wsl_devflow_version(distro: &str) -> Option<String> {
    // Try multiple locations since PATH might not include ~/.local/bin
    run_wsl_command(
        distro,
        "devflow --version 2>/dev/null || \
         ~/.local/bin/devflow --version 2>/dev/null || \
         $HOME/.local/share/devflow-venv/bin/devflow --version 2>/dev/null",
    )
    .ok()
    .filter(|o| o.status.success())
    .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
}

#[cfg(not(windows))]
pub fn install_devflow_wsl(_distro: &str) -> InstallResult {
    InstallResult::err("WSL2 is only available on Windows")
}

/// Start the devflow bridge service in WSL2.
#[cfg(windows)]
pub fn start_wsl_service(distro: &str, port: u16) -> InstallResult {
    log::info!("Starting devflow service in WSL2 ({})", distro);

    // Kill any existing service
    let _ = run_wsl_command(distro, &format!("pkill -f 'bridge.main.*--port {}' || true", port));

    // Start the service in the background
    let start_cmd = format!(
        "nohup python3 -m bridge.main --tcp --port {} > /tmp/devflow-bridge.log 2>&1 &",
        port
    );

    let output = run_wsl_command(distro, &start_cmd);

    match output {
        Ok(o) if o.status.success() => {
            // Give it a moment to start
            std::thread::sleep(std::time::Duration::from_secs(2));

            // Verify it's running
            let check = run_wsl_command(distro, &format!("pgrep -f 'bridge.main.*--port {}'", port));

            if check.map(|o| o.status.success()).unwrap_or(false) {
                InstallResult::ok(format!("DevFlow service started in WSL2 on port {}", port))
            } else {
                InstallResult::err("Service started but process not found")
            }
        }
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to start service: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run wsl: {}", e)),
    }
}

#[cfg(not(windows))]
pub fn start_wsl_service(_distro: &str, _port: u16) -> InstallResult {
    InstallResult::err("WSL2 is only available on Windows")
}

/// Stop the devflow bridge service in WSL2.
#[cfg(windows)]
pub fn stop_wsl_service(distro: &str, port: u16) -> InstallResult {
    log::info!("Stopping devflow service in WSL2 ({})", distro);

    let output = run_wsl_command(distro, &format!("pkill -f 'bridge.main.*--port {}'", port));

    match output {
        Ok(_) => InstallResult::ok("DevFlow service stopped in WSL2"),
        Err(e) => InstallResult::err(format!("Failed to stop service: {}", e)),
    }
}

#[cfg(not(windows))]
pub fn stop_wsl_service(_distro: &str, _port: u16) -> InstallResult {
    InstallResult::err("WSL2 is only available on Windows")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_install_result() {
        let ok = InstallResult::ok("Success");
        assert!(ok.success);
        assert_eq!(ok.message, "Success");

        let err = InstallResult::err("Failed");
        assert!(!err.success);
        assert_eq!(err.message, "Failed");
    }

    #[test]
    fn test_python_version_check() {
        // Test valid versions
        assert!(check_python_version_meets_minimum("3.10.0", 3, 10));
        assert!(check_python_version_meets_minimum("3.11.5", 3, 10));
        assert!(check_python_version_meets_minimum("3.12.0", 3, 10));
        assert!(check_python_version_meets_minimum("4.0.0", 3, 10));

        // Test invalid versions
        assert!(!check_python_version_meets_minimum("3.9.0", 3, 10));
        assert!(!check_python_version_meets_minimum("3.8.15", 3, 10));
        assert!(!check_python_version_meets_minimum("2.7.18", 3, 10));

        // Test edge cases
        assert!(check_python_version_meets_minimum("3.10", 3, 10));
        assert!(!check_python_version_meets_minimum("3", 3, 10));
        assert!(!check_python_version_meets_minimum("invalid", 3, 10));
    }

    #[test]
    fn test_wsl_install_issue_serialization() {
        let issue = WslInstallIssue::PythonVersionTooOld {
            version: "3.8.10".to_string(),
            required: "3.10".to_string(),
        };

        let json = serde_json::to_string(&issue).unwrap();
        assert!(json.contains("python_version_too_old"));
        assert!(json.contains("3.8.10"));
        assert!(json.contains("3.10"));

        let port_issue = WslInstallIssue::PortInUse { port: 9876 };
        let json2 = serde_json::to_string(&port_issue).unwrap();
        assert!(json2.contains("port_in_use"));
        assert!(json2.contains("9876"));
    }

    #[test]
    fn test_wsl_install_validation_serialization() {
        let validation = WslInstallValidation {
            distro: "Ubuntu".to_string(),
            can_install: false,
            issues: vec![
                WslInstallIssue::DistroNotRunning,
                WslInstallIssue::PythonNotInstalled,
            ],
            warnings: vec!["Low disk space".to_string()],
        };

        let json = serde_json::to_string(&validation).unwrap();
        let parsed: WslInstallValidation = serde_json::from_str(&json).unwrap();

        assert_eq!(parsed.distro, "Ubuntu");
        assert!(!parsed.can_install);
        assert_eq!(parsed.issues.len(), 2);
        assert_eq!(parsed.warnings.len(), 1);
    }

    // Platform-specific tests for WSL installation validation

    #[test]
    fn test_validate_wsl_installation_returns_valid_result() {
        // Should not panic on any platform
        let validation = validate_wsl_installation("Ubuntu", 9876);
        println!("Validation result: {:?}", validation);

        // Should always return a valid struct with the distro name
        assert_eq!(validation.distro, "Ubuntu");

        #[cfg(not(windows))]
        {
            // On non-Windows, validation should fail
            assert!(!validation.can_install, "Should not be installable on non-Windows");
            // Non-Windows stub returns a warning message instead of issues
            assert!(!validation.warnings.is_empty(), "Should have warnings on non-Windows");
        }
    }

    #[test]
    fn test_validate_wsl_installation_nonexistent_distro() {
        // Should handle nonexistent distro gracefully
        let validation = validate_wsl_installation("nonexistent-distro-12345", 9876);
        println!("Validation for nonexistent distro: {:?}", validation);

        assert_eq!(validation.distro, "nonexistent-distro-12345");
        assert!(!validation.can_install, "Should not be installable for nonexistent distro");
    }

    #[test]
    fn test_validate_wsl_installation_different_ports() {
        // Test with various port numbers
        for port in [1024u16, 8080, 9876, 49152, 65535] {
            let validation = validate_wsl_installation("Ubuntu", port);
            assert_eq!(validation.distro, "Ubuntu");
            // Validation should complete without panic
            println!("Validation with port {}: can_install={}", port, validation.can_install);
        }
    }

    #[test]
    fn test_is_port_available() {
        // High ports are usually available
        let high_port = is_port_available(59999);
        println!("Port 59999 available: {}", high_port);
        // Can't assert true because something might be using it

        // Low ports (< 1024) might require elevated permissions
        // Just verify it doesn't panic
        let _low_port = is_port_available(80);
    }

    #[test]
    fn test_wsl_install_all_issue_types_serialize() {
        // Ensure all issue variants serialize correctly
        let issues = vec![
            WslInstallIssue::DistroNotWsl2,
            WslInstallIssue::DistroNotRunning,
            WslInstallIssue::PythonNotInstalled,
            WslInstallIssue::PythonVersionTooOld {
                version: "3.8.0".to_string(),
                required: "3.10".to_string(),
            },
            WslInstallIssue::NoNetworkAccess,
            WslInstallIssue::InsufficientDiskSpace {
                available_mb: 100,
                required_mb: 500,
            },
            WslInstallIssue::PipxNotAvailable,
            WslInstallIssue::PortInUse { port: 9876 },
        ];

        for issue in issues {
            let json = serde_json::to_string(&issue).unwrap();
            println!("Issue JSON: {}", json);
            // Verify it can be deserialized back
            let _: WslInstallIssue = serde_json::from_str(&json).unwrap();
        }
    }
}
