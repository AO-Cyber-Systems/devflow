//! Backend setup commands - work without Python bridge.
//!
//! These commands handle backend detection, installation, and configuration
//! before the Python bridge is running.

use super::CommandResponse;
use crate::backend::{
    check_devflow_installed, check_docker_container, detect_all_prerequisites, detect_docker,
    detect_python, detect_wsl, detect_wsl_distros_detailed, install_devflow_local,
    install_devflow_wsl_with_progress, pull_docker_image_with_progress, remove_docker_container,
    start_docker_container, start_wsl_distro, start_wsl_service, stop_docker_container,
    stop_wsl_service, test_devflow_connection, validate_wsl_installation, BackendConfig,
    BackendType, GlobalBackendConfig, PrerequisiteStatus, WslDistroStatus, WslInstallValidation,
};
use crate::bridge::{BridgeManager, ConnectionMode};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;
use tauri::{AppHandle, Emitter, State};

/// Response for prerequisite detection.
#[derive(Debug, Serialize, Deserialize)]
pub struct PrerequisiteResponse {
    pub python_available: bool,
    pub python_version: Option<String>,
    pub python_path: Option<String>,
    pub devflow_installed: bool,
    pub devflow_version: Option<String>,
    pub docker_available: bool,
    pub docker_running: bool,
    pub docker_version: Option<String>,
    pub wsl_available: bool,
    pub wsl_distros: Vec<String>,
}

impl From<PrerequisiteStatus> for PrerequisiteResponse {
    fn from(status: PrerequisiteStatus) -> Self {
        Self {
            python_available: status.python_available,
            python_version: status.python_version,
            python_path: status.python_path.map(|p| p.to_string_lossy().to_string()),
            devflow_installed: status.devflow_installed,
            devflow_version: status.devflow_version,
            docker_available: status.docker_available,
            docker_running: status.docker_running,
            docker_version: status.docker_version,
            wsl_available: status.wsl_available,
            wsl_distros: status.wsl_distros,
        }
    }
}

/// Detect system prerequisites for backend installation.
///
/// This command runs without the Python bridge and detects:
/// - Python installation
/// - DevFlow package installation
/// - Docker availability
/// - WSL2 availability (Windows only)
#[tauri::command]
pub fn detect_prerequisites() -> CommandResponse<PrerequisiteResponse> {
    log::info!("Detecting system prerequisites");
    let status = detect_all_prerequisites();
    CommandResponse::ok(PrerequisiteResponse::from(status))
}

/// Get the current backend configuration.
///
/// Returns the global backend config from ~/.devflow/backend.json.
#[tauri::command]
pub fn get_backend_config() -> CommandResponse<GlobalBackendConfig> {
    log::info!("Loading backend configuration");
    let config = GlobalBackendConfig::load();
    CommandResponse::ok(config)
}

/// Save the backend configuration.
///
/// Saves to ~/.devflow/backend.json.
#[tauri::command]
pub fn save_backend_config(config: BackendConfig) -> CommandResponse<()> {
    log::info!("Saving backend configuration: {:?}", config.backend_type);

    let mut global_config = GlobalBackendConfig::load();
    global_config.set_configured(config);

    match global_config.save() {
        Ok(()) => CommandResponse::ok(()),
        Err(e) => CommandResponse::err(e),
    }
}

/// Install log entry for streaming to frontend.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct InstallLogEntry {
    /// Log level: "info", "warning", "error", "success"
    pub level: String,
    /// Log message
    pub message: String,
    /// Optional command output
    pub output: Option<String>,
}

/// Emit an installation log event.
fn emit_install_log(app: &AppHandle, level: &str, message: &str, output: Option<&str>) {
    let entry = InstallLogEntry {
        level: level.to_string(),
        message: message.to_string(),
        output: output.map(|s| s.to_string()),
    };
    let _ = app.emit("install-log", entry);
}

