/**
 * Secrets API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse } from '../types';

export interface SecretInfo {
  name: string;
  source: string; // "1password" | "env" | "docker"
  mapped_to: string[];
  last_synced: string | null;
}

export interface SecretsList {
  source: string;
  environment: string;
  secrets: SecretInfo[];
  mapped_count: number;
  total_count: number;
  error?: string;
}

export interface SyncResult {
  success: boolean;
  synced: number;
  failed: number;
  dry_run: boolean;
  results: Array<{
    secret: string;
    from_source: string;
    to_target: string;
    status: string;
    error: string | null;
  }>;
}

export interface VerifyResult {
  success: boolean;
  in_sync: number;
  out_of_sync: number;
  results: Array<{
    secret: string;
    status: string;
    details: string | null;
  }>;
}

export interface SecretProvider {
  name: string;
  type: string;
  available: boolean;
  authenticated: boolean;
}

/**
 * List secrets
 */
export async function listSecrets(
  projectPath: string,
  environment?: string,
  source?: string
): Promise<SecretsList> {
  const response = await invoke<CommandResponse<SecretsList>>('list_secrets', {
    projectPath,
    environment,
    source,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to list secrets');
  }
  return response.data;
}

/**
 * Sync secrets between sources
 */
export async function syncSecrets(
  projectPath: string,
  fromSource: string,
  toTarget: string,
  environment?: string,
  dryRun: boolean = false
): Promise<SyncResult> {
  const response = await invoke<CommandResponse<SyncResult>>('sync_secrets', {
    projectPath,
    fromSource,
    toTarget,
    environment,
    dryRun,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to sync secrets');
  }
  return response.data;
}

/**
 * Verify secrets are in sync
 */
export async function verifySecrets(
  projectPath: string,
  environment?: string
): Promise<VerifyResult> {
  const response = await invoke<CommandResponse<VerifyResult>>('verify_secrets', {
    projectPath,
    environment,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to verify secrets');
  }
  return response.data;
}

/**
 * Export secrets to file or env format
 */
export async function exportSecrets(
  projectPath: string,
  environment: string,
  format: 'env' | 'json' | 'yaml' = 'env'
): Promise<{ content: string; format: string }> {
  const response = await invoke<CommandResponse<{ content: string; format: string }>>(
    'export_secrets',
    {
      projectPath,
      environment,
      format,
    }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to export secrets');
  }
  return response.data;
}

/**
 * Get available secret providers
 */
export async function getSecretProviders(): Promise<{ providers: SecretProvider[] }> {
  const response = await invoke<CommandResponse<{ providers: SecretProvider[] }>>(
    'get_secret_providers'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get secret providers');
  }
  return response.data;
}
