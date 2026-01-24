/**
 * Deployment API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse } from '../types';

export interface ServiceStatus {
  name: string;
  image: string;
  replicas: string;
  status: string; // "running" | "stopped" | "partial" | "unknown"
  last_updated: string | null;
}

export interface DeployStatus {
  environment: string;
  host: string | null;
  services: ServiceStatus[];
  last_deploy: string | null;
  error?: string;
}

export interface DeployResult {
  success: boolean;
  deployed: number;
  failed: number;
  dry_run: boolean;
  requires_approval?: boolean;
  results: Array<{
    service: string;
    status: string;
    image: string | null;
    error: string | null;
  }>;
}

export interface RollbackDeployResult {
  success: boolean;
  rolled_back: number;
  failed: number;
  results: Array<{
    service: string;
    status: string;
    error: string | null;
  }>;
}

export interface DeployLogs {
  service: string;
  environment: string;
  logs: string;
}

/**
 * Get deployment status
 */
export async function getDeployStatus(
  projectPath: string,
  environment: string,
  service?: string
): Promise<DeployStatus> {
  const response = await invoke<CommandResponse<DeployStatus>>('get_deploy_status', {
    projectPath,
    environment,
    service,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get deploy status');
  }
  return response.data;
}

/**
 * Deploy to environment
 */
export async function deploy(
  projectPath: string,
  environment: string,
  service?: string,
  migrate: boolean = false,
  dryRun: boolean = false
): Promise<DeployResult> {
  const response = await invoke<CommandResponse<DeployResult>>('deploy', {
    projectPath,
    environment,
    service,
    migrate,
    dryRun,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to deploy');
  }
  return response.data;
}

/**
 * Rollback deployment
 */
export async function rollbackDeploy(
  projectPath: string,
  environment: string,
  service?: string
): Promise<RollbackDeployResult> {
  const response = await invoke<CommandResponse<RollbackDeployResult>>('rollback_deploy', {
    projectPath,
    environment,
    service,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to rollback deployment');
  }
  return response.data;
}

/**
 * Get deployment logs
 */
export async function getDeployLogs(
  projectPath: string,
  environment: string,
  service: string,
  tail?: number,
  follow: boolean = false
): Promise<DeployLogs> {
  const response = await invoke<CommandResponse<DeployLogs>>('get_deploy_logs', {
    projectPath,
    environment,
    service,
    tail,
    follow,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get deploy logs');
  }
  return response.data;
}

/**
 * Get SSH command for environment
 */
export async function getSshCommand(
  projectPath: string,
  environment: string,
  node?: string
): Promise<{ command: string; user: string; host: string }> {
  const response = await invoke<
    CommandResponse<{ command: string; user: string; host: string }>
  >('get_ssh_command', {
    projectPath,
    environment,
    node,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get SSH command');
  }
  return response.data;
}
