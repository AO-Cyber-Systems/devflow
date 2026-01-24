use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
use std::process::{ChildStdin, ChildStdout};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RpcError {
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

    #[error("Bridge not connected")]
    NotConnected,

    #[error("Invalid response: {0}")]
    InvalidResponse(String),
}

#[derive(Debug, Serialize)]
pub struct RpcRequest {
    pub jsonrpc: String,
    pub method: String,
    pub params: Option<Value>,
    pub id: u64,
}

impl RpcRequest {
    pub fn new(method: &str, params: Option<Value>, id: u64) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            method: method.to_string(),
            params,
            id,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct RpcResponse {
    pub jsonrpc: String,
    pub result: Option<Value>,
    pub error: Option<RpcErrorObject>,
    pub id: Option<u64>,
}

#[derive(Debug, Deserialize)]
pub struct RpcErrorObject {
    pub code: i64,
    pub message: String,
    pub data: Option<Value>,
}

pub struct RpcClient {
    stdin: Mutex<Option<ChildStdin>>,
    stdout: Mutex<Option<BufReader<ChildStdout>>>,
    request_id: AtomicU64,
}

impl RpcClient {
    pub fn new() -> Self {
        Self {
            stdin: Mutex::new(None),
            stdout: Mutex::new(None),
            request_id: AtomicU64::new(1),
        }
    }

    pub fn connect(&self, stdin: ChildStdin, stdout: ChildStdout) {
        *self.stdin.lock().unwrap() = Some(stdin);
        *self.stdout.lock().unwrap() = Some(BufReader::new(stdout));
    }

    pub fn disconnect(&self) {
        *self.stdin.lock().unwrap() = None;
        *self.stdout.lock().unwrap() = None;
    }

    pub fn is_connected(&self) -> bool {
        self.stdin.lock().unwrap().is_some()
    }

    pub fn call(&self, method: &str, params: Option<Value>) -> Result<Value, RpcError> {
        let id = self.request_id.fetch_add(1, Ordering::SeqCst);
        let request = RpcRequest::new(method, params, id);

        // Send request
        {
            let mut stdin_guard = self.stdin.lock().unwrap();
            let stdin = stdin_guard.as_mut().ok_or(RpcError::NotConnected)?;

            let request_json = serde_json::to_string(&request)?;
            log::debug!("RPC request: {}", request_json);

            writeln!(stdin, "{}", request_json)?;
            stdin.flush()?;
        }

        // Read response
        {
            let mut stdout_guard = self.stdout.lock().unwrap();
            let stdout = stdout_guard.as_mut().ok_or(RpcError::NotConnected)?;

            let mut response_line = String::new();
            stdout.read_line(&mut response_line)?;

            log::debug!("RPC response: {}", response_line.trim());

            let response: RpcResponse = serde_json::from_str(&response_line)?;

            // Check for error
            if let Some(error) = response.error {
                return Err(RpcError::Rpc {
                    code: error.code,
                    message: error.message,
                    data: error.data,
                });
            }

            // Verify response ID matches
            if response.id != Some(id) {
                return Err(RpcError::InvalidResponse(format!(
                    "Response ID {} doesn't match request ID {}",
                    response.id.unwrap_or(0),
                    id
                )));
            }

            response.result.ok_or_else(|| {
                RpcError::InvalidResponse("Response has neither result nor error".to_string())
            })
        }
    }
}

impl Default for RpcClient {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rpc_request_new() {
        let request = RpcRequest::new("test.method", None, 1);
        assert_eq!(request.jsonrpc, "2.0");
        assert_eq!(request.method, "test.method");
        assert!(request.params.is_none());
        assert_eq!(request.id, 1);
    }

    #[test]
    fn test_rpc_request_with_params() {
        let params = serde_json::json!({"key": "value"});
        let request = RpcRequest::new("test.method", Some(params.clone()), 42);
        assert_eq!(request.params, Some(params));
        assert_eq!(request.id, 42);
    }

    #[test]
    fn test_rpc_request_serialization() {
        let request = RpcRequest::new("test.ping", None, 1);
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("\"jsonrpc\":\"2.0\""));
        assert!(json.contains("\"method\":\"test.ping\""));
        assert!(json.contains("\"id\":1"));
    }

    #[test]
    fn test_rpc_response_deserialization_success() {
        let json = r#"{"jsonrpc":"2.0","result":{"status":"ok"},"id":1}"#;
        let response: RpcResponse = serde_json::from_str(json).unwrap();
        assert_eq!(response.jsonrpc, "2.0");
        assert!(response.result.is_some());
        assert!(response.error.is_none());
        assert_eq!(response.id, Some(1));
    }

    #[test]
    fn test_rpc_response_deserialization_error() {
        let json =
            r#"{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":1}"#;
        let response: RpcResponse = serde_json::from_str(json).unwrap();
        assert!(response.result.is_none());
        assert!(response.error.is_some());
        let error = response.error.unwrap();
        assert_eq!(error.code, -32601);
        assert_eq!(error.message, "Method not found");
    }

    #[test]
    fn test_rpc_client_new() {
        let client = RpcClient::new();
        assert!(!client.is_connected());
    }

    #[test]
    fn test_rpc_client_default() {
        let client = RpcClient::default();
        assert!(!client.is_connected());
    }

    #[test]
    fn test_rpc_client_not_connected_error() {
        let client = RpcClient::new();
        let result = client.call("test.method", None);
        assert!(result.is_err());
        match result.unwrap_err() {
            RpcError::NotConnected => (),
            e => panic!("Expected NotConnected error, got {:?}", e),
        }
    }

    #[test]
    fn test_rpc_error_display() {
        let io_error = RpcError::Io(std::io::Error::new(std::io::ErrorKind::Other, "test"));
        assert!(io_error.to_string().contains("IO error"));

        let rpc_error = RpcError::Rpc {
            code: -32600,
            message: "Invalid Request".to_string(),
            data: None,
        };
        assert!(rpc_error.to_string().contains("-32600"));
        assert!(rpc_error.to_string().contains("Invalid Request"));

        let not_connected = RpcError::NotConnected;
        assert!(not_connected.to_string().contains("not connected"));
    }

    #[test]
    fn test_request_id_increments() {
        let client = RpcClient::new();
        let id1 = client.request_id.fetch_add(1, Ordering::SeqCst);
        let id2 = client.request_id.fetch_add(1, Ordering::SeqCst);
        assert_eq!(id2, id1 + 1);
    }
}
