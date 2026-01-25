//! Backend configuration types and persistence.

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

/// Backend type enumeration.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BackendType {
    /// Local Python installation (pip install devflow, subprocess mode)
    LocalPython,
    /// Docker container (ghcr.io/ao-cyber-systems/devflow, TCP mode)
    Docker,
    /// WSL2 service (Windows only, TCP mode)
    Wsl2,
    /// Remote DevFlow instance (TCP mode)
    Remote,
}

impl Default for BackendType {
    fn default() -> Self {
        Self::LocalPython
    }
}

/// Backend configuration for a specific type.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct BackendConfig {
    /// The type of backend
    pub backend_type: BackendType,
    /// Path to Python executable (for LocalPython)
    pub python_path: Option<PathBuf>,
    /// Docker container name (for Docker)
    pub container_name: Option<String>,
    /// WSL distribution name (for Wsl2)
    pub wsl_distro: Option<String>,
    /// Remote host (for Remote, Docker, Wsl2)
    pub remote_host: Option<String>,
    /// Remote port (for Remote, Docker, Wsl2) - defaults to 9876
    pub remote_port: Option<u16>,
    /// Whether to auto-start the backend on app launch
    pub auto_start: bool,
}

impl BackendConfig {
    /// Create a new LocalPython backend config.
    pub fn local_python(python_path: Option<PathBuf>) -> Self {
        Self {
            backend_type: BackendType::LocalPython,
            python_path,
            auto_start: true,
            ..Default::default()
        }
    }

    /// Create a new Docker backend config.
    pub fn docker(container_name: Option<String>) -> Self {
        Self {
            backend_type: BackendType::Docker,
            container_name: container_name.or_else(|| Some("devflow-backend".to_string())),
            remote_host: Some("127.0.0.1".to_string()),
            remote_port: Some(9876),
            auto_start: true,
            ..Default::default()
        }
    }

    /// Create a new WSL2 backend config.
    pub fn wsl2(distro: Option<String>) -> Self {
        Self {
            backend_type: BackendType::Wsl2,
            wsl_distro: distro.or_else(|| Some("Ubuntu".to_string())),
            remote_host: Some("127.0.0.1".to_string()),
            remote_port: Some(9876),
            auto_start: true,
            ..Default::default()
        }
    }

    /// Create a new Remote backend config.
    pub fn remote(host: String, port: u16) -> Self {
        Self {
            backend_type: BackendType::Remote,
            remote_host: Some(host),
            remote_port: Some(port),
            auto_start: false,
            ..Default::default()
        }
    }

    /// Get the TCP host for this backend (Docker, WSL2, Remote).
    pub fn tcp_host(&self) -> String {
        self.remote_host
            .clone()
            .unwrap_or_else(|| "127.0.0.1".to_string())
    }

    /// Get the TCP port for this backend.
    pub fn tcp_port(&self) -> u16 {
        self.remote_port.unwrap_or(9876)
    }
}

/// Global backend configuration stored at ~/.devflow/backend.json
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct GlobalBackendConfig {
    /// The default backend configuration
    pub default_backend: Option<BackendConfig>,
    /// Whether the backend has been configured at least once
    pub configured: bool,
}

impl GlobalBackendConfig {
    /// Get the path to the global backend config file.
    pub fn config_path() -> Option<PathBuf> {
        dirs::home_dir().map(|home| home.join(".devflow").join("backend.json"))
    }

    /// Load the global backend config from disk.
    pub fn load() -> Self {
        Self::config_path()
            .and_then(|path| fs::read_to_string(&path).ok())
            .and_then(|content| serde_json::from_str(&content).ok())
            .unwrap_or_default()
    }

    /// Save the global backend config to disk.
    pub fn save(&self) -> Result<(), String> {
        let path = Self::config_path().ok_or("Could not determine config path")?;

        // Ensure directory exists
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("Failed to create config dir: {}", e))?;
        }

        let content =
            serde_json::to_string_pretty(self).map_err(|e| format!("Failed to serialize: {}", e))?;

        fs::write(&path, content).map_err(|e| format!("Failed to write config: {}", e))?;

        Ok(())
    }

    /// Mark as configured with the given backend.
    pub fn set_configured(&mut self, backend: BackendConfig) {
        self.default_backend = Some(backend);
        self.configured = true;
    }
}

/// Project-level backend override (from devflow.yml).
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct ProjectBackendConfig {
    /// Override backend type
    #[serde(rename = "type")]
    pub backend_type: Option<BackendType>,
    /// Container name override (for Docker)
    pub container_name: Option<String>,
    /// WSL distro override (for WSL2)
    pub wsl_distro: Option<String>,
    /// Remote host override
    pub host: Option<String>,
    /// Remote port override
    pub port: Option<u16>,
}

impl ProjectBackendConfig {
    /// Merge project config with global config.
    pub fn merge_with(&self, global: &BackendConfig) -> BackendConfig {
        let mut result = global.clone();

        if let Some(ref bt) = self.backend_type {
            result.backend_type = bt.clone();
        }
        if let Some(ref cn) = self.container_name {
            result.container_name = Some(cn.clone());
        }
        if let Some(ref wd) = self.wsl_distro {
            result.wsl_distro = Some(wd.clone());
        }
        if let Some(ref h) = self.host {
            result.remote_host = Some(h.clone());
        }
        if let Some(p) = self.port {
            result.remote_port = Some(p);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backend_config_defaults() {
        let config = BackendConfig::default();
        assert_eq!(config.backend_type, BackendType::LocalPython);
        assert!(config.python_path.is_none());
    }

    #[test]
    fn test_docker_config() {
        let config = BackendConfig::docker(None);
        assert_eq!(config.backend_type, BackendType::Docker);
        assert_eq!(config.container_name, Some("devflow-backend".to_string()));
        assert_eq!(config.tcp_port(), 9876);
    }

    #[test]
    fn test_remote_config() {
        let config = BackendConfig::remote("192.168.1.100".to_string(), 8080);
        assert_eq!(config.backend_type, BackendType::Remote);
        assert_eq!(config.tcp_host(), "192.168.1.100");
        assert_eq!(config.tcp_port(), 8080);
    }

    #[test]
    fn test_project_override_merge() {
        let global = BackendConfig::docker(Some("global-container".to_string()));
        let project = ProjectBackendConfig {
            container_name: Some("project-container".to_string()),
            port: Some(9999),
            ..Default::default()
        };

        let merged = project.merge_with(&global);
        assert_eq!(merged.backend_type, BackendType::Docker);
        assert_eq!(
            merged.container_name,
            Some("project-container".to_string())
        );
        assert_eq!(merged.tcp_port(), 9999);
    }

    #[test]
    fn test_serialization() {
        let config = BackendConfig::local_python(Some(PathBuf::from("/usr/bin/python3")));
        let json = serde_json::to_string(&config).unwrap();
        let parsed: BackendConfig = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.backend_type, BackendType::LocalPython);
        assert_eq!(parsed.python_path, Some(PathBuf::from("/usr/bin/python3")));
    }
}
