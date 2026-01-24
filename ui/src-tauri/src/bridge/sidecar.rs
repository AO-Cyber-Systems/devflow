use super::rpc::{RpcClient, RpcError};
use super::tcp::{TcpRpcClient, TcpRpcError};
use serde_json::Value;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use thiserror::Error;

/// Errors that can occur during bridge operations.
#[derive(Error, Debug)]
pub enum BridgeError {
    #[error("Failed to start bridge: {0}")]
    StartFailed(String),

    #[error("Bridge not running")]
    NotRunning,

    #[error("RPC error: {0}")]
    Rpc(#[from] RpcError),

    #[error("TCP RPC error: {0}")]
    TcpRpc(#[from] TcpRpcError),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid connection mode configuration")]
    InvalidConfig,
}

/// State of the bridge connection.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum BridgeState {
    Stopped,
    Starting,
    Running,
    Error,
}

/// Connection mode for the bridge.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ConnectionMode {
    /// Subprocess mode using stdio (Linux/macOS)
    Subprocess,
    /// TCP mode connecting to a remote service (Windows -> WSL2)
    Tcp,
}

impl Default for ConnectionMode {
    fn default() -> Self {
        Self::detect()
    }
}

impl ConnectionMode {
    /// Detect the appropriate connection mode for the current platform.
    pub fn detect() -> Self {
        if cfg!(windows) {
            // On Windows, use TCP to connect to WSL2 service
            ConnectionMode::Tcp
        } else {
            // On Linux/macOS, use subprocess
            ConnectionMode::Subprocess
        }
    }
}

/// TCP connection configuration.
#[derive(Clone, Debug)]
pub struct TcpConfig {
    pub host: String,
    pub port: u16,
}

impl Default for TcpConfig {
    fn default() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 9876,
        }
    }
}

/// Manages the bridge connection to the Python backend.
///
/// Supports two connection modes:
/// - Subprocess: Spawns Python process with stdio communication (Linux/macOS)
/// - TCP: Connects to a running DevFlow service via TCP (Windows -> WSL2)
pub struct BridgeManager {
    state: Mutex<BridgeState>,
    mode: Mutex<ConnectionMode>,
    // Subprocess mode fields
    process: Mutex<Option<Child>>,
    rpc_client: Arc<RpcClient>,
    python_path: Mutex<Option<PathBuf>>,
    // TCP mode fields
    tcp_client: Arc<TcpRpcClient>,
    tcp_config: Mutex<Option<TcpConfig>>,
}

impl BridgeManager {
    /// Create a new BridgeManager with automatic mode detection.
    pub fn new() -> Self {
        Self {
            state: Mutex::new(BridgeState::Stopped),
            mode: Mutex::new(ConnectionMode::detect()),
            process: Mutex::new(None),
            rpc_client: Arc::new(RpcClient::new()),
            python_path: Mutex::new(None),
            tcp_client: Arc::new(TcpRpcClient::new()),
            tcp_config: Mutex::new(None),
        }
    }

    /// Create a new BridgeManager with a specific connection mode.
    pub fn with_mode(mode: ConnectionMode) -> Self {
        Self {
            state: Mutex::new(BridgeState::Stopped),
            mode: Mutex::new(mode),
            process: Mutex::new(None),
            rpc_client: Arc::new(RpcClient::new()),
            python_path: Mutex::new(None),
            tcp_client: Arc::new(TcpRpcClient::new()),
            tcp_config: Mutex::new(None),
        }
    }

    /// Set the connection mode.
    pub fn set_mode(&self, mode: ConnectionMode) {
        *self.mode.lock().unwrap() = mode;
    }

    /// Get the current connection mode.
    pub fn get_mode(&self) -> ConnectionMode {
        *self.mode.lock().unwrap()
    }

    /// Set TCP configuration for TCP mode.
    pub fn set_tcp_config(&self, host: String, port: u16) {
        *self.tcp_config.lock().unwrap() = Some(TcpConfig { host, port });
    }

    /// Set the Python executable path for subprocess mode.
    pub fn set_python_path(&self, path: PathBuf) {
        *self.python_path.lock().unwrap() = Some(path);
    }

    /// Get the current bridge state.
    pub fn get_state(&self) -> BridgeState {
        *self.state.lock().unwrap()
    }