/// Install the backend based on type.
#[tauri::command]
pub fn install_backend(backend_type: BackendType, config: Option<Value>) -> CommandResponse<String> {
    log::info!("Installing backend: {:?}", backend_type);

    match backend_type {
        BackendType::LocalPython => {
            // Get python path from config if provided
            let python_path = config
                .and_then(|c| c.get("python_path")?.as_str().map(|s| s.into()));

            let result = install_devflow_local(python_path.as_ref());
            if result.success {
                CommandResponse::ok(result.message)
            } else {
                CommandResponse::err(result.message)
            }
        }
        BackendType::Docker => {
            // Pull the image
            let pull_result = pull_docker_image_with_progress(|msg| {
                log::info!("{}", msg);
            });
            if !pull_result.success {
                return CommandResponse::err(pull_result.message);
            }

            // Start the container
            let container_name = config
                .as_ref()
                .and_then(|c| c.get("container_name")?.as_str())
                .unwrap_or("devflow-backend");
            let port = config
                .as_ref()
                .and_then(|c| c.get("port")?.as_u64())
                .unwrap_or(9876) as u16;

            let start_result = start_docker_container(container_name, port);
            if start_result.success {
                CommandResponse::ok(start_result.message)
            } else {
                CommandResponse::err(start_result.message)
            }
        }
        BackendType::Wsl2 => {
            let distro = config
                .as_ref()
                .and_then(|c| c.get("wsl_distro")?.as_str())
                .unwrap_or("Ubuntu");
            let port = config
                .as_ref()
                .and_then(|c| c.get("port")?.as_u64())
                .unwrap_or(9876) as u16;

            // Install devflow in WSL
            let install_result = install_devflow_wsl_with_progress(distro, |msg| {
                log::info!("{}", msg);
            });
            if !install_result.success {
                return CommandResponse::err(install_result.message);
            }

            // Start the service
            let start_result = start_wsl_service(distro, port);
            if start_result.success {
                CommandResponse::ok(start_result.message)
            } else {
                CommandResponse::err(start_result.message)
            }
        }
        BackendType::Remote => {
            // Remote backend doesn't need installation, just verify connection
            let host = config
                .as_ref()
                .and_then(|c| c.get("remote_host")?.as_str())
                .unwrap_or("127.0.0.1");
            let port = config
                .as_ref()
                .and_then(|c| c.get("remote_port")?.as_u64())
                .unwrap_or(9876) as u16;

            if test_devflow_connection(host, port) {
                CommandResponse::ok("Remote backend is accessible".to_string())
            } else {
                CommandResponse::err(format!(
                    "Cannot connect to remote backend at {}:{}",
                    host, port
                ))
            }
        }
    }
}

/// Install the backend with progress events.
///
/// Emits "install-log" events to the frontend with detailed progress information.
#[tauri::command]
pub async fn install_backend_with_logs(
    app: AppHandle,
    backend_type: BackendType,
    config: Option<Value>,
) -> CommandResponse<String> {
    log::info!("Installing backend with logs: {:?}", backend_type);

    match backend_type {
        BackendType::LocalPython => {
            emit_install_log(&app, "info", "Starting local Python installation...", None);

            let python_path = config
                .and_then(|c| c.get("python_path")?.as_str().map(|s| s.into()));

            emit_install_log(&app, "info", "Running pip install devflow...", None);
            let result = install_devflow_local(python_path.as_ref());

            if result.success {
                emit_install_log(&app, "success", &result.message, None);
                CommandResponse::ok(result.message)
            } else {
                emit_install_log(&app, "error", &result.message, None);
                CommandResponse::err(result.message)
            }
        }
        BackendType::Docker => {
            emit_install_log(&app, "info", "Starting Docker installation...", None);

            // Pull the image with progress
            emit_install_log(&app, "info", "Pulling Docker image ghcr.io/ao-cyber-systems/devflow:latest...", None);

            let app_clone = app.clone();
            let pull_result = pull_docker_image_with_progress(move |msg| {
                emit_install_log(&app_clone, "info", msg, None);
            });

            if !pull_result.success {
                emit_install_log(&app, "error", &pull_result.message, None);
                return CommandResponse::err(pull_result.message);
            }
            emit_install_log(&app, "success", "Docker image pulled successfully", None);

            // Start the container
            let container_name = config
                .as_ref()
                .and_then(|c| c.get("container_name")?.as_str())
                .unwrap_or("devflow-backend");
            let port = config
                .as_ref()
                .and_then(|c| c.get("port")?.as_u64())
                .unwrap_or(9876) as u16;

            emit_install_log(&app, "info", &format!("Starting container '{}' on port {}...", container_name, port), None);
            let start_result = start_docker_container(container_name, port);

            if start_result.success {
                emit_install_log(&app, "success", &start_result.message, None);
                CommandResponse::ok(start_result.message)
            } else {
                emit_install_log(&app, "error", &start_result.message, None);
                CommandResponse::err(start_result.message)
            }
        }
        BackendType::Wsl2 => {
            let distro = config
                .as_ref()
                .and_then(|c| c.get("wsl_distro")?.as_str())
                .unwrap_or("Ubuntu");
            let port = config
                .as_ref()
                .and_then(|c| c.get("port")?.as_u64())
                .unwrap_or(9876) as u16;

            emit_install_log(&app, "info", &format!("Starting WSL2 installation in {}...", distro), None);

            // Install devflow in WSL with progress
            let app_clone = app.clone();
            let install_result = install_devflow_wsl_with_progress(distro, move |msg| {
                emit_install_log(&app_clone, "info", msg, None);
            });

            if !install_result.success {
                emit_install_log(&app, "error", &install_result.message, None);
                return CommandResponse::err(install_result.message);
            }
            emit_install_log(&app, "success", "DevFlow package installed successfully", None);

            // Start the service
            emit_install_log(&app, "info", &format!("Starting DevFlow service on port {}...", port), None);
            let start_result = start_wsl_service(distro, port);

            if start_result.success {
                emit_install_log(&app, "success", &start_result.message, None);
                CommandResponse::ok(start_result.message)
            } else {
                emit_install_log(&app, "error", &start_result.message, None);
                CommandResponse::err(start_result.message)
            }
        }
        BackendType::Remote => {
            emit_install_log(&app, "info", "Testing remote backend connection...", None);

            let host = config
                .as_ref()
                .and_then(|c| c.get("remote_host")?.as_str())
                .unwrap_or("127.0.0.1");
            let port = config
                .as_ref()
                .and_then(|c| c.get("remote_port")?.as_u64())
                .unwrap_or(9876) as u16;

            emit_install_log(&app, "info", &format!("Connecting to {}:{}...", host, port), None);

            if test_devflow_connection(host, port) {
                emit_install_log(&app, "success", "Remote backend is accessible", None);
                CommandResponse::ok("Remote backend is accessible".to_string())
            } else {
                let msg = format!("Cannot connect to remote backend at {}:{}", host, port);
                emit_install_log(&app, "error", &msg, None);
                CommandResponse::err(msg)
            }
        }
    }
}

