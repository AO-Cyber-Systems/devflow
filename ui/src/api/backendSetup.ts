/**
 * Backend setup API - works without Python bridge
 *
 * These functions handle backend detection, installation, and configuration
 * before the Python bridge is running.
 */

import { invoke } from '@tauri-apps/api/core';
import type {
  CommandResponse,
  BackendType,
  BackendConfig,
  GlobalBackendConfig,
  PrerequisiteStatus,
  WslDistroStatus,
  WslInstallValidation,
} from '../types';

/**
 * Detect system prerequisites for backend installation.
 *
 * Detects Python, DevFlow package, Docker, and WSL2 availability.
 */
export async function detectPrerequisites(): Promise<PrerequisiteStatus> {
  const response = await invoke<CommandResponse<PrerequisiteStatus>>('detect_prerequisites');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to detect prerequisites');
  }
  return response.data;
}

/**
 * Get the current backend configuration.
 *
 * Returns the global backend config from ~/.devflow/backend.json.
 */
export async function getBackendConfig(): Promise<GlobalBackendConfig> {
  const response = await invoke<CommandResponse<GlobalBackendConfig>>('get_backend_config');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get backend config');
  }
  return response.data;
}

/**
 * Save the backend configuration.
 *
 * Saves to ~/.devflow/backend.json.
 */
export async function saveBackendConfig(config: BackendConfig): Promise<void> {
  const response = await invoke<CommandResponse<void>>('save_backend_config', { config });
  if (!response.success) {
    throw new Error(response.error || 'Failed to save backend config');
  }
}

/**
 * Install the backend based on type.
 *
 * For local_python: Runs pip install devflow
 * For docker: Pulls image and starts container
 * For wsl2: Installs devflow in WSL2 and starts service
 * For remote: Verifies connection to remote backend
 */
export async function installBackend(
  backendType: BackendType,
  config?: Partial<BackendConfig>
): Promise<string> {
  const response = await invoke<CommandResponse<string>>('install_backend', {
    backendType,
    config: config || null,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to install backend');
  }
  return response.data;
}

/**
 * Install the backend with real-time log events.
 *
 * This is the same as installBackend but emits "install-log" events
 * during installation that can be listened to for progress updates.
 *
 * Listen for events using:
 * ```typescript
 * import { listen } from '@tauri-apps/api/event';
 * const unlisten = await listen<InstallLogEntry>('install-log', (event) => {
 *   console.log(event.payload);
 * });
 * ```
 */
export async function installBackendWithLogs(
  backendType: BackendType,
  config?: Partial<BackendConfig>
): Promise<string> {
  const response = await invoke<CommandResponse<string>>('install_backend_with_logs', {
    backendType,
    config: config || null,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to install backend');
  }
  return response.data;
}

/**
 * Log entry from installation process.
 */
export interface InstallLogEntry {
  level: 'info' | 'success' | 'warning' | 'error' | 'output';
  message: string;
  output?: string;
}

/**
 * Start the backend service (Docker container or WSL2 service).
 */
export async function startBackendService(config: BackendConfig): Promise<void> {
  const response = await invoke<CommandResponse<void>>('start_backend_service', { config });
  if (!response.success) {
    throw new Error(response.error || 'Failed to start backend service');
  }
}

/**
 * Stop the backend service (Docker container or WSL2 service).
 */
export async function stopBackendService(config: BackendConfig): Promise<void> {
  const response = await invoke<CommandResponse<void>>('stop_backend_service', { config });
  if (!response.success) {
    throw new Error(response.error || 'Failed to stop backend service');
  }
}

/**
 * Test connection to the backend.
 *
 * Returns true if the backend is accessible and responding.
 */
export async function testBackendConnection(config: BackendConfig): Promise<boolean> {
  const response = await invoke<CommandResponse<boolean>>('test_backend_connection', { config });
  if (!response.success) {
    throw new Error(response.error || 'Failed to test backend connection');
  }
  return response.data ?? false;
}

/**
 * Configure the bridge manager with the backend config and start it.
 */
export async function startBridgeWithConfig(config: BackendConfig): Promise<void> {
  const response = await invoke<CommandResponse<void>>('start_bridge_with_config', { config });
  if (!response.success) {
    throw new Error(response.error || 'Failed to start bridge with config');
  }
}

/**
 * Get recommended backend type based on prerequisites.
 */
export async function getRecommendedBackend(): Promise<BackendType> {
  const response = await invoke<CommandResponse<BackendType>>('get_recommended_backend');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get recommended backend');
  }
  return response.data;
}

/**
 * Create a default BackendConfig for a given type.
 */
export function createDefaultConfig(backendType: BackendType): BackendConfig {
  switch (backendType) {
    case 'local_python':
      return {
        backend_type: 'local_python',
        python_path: null,
        container_name: null,
        wsl_distro: null,
        remote_host: null,
        remote_port: null,
        auto_start: true,
      };
    case 'docker':
      return {
        backend_type: 'docker',
        python_path: null,
        container_name: 'devflow-backend',
        wsl_distro: null,
        remote_host: '127.0.0.1',
        remote_port: 9876,
        auto_start: true,
      };
    case 'wsl2':
      return {
        backend_type: 'wsl2',
        python_path: null,
        container_name: null,
        wsl_distro: 'Ubuntu',
        remote_host: '127.0.0.1',
        remote_port: 9876,
        auto_start: true,
      };
    case 'remote':
      return {
        backend_type: 'remote',
        python_path: null,
        container_name: null,
        wsl_distro: null,
        remote_host: 'localhost',
        remote_port: 9876,
        auto_start: false,
      };
  }
}

/**
 * Get a human-readable name for a backend type.
 */
export function getBackendTypeName(backendType: BackendType): string {
  switch (backendType) {
    case 'local_python':
      return 'Local Python';
    case 'docker':
      return 'Docker Container';
    case 'wsl2':
      return 'WSL2 Service';
    case 'remote':
      return 'Remote Server';
  }
}

/**
 * Get a description for a backend type.
 */
export function getBackendTypeDescription(backendType: BackendType): string {
  switch (backendType) {
    case 'local_python':
      return 'Run DevFlow directly using your local Python installation. Recommended for most users.';
    case 'docker':
      return 'Run DevFlow in a Docker container. Isolated environment, easy to manage.';
    case 'wsl2':
      return 'Run DevFlow as a service in Windows Subsystem for Linux 2. Best for Windows users.';
    case 'remote':
      return 'Connect to a DevFlow instance running on a remote server.';
  }
}

/**
 * Get detailed status for all WSL distributions.
 *
 * Returns information about each distro including WSL version,
 * running state, Python availability, and DevFlow installation status.
 */
export async function getWslDistrosDetailed(): Promise<WslDistroStatus[]> {
  const response = await invoke<CommandResponse<WslDistroStatus[]>>('get_wsl_distros_detailed');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get WSL distros');
  }
  return response.data;
}

