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
    const mockGlobalConfig = {
      version: '1.0',
      git: {
        user_name: 'Test User',
        user_email: 'test@example.com',
        co_author_enabled: false,
        co_author_name: 'Claude',
        co_author_email: 'claude@anthropic.com',
      },
      defaults: {
        secrets_provider: null,
        network_name: 'devflow-net',
        registry: null,
      },
      infrastructure: {
        auto_start: true,
        traefik_http_port: 80,
        traefik_https_port: 443,
        traefik_dashboard_port: 8080,
      },
      setup_completed: true,
    };

    it('should have initial global config as null', () => {
      expect(useAppStore.getState().globalConfig).toBeNull();
    });

    it('should set global config', () => {
      act(() => {
        useAppStore.getState().setGlobalConfig(mockGlobalConfig);
      });

      expect(useAppStore.getState().globalConfig).toEqual(mockGlobalConfig);
    });

    it('should clear global config', () => {
      act(() => {
        useAppStore.getState().setGlobalConfig(mockGlobalConfig);
        useAppStore.getState().setGlobalConfig(null);
      });

      expect(useAppStore.getState().globalConfig).toBeNull();
    });
  });

  describe('Projects', () => {
    const mockProject = {
      path: '/path/to/project',
      name: 'Test Project',
      configured_at: '2024-01-01T00:00:00Z',
      last_accessed: '2024-01-01T00:00:00Z',
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
      const anotherProject = {
        path: '/another/project',
        name: 'Another',
        configured_at: '2024-01-01T00:00:00Z',
        last_accessed: '2024-01-01T00:00:00Z',
      };

      act(() => {
        useAppStore.getState().addProject(mockProject);
        useAppStore.getState().addProject(anotherProject);
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
        project: { name: 'Test Project', preset: null },
        database: null,
        secrets: null,
        deployment: null,
        development: null,
        infrastructure: null,
        git: null,
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
        .mockReturnValueOnce('11111111-1111-1111-1111-111111111111')
        .mockReturnValueOnce('22222222-2222-2222-2222-222222222222');

      act(() => {
        useAppStore.getState().addNotification({ type: 'info', title: 'First' });
        useAppStore.getState().addNotification({ type: 'info', title: 'Second' });
        useAppStore.getState().removeNotification('11111111-1111-1111-1111-111111111111');
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
      network_exists: true,
      network_name: 'devflow-net',
      traefik_running: true,
      traefik_container_id: 'abc123',
      traefik_url: 'http://localhost:8080',
      certificates_valid: true,
      certificates_path: '/path/to/certs',
      registered_projects: [],
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
