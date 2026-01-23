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
    Rpc { code: i64, message: String, data: Option<Value> },

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
