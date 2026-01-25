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

/// Detailed status of a WSL distribution.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct WslDistroStatus {
    /// Distribution name
    pub name: String,
    /// Whether this is a WSL2 distribution (vs WSL1)
    pub is_wsl2: bool,
    /// Whether the distribution is currently running
    pub is_running: bool,
    /// Whether Python is available in this distro
    pub python_available: bool,
    /// Python version string (e.g., "3.11.5")
    pub python_version: Option<String>,
    /// Whether devflow package is installed in this distro
    pub devflow_installed: bool,
    /// DevFlow package version in this distro
    pub devflow_version: Option<String>,
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

/// Check if a specific WSL distribution is WSL2 (vs WSL1).
#[cfg(windows)]
pub fn is_wsl2_distro(distro: &str) -> bool {
    // Parse `wsl --list --verbose` to get WSL version
    let output = Command::new("wsl")
        .args(["--list", "--verbose"])
        .output();

    match output {
        Ok(o) if o.status.success() => {
            // WSL output may be UTF-16 on Windows, handle both UTF-8 and UTF-16
            let stdout = String::from_utf8_lossy(&o.stdout);
            for line in stdout.lines() {
                // Clean up null characters and whitespace
                let line = line.replace('\0', "").trim().to_string();
                // Line format: "* Ubuntu    Running    2" or "  Debian    Stopped    1"
                // The asterisk indicates the default distro
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.is_empty() {
                    continue;
                }

                // Skip the asterisk if present
                let name_idx = if parts[0] == "*" { 1 } else { 0 };
                if parts.len() > name_idx {
                    let name = parts[name_idx];
                    if name.eq_ignore_ascii_case(distro) {
                        // Version is typically the last column
                        if let Some(version_str) = parts.last() {
                            return *version_str == "2";
                        }
                    }
                }
            }
            false
        }
        _ => false,
    }
}

#[cfg(not(windows))]
pub fn is_wsl2_distro(_distro: &str) -> bool {
    false
}

/// Check if a specific WSL distribution is currently running.
#[cfg(windows)]
pub fn is_distro_running(distro: &str) -> bool {
    // Parse `wsl --list --verbose` to get running state
    let output = Command::new("wsl")
        .args(["--list", "--verbose"])
        .output();

    match output {
        Ok(o) if o.status.success() => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            for line in stdout.lines() {
                let line = line.replace('\0', "").trim().to_string();
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.is_empty() {
                    continue;
                }

                let name_idx = if parts[0] == "*" { 1 } else { 0 };
                if parts.len() > name_idx + 1 {
                    let name = parts[name_idx];
                    if name.eq_ignore_ascii_case(distro) {
                        let state = parts[name_idx + 1];
                        return state.eq_ignore_ascii_case("Running");
                    }
                }
            }
            false
        }
        _ => false,
    }
}

#[cfg(not(windows))]
pub fn is_distro_running(_distro: &str) -> bool {
    false
}

/// Check Python availability in a WSL distro.
#[cfg(windows)]
fn check_python_in_wsl(distro: &str) -> (bool, Option<String>) {
    let check_cmd = r#"python3 --version 2>/dev/null || python --version 2>/dev/null"#;

    if let Ok(output) = Command::new("wsl")
        .args(["-d", distro, "--", "bash", "-c", check_cmd])
        .output()
    {
        if output.status.success() {
            let result = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if result.is_empty() {
                return (false, None);
            }
            // Extract version from "Python 3.11.5"
            let version = result
                .strip_prefix("Python ")
                .map(|s| s.to_string())
                .or(Some(result));
            return (true, version);
        }
    }

    (false, None)
}

#[cfg(not(windows))]
fn check_python_in_wsl(_distro: &str) -> (bool, Option<String>) {
    (false, None)
}

/// Get detailed status for a single WSL distribution.
#[cfg(windows)]
pub fn check_wsl_distro_status(distro: &str) -> WslDistroStatus {
    let is_wsl2 = is_wsl2_distro(distro);
    let is_running = is_distro_running(distro);
    let (python_available, python_version) = if is_running {
        check_python_in_wsl(distro)
    } else {
        (false, None)
    };
    let (devflow_installed, devflow_version) = if is_running && python_available {
        check_devflow_in_wsl(distro)
    } else {
        (false, None)
    };

    WslDistroStatus {
        name: distro.to_string(),
        is_wsl2,
        is_running,
        python_available,
        python_version,
        devflow_installed,
        devflow_version,
    }
}

#[cfg(not(windows))]
pub fn check_wsl_distro_status(_distro: &str) -> WslDistroStatus {
    WslDistroStatus::default()
}

/// Detect all WSL distributions with detailed status.
#[cfg(windows)]
pub fn detect_wsl_distros_detailed() -> Vec<WslDistroStatus> {
    let (available, distros) = detect_wsl();
    if !available || distros.is_empty() {
        return vec![];
    }

    distros
        .iter()
        .map(|name| check_wsl_distro_status(name))
        .collect()
}

