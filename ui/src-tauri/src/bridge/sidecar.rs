use super::rpc::{RpcClient, RpcError};
use serde_json::Value;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum BridgeError {
    #[error("Failed to start bridge: {0}")]
    StartFailed(String),

    #[error("Bridge not running")]
    NotRunning,

    #[error("RPC error: {0}")]
    Rpc(#[from] RpcError),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum BridgeState {
    Stopped,
    Starting,
    Running,
    Error,
}

pub struct BridgeManager {
    state: Mutex<BridgeState>,
    process: Mutex<Option<Child>>,
    rpc_client: Arc<RpcClient>,
    python_path: Mutex<Option<PathBuf>>,
}

impl BridgeManager {
    pub fn new() -> Self {
        Self {
            state: Mutex::new(BridgeState::Stopped),
            process: Mutex::new(None),
            rpc_client: Arc::new(RpcClient::new()),
            python_path: Mutex::new(None),
        }
    }

    pub fn set_python_path(&self, path: PathBuf) {
        *self.python_path.lock().unwrap() = Some(path);
    }

    pub fn get_state(&self) -> BridgeState {
        *self.state.lock().unwrap()
    }

    pub fn start(&self, bridge_module: &str, working_dir: Option<&str>) -> Result<(), BridgeError> {
        let mut state = self.state.lock().unwrap();
        if *state == BridgeState::Running {
            return Ok(());
        }

        *state = BridgeState::Starting;
        drop(state);

        // Determine python executable
        let python = self
            .python_path
            .lock()
            .unwrap()
            .clone()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| {
                // Try common python paths
                if cfg!(windows) {
                    "python".to_string()
                } else {
                    "python3".to_string()
                }
            });

        log::info!("Starting bridge with python: {}", python);
        log::info!("Bridge module: {}", bridge_module);
        if let Some(dir) = working_dir {
            log::info!("Working directory: {}", dir);
        }

        // Start the bridge process using -m flag for module execution
        let mut cmd = Command::new(&python);
        cmd.arg("-u") // Unbuffered output
            .arg("-m")
            .arg(bridge_module)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        // Set working directory if provided
        if let Some(dir) = working_dir {
            cmd.current_dir(dir);
        }

        let mut child = cmd
            .spawn()
            .map_err(|e| BridgeError::StartFailed(format!("Failed to spawn process: {}", e)))?;

        // Get stdin/stdout handles
        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| BridgeError::StartFailed("Failed to get stdin".to_string()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| BridgeError::StartFailed("Failed to get stdout".to_string()))?;

        // Connect RPC client
        self.rpc_client.connect(stdin, stdout);

        // Store process
        *self.process.lock().unwrap() = Some(child);

        // Test connection with ping
        match self.rpc_client.call("system.ping", None) {
            Ok(result) => {
                log::info!("Bridge connected, ping response: {:?}", result);
                *self.state.lock().unwrap() = BridgeState::Running;
                Ok(())
            }
            Err(e) => {
                log::error!("Bridge ping failed: {}", e);
                self.stop();
                *self.state.lock().unwrap() = BridgeState::Error;
                Err(BridgeError::StartFailed(format!("Ping failed: {}", e)))
            }
        }
    }

    pub fn stop(&self) {
        self.rpc_client.disconnect();

        if let Some(mut child) = self.process.lock().unwrap().take() {
            let _ = child.kill();
            let _ = child.wait();
        }

        *self.state.lock().unwrap() = BridgeState::Stopped;
        log::info!("Bridge stopped");
    }

    pub fn call(&self, method: &str, params: Option<Value>) -> Result<Value, BridgeError> {
        if self.get_state() != BridgeState::Running {
            return Err(BridgeError::NotRunning);
        }

        self.rpc_client.call(method, params).map_err(|e| {
            // Check if the bridge died
            if matches!(e, RpcError::Io(_) | RpcError::NotConnected) {
                *self.state.lock().unwrap() = BridgeState::Error;
            }
            BridgeError::Rpc(e)
        })
    }

    pub fn rpc_client(&self) -> Arc<RpcClient> {
        Arc::clone(&self.rpc_client)
    }
}

impl Default for BridgeManager {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for BridgeManager {
    fn drop(&mut self) {
        self.stop();
    }
}
