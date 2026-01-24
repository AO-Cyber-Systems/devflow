/**
 * Mock implementations of Tauri APIs for testing.
 * These mocks allow tests to run without the actual Tauri runtime.
 */

import { vi } from 'vitest';

// Store for mock invoke responses
const invokeResponses: Map<string, unknown> = new Map();

/**
 * Mock the Tauri invoke function.
 * Tests can set expected responses using setInvokeResponse.
 */
export const invoke = vi.fn().mockImplementation(async (cmd: string, args?: unknown) => {
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
      console.warn(`[Mock] Unhandled invoke command: ${cmd}`, args);
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

// Mock core module
export const core = {
  invoke,
};

// Mock event module
export const event = {
  listen: vi.fn().mockImplementation(async (_event: string, _handler: unknown) => {
    return vi.fn(); // Returns unlisten function
  }),
  emit: vi.fn(),
  once: vi.fn().mockImplementation(async (_event: string, _handler: unknown) => {
    return vi.fn();
  }),
};

// Mock window module
export const window = {
  appWindow: {
    listen: vi.fn().mockImplementation(async (_event: string, _handler: unknown) => {
      return vi.fn();
    }),
    emit: vi.fn(),
    setTitle: vi.fn(),
    show: vi.fn(),
    hide: vi.fn(),
    close: vi.fn(),
    minimize: vi.fn(),
    maximize: vi.fn(),
    unmaximize: vi.fn(),
    toggleMaximize: vi.fn(),
    setFullscreen: vi.fn(),
    isFullscreen: vi.fn().mockResolvedValue(false),
    isMaximized: vi.fn().mockResolvedValue(false),
    isMinimized: vi.fn().mockResolvedValue(false),
    isVisible: vi.fn().mockResolvedValue(true),
  },
  getCurrentWindow: vi.fn().mockReturnValue({
    listen: vi.fn().mockImplementation(async () => vi.fn()),
    emit: vi.fn(),
  }),
};

// Mock path module
export const path = {
  appDataDir: vi.fn().mockResolvedValue('/mock/app/data'),
  appConfigDir: vi.fn().mockResolvedValue('/mock/app/config'),
  homeDir: vi.fn().mockResolvedValue('/mock/home'),
  join: vi.fn().mockImplementation((...parts: string[]) => parts.join('/')),
  resolve: vi.fn().mockImplementation((...parts: string[]) => parts.join('/')),
};

// Mock fs module (if needed)
export const fs = {
  readTextFile: vi.fn().mockResolvedValue(''),
  writeTextFile: vi.fn().mockResolvedValue(undefined),
  exists: vi.fn().mockResolvedValue(false),
  createDir: vi.fn().mockResolvedValue(undefined),
  removeDir: vi.fn().mockResolvedValue(undefined),
  removeFile: vi.fn().mockResolvedValue(undefined),
  readDir: vi.fn().mockResolvedValue([]),
};

// Mock dialog module
export const dialog = {
  open: vi.fn().mockResolvedValue(null),
  save: vi.fn().mockResolvedValue(null),
  message: vi.fn().mockResolvedValue(undefined),
  ask: vi.fn().mockResolvedValue(false),
  confirm: vi.fn().mockResolvedValue(false),
};

// Mock shell module
export const shell = {
  open: vi.fn().mockResolvedValue(undefined),
  Command: vi.fn().mockImplementation(() => ({
    execute: vi.fn().mockResolvedValue({ code: 0, stdout: '', stderr: '' }),
    spawn: vi.fn().mockResolvedValue({
      pid: 1234,
      kill: vi.fn(),
      write: vi.fn(),
    }),
  })),
};

// Default export for @tauri-apps/api
export default {
  invoke,
  core,
  event,
  window,
  path,
  fs,
  dialog,
  shell,
};
