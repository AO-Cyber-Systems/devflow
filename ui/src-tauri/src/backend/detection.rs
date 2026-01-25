//! Prerequisite detection - runs in pure Rust without Python bridge.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;

/// Status of system prerequisites for backend installation.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct PrerequisiteStatus {
    /// Python availability
    pub python_available: bool,
    /// Python version string (e.g., "3.11.5")
    pub python_version: Option<String>,
    /// Path to Python executable
    pub python_path: Option<PathBuf>,
    /// Whether devflow package is installed
    pub devflow_installed: bool,
    /// DevFlow package version
    pub devflow_version: Option<String>,
    /// Docker availability
    pub docker_available: bool,
    /// Whether Docker daemon is running
    pub docker_running: bool,
    /// Docker version string
    pub docker_version: Option<String>,
    /// WSL2 availability (Windows only)
    pub wsl_available: bool,
    /// List of available WSL distributions
    pub wsl_distros: Vec<String>,
}

/// Detect Python installation.
///
/// Tries python3 first (Linux/macOS), then python (Windows).
/// Returns (available, version, path).
pub fn detect_python() -> (bool, Option<String>, Option<PathBuf>) {
    let python_commands = if cfg!(windows) {
        vec!["python", "python3", "py"]
    } else {
        vec!["python3", "python"]
    };

    for cmd in python_commands {
        if let Ok(output) = Command::new(cmd).args(["--version"]).output() {
            if output.status.success() {
                let version_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
                // Version is like "Python 3.11.5", extract just the version number
                let version = version_str
                    .strip_prefix("Python ")
                    .map(|s| s.to_string())
                    .or(Some(version_str));

                // Get the path using `which` or `where`
                let path = find_executable(cmd);

                return (true, version, path);
            }
        }
    }

    (false, None, None)
}

/// Check if devflow package is installed.
///
/// Runs `python -c "import devflow; print(devflow.__version__)"`.
pub fn check_devflow_installed(python_path: Option<&PathBuf>) -> (bool, Option<String>) {
    let python = python_path
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "python".to_string()
            } else {
                "python3".to_string()
            }
        });

    let check_script = r#"
try:
    import devflow
    print(devflow.__version__)
except ImportError:
    print("NOT_INSTALLED")
except AttributeError:
    print("UNKNOWN_VERSION")
"#;

    if let Ok(output) = Command::new(&python).args(["-c", check_script]).output() {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if result == "NOT_INSTALLED" {
                return (false, None);
            } else if result == "UNKNOWN_VERSION" {
                return (true, None);
            } else {
                return (true, Some(result));
            }
        }
    }

    (false, None)
}

/// Detect Docker installation and daemon status.
///
/// Returns (available, running, version).
pub fn detect_docker() -> (bool, bool, Option<String>) {
    // Check if docker command exists and get version
    let version = Command::new("docker")
        .args(["--version"])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| {
            String::from_utf8_lossy(&o.stdout)
                .trim()
                .to_string()
                // Extract version from "Docker version 24.0.5, build..."
                .split(',')
                .next()
                .unwrap_or("")
                .strip_prefix("Docker version ")
                .unwrap_or("")
                .to_string()
        })
        .filter(|v| !v.is_empty());

    let available = version.is_some();

    // Check if Docker daemon is running
    let running = if available {
        Command::new("docker")
            .args(["info"])
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
    } else {
        false
    };

    (available, running, version)
}

/// Detect WSL2 availability (Windows only).
///
/// Returns (available, list of distros).
#[cfg(windows)]
pub fn detect_wsl() -> (bool, Vec<String>) {
    // Check if WSL is available
    let wsl_available = Command::new("wsl")
        .args(["--status"])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    if !wsl_available {
        return (false, vec![]);
    }

    // List available distributions
    let distros = Command::new("wsl")
        .args(["--list", "--quiet"])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| {
            // WSL output may be UTF-16 on Windows
            let output = String::from_utf8_lossy(&o.stdout);
            output
                .lines()
                .map(|s| s.trim().replace('\0', ""))
                .filter(|s| !s.is_empty())
                .collect()
        })
        .unwrap_or_default();

    (true, distros)
}

#[cfg(not(windows))]
pub fn detect_wsl() -> (bool, Vec<String>) {
    (false, vec![])
}

