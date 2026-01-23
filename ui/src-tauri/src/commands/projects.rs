use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct Project {
    pub name: String,
    pub path: String,
    pub configured_at: Option<String>,
    pub last_accessed: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProjectStatus {
    pub name: String,
    pub path: String,
    pub has_devflow_config: bool,
    pub infrastructure_enabled: bool,
    pub services_running: u32,
    pub services_total: u32,
}

/// List all registered projects
#[tauri::command]
pub fn list_projects(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "projects.list", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Add a project to the registry
#[tauri::command]
pub fn add_project(bridge: State<Arc<BridgeManager>>, path: String) -> CommandResponse<Value> {
    match bridge_call(&bridge, "projects.add", Some(json!({ "path": path }))) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Remove a project from the registry
#[tauri::command]
pub fn remove_project(bridge: State<Arc<BridgeManager>>, path: String) -> CommandResponse<Value> {
    match bridge_call(&bridge, "projects.remove", Some(json!({ "path": path }))) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get project status
#[tauri::command]
pub fn get_project_status(
    bridge: State<Arc<BridgeManager>>,
    path: String,
) -> CommandResponse<Value> {
    match bridge_call(&bridge, "projects.status", Some(json!({ "path": path }))) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Open project in file manager
#[tauri::command]
pub fn open_project_folder(path: String) -> CommandResponse<()> {
    match open::that(&path) {
        Ok(()) => CommandResponse::ok(()),
        Err(e) => CommandResponse::err(format!("Failed to open folder: {}", e)),
    }
}

/// Initialize a new project with devflow.yml
#[tauri::command]
pub fn init_project(
    bridge: State<Arc<BridgeManager>>,
    path: String,
    preset: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "projects.init",
        Some(json!({ "path": path, "preset": preset })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
