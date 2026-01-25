/**
 * Setup API - Prerequisites and tool installation
 */

import { invoke } from '@tauri-apps/api/core';
import type {
  CategoryInfo,
  CommandResponse,
  InstallMethodsResult,
  InstallResult,
  InstallerInfo,
  MiseStatus,
  MultiInstallResult,
  PlatformInfo,
  PrerequisitesSummary,
  ToolInfo,
  ToolStatus,
} from '../types';

/**
 * Get platform information
 */
export async function getPlatformInfo(): Promise<PlatformInfo> {
  const response = await invoke<CommandResponse<PlatformInfo>>('get_platform_info');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get platform info');
  }
  return response.data;
}

/**
 * Get all tool categories
 */
export async function getToolCategories(): Promise<Record<string, CategoryInfo>> {
  const response = await invoke<CommandResponse<Record<string, CategoryInfo>>>(
    'get_tool_categories'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get tool categories');
  }
  return response.data;
}

/**
 * Get all available tools
 */
export async function getAllTools(): Promise<ToolInfo[]> {
  const response = await invoke<CommandResponse<ToolInfo[]>>('get_all_tools');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get all tools');
  }
  return response.data;
}

/**
 * Get essential tools
 */
export async function getEssentialTools(): Promise<ToolInfo[]> {
  const response = await invoke<CommandResponse<ToolInfo[]>>('get_essential_tools');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get essential tools');
  }
  return response.data;
}

/**
 * Get tools by category
 */
export async function getToolsByCategory(category: string): Promise<ToolInfo[]> {
  const response = await invoke<CommandResponse<ToolInfo[]>>('get_tools_by_category', {
    category,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get tools by category');
  }
  return response.data;
}

/**
 * Get a specific tool by ID
 */
export async function getTool(toolId: string): Promise<ToolInfo | null> {
  const response = await invoke<CommandResponse<ToolInfo | null>>('get_tool', {
    toolId,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to get tool');
  }
  return response.data ?? null;
}

/**
 * Detect installation status of a tool
 */
export async function detectTool(toolId: string): Promise<ToolStatus> {
  const response = await invoke<CommandResponse<ToolStatus>>('detect_tool', {
    toolId,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to detect tool');
  }
  return response.data;
}

/**
 * Detect all tools
 */
export async function detectAllTools(): Promise<ToolStatus[]> {
  const response = await invoke<CommandResponse<ToolStatus[]>>('detect_all_tools');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to detect all tools');
  }
  return response.data;
}

/**
 * Detect essential tools
 */
export async function detectEssentialTools(): Promise<ToolStatus[]> {
  const response = await invoke<CommandResponse<ToolStatus[]>>('detect_essential_tools');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to detect essential tools');
  }
  return response.data;
}

/**
 * Get installation methods for a tool
 */
export async function getInstallMethods(toolId: string): Promise<InstallMethodsResult> {
  const response = await invoke<CommandResponse<InstallMethodsResult>>('get_install_methods', {
    toolId,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get install methods');
  }
  return response.data;
}

/**
 * Install a tool
 */
export async function installTool(
  toolId: string,
  method?: string
): Promise<InstallResult> {
  const response = await invoke<CommandResponse<InstallResult>>('install_tool', {
    toolId,
    method,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to install tool');
  }
  return response.data;
}

/**
 * Install multiple tools
 */
export async function installMultipleTools(
  toolIds: string[]
): Promise<MultiInstallResult> {
  const response = await invoke<CommandResponse<MultiInstallResult>>(
    'install_multiple_tools',
    { toolIds }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to install tools');
  }
  return response.data;
}

/**
 * Check if Mise is available
 */
export async function checkMiseAvailable(): Promise<MiseStatus> {
  const response = await invoke<CommandResponse<MiseStatus>>('check_mise_available');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to check Mise status');
  }
  return response.data;
}

/**
 * Get Mise installed tools
 */
export async function getMiseInstalledTools(): Promise<{
  success: boolean;
  tools?: Record<string, string>;
  error?: string;
}> {
  const response = await invoke<
    CommandResponse<{
      success: boolean;
      tools?: Record<string, string>;
      error?: string;
    }>
  >('get_mise_installed_tools');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get Mise installed tools');
  }
  return response.data;
}

/**
 * Get available installers for current platform
 */
export async function getAvailableInstallers(): Promise<InstallerInfo[]> {
  const response = await invoke<CommandResponse<InstallerInfo[]>>(
    'get_available_installers'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get available installers');
  }
  return response.data;
}

/**
 * Get prerequisites summary
 */
export async function getPrerequisitesSummary(): Promise<PrerequisitesSummary> {
  const response = await invoke<CommandResponse<PrerequisitesSummary>>(
    'get_prerequisites_summary'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get prerequisites summary');
  }
  return response.data;
}

/**
 * Refresh platform info (clears cache)
 */
export async function refreshPlatformInfo(): Promise<PlatformInfo> {
  const response = await invoke<CommandResponse<PlatformInfo>>('refresh_platform_info');
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to refresh platform info');
  }
  return response.data;
}
