/**
 * Global application state using Zustand
 */

import { create } from 'zustand';
import type {
  BackendConfig,
  BridgeState,
  DevflowConfig,
  GlobalConfig,
  InfraStatus,
  Project,
} from '../types';

interface AppState {
  // Backend configuration
  backendConfigured: boolean;
  setBackendConfigured: (configured: boolean) => void;
  backendConfig: BackendConfig | null;
  setBackendConfig: (config: BackendConfig | null) => void;

  // Bridge state
  bridgeState: BridgeState;
  setBridgeState: (state: BridgeState) => void;

  // Global config
  globalConfig: GlobalConfig | null;
  setGlobalConfig: (config: GlobalConfig | null) => void;

  // Infrastructure status
  infraStatus: InfraStatus | null;
  setInfraStatus: (status: InfraStatus | null) => void;

  // Projects
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  removeProject: (path: string) => void;

  // Active project
  activeProject: { path: string; config: DevflowConfig } | null;
  setActiveProject: (project: { path: string; config: DevflowConfig } | null) => void;

  // UI state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Notifications
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number;
}

export const useAppStore = create<AppState>((set) => ({
  // Backend configuration
  backendConfigured: false,
  setBackendConfigured: (backendConfigured) => set({ backendConfigured }),
  backendConfig: null,
  setBackendConfig: (backendConfig) => set({ backendConfig }),

  // Bridge state
  bridgeState: 'Stopped',
  setBridgeState: (bridgeState) => set({ bridgeState }),

  // Global config
  globalConfig: null,
  setGlobalConfig: (globalConfig) => set({ globalConfig }),

  // Infrastructure status
  infraStatus: null,
  setInfraStatus: (infraStatus) => set({ infraStatus }),

  // Projects
  projects: [],
  setProjects: (projects) => set({ projects }),
  addProject: (project) =>
    set((state) => ({ projects: [...state.projects, project] })),
  removeProject: (path) =>
    set((state) => ({
      projects: state.projects.filter((p) => p.path !== path),
    })),

  // Active project
  activeProject: null,
  setActiveProject: (activeProject) => set({ activeProject }),

  // UI state
  sidebarCollapsed: false,
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  // Notifications
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: crypto.randomUUID() },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));