/**
 * Validate WSL installation prerequisites for a specific distribution.
 *
 * Checks: WSL version, running state, Python version, pipx, port availability, network.
 */
export async function validateWslInstallation(
  distro: string,
  port: number
): Promise<WslInstallValidation> {
  const response = await invoke<CommandResponse<WslInstallValidation>>('validate_wsl_install', {
    distro,
    port,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to validate WSL installation');
  }
  return response.data;
}

/**
 * Start a WSL distribution.
 *
 * Useful when a distro is not running and needs to be started
 * before installation can proceed.
 */
export async function startWslDistro(distro: string): Promise<void> {
  const response = await invoke<CommandResponse<void>>('start_wsl', { distro });
  if (!response.success) {
    throw new Error(response.error || 'Failed to start WSL distro');
  }
}

/**
 * Get a user-friendly message for a WSL installation issue.
 */
export function getWslIssueMessage(issue: import('../types').WslInstallIssue): {
  title: string;
  description: string;
  resolution: string | null;
} {
  switch (issue.type) {
    case 'distro_not_wsl2':
      return {
        title: 'WSL1 Distribution',
        description: 'This distribution is running WSL version 1, which is not supported.',
        resolution: 'Upgrade to WSL2 by running: wsl --set-version <distro> 2',
      };
    case 'distro_not_running':
      return {
        title: 'Distribution Not Running',
        description: 'The selected distribution is not currently running.',
        resolution: null, // We offer a "Start" button instead
      };
    case 'python_not_installed':
      return {
        title: 'Python Not Installed',
        description: 'Python is not installed in this distribution.',
        resolution: 'Install Python: sudo apt update && sudo apt install python3 python3-pip',
      };
    case 'python_version_too_old':
      return {
        title: 'Python Version Too Old',
        description: `Python ${issue.version} is installed, but version ${issue.required}+ is required.`,
        resolution: 'Upgrade Python or use a different distribution with a newer Python version.',
      };
    case 'no_network_access':
      return {
        title: 'No Network Access',
        description: 'Cannot reach package servers from this distribution.',
        resolution: 'Check your network connection and WSL network settings.',
      };
    case 'insufficient_disk_space':
      return {
        title: 'Insufficient Disk Space',
        description: `Only ${issue.available_mb}MB available, but ${issue.required_mb}MB is required.`,
        resolution: 'Free up disk space: sudo apt clean && sudo apt autoremove',
      };
    case 'pipx_not_available':
      return {
        title: 'pipx Not Available',
        description: 'pipx is not installed and cannot be installed automatically.',
        resolution: 'Install pipx manually: sudo apt install pipx && pipx ensurepath',
      };
    case 'port_in_use':
      return {
        title: 'Port In Use',
        description: `Port ${issue.port} is already in use by another application.`,
        resolution: null, // We offer port selection instead
      };
  }
}
