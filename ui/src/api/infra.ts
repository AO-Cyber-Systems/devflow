/**
 * Infrastructure API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse, InfraStatus, OperationResult } from '../types';

export async function getInfraStatus(): Promise<InfraStatus> {
  const response = await invoke<CommandResponse<InfraStatus>>('get_infra_status');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get infrastructure status');
  }
  return response.data;
}

export async function startInfra(forceRecreate = false): Promise<OperationResult> {
  const response = await invoke<CommandResponse<OperationResult>>('start_infra', {
    forceRecreate,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to start infrastructure');
  }
  return response.data;
}

export async function stopInfra(
  removeVolumes = false,
  removeNetwork = false
): Promise<OperationResult> {
  const response = await invoke<CommandResponse<OperationResult>>('stop_infra', {
    removeVolumes,
    removeNetwork,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to stop infrastructure');
  }
  return response.data;
}

export async function configureProjectInfra(
  projectPath: string,
  composeFile?: string,
  dryRun = false
): Promise<OperationResult> {
  const response = await invoke<CommandResponse<OperationResult>>(
    'configure_project_infra',
    { projectPath, composeFile, dryRun }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to configure project');
  }
  return response.data;
}

export async function unconfigureProjectInfra(
  projectPath: string
): Promise<OperationResult> {
  const response = await invoke<CommandResponse<OperationResult>>(
    'unconfigure_project_infra',
    { projectPath }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to unconfigure project');
  }
  return response.data;
}

export async function regenerateCerts(domains?: string[]): Promise<OperationResult> {
  const response = await invoke<CommandResponse<OperationResult>>('regenerate_certs', {
    domains,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to regenerate certificates');
  }
  return response.data;
}

export async function manageHosts(
  action: 'add' | 'remove' | 'list',
  domains?: string[]
): Promise<OperationResult | { entries: string[] }> {
  const response = await invoke<CommandResponse<OperationResult | { entries: string[] }>>(
    'manage_hosts',
    { action, domains }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to manage hosts');
  }
  return response.data;
}
