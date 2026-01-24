use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::Duration;
use thiserror::Error;

/// Error types for TCP RPC communication.
#[derive(Error, Debug)]
pub enum TcpRpcError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("RPC error {code}: {message}")]
    Rpc {
        code: i64,
        message: String,
        data: Option<Value>,
    },

    #[error("Not connected")]
    NotConnected,

    #[error("Connection timeout")]
    Timeout,

    #[error("Invalid response: {0}")]
    InvalidResponse(String),
}

/// JSON-RPC 2.0 request structure.
#[derive(Debug, Serialize)]
struct RpcRequest {
    jsonrpc: String,
    method: String,
    params: Option<Value>,
    id: u64,
}

impl RpcRequest {
    fn new(method: &str, params: Option<Value>, id: u64) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            method: method.to_string(),
            params,
            id,
        }
    }
}

/// JSON-RPC 2.0 response structure.
#[derive(Debug, Deserialize)]
struct RpcResponse {
    #[allow(dead_code)]
    jsonrpc: String,
    result: Option<Value>,
    error: Option<RpcErrorObject>,
    id: Option<u64>,
}

/// JSON-RPC 2.0 error object.
#[derive(Debug, Deserialize)]
struct RpcErrorObject {
    code: i64,
    message: String,
    data: Option<Value>,
}

/// TCP RPC client for connecting to DevFlow service.
///
/// This client is used on Windows to communicate with the Python
/// backend running in WSL2 via TCP instead of stdio.
pub struct TcpRpcClient {
    stream: Mutex<Option<TcpStream>>,
    reader: Mutex<Option<BufReader<TcpStream>>>,
    request_id: AtomicU64,
    connect_timeout: Duration,
    read_timeout: Duration,
}

impl TcpRpcClient {
    /// Create a new TCP RPC client.
    pub fn new() -> Self {
        Self {
            stream: Mutex::new(None),
            reader: Mutex::new(None),
            request_id: AtomicU64::new(1),
            connect_timeout: Duration::from_secs(10),
            read_timeout: Duration::from_secs(60),
        }
    }

    /// Create a new client with custom timeouts.
    pub fn with_timeouts(connect_timeout: Duration, read_timeout: Duration) -> Self {
        Self {
            stream: Mutex::new(None),
            reader: Mutex::new(None),
            request_id: AtomicU64::new(1),
            connect_timeout,
            read_timeout,
        }
    }

    /// Connect to the DevFlow service.
    ///
    /// # Arguments
    /// * `host` - The hostname or IP address
    /// * `port` - The port number
    pub fn connect(&self, host: &str, port: u16) -> Result<(), TcpRpcError> {
        let addr = format!("{}:{}", host, port);
        log::info!("Connecting to DevFlow service at {}", addr);

        // Connect with timeout
        let stream = TcpStream::connect_timeout(
            &addr.parse().map_err(|e| {
                TcpRpcError::ConnectionFailed(format!("Invalid address {}: {}", addr, e))
            })?,
            self.connect_timeout,
        )
        .map_err(|e| {
            TcpRpcError::ConnectionFailed(format!("Failed to connect to {}: {}", addr, e))
        })?;

        // Set TCP options
        stream.set_nodelay(true)?;
        stream.set_read_timeout(Some(self.read_timeout))?;
        stream.set_write_timeout(Some(Duration::from_secs(10)))?;

        // Clone stream for reader
        let reader_stream = stream.try_clone()?;
        let reader = BufReader::new(reader_stream);

        // Store connections
        *self.stream.lock().unwrap() = Some(stream);
        *self.reader.lock().unwrap() = Some(reader);

        log::info!("Connected to DevFlow service at {}", addr);
        Ok(())
    }

    /// Disconnect from the service.
    pub fn disconnect(&self) {
        *self.stream.lock().unwrap() = None;
        *self.reader.lock().unwrap() = None;
        log::info!("Disconnected from DevFlow service");
    }

    /// Check if connected to the service.
    pub fn is_connected(&self) -> bool {
        self.stream.lock().unwrap().is_some()
    }

    /// Call an RPC method.
    ///
    /// # Arguments
    /// * `method` - The method name (e.g., "system.ping")
    /// * `params` - Optional parameters as JSON Value
    ///
    /// # Returns
    /// The result value from the RPC call.
    pub fn call(&self, method: &str, params: Option<Value>) -> Result<Value, TcpRpcError> {
        let id = self.request_id.fetch_add(1, Ordering::SeqCst);
        let request = RpcRequest::new(method, params, id);

        log::debug!("RPC call: {} (id={})", method, id);

        // Send request
        {
            let mut stream_guard = self.stream.lock().unwrap();
            let stream = stream_guard.as_mut().ok_or(TcpRpcError::NotConnected)?;

            let request_json = serde_json::to_string(&request)?;
            log::debug!("Sending: {}", request_json);

            writeln!(stream, "{}", request_json)?;
            stream.flush()?;
        }

        // Read response
        {
            let mut reader_guard = self.reader.lock().unwrap();
            let reader = reader_guard.as_mut().ok_or(TcpRpcError::NotConnected)?;

            let mut response_line = String::new();
            reader.read_line(&mut response_line)?;

            log::debug!("Received: {}", response_line.trim());

            let response: RpcResponse = serde_json::from_str(&response_line)?;

            // Check for error
            if let Some(error) = response.error {
                return Err(TcpRpcError::Rpc {
                    code: error.code,
                    message: error.message,
                    data: error.data,
                });
            }

            // Verify response ID matches
            if response.id != Some(id) {
                return Err(TcpRpcError::InvalidResponse(format!(
                    "Response ID {:?} doesn't match request ID {}",
                    response.id, id
                )));
            }

            response.result.ok_or_else(|| {
                TcpRpcError::InvalidResponse("Response has neither result nor error".to_string())
            })
        }
    }

    /// Test the connection with a ping.
    pub fn ping(&self) -> Result<Value, TcpRpcError> {
        self.call("system.ping", None)
    }
}

impl Default for TcpRpcClient {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for TcpRpcClient {
    fn drop(&mut self) {
        self.disconnect();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rpc_request_serialization() {
        let request = RpcRequest::new("system.ping", None, 1);
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"jsonrpc\":\"2.0\""));
        assert!(json.contains("\"method\":\"system.ping\""));
        assert!(json.contains("\"id\":1"));
    }

    #[test]
    fn test_client_not_connected() {
        let client = TcpRpcClient::new();
        assert!(!client.is_connected());

        let result = client.call("system.ping", None);
        assert!(matches!(result, Err(TcpRpcError::NotConnected)));
    }
}
