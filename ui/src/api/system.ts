/**
 * System API
 */

import { invoke } from '@tauri-apps/api/core';
import type {
  CommandResponse,
  DoctorResult,
  ProviderStatus,
  SystemInfo,
} from '../types';

export async function runDoctor(): Promise<DoctorResult> {
  const response = await invoke<CommandResponse<DoctorResult>>('run_doctor');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to run doctor');
  }
  return response.data;
}

export async function runProjectDoctor(projectPath: string): Promise<DoctorResult> {
  const response = await invoke<CommandResponse<DoctorResult>>('run_project_doctor', {
    projectPath,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to run project doctor');
  }
  return response.data;
}

export async function getSystemInfo(): Promise<SystemInfo> {
  const response = await invoke<CommandResponse<SystemInfo>>('get_system_info');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get system info');
  }
  return response.data;
}

export async function getProviderStatus(provider: string): Promise<ProviderStatus> {
  const response = await invoke<CommandResponse<ProviderStatus>>('get_provider_status', {
    provider,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get provider status');
  }
  return response.data;
}

export async function getAllProviders(): Promise<Record<string, ProviderStatus>> {
  const response = await invoke<CommandResponse<Record<string, ProviderStatus>>>(
    'get_all_providers'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get providers');
  }
  return response.data;
}

export async function checkUpdates(): Promise<{
  current_version: string;
  latest_version: string;
  update_available: boolean;
}> {
  const response = await invoke<
    CommandResponse<{
      current_version: string;
      latest_version: string;
      update_available: boolean;
    }>
  >('check_updates');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to check updates');
  }
  return response.data;
}

export async function getVersion(): Promise<{ devflow: string; python: string }> {
  const response = await invoke<
    CommandResponse<{ devflow: string; python: string }>
  >('get_version');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get version');
  }
  return response.data;
}