/// Start the backend service (Docker container or WSL2 service).
#[tauri::command]
pub fn start_backend_service(config: BackendConfig) -> CommandResponse<()> {
    log::info!("Starting backend service: {:?}", config.backend_type);

    match config.backend_type {
        BackendType::LocalPython => {
            // Local Python doesn't have a separate service - the bridge handles it
            CommandResponse::ok(())
        }
        BackendType::Docker => {
            let container_name = config.container_name.as_deref().unwrap_or("devflow-backend");
            let port = config.tcp_port();
            let result = start_docker_container(container_name, port);
            if result.success {
                CommandResponse::ok(())
            } else {
                CommandResponse::err(result.message)
            }
        }
        BackendType::Wsl2 => {
            let distro = config.wsl_distro.as_deref().unwrap_or("Ubuntu");
            let port = config.tcp_port();
            let result = start_wsl_service(distro, port);
            if result.success {
                CommandResponse::ok(())
            } else {
                CommandResponse::err(result.message)
            }
        }
        BackendType::Remote => {
            // Remote backend is managed externally
            CommandResponse::ok(())
        }
    }
}

/// Stop the backend service (Docker container or WSL2 service).
#[tauri::command]
pub fn stop_backend_service(config: BackendConfig) -> CommandResponse<()> {
    log::info!("Stopping backend service: {:?}", config.backend_type);

    match config.backend_type {
        BackendType::LocalPython => {
            // Local Python is handled by the bridge
            CommandResponse::ok(())
        }
        BackendType::Docker => {
            let container_name = config.container_name.as_deref().unwrap_or("devflow-backend");
            let result = stop_docker_container(container_name);
            if result.success {
                CommandResponse::ok(())
            } else {
                CommandResponse::err(result.message)
            }
        }
        BackendType::Wsl2 => {
            let distro = config.wsl_distro.as_deref().unwrap_or("Ubuntu");
            let port = config.tcp_port();
            let result = stop_wsl_service(distro, port);
            if result.success {
                CommandResponse::ok(())
            } else {
                CommandResponse::err(result.message)
            }
        }
        BackendType::Remote => {
            // Remote backend is managed externally
            CommandResponse::ok(())
        }
    }
}

