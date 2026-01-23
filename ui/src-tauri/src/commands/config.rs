use super::{bridge_call, CommandResponse};
use crate::bridge::BridgeManager;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct GlobalConfig {
    pub version: String,
    pub git: GlobalGitConfig,
    pub defaults: GlobalDefaultsConfig,
    pub infrastructure: GlobalInfrastructureConfig,
    pub setup_completed: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GlobalGitConfig {
    pub user_name: Option<String>,
    pub user_email: Option<String>,
    pub co_author_enabled: bool,
    pub co_author_name: String,
    pub co_author_email: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GlobalDefaultsConfig {
    pub secrets_provider: Option<String>,
    pub network_name: String,
    pub registry: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GlobalInfrastructureConfig {
    pub auto_start: bool,
    pub traefik_http_port: u16,
    pub traefik_https_port: u16,
    pub traefik_dashboard_port: u16,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DevflowConfig {
    pub version: String,
    pub project: ProjectConfig,
    pub database: Option<DatabaseConfig>,
    pub secrets: Option<SecretsConfig>,
    pub deployment: Option<DeploymentConfig>,
    pub development: Option<DevelopmentConfig>,
    pub infrastructure: Option<InfrastructureConfig>,
    pub git: Option<GitConfig>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProjectConfig {
    pub name: String,
    pub preset: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub migrations: MigrationsConfig,
    pub environments: std::collections::HashMap<String, DatabaseEnvConfig>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MigrationsConfig {
    pub directory: String,
    pub format: String,
    pub tracking_table: String,
    pub tracking_schema: String,
    pub use_supabase_cli: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseEnvConfig {
    pub url_env: Option<String>,
    pub url_secret: Option<String>,
    pub host: Option<String>,
    pub ssh_user: Option<String>,
    pub direct_port: Option<u16>,
    pub require_approval: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SecretsConfig {
    pub provider: Option<String>,
    pub vault: Option<String>,
    pub mappings: Vec<SecretMapping>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SecretMapping {
    pub name: String,
    pub op_item: Option<String>,
    pub op_field: Option<String>,
    pub github_secret: Option<String>,
    pub docker_secret: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeploymentConfig {
    pub registry: Option<String>,
    pub organization: Option<String>,
    pub services: std::collections::HashMap<String, ServiceConfig>,
    pub environments: std::collections::HashMap<String, DeploymentEnvConfig>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ServiceConfig {
    pub image: String,
    pub stack: String,
    pub replicas: u32,
    pub health_endpoint: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeploymentEnvConfig {
    pub host: Option<String>,
    pub ssh_user: String,
    pub ssh_key_secret: Option<String>,
    pub auto_deploy_branch: Option<String>,
    pub require_approval: bool,
    pub approval_environment: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DevelopmentConfig {
    pub compose_file: String,
    pub services: Vec<String>,
    pub env: std::collections::HashMap<String, String>,
    pub ports: std::collections::HashMap<String, u16>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InfrastructureConfig {
    pub enabled: bool,
    pub network_name: String,
    pub traefik: TraefikConfig,
    pub certificates: CertificatesConfig,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TraefikConfig {
    pub http_port: u16,
    pub https_port: u16,
    pub dashboard_port: u16,
    pub dashboard_enabled: bool,
    pub log_level: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CertificatesConfig {
    pub domains: Vec<String>,
    pub cert_dir: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GitConfig {
    pub user: GitUserConfig,
    pub co_author: GitCoAuthorConfig,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GitUserConfig {
    pub name: Option<String>,
    pub email: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GitCoAuthorConfig {
    pub enabled: bool,
    pub name: String,
    pub email: String,
}

/// Get global configuration
#[tauri::command]
pub fn get_global_config(bridge: State<Arc<BridgeManager>>) -> CommandResponse<Value> {
    match bridge_call(&bridge, "config.get_global", None) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Get project configuration
#[tauri::command]
pub fn get_project_config(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "config.get_project",
        Some(json!({ "path": project_path })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Update global configuration
#[tauri::command]
pub fn update_global_config(
    bridge: State<Arc<BridgeManager>>,
    key: String,
    value: Value,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "config.set_global",
        Some(json!({ "key": key, "value": value })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Update project configuration
#[tauri::command]
pub fn update_project_config(
    bridge: State<Arc<BridgeManager>>,
    project_path: String,
    config: Value,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "config.set_project",
        Some(json!({ "path": project_path, "config": config })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}

/// Validate configuration
#[tauri::command]
pub fn validate_config(
    bridge: State<Arc<BridgeManager>>,
    project_path: Option<String>,
) -> CommandResponse<Value> {
    match bridge_call(
        &bridge,
        "config.validate",
        Some(json!({ "path": project_path })),
    ) {
        Ok(data) => CommandResponse::ok(data),
        Err(e) => CommandResponse::err(e),
    }
}
