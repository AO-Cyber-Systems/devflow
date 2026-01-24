/**
 * Unit tests for the application store.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useAppStore } from './index';

// Mock crypto.randomUUID for consistent test results
vi.stubGlobal('crypto', {
  randomUUID: vi.fn().mockReturnValue('test-uuid-123'),
});

describe('useAppStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { getState } = useAppStore;
    act(() => {
      getState().setBridgeState('Stopped');
      getState().setGlobalConfig(null);
      getState().setInfraStatus(null);
      getState().setProjects([]);
      getState().setActiveProject(null);
      getState().clearNotifications();
    });
  });

  describe('Bridge State', () => {
    it('should have initial bridge state as Stopped', () => {
      const state = useAppStore.getState();
      expect(state.bridgeState).toBe('Stopped');
    });

    it('should update bridge state', () => {
      const { setBridgeState } = useAppStore.getState();

      act(() => {
        setBridgeState('Running');
      });

      expect(useAppStore.getState().bridgeState).toBe('Running');
    });

    it('should handle all bridge states', () => {
      const { setBridgeState } = useAppStore.getState();
      const states = ['Stopped', 'Starting', 'Running', 'Error'] as const;

      states.forEach((state) => {
        act(() => {
          setBridgeState(state);
        });
        expect(useAppStore.getState().bridgeState).toBe(state);
      });
    });
  });

  describe('Global Config', () => {
    it('should have initial global config as null', () => {
      expect(useAppStore.getState().globalConfig).toBeNull();
    });

    it('should set global config', () => {
      const config = {
        bridge_port: 9876,
        default_project: '/path/to/project',
      };

      act(() => {
        useAppStore.getState().setGlobalConfig(config);
      });

      expect(useAppStore.getState().globalConfig).toEqual(config);
    });

    it('should clear global config', () => {
      act(() => {
        useAppStore.getState().setGlobalConfig({ bridge_port: 9876 });
        useAppStore.getState().setGlobalConfig(null);
      });

      expect(useAppStore.getState().globalConfig).toBeNull();
    });
  });

  describe('Projects', () => {
    const mockProject = {
      path: '/path/to/project',
      name: 'Test Project',
    };

    it('should have initial projects as empty array', () => {
      expect(useAppStore.getState().projects).toEqual([]);
    });

    it('should set projects', () => {
      const projects = [mockProject];

      act(() => {
        useAppStore.getState().setProjects(projects);
      });

      expect(useAppStore.getState().projects).toEqual(projects);
    });

    it('should add a project', () => {
      act(() => {
        useAppStore.getState().addProject(mockProject);
      });

      expect(useAppStore.getState().projects).toHaveLength(1);
      expect(useAppStore.getState().projects[0]).toEqual(mockProject);
    });

    it('should remove a project by path', () => {
      act(() => {
        useAppStore.getState().addProject(mockProject);
        useAppStore.getState().addProject({ path: '/another/project', name: 'Another' });
        useAppStore.getState().removeProject('/path/to/project');
      });

      expect(useAppStore.getState().projects).toHaveLength(1);
      expect(useAppStore.getState().projects[0].path).toBe('/another/project');
    });
  });

  describe('Active Project', () => {
    const mockActiveProject = {
      path: '/path/to/project',
      config: {
        version: '1',
        project: { name: 'Test Project' },
      },
    };

    it('should have initial active project as null', () => {
      expect(useAppStore.getState().activeProject).toBeNull();
    });

    it('should set active project', () => {
      act(() => {
        useAppStore.getState().setActiveProject(mockActiveProject);
      });

      expect(useAppStore.getState().activeProject).toEqual(mockActiveProject);
    });

    it('should clear active project', () => {
      act(() => {
        useAppStore.getState().setActiveProject(mockActiveProject);
        useAppStore.getState().setActiveProject(null);
      });

      expect(useAppStore.getState().activeProject).toBeNull();
    });
  });

  describe('Sidebar', () => {
    it('should have sidebar expanded by default', () => {
      expect(useAppStore.getState().sidebarCollapsed).toBe(false);
    });

    it('should toggle sidebar', () => {
      act(() => {
        useAppStore.getState().toggleSidebar();
      });

      expect(useAppStore.getState().sidebarCollapsed).toBe(true);

      act(() => {
        useAppStore.getState().toggleSidebar();
      });

      expect(useAppStore.getState().sidebarCollapsed).toBe(false);
    });
  });

  describe('Notifications', () => {
    it('should have initial notifications as empty array', () => {
      expect(useAppStore.getState().notifications).toEqual([]);
    });

    it('should add notification with generated id', () => {
      act(() => {
        useAppStore.getState().addNotification({
          type: 'success',
          title: 'Test notification',
        });
      });

      const notifications = useAppStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0]).toEqual({
        id: 'test-uuid-123',
        type: 'success',
        title: 'Test notification',
      });
    });

    it('should add notification with message', () => {
      act(() => {
        useAppStore.getState().addNotification({
          type: 'error',
          title: 'Error occurred',
          message: 'Something went wrong',
        });
      });

      const notifications = useAppStore.getState().notifications;
      expect(notifications[0].message).toBe('Something went wrong');
    });

    it('should remove notification by id', () => {
      vi.mocked(crypto.randomUUID)
        .mockReturnValueOnce('uuid-1')
        .mockReturnValueOnce('uuid-2');

      act(() => {
        useAppStore.getState().addNotification({ type: 'info', title: 'First' });
        useAppStore.getState().addNotification({ type: 'info', title: 'Second' });
        useAppStore.getState().removeNotification('uuid-1');
      });

      const notifications = useAppStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].title).toBe('Second');
    });

    it('should clear all notifications', () => {
      act(() => {
        useAppStore.getState().addNotification({ type: 'info', title: 'First' });
        useAppStore.getState().addNotification({ type: 'info', title: 'Second' });
        useAppStore.getState().clearNotifications();
      });

      expect(useAppStore.getState().notifications).toEqual([]);
    });

    it('should handle all notification types', () => {
      const types = ['info', 'success', 'warning', 'error'] as const;

      types.forEach((type) => {
        act(() => {
          useAppStore.getState().clearNotifications();
          useAppStore.getState().addNotification({ type, title: `${type} notification` });
        });

        expect(useAppStore.getState().notifications[0].type).toBe(type);
      });
    });
  });

  describe('Infrastructure Status', () => {
    const mockInfraStatus = {
      running: true,
      traefik_healthy: true,
      network_exists: true,
    };

    it('should have initial infra status as null', () => {
      expect(useAppStore.getState().infraStatus).toBeNull();
    });

    it('should set infra status', () => {
      act(() => {
        useAppStore.getState().setInfraStatus(mockInfraStatus);
      });

      expect(useAppStore.getState().infraStatus).toEqual(mockInfraStatus);
    });
  });
});