/// Check if devflow is installed in a WSL distro.
#[cfg(windows)]
pub fn check_devflow_in_wsl(distro: &str) -> (bool, Option<String>) {
    let check_cmd = r#"python3 -c "import devflow; print(devflow.__version__)" 2>/dev/null || echo "NOT_INSTALLED""#;

    if let Ok(output) = Command::new("wsl")
        .args(["-d", distro, "--", "bash", "-c", check_cmd])
        .output()
    {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if result == "NOT_INSTALLED" || result.is_empty() {
                return (false, None);
            }
            return (true, Some(result));
        }
    }

    (false, None)
}

#[cfg(not(windows))]
pub fn check_devflow_in_wsl(_distro: &str) -> (bool, Option<String>) {
    (false, None)
}

/// Detect all prerequisites at once.
pub fn detect_all_prerequisites() -> PrerequisiteStatus {
    let (python_available, python_version, python_path) = detect_python();
    let (devflow_installed, devflow_version) = if python_available {
        check_devflow_installed(python_path.as_ref())
    } else {
        (false, None)
    };
    let (docker_available, docker_running, docker_version) = detect_docker();
    let (wsl_available, wsl_distros) = detect_wsl();

    PrerequisiteStatus {
        python_available,
        python_version,
        python_path,
        devflow_installed,
        devflow_version,
        docker_available,
        docker_running,
        docker_version,
        wsl_available,
        wsl_distros,
    }
}

/// Find the path to an executable.
fn find_executable(name: &str) -> Option<PathBuf> {
    #[cfg(windows)]
    let which_cmd = "where";
    #[cfg(not(windows))]
    let which_cmd = "which";

    Command::new(which_cmd)
        .arg(name)
        .output()
        .ok()
        .filter(|o| o.status.success())
        .and_then(|o| {
            String::from_utf8_lossy(&o.stdout)
                .lines()
                .next()
                .map(|s| PathBuf::from(s.trim()))
        })
}

/// Check if a Docker container exists and is running.
pub fn check_docker_container(container_name: &str) -> (bool, bool) {
    // Check if container exists
    let exists = Command::new("docker")
        .args(["inspect", "--format", "{{.State.Status}}", container_name])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    if !exists {
        return (false, false);
    }

    // Get container status
    let running = Command::new("docker")
        .args(["inspect", "--format", "{{.State.Running}}", container_name])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim() == "true")
        .unwrap_or(false);

    (true, running)
}

/// Test TCP connection to a host:port.
pub fn test_tcp_connection(host: &str, port: u16) -> bool {
    use std::net::TcpStream;
    use std::time::Duration;

    TcpStream::connect_timeout(
        &format!("{}:{}", host, port).parse().unwrap(),
        Duration::from_secs(5),
    )
    .is_ok()
}

/// Test if a DevFlow service is responding at host:port.
pub fn test_devflow_connection(host: &str, port: u16) -> bool {
    use std::io::{BufRead, BufReader, Write};
    use std::net::TcpStream;
    use std::time::Duration;

    let addr = format!("{}:{}", host, port);
    let stream = match TcpStream::connect_timeout(&addr.parse().unwrap(), Duration::from_secs(5)) {
        Ok(s) => s,
        Err(_) => return false,
    };

    // Set read timeout
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(5)));

    let mut stream = stream;
    let ping_request = r#"{"jsonrpc":"2.0","method":"system.ping","params":null,"id":1}"#;

    // Send ping request
    if writeln!(stream, "{}", ping_request).is_err() {
        return false;
    }
    if stream.flush().is_err() {
        return false;
    }

    // Read response
    let mut reader = BufReader::new(stream);
    let mut response = String::new();
    if reader.read_line(&mut response).is_err() {
        return false;
    }

    // Check if response contains "result" (success)
    response.contains("\"result\"")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_python() {
        // This test depends on the environment
        let (available, version, path) = detect_python();
        if available {
            assert!(version.is_some());
            println!("Python found: {:?} at {:?}", version, path);
        }
    }

    #[test]
    fn test_detect_docker() {
        let (available, running, version) = detect_docker();
        println!(
            "Docker: available={}, running={}, version={:?}",
            available, running, version
        );
    }

    #[test]
    fn test_prerequisite_status_serialization() {
        let status = PrerequisiteStatus {
            python_available: true,
            python_version: Some("3.11.5".to_string()),
            python_path: Some(PathBuf::from("/usr/bin/python3")),
            devflow_installed: true,
            devflow_version: Some("0.1.0".to_string()),
            docker_available: true,
            docker_running: true,
            docker_version: Some("24.0.5".to_string()),
            wsl_available: false,
            wsl_distros: vec![],
        };

        let json = serde_json::to_string(&status).unwrap();
        let parsed: PrerequisiteStatus = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.python_available, true);
        assert_eq!(parsed.python_version, Some("3.11.5".to_string()));
    }
}
