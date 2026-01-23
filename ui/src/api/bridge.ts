/**
 * Bridge API - Communication with Tauri backend
 */

import { invoke } from '@tauri-apps/api/core';
import type { BridgeState, CommandResponse } from '../types';

/**
 * Get bridge status
 */
export async function getBridgeStatus(): Promise<BridgeState> {
  const response = await invoke<CommandResponse<string>>('get_bridge_status');
  return (response.data as BridgeState) || 'Stopped';
}

/**
 * Start the Python bridge server
 * @param bridgeModule - Python module name (e.g., 'bridge.main')
 * @param workingDir - Optional working directory for the Python process
 */
export async function startBridge(bridgeModule: string, workingDir?: string): Promise<void> {
  const response = await invoke<CommandResponse<void>>('start_bridge', {
    bridgeModule,
    workingDir,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to start bridge');
  }
}

/**
 * Stop the Python bridge server
 */
export async function stopBridge(): Promise<void> {
  await invoke<CommandResponse<void>>('stop_bridge');
}
