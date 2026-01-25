pub mod config;
pub mod database;
pub mod deploy;
pub mod dev;
pub mod infra;
pub mod projects;
pub mod secrets;
pub mod setup;
pub mod system;

use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;
use tauri::State;

/// Standard response wrapper for all commands
#[derive(Debug, Serialize, Deserialize)]
pub struct CommandResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T> CommandResponse<T> {
    pub fn ok(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn err(message: impl Into<String>) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message.into()),
        }
    }
}

/// Helper to call bridge RPC method and handle errors
pub fn bridge_call(
    bridge: &State<Arc<BridgeManager>>,
    method: &str,
    params: Option<Value>,
) -> Result<Value, String> {
    bridge
        .call(method, params)
        .map_err(|e| format!("Bridge error: {}", e))
}

/// Bridge status command
#[tauri::command]
pub fn get_bridge_status(bridge: State<Arc<BridgeManager>>) -> CommandResponse<String> {
    let state = bridge.get_state();
    CommandResponse::ok(format!("{:?}", state))
}

/// Start bridge command
#[tauri::command]
pub async fn start_bridge(
    bridge: State<'_, Arc<BridgeManager>>,
    bridge_module: String,
    working_dir: Option<String>,
) -> Result<CommandResponse<()>, ()> {
    match bridge.start(&bridge_module, working_dir.as_deref()) {
        Ok(()) => Ok(CommandResponse::ok(())),
        Err(e) => Ok(CommandResponse::err(format!("{}", e))),
    }
}

/// Stop bridge command
#[tauri::command]
pub fn stop_bridge(bridge: State<Arc<BridgeManager>>) -> CommandResponse<()> {
    bridge.stop();
    CommandResponse::ok(())
}
