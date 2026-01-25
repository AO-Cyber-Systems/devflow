/**
 * Mock implementation of @tauri-apps/api/core for testing.
 */

import { vi } from 'vitest';

// Store for mock invoke responses
const invokeResponses: Map<string, unknown> = new Map();

/**
 * Mock the Tauri invoke function.
 */
export const invoke = vi.fn().mockImplementation(async (cmd: string, _args?: unknown) => {
  if (invokeResponses.has(cmd)) {
    const response = invokeResponses.get(cmd);
    if (response instanceof Error) {
      throw response;
    }
    return response;
  }

  // Default mock responses for common commands
  switch (cmd) {
    case 'get_bridge_status':
      return { success: true, data: 'Running', error: null };
    case 'start_bridge':
      return { success: true, data: null, error: null };
    case 'stop_bridge':
      return { success: true, data: null, error: null };
    default:
      console.warn(`[Mock] Unhandled invoke command: ${cmd}`);
      return { success: true, data: null, error: null };
  }
});

/**
 * Helper to set mock response for a specific command.
 */
export function setInvokeResponse(cmd: string, response: unknown): void {
  invokeResponses.set(cmd, response);
}

/**
 * Helper to set mock error for a specific command.
 */
export function setInvokeError(cmd: string, error: Error): void {
  invokeResponses.set(cmd, error);
}

/**
 * Clear all mock responses.
 */
export function clearInvokeResponses(): void {
  invokeResponses.clear();
}
