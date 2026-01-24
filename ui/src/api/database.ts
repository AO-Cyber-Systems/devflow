/**
 * Database Migration API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse } from '../types';

export interface MigrationStatus {
  environment: string;
  executor: string;
  applied: number;
  pending: number;
  total: number;
  pending_files: string[];
  migrations_dir_exists?: boolean;
  error?: string;
}

export interface MigrationResult {
  success: boolean;
  applied: number;
  skipped: number;
  error?: string;
  dry_run?: boolean;
  would_apply?: number;
  files?: string[];
  results: Array<{
    file: string;
    status: string;
    error: string | null;
  }>;
}

export interface RollbackResult {
  success: boolean;
  rolled_back: number;
  failed: number;
  dry_run?: boolean;
  would_rollback?: number;
  results: Array<{
    file: string;
    status: string;
    error: string | null;
  }>;
}

export interface MigrationHistory {
  environment: string;
  history: Array<{
    file: string;
    applied_at: string;
    status: string;
  }>;
  total: number;
}

/**
 * Get migration status
 */
export async function getMigrationStatus(
  projectPath: string,
  environment: string = 'local'
): Promise<MigrationStatus> {
  const response = await invoke<CommandResponse<MigrationStatus>>('get_migration_status', {
    projectPath,
    environment,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get migration status');
  }
  return response.data;
}

/**
 * Run pending migrations
 */
export async function runMigrations(
  projectPath: string,
  environment: string = 'local',
  dryRun: boolean = false
): Promise<MigrationResult> {
  const response = await invoke<CommandResponse<MigrationResult>>('run_migrations', {
    projectPath,
    environment,
    dryRun,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to run migrations');
  }
  return response.data;
}

/**
 * Rollback migrations
 */
export async function rollbackMigrations(
  projectPath: string,
  environment: string = 'local',
  steps: number = 1,
  dryRun: boolean = false,
  force: boolean = false
): Promise<RollbackResult> {
  const response = await invoke<CommandResponse<RollbackResult>>('rollback_migrations', {
    projectPath,
    environment,
    steps,
    dryRun,
    force,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to rollback migrations');
  }
  return response.data;
}

/**
 * Create a new migration
 */
export async function createMigration(
  projectPath: string,
  name: string
): Promise<{ success: boolean; file: string; path: string }> {
  const response = await invoke<
    CommandResponse<{ success: boolean; file: string; path: string }>
  >('create_migration', {
    projectPath,
    name,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to create migration');
  }
  return response.data;
}

/**
 * Get migration history
 */
export async function getMigrationHistory(
  projectPath: string,
  environment: string = 'local',
  limit?: number
): Promise<MigrationHistory> {
  const response = await invoke<CommandResponse<MigrationHistory>>('get_migration_history', {
    projectPath,
    environment,
    limit,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get migration history');
  }
  return response.data;
}

/**
 * Test database connection
 */
export async function testDbConnection(
  projectPath: string,
  environment: string = 'local'
): Promise<{ success: boolean; environment: string; message: string }> {
  const response = await invoke<
    CommandResponse<{ success: boolean; environment: string; message: string }>
  >('test_db_connection', {
    projectPath,
    environment,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to test connection');
  }
  return response.data;
}
