//! Backend installation commands - pure Rust, no Python bridge needed.

use std::path::PathBuf;
use std::process::Command;

/// Result of an installation operation.
#[derive(Debug)]
pub struct InstallResult {
    pub success: bool,
    pub message: String,
    pub version: Option<String>,
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
    const IMAGE: &str = "ghcr.io/ao-cyber-systems/devflow:latest";

    log::info!("Pulling Docker image: {}", IMAGE);

    let output = Command::new("docker").args(["pull", IMAGE]).output();

    match output {
        Ok(o) if o.status.success() => InstallResult::ok("Docker image pulled successfully"),
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            InstallResult::err(format!("Failed to pull image: {}", stderr))
        }
        Err(e) => InstallResult::err(format!("Failed to run docker: {}", e)),
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

/// Install devflow in a WSL2 distribution.
///
/// Uses pipx for installation (PEP 668 compliant). Falls back to a venv if pipx
/// is unavailable. This avoids the "externally-managed-environment" error on
/// modern Debian/Ubuntu systems.
#[cfg(windows)]
pub fn install_devflow_wsl(distro: &str) -> InstallResult {
    log::info!("Installing devflow in WSL2 distro: {}", distro);

    // Check if pipx is available
    let pipx_check = run_wsl_command(distro, "command -v pipx");
    let has_pipx = pipx_check.map(|o| o.status.success()).unwrap_or(false);

    if has_pipx {
        // Use pipx (preferred for CLI applications)
        log::info!("Using pipx to install devflow");
        return install_devflow_wsl_pipx(distro);
    }

    // Try to install pipx
    log::info!("pipx not found, attempting to install it");
    let pipx_install = run_wsl_command(
        distro,
        "sudo apt-get update && sudo apt-get install -y pipx && pipx ensurepath",
    );

    if pipx_install.map(|o| o.status.success()).unwrap_or(false) {
        return install_devflow_wsl_pipx(distro);
    }

    // Fall back to venv if pipx installation failed
    log::info!("pipx installation failed, falling back to venv");
    install_devflow_wsl_venv(distro)
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
}
