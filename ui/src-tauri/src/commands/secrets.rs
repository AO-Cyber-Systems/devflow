use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct SecretInfo {
    pub name: String,
    pub source: String, // "1password" | "env" | "docker"
    pub mapped_to: Vec<String>,
    pub last_synced: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SecretsList {
    pub source: String,
    pub environment: String,
    pub secrets: Vec<SecretInfo>,
    pub mapped_count: u32,
    pub total_count: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncResult {
    pub success: bool,
    pub synced: u32,
    pub failed: u32,
    pub dry_run: bool,
    pub results: Vec<SyncStepResult>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncStepResult {
    pub secret: String,
    pub from_source: String,
    pub to_target: String,
    pub status: String, // "synced" | "failed" | "would_sync" | "skipped"
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerifyResult {
    pub success: bool,
    pub in_sync: u32,
    pub out_of_sync: u32,
    pub results: Vec<VerifyStepResult>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerifyStepResult {
    pub secret: String,
    pub status: String, // "in_sync" | "out_of_sync" | "missing" | "error"
    pub details: Option<String>,
}

/// List secrets
#[tauri::command]
pub fn list_secrets(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: Option<String>,
    source: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "secrets.list",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "source": source
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Sync secrets between sources
#[tauri::command]
pub fn sync_secrets(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    from_source: String,
    to_target: String,
    environment: Option<String>,
    dry_run: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "secrets.sync",
        Some(json!({
            "path": project_path,
            "from": from_source,
            "to": to_target,
            "environment": environment,
            "dry_run": dry_run
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Verify secrets are in sync
#[tauri::command]
pub fn verify_secrets(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "secrets.verify",
        Some(json!({
            "path": project_path,
            "environment": environment
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Export secrets to file or env format
#[tauri::command]
pub fn export_secrets(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    format: String, // "env" | "json" | "yaml"
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "secrets.export",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "format": format
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get available secret providers
#[tauri::command]
pub fn get_secret_providers(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "secrets.providers", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