/// Test connection to the backend.
#[tauri::command]
pub fn test_backend_connection(config: BackendConfig) -> CommandResponse<bool> {
    log::info!("Testing backend connection: {:?}", config.backend_type);

    match config.backend_type {
        BackendType::LocalPython => {
            // For local Python, we check if devflow is installed
            let python_path = config.python_path.as_ref();
            let (installed, _version) = check_devflow_installed(python_path);
            CommandResponse::ok(installed)
        }
        BackendType::Docker => {
            // Check if container is running and responsive
            let container_name = config.container_name.as_deref().unwrap_or("devflow-backend");
            let (_exists, running) = check_docker_container(container_name);
            if !running {
                return CommandResponse::ok(false);
            }
            // Test the TCP connection
            let connected = test_devflow_connection(&config.tcp_host(), config.tcp_port());
            CommandResponse::ok(connected)
        }
        BackendType::Wsl2 | BackendType::Remote => {
            // Test TCP connection
            let connected = test_devflow_connection(&config.tcp_host(), config.tcp_port());
            CommandResponse::ok(connected)
        }
    }
}

/// Configure the bridge manager with the backend config and start it.
#[tauri::command]
pub async fn start_bridge_with_config(
    bridge: State<'_, Arc<BridgeManager>>,
    config: BackendConfig,
) -> Result<CommandResponse<()>, ()> {
    log::info!("Starting bridge with config: {:?}", config.backend_type);

    match config.backend_type {
        BackendType::LocalPython => {
            bridge.set_mode(ConnectionMode::Subprocess);
            if let Some(ref python_path) = config.python_path {
                bridge.set_python_path(python_path.clone());
            }
            // Start in subprocess mode
            match bridge.start("bridge.main", None) {
                Ok(()) => Ok(CommandResponse::ok(())),
                Err(e) => Ok(CommandResponse::err(format!("{}", e))),
            }
        }
        BackendType::Docker | BackendType::Wsl2 | BackendType::Remote => {
            bridge.set_mode(ConnectionMode::Tcp);
            bridge.set_tcp_config(config.tcp_host(), config.tcp_port());
            // Start in TCP mode
            match bridge.start("", None) {
                Ok(()) => Ok(CommandResponse::ok(())),
                Err(e) => Ok(CommandResponse::err(format!("{}", e))),
            }
        }
    }
}

/// Get recommended backend type based on prerequisites.
#[tauri::command]
pub fn get_recommended_backend() -> CommandResponse<BackendType> {
    let status = detect_all_prerequisites();

    // Priority: LocalPython (if devflow installed) > Docker (if running) > WSL2 > LocalPython (if python available)
    if status.devflow_installed {
        return CommandResponse::ok(BackendType::LocalPython);
    }

    if status.docker_available && status.docker_running {
        return CommandResponse::ok(BackendType::Docker);
    }

    if status.wsl_available && !status.wsl_distros.is_empty() {
        return CommandResponse::ok(BackendType::Wsl2);
    }

    if status.python_available {
        return CommandResponse::ok(BackendType::LocalPython);
    }

    // Default to Docker if nothing else is available
    CommandResponse::ok(BackendType::Docker)
}

/// Get detailed status for all WSL distributions.
///
/// Returns information about each distro including:
/// - WSL version (1 vs 2)
/// - Running state
/// - Python availability and version
/// - DevFlow installation status
#[tauri::command]
pub fn get_wsl_distros_detailed() -> CommandResponse<Vec<WslDistroStatus>> {
    log::info!("Getting detailed WSL distro status");
    let distros = detect_wsl_distros_detailed();
    CommandResponse::ok(distros)
}

/// Validate WSL installation prerequisites for a specific distribution.
///
/// Checks:
/// - Is distro WSL2 (not WSL1)?
/// - Is distro running?
/// - Is Python installed with version >= 3.10?
/// - Is pipx available?
/// - Is port available?
/// - Network connectivity
#[tauri::command]
pub fn validate_wsl_install(distro: String, port: u16) -> CommandResponse<WslInstallValidation> {
    log::info!("Validating WSL installation for {}", distro);
    let validation = validate_wsl_installation(&distro, port);
    CommandResponse::ok(validation)
}

/// Start a WSL distribution.
///
/// Useful when a distro is not running and needs to be started
/// before installation can proceed.
#[tauri::command]
pub fn start_wsl(distro: String) -> CommandResponse<()> {
    log::info!("Starting WSL distro: {}", distro);
    match start_wsl_distro(&distro) {
        Ok(()) => CommandResponse::ok(()),
        Err(e) => CommandResponse::err(e),
    }
}
