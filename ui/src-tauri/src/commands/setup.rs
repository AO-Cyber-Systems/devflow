use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

/// Get platform information
#[tauri::command]
pub fn get_platform_info(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_platform_info", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get all tool categories
#[tauri::command]
pub fn get_tool_categories(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_categories", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get all available tools
#[tauri::command]
pub fn get_all_tools(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_all_tools", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get essential tools
#[tauri::command]
pub fn get_essential_tools(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_essential_tools", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get tools by category
#[tauri::command]
pub fn get_tools_by_category(
    bridge: State<Arc<BridgeManager>>,
    category: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "setup.get_tools_by_category",
        Some(json!({ "category": category })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get a specific tool by ID
#[tauri::command]
pub fn get_tool(bridge: State<Arc<BridgeManager>>, tool_id: String) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "setup.get_tool",
        Some(json!({ "tool_id": tool_id })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Detect installation status of a tool
#[tauri::command]
pub fn detect_tool(bridge: State<Arc<BridgeManager>>, tool_id: String) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "setup.detect_tool",
        Some(json!({ "tool_id": tool_id })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Detect all tools
#[tauri::command]
pub fn detect_all_tools(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.detect_all_tools", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Detect essential tools
#[tauri::command]
pub fn detect_essential_tools(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.detect_essential_tools", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get installation methods for a tool
#[tauri::command]
pub fn get_install_methods(
    bridge: State<Arc<BridgeManager>>,
    tool_id: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "setup.get_install_methods",
        Some(json!({ "tool_id": tool_id })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Install a tool
#[tauri::command]
pub fn install_tool(
    bridge: State<Arc<BridgeManager>>,
    tool_id: String,
    method: Option<String>,
) -> CommandResponse<Value> {
    let params = match method {
        Some(m) => json!({ "tool_id": tool_id, "method": m }),
        None => json!({ "tool_id": tool_id }),
    };
    match bridge_call(&bridge, "setup.install", Some(params)) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Install multiple tools
#[tauri::command]
pub fn install_multiple_tools(
    bridge: State<Arc<BridgeManager>>,
    tool_ids: Vec<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "setup.install_multiple",
        Some(json!({ "tool_ids": tool_ids })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Check if Mise is available
#[tauri::command]
pub fn check_mise_available(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.check_mise_available", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get Mise installed tools
#[tauri::command]
pub fn get_mise_installed_tools(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_mise_installed_tools", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get available installers
#[tauri::command]
pub fn get_available_installers(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_available_installers", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get prerequisites summary
#[tauri::command]
pub fn get_prerequisites_summary(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.get_prerequisites_summary", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Refresh platform info
#[tauri::command]
pub fn refresh_platform_info(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "setup.refresh_platform_info", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
