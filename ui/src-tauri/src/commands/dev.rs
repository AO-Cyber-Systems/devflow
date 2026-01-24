use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct DevStatus {
    pub project: String,
    pub services: Vec<ContainerStatus>,
    pub infrastructure_connected: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ContainerStatus {
    pub name: String,
    pub image: String,
    pub status: String, // "running" | "stopped" | "exited" | "paused"
    pub ports: Vec<String>,
    pub health: Option<String>, // "healthy" | "unhealthy" | "starting" | null
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DevResult {
    pub success: bool,
    pub message: String,
    pub services_affected: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SetupStep {
    pub step: String,
    pub status: String, // "pending" | "running" | "completed" | "failed"
    pub message: Option<String>,
    pub error: Option<String>,
}

/// Get development environment status
#[tauri::command]
pub fn get_dev_status(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
) -> CommandResponse<Value> {
    match bridge_call(&bridge, "dev.status", Some(json!({ "path": project_path }))) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Start development environment
#[tauri::command]
pub fn start_dev(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    service: Option<String>,
    detach: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.start",
        Some(json!({
            "path": project_path,
            "service": service,
            "detach": detach
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Stop development environment
#[tauri::command]
pub fn stop_dev(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    service: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.stop",
        Some(json!({
            "path": project_path,
            "service": service
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Restart a service
#[tauri::command]
pub fn restart_dev_service(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    service: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.restart",
        Some(json!({
            "path": project_path,
            "service": service
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get service logs
#[tauri::command]
pub fn get_dev_logs(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    service: String,
    tail: Option<u32>,
    follow: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.logs",
        Some(json!({
            "path": project_path,
            "service": service,
            "tail": tail,
            "follow": follow
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Execute command in container
#[tauri::command]
pub fn exec_in_container(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    service: String,
    command: Vec<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.exec",
        Some(json!({
            "path": project_path,
            "service": service,
            "command": command
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Reset development environment (remove containers and optionally volumes)
#[tauri::command]
pub fn reset_dev(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    remove_volumes: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "dev.reset",
        Some(json!({
            "path": project_path,
            "remove_volumes": remove_volumes
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Run development setup
#[tauri::command]
pub fn setup_dev(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
) -> CommandResponse<Value> {
    match bridge_call(&bridge, "dev.setup", Some(json!({ "path": project_path }))) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
