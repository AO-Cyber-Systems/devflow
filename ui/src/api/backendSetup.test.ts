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
  getWslDistrosDetailed,
  validateWslInstallation,
  getWslIssueMessage,
} from './backendSetup';
import type { WslInstallIssue } from '../types';

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

  it('getWslDistrosDetailed returns distro list', async () => {
    setInvokeResponse('get_wsl_distros_detailed', {
      success: true,
      data: [
        {
          name: 'Ubuntu',
          is_wsl2: true,
          is_running: true,
          python_available: true,
          python_version: '3.11.5',
          devflow_installed: false,
          devflow_version: null,
        },
        {
          name: 'Debian',
          is_wsl2: true,
          is_running: false,
          python_available: true,
          python_version: '3.9.2',
          devflow_installed: true,
          devflow_version: '0.2.0',
        },
      ],
    });

    const result = await getWslDistrosDetailed();
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('Ubuntu');
    expect(result[0].is_wsl2).toBe(true);
    expect(result[0].is_running).toBe(true);
    expect(result[1].name).toBe('Debian');
    expect(result[1].devflow_installed).toBe(true);
    expect(invoke).toHaveBeenCalledWith('get_wsl_distros_detailed');
  });

  it('validateWslInstallation returns validation result', async () => {
    setInvokeResponse('validate_wsl_install', {
      success: true,
      data: {
        distro: 'Ubuntu',
        can_install: true,
        issues: [],
        warnings: ['pipx will be installed automatically'],
      },
    });

    const result = await validateWslInstallation('Ubuntu', 9876);
    expect(result.distro).toBe('Ubuntu');
    expect(result.can_install).toBe(true);
    expect(result.issues).toHaveLength(0);
    expect(result.warnings).toHaveLength(1);
    expect(invoke).toHaveBeenCalledWith('validate_wsl_install', { distro: 'Ubuntu', port: 9876 });
  });

  it('validateWslInstallation returns issues for invalid distro', async () => {
    setInvokeResponse('validate_wsl_install', {
      success: true,
      data: {
        distro: 'OldDistro',
        can_install: false,
        issues: [
          { type: 'distro_not_wsl2' },
          { type: 'python_version_too_old', version: '3.8.10', required: '3.10' },
        ],
        warnings: [],
      },
    });

    const result = await validateWslInstallation('OldDistro', 9876);
    expect(result.can_install).toBe(false);
    expect(result.issues).toHaveLength(2);
    expect(result.issues[0].type).toBe('distro_not_wsl2');
    expect(result.issues[1].type).toBe('python_version_too_old');
  });
});

describe('backendSetup API - getWslIssueMessage helper', () => {
  it('returns correct message for distro_not_wsl2', () => {
    const issue: WslInstallIssue = { type: 'distro_not_wsl2' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('WSL1 Distribution');
    expect(result.resolution).toContain('wsl --set-version');
  });

  it('returns correct message for distro_not_running', () => {
    const issue: WslInstallIssue = { type: 'distro_not_running' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('Distribution Not Running');
    expect(result.resolution).toBeNull(); // We show a start button instead
  });

  it('returns correct message for python_not_installed', () => {
    const issue: WslInstallIssue = { type: 'python_not_installed' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('Python Not Installed');
    expect(result.resolution).toContain('apt install python3');
  });

  it('returns correct message for python_version_too_old', () => {
    const issue: WslInstallIssue = { type: 'python_version_too_old', version: '3.8.10', required: '3.10' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('Python Version Too Old');
    expect(result.description).toContain('3.8.10');
    expect(result.description).toContain('3.10');
  });

  it('returns correct message for no_network_access', () => {
    const issue: WslInstallIssue = { type: 'no_network_access' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('No Network Access');
  });

  it('returns correct message for insufficient_disk_space', () => {
    const issue: WslInstallIssue = { type: 'insufficient_disk_space', available_mb: 100, required_mb: 500 };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('Insufficient Disk Space');
    expect(result.description).toContain('100');
    expect(result.description).toContain('500');
  });

  it('returns correct message for pipx_not_available', () => {
    const issue: WslInstallIssue = { type: 'pipx_not_available' };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('pipx Not Available');
    expect(result.resolution).toContain('pipx');
  });

  it('returns correct message for port_in_use', () => {
    const issue: WslInstallIssue = { type: 'port_in_use', port: 9876 };
    const result = getWslIssueMessage(issue);
    expect(result.title).toBe('Port In Use');
    expect(result.description).toContain('9876');
    expect(result.resolution).toBeNull(); // We show port selector instead
  });
});
