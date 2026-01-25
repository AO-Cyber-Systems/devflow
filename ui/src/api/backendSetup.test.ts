/**
 * Unit tests for backend setup API
 */

import { describe, it, expect, beforeEach } from 'vitest';
import type { BackendType } from '../types';
import { invoke, clearInvokeResponses, setInvokeResponse } from '@tauri-apps/api/core';
import {
  detectPrerequisites,
  getBackendConfig,
  createDefaultConfig,
  getBackendTypeName,
  getBackendTypeDescription,
} from './backendSetup';

describe('backendSetup API - helper functions', () => {
  describe('createDefaultConfig', () => {
    it('creates local_python config with correct defaults', () => {
      const config = createDefaultConfig('local_python');
      expect(config.backend_type).toBe('local_python');
      expect(config.auto_start).toBe(true);
      expect(config.python_path).toBeNull();
      expect(config.container_name).toBeNull();
      expect(config.remote_host).toBeNull();
    });

    it('creates docker config with correct defaults', () => {
      const config = createDefaultConfig('docker');
      expect(config.backend_type).toBe('docker');
      expect(config.auto_start).toBe(true);
      expect(config.container_name).toBe('devflow-backend');
      expect(config.remote_host).toBe('127.0.0.1');
      expect(config.remote_port).toBe(9876);
    });

    it('creates wsl2 config with correct defaults', () => {
      const config = createDefaultConfig('wsl2');
      expect(config.backend_type).toBe('wsl2');
      expect(config.auto_start).toBe(true);
      expect(config.wsl_distro).toBe('Ubuntu');
      expect(config.remote_host).toBe('127.0.0.1');
      expect(config.remote_port).toBe(9876);
    });

    it('creates remote config with correct defaults', () => {
      const config = createDefaultConfig('remote');
      expect(config.backend_type).toBe('remote');
      expect(config.auto_start).toBe(false); // Remote doesn't auto-start
      expect(config.remote_host).toBe('localhost');
      expect(config.remote_port).toBe(9876);
    });
  });

  describe('getBackendTypeName', () => {
    it('returns correct names for all types', () => {
      expect(getBackendTypeName('local_python')).toBe('Local Python');
      expect(getBackendTypeName('docker')).toBe('Docker Container');
      expect(getBackendTypeName('wsl2')).toBe('WSL2 Service');
      expect(getBackendTypeName('remote')).toBe('Remote Server');
    });
  });

  describe('getBackendTypeDescription', () => {
    it('returns non-empty descriptions for all types', () => {
      const types: BackendType[] = ['local_python', 'docker', 'wsl2', 'remote'];
      types.forEach((type) => {
        const description = getBackendTypeDescription(type);
        expect(description).toBeTruthy();
        expect(description.length).toBeGreaterThan(10);
      });
    });
  });
});

describe('backendSetup API - invoke calls', () => {
  beforeEach(() => {
    clearInvokeResponses();
  });

  it('detectPrerequisites returns parsed data', async () => {
    setInvokeResponse('detect_prerequisites', {
      success: true,
      data: {
        python_available: true,
        python_version: '3.11.5',
        python_path: '/usr/bin/python3',
        devflow_installed: true,
        devflow_version: '0.1.0',
        docker_available: true,
        docker_running: true,
        docker_version: '24.0.5',
        wsl_available: false,
        wsl_distros: [],
      },
    });

    const result = await detectPrerequisites();
    expect(result.python_available).toBe(true);
    expect(result.python_version).toBe('3.11.5');
    expect(result.docker_running).toBe(true);
    expect(invoke).toHaveBeenCalledWith('detect_prerequisites');
  });

  it('getBackendConfig returns unconfigured state', async () => {
    setInvokeResponse('get_backend_config', {
      success: true,
      data: {
        configured: false,
        default_backend: null,
      },
    });

    const result = await getBackendConfig();
    expect(result.configured).toBe(false);
    expect(result.default_backend).toBeNull();
    expect(invoke).toHaveBeenCalledWith('get_backend_config');
  });

  it('getBackendConfig returns configured backend', async () => {
    setInvokeResponse('get_backend_config', {
      success: true,
      data: {
        configured: true,
        default_backend: {
          backend_type: 'local_python',
          python_path: '/usr/bin/python3',
          auto_start: true,
        },
      },
    });

    const result = await getBackendConfig();
    expect(result.configured).toBe(true);
    expect(result.default_backend?.backend_type).toBe('local_python');
  });

  it('throws on API error', async () => {
    setInvokeResponse('detect_prerequisites', {
      success: false,
      error: 'Test error',
    });

    await expect(detectPrerequisites()).rejects.toThrow('Test error');
  });
});
