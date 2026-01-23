/**
 * Projects API
 */

import { invoke } from '@tauri-apps/api/core';
import type { CommandResponse, Project, ProjectStatus } from '../types';

export async function listProjects(): Promise<Project[]> {
  const response = await invoke<CommandResponse<{ projects: Project[]; total: number }>>(
    'list_projects'
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to list projects');
  }
  return response.data.projects;
}

export async function addProject(path: string): Promise<Project> {
  const response = await invoke<CommandResponse<{ project: Project }>>('add_project', {
    path,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to add project');
  }
  return response.data.project;
}

export async function removeProject(path: string): Promise<void> {
  const response = await invoke<CommandResponse<unknown>>('remove_project', {
    path,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to remove project');
  }
}

export async function getProjectStatus(path: string): Promise<ProjectStatus> {
  const response = await invoke<CommandResponse<ProjectStatus>>('get_project_status', {
    path,
  });
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to get project status');
  }
  return response.data;
}

export async function openProjectFolder(path: string): Promise<void> {
  const response = await invoke<CommandResponse<void>>('open_project_folder', {
    path,
  });
  if (!response.success) {
    throw new Error(response.error || 'Failed to open project folder');
  }
}

export async function initProject(
  path: string,
  preset?: string
): Promise<{ path: string; preset?: string }> {
  const response = await invoke<CommandResponse<{ path: string; preset?: string }>>(
    'init_project',
    { path, preset }
  );
  if (!response.success || !response.data) {
    throw new Error(response.error || 'Failed to initialize project');
  }
  return response.data;
}
