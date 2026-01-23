use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct DoctorResult {
    pub overall_status: String, // "healthy" | "warning" | "error"
    pub checks: Vec<DoctorCheck>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DoctorCheck {
    pub name: String,
    pub category: String, // "tool" | "auth" | "config" | "infrastructure"
    pub status: String,   // "ok" | "warning" | "error" | "skipped"
    pub message: String,
    pub details: Option<Value>,
    pub fix_hint: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProviderStatus {
    pub name: String,
    pub binary: String,
    pub available: bool,
    pub authenticated: bool,
    pub version: Option<String>,
    pub path: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    pub platform: String,
    pub os_version: String,
    pub devflow_version: String,
    pub python_version: String,
    pub docker_version: Option<String>,
    pub home_dir: String,
    pub config_dir: String,
}

/// Run system doctor
#[tauri::command]
pub fn run_doctor(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "system.doctor", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Run doctor for specific project
#[tauri::command]
pub fn run_project_doctor(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "system.doctor",
        Some(json!({ "path": project_path })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get system information
#[tauri::command]
pub fn get_system_info(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "system.info", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get provider status
#[tauri::command]
pub fn get_provider_status(
    bridge: State<Arc<BridgeManager>>,
    provider: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "system.provider_status",
        Some(json!({ "provider": provider })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get all provider statuses
#[tauri::command]
pub fn get_all_providers(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "system.all_providers", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Check for updates
#[tauri::command]
pub fn check_updates(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "system.check_updates", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get DevFlow version
#[tauri::command]
pub fn get_version(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "system.version", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
