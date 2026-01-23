use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct InfraStatus {
    pub network_exists: bool,
    pub network_name: String,
    pub traefik_running: bool,
    pub traefik_container_id: Option<String>,
    pub traefik_url: Option<String>,
    pub certificates_valid: bool,
    pub certificates_path: Option<String>,
    pub registered_projects: Vec<RegisteredProject>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RegisteredProject {
    pub name: String,
    pub path: String,
    pub domains: Vec<String>,
    pub compose_files: Vec<String>,
    pub configured_at: String,
    pub backup_path: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InfraResult {
    pub success: bool,
    pub message: String,
    pub details: Option<Value>,
}

/// Get infrastructure status
#[tauri::command]
pub fn get_infra_status(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "infra.status", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Start infrastructure (Traefik, network)
#[tauri::command]
pub fn start_infra(
    bridge: State<Arc<BridgeManager>>,
    force_recreate: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.start",
        Some(json!({ "force_recreate": force_recreate })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Stop infrastructure
#[tauri::command]
pub fn stop_infra(
    bridge: State<Arc<BridgeManager>>,
    remove_volumes: bool,
    remove_network: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.stop",
        Some(json!({
            "remove_volumes": remove_volumes,
            "remove_network": remove_network
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Configure a project for infrastructure
#[tauri::command]
pub fn configure_project_infra(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    compose_file: Option<String>,
    dry_run: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.configure",
        Some(json!({
            "path": project_path,
            "compose_file": compose_file,
            "dry_run": dry_run
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Unconfigure a project from infrastructure
#[tauri::command]
pub fn unconfigure_project_infra(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.unconfigure",
        Some(json!({ "path": project_path })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Regenerate certificates
#[tauri::command]
pub fn regenerate_certs(
    bridge: State<Arc<BridgeManager>>,
    domains: Option<Vec<String>>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.regenerate_certs",
        Some(json!({ "domains": domains })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Manage hosts file entries
#[tauri::command]
pub fn manage_hosts(
    bridge: State<Arc<BridgeManager>>,
    action: String, // "add" | "remove" | "list"
    domains: Option<Vec<String>>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "infra.hosts",
        Some(json!({ "action": action, "domains": domains })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
