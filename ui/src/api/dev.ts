/**
 * Development Environment API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse } from '../types';

export interface ContainerStatus {
  name: string;
  image: string;
  status: string; // "running" | "stopped" | "exited" | "paused"
  ports: string[];
  health: string | null; // "healthy" | "unhealthy" | "starting" | null
}

export interface DevStatus {
  project: string;
  services: ContainerStatus[];
  infrastructure_connected: boolean;
}

export interface DevResult {
  success: boolean;
  message: string;
  services_affected: string[];
}

export interface LogsResult {
  service: string;
  logs: string;
}

/**
 * Get development environment status
 */
export async function getDevStatus(projectPath: string): Promise<DevStatus> {
  const response = await invoke<CommandResponse<DevStatus>>('get_dev_status', {
    projectPath,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get dev status');
  }
  return response.data;
}

/**
 * Start development environment
 */
export async function startDev(
  projectPath: string,
  service?: string,
  detach: boolean = true
): Promise<DevResult> {
  const response = await invoke<CommandResponse<DevResult>>('start_dev', {
    projectPath,
    service,
    detach,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to start dev environment');
  }
  return response.data;
}

/**
 * Stop development environment
 */
export async function stopDev(projectPath: string, service?: string): Promise<DevResult> {
  const response = await invoke<CommandResponse<DevResult>>('stop_dev', {
    projectPath,
    service,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to stop dev environment');
  }
  return response.data;
}

/**
 * Restart a service
 */
export async function restartDevService(projectPath: string, service: string): Promise<DevResult> {
  const response = await invoke<CommandResponse<DevResult>>('restart_dev_service', {
    projectPath,
    service,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to restart service');
  }
  return response.data;
}

/**
 * Get service logs
 */
export async function getDevLogs(
  projectPath: string,
  service: string,
  tail?: number,
  follow: boolean = false
): Promise<LogsResult> {
  const response = await invoke<CommandResponse<LogsResult>>('get_dev_logs', {
    projectPath,
    service,
    tail,
    follow,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get logs');
  }
  return response.data;
}

/**
 * Execute command in container
 */
export async function execInContainer(
  projectPath: string,
  service: string,
  command: string[]
): Promise<{ success: boolean; stdout: string; stderr: string; returncode: number }> {
  const response = await invoke<
    CommandResponse<{ success: boolean; stdout: string; stderr: string; returncode: number }>
  >('exec_in_container', {
    projectPath,
    service,
    command,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to execute command');
  }
  return response.data;
}

/**
 * Reset development environment
 */
export async function resetDev(
  projectPath: string,
  removeVolumes: boolean = false
): Promise<DevResult> {
  const response = await invoke<CommandResponse<DevResult>>('reset_dev', {
    projectPath,
    removeVolumes,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to reset dev environment');
  }
  return response.data;
}

/**
 * Run development setup
 */
export async function setupDev(
  projectPath: string
): Promise<{ success: boolean; steps: Array<{ step: string; status: string; message: string }> }> {
  const response = await invoke<
    CommandResponse<{
      success: boolean;
      steps: Array<{ step: string; status: string; message: string }>;
    }>
  >('setup_dev', {
    projectPath,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to setup dev environment');
  }
  return response.data;
}
