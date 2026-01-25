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
