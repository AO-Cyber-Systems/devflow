/**
 * Configuration API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse, DevflowConfig, GlobalConfig } from '../types';

export async function getGlobalConfig(): Promise<GlobalConfig> {
  const response = await invoke<CommandResponse<GlobalConfig>>('get_global_config');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get global config');
  }
  return response.data;
}

export async function getProjectConfig(projectPath: string): Promise<DevflowConfig> {
  const response = await invoke<CommandResponse<DevflowConfig>>('get_project_config', {
    projectPath,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get project config');
  }
  return response.data;
}

export async function updateGlobalConfig(
  key: string,
  value: unknown
): Promise<void> {
  const response = await invoke<CommandResponse<unknown>>('update_global_config', {
    key,
    value,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to update global config');
  }
}

export async function updateProjectConfig(
  projectPath: string,
  config: DevflowConfig
): Promise<void> {
  const response = await invoke<CommandResponse<unknown>>('update_project_config', {
    projectPath,
    config,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to update project config');
  }
}

export async function validateConfig(
  projectPath?: string
): Promise<{ valid: boolean; errors: string[]; warnings: string[] }> {
  const response = await invoke<
    CommandResponse<{ valid: boolean; errors: string[]; warnings: string[] }>
  >('validate_config', { projectPath });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to validate config');
  }
  return response.data;
}
