use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct DeployStatus {
    pub environment: String,
    pub host: Option<String>,
    pub services: Vec<ServiceStatus>,
    pub last_deploy: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub name: String,
    pub image: String,
    pub replicas: String,
    pub status: String, // "running" | "stopped" | "partial" | "unknown"
    pub last_updated: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeployResult {
    pub success: bool,
    pub deployed: u32,
    pub failed: u32,
    pub dry_run: bool,
    pub results: Vec<DeployServiceResult>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeployServiceResult {
    pub service: String,
    pub status: String, // "deployed" | "failed" | "would_deploy" | "skipped"
    pub image: Option<String>,
    pub error: Option<String>,
}

/// Get deployment status
#[tauri::command]
pub fn get_deploy_status(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    service: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "deploy.status",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "service": service
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Deploy to environment
#[tauri::command]
pub fn deploy(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    service: Option<String>,
    migrate: bool,
    dry_run: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "deploy.deploy",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "service": service,
            "migrate": migrate,
            "dry_run": dry_run
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Rollback deployment
#[tauri::command]
pub fn rollback_deploy(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    service: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "deploy.rollback",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "service": service
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get deployment logs
#[tauri::command]
pub fn get_deploy_logs(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    service: String,
    tail: Option<u32>,
    follow: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "deploy.logs",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "service": service,
            "tail": tail,
            "follow": follow
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// SSH into deployment environment
#[tauri::command]
pub fn get_ssh_command(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    node: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "deploy.ssh_command",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "node": node
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
