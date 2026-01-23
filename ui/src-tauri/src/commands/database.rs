use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct MigrationStatus {
    pub environment: String,
    pub executor: String,
    pub applied: u32,
    pub pending: u32,
    pub total: u32,
    pub pending_files: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MigrationResult {
    pub success: bool,
    pub applied: u32,
    pub skipped: u32,
    pub error: Option<String>,
    pub results: Vec<MigrationStepResult>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MigrationStepResult {
    pub file: String,
    pub status: String, // "applied" | "skipped" | "failed"
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RollbackResult {
    pub success: bool,
    pub rolled_back: u32,
    pub failed: u32,
    pub results: Vec<MigrationStepResult>,
}

/// Get migration status
#[tauri::command]
pub fn get_migration_status(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.status",
        Some(json!({
            "path": project_path,
            "environment": environment
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Run pending migrations
#[tauri::command]
pub fn run_migrations(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    dry_run: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.migrate",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "dry_run": dry_run
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Rollback migrations
#[tauri::command]
pub fn rollback_migrations(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    steps: u32,
    dry_run: bool,
    force: bool,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.rollback",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "steps": steps,
            "dry_run": dry_run,
            "force": force
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Create a new migration
#[tauri::command]
pub fn create_migration(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    name: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.create",
        Some(json!({
            "path": project_path,
            "name": name
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get migration history
#[tauri::command]
pub fn get_migration_history(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
    limit: Option<u32>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.history",
        Some(json!({
            "path": project_path,
            "environment": environment,
            "limit": limit
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Test database connection
#[tauri::command]
pub fn test_db_connection(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    environment: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "db.test_connection",
        Some(json!({
            "path": project_path,
            "environment": environment
        })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