    /// Start the bridge connection.
    ///
    /// For subprocess mode, spawns the Python process.
    /// For TCP mode, connects to the running service.
    pub fn start(&self, bridge_module: &str, working_dir: Option<&str>) -> Result<(), BridgeError> {
        let mode = *self.mode.lock().unwrap();

        match mode {
            ConnectionMode::Subprocess => self.start_subprocess(bridge_module, working_dir),
            ConnectionMode::Tcp => self.start_tcp(),
        }
    }

    /// Start the bridge in subprocess mode.
    fn start_subprocess(
        &self,
        bridge_module: &str,
        working_dir: Option<&str>,
    ) -> Result<(), BridgeError> {
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
                log::info!("Bridge connected (subprocess), ping response: {:?}", result);
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

    /// Start the bridge in TCP mode.
    fn start_tcp(&self) -> Result<(), BridgeError> {
        let mut state = self.state.lock().unwrap();
        if *state == BridgeState::Running {
            return Ok(());
        }

        *state = BridgeState::Starting;
        drop(state);

        // Get TCP configuration
        let config = self.tcp_config.lock().unwrap();
        let tcp_config = config.as_ref().cloned().unwrap_or_default();
        drop(config);

        log::info!(
            "Connecting to DevFlow service at {}:{}",
            tcp_config.host,
            tcp_config.port
        );

        // Connect TCP client
        self.tcp_client
            .connect(&tcp_config.host, tcp_config.port)
            .map_err(|e| BridgeError::StartFailed(format!("TCP connection failed: {}", e)))?;

        // Test connection with ping
        match self.tcp_client.ping() {
            Ok(result) => {
                log::info!("Bridge connected (TCP), ping response: {:?}", result);
                *self.state.lock().unwrap() = BridgeState::Running;
                Ok(())
            }
            Err(e) => {
                log::error!("Bridge ping failed: {}", e);
                self.tcp_client.disconnect();
                *self.state.lock().unwrap() = BridgeState::Error;
                Err(BridgeError::StartFailed(format!("Ping failed: {}", e)))
            }
        }
    }

    /// Stop the bridge connection.
    pub fn stop(&self) {
        let mode = *self.mode.lock().unwrap();

        match mode {
            ConnectionMode::Subprocess => {
                self.rpc_client.disconnect();

                if let Some(mut child) = self.process.lock().unwrap().take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
            ConnectionMode::Tcp => {
                self.tcp_client.disconnect();
            }
        }

        *self.state.lock().unwrap() = BridgeState::Stopped;
        log::info!("Bridge stopped");
    }

    /// Call an RPC method.
    pub fn call(&self, method: &str, params: Option<Value>) -> Result<Value, BridgeError> {
        if self.get_state() != BridgeState::Running {
            return Err(BridgeError::NotRunning);
        }

        let mode = *self.mode.lock().unwrap();

        match mode {
            ConnectionMode::Subprocess => {
                self.rpc_client.call(method, params).map_err(|e| {
                    // Check if the bridge died
                    if matches!(e, RpcError::Io(_) | RpcError::NotConnected) {
                        *self.state.lock().unwrap() = BridgeState::Error;
                    }
                    BridgeError::Rpc(e)
                })
            }
            ConnectionMode::Tcp => {
                self.tcp_client.call(method, params).map_err(|e| {
                    // Check if the connection died
                    if matches!(e, TcpRpcError::Io(_) | TcpRpcError::NotConnected) {
                        *self.state.lock().unwrap() = BridgeState::Error;
                    }
                    BridgeError::TcpRpc(e)
                })
            }
        }
    }

    /// Get the subprocess RPC client (for advanced use).
    pub fn rpc_client(&self) -> Arc<RpcClient> {
        Arc::clone(&self.rpc_client)
    }

    /// Get the TCP RPC client (for advanced use).
    pub fn tcp_client(&self) -> Arc<TcpRpcClient> {
        Arc::clone(&self.tcp_client)
    }

    /// Check if using TCP mode.
    pub fn is_tcp_mode(&self) -> bool {
        *self.mode.lock().unwrap() == ConnectionMode::Tcp
    }

    /// Check if using subprocess mode.
    pub fn is_subprocess_mode(&self) -> bool {
        *self.mode.lock().unwrap() == ConnectionMode::Subprocess
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

/// Get the default WSL2 host address.
///
/// On Windows, WSL2 is accessible via localhost when using
/// the newer WSL2 networking mode.
pub fn get_wsl2_host() -> String {
    "127.0.0.1".to_string()
}

/// Get the default DevFlow service port.
pub fn get_default_port() -> u16 {
    9876
}