#[cfg(not(windows))]
pub fn detect_wsl_distros_detailed() -> Vec<WslDistroStatus> {
    vec![]
}

/// Start a WSL distribution.
#[cfg(windows)]
pub fn start_wsl_distro(distro: &str) -> Result<(), String> {
    // Starting a distro can be done by running a simple command in it
    let output = Command::new("wsl")
        .args(["-d", distro, "--", "echo", "started"])
        .output();

    match output {
        Ok(o) if o.status.success() => Ok(()),
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            Err(format!("Failed to start {}: {}", distro, stderr.trim()))
        }
        Err(e) => Err(format!("Failed to run wsl: {}", e)),
    }
}

#[cfg(not(windows))]
pub fn start_wsl_distro(_distro: &str) -> Result<(), String> {
    Err("WSL is only available on Windows".to_string())
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

    #[test]
    fn test_wsl_distro_status_serialization() {
        let status = WslDistroStatus {
            name: "Ubuntu".to_string(),
            is_wsl2: true,
            is_running: true,
            python_available: true,
            python_version: Some("3.11.5".to_string()),
            devflow_installed: true,
            devflow_version: Some("0.2.0".to_string()),
        };

        let json = serde_json::to_string(&status).unwrap();
        let parsed: WslDistroStatus = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.name, "Ubuntu");
        assert!(parsed.is_wsl2);
        assert!(parsed.is_running);
        assert!(parsed.python_available);
        assert_eq!(parsed.python_version, Some("3.11.5".to_string()));
        assert!(parsed.devflow_installed);
        assert_eq!(parsed.devflow_version, Some("0.2.0".to_string()));
    }

    #[test]
    fn test_wsl_distro_status_default() {
        let status = WslDistroStatus::default();
        assert_eq!(status.name, "");
        assert!(!status.is_wsl2);
        assert!(!status.is_running);
        assert!(!status.python_available);
        assert!(status.python_version.is_none());
        assert!(!status.devflow_installed);
        assert!(status.devflow_version.is_none());
    }

    // Platform-specific tests for WSL functions
    // On Linux/macOS, these should return empty/false values
    // On Windows without WSL2, these should also return empty/false without panicking

    #[test]
    fn test_detect_wsl_returns_valid_result() {
        // Should not panic on any platform
        let (available, distros) = detect_wsl();
        println!("WSL available: {}, distros: {:?}", available, distros);

        #[cfg(not(windows))]
        {
            // On non-Windows, WSL should never be available
            assert!(!available, "WSL should not be available on non-Windows");
            assert!(distros.is_empty(), "WSL distros should be empty on non-Windows");
        }

        // On Windows, result depends on WSL installation
        // Just verify we get a valid response without panicking
    }

    #[test]
    fn test_detect_wsl_distros_detailed_returns_valid_result() {
        // Should not panic on any platform
        let distros = detect_wsl_distros_detailed();
        println!("Detailed distros: {:?}", distros);

        #[cfg(not(windows))]
        {
            // On non-Windows, should return empty list
            assert!(distros.is_empty(), "WSL distros should be empty on non-Windows");
        }
    }

    #[test]
    fn test_is_wsl2_distro_handles_missing_distro() {
        // Should not panic when distro doesn't exist
        let result = is_wsl2_distro("nonexistent-distro-12345");

        #[cfg(not(windows))]
        {
            assert!(!result, "Should return false on non-Windows");
        }
    }

    #[test]
    fn test_is_distro_running_handles_missing_distro() {
        // Should not panic when distro doesn't exist
        let result = is_distro_running("nonexistent-distro-12345");

        #[cfg(not(windows))]
        {
            assert!(!result, "Should return false on non-Windows");
        }
    }

    #[test]
    fn test_check_wsl_distro_status_handles_missing_distro() {
        // Should not panic when distro doesn't exist
        let status = check_wsl_distro_status("nonexistent-distro-12345");
        println!("Status for nonexistent distro: {:?}", status);

        #[cfg(windows)]
        {
            // On Windows, should return a valid struct with the distro name
            assert_eq!(status.name, "nonexistent-distro-12345");
        }

        #[cfg(not(windows))]
        {
            // On non-Windows, returns empty default struct
            assert!(status.name.is_empty());
        }

        // On all platforms, all checks should fail for nonexistent distro
        assert!(!status.is_wsl2);
        assert!(!status.is_running);
        assert!(!status.python_available);
        assert!(!status.devflow_installed);
    }

    #[test]
    fn test_start_wsl_distro_handles_missing_distro() {
        // Should return an error for nonexistent distro, not panic
        let result = start_wsl_distro("nonexistent-distro-12345");
        assert!(result.is_err(), "Should fail for nonexistent distro");
        println!("Expected error: {:?}", result.err());
    }
}
