/**
 * Unit tests for the updater API.
 */

import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { checkForUpdates, installUpdate, downloadAndInstallUpdate } from './updater';

// Mock the Tauri plugins
vi.mock('@tauri-apps/plugin-updater', () => ({
  check: vi.fn(),
}));

vi.mock('@tauri-apps/plugin-process', () => ({
  relaunch: vi.fn(),
}));

import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

describe('updater API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('checkForUpdates', () => {
    it('should return available: true when update is available', async () => {
      const mockUpdate = {
        version: '1.2.0',
        body: 'New features and bug fixes',
        date: '2024-01-15T12:00:00Z',
        downloadAndInstall: vi.fn(),
      };
      (check as Mock).mockResolvedValue(mockUpdate);

      const result = await checkForUpdates();

      expect(result.available).toBe(true);
      expect(result.version).toBe('1.2.0');
      expect(result.notes).toBe('New features and bug fixes');
      expect(result.date).toBe('2024-01-15T12:00:00Z');
    });

    it('should return available: false when no update is available', async () => {
      (check as Mock).mockResolvedValue(null);

      const result = await checkForUpdates();

      expect(result.available).toBe(false);
      expect(result.version).toBeUndefined();
    });

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (check as Mock).mockRejectedValue(new Error('Network error'));

      const result = await checkForUpdates();

      expect(result.available).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith('Update check failed:', expect.any(Error));
      consoleSpy.mockRestore();
    });

    it('should handle update with null body and date', async () => {
      const mockUpdate = {
        version: '1.2.0',
        body: null,
        date: null,
        downloadAndInstall: vi.fn(),
      };
      (check as Mock).mockResolvedValue(mockUpdate);

      const result = await checkForUpdates();

      expect(result.available).toBe(true);
      expect(result.version).toBe('1.2.0');
      expect(result.notes).toBeUndefined();
      expect(result.date).toBeUndefined();
    });
  });

  describe('installUpdate', () => {
    it('should download, install, and relaunch when update is available', async () => {
      const mockDownloadAndInstall = vi.fn().mockResolvedValue(undefined);
      const mockUpdate = {
        version: '1.2.0',
        downloadAndInstall: mockDownloadAndInstall,
      };
      (check as Mock).mockResolvedValue(mockUpdate);
      (relaunch as Mock).mockResolvedValue(undefined);

      await installUpdate();

      expect(mockDownloadAndInstall).toHaveBeenCalled();
      expect(relaunch).toHaveBeenCalled();
    });

    it('should not do anything when no update is available', async () => {
      (check as Mock).mockResolvedValue(null);

      await installUpdate();

      expect(relaunch).not.toHaveBeenCalled();
    });
  });

  describe('downloadAndInstallUpdate', () => {
    it('should throw error when no update is available', async () => {
      (check as Mock).mockResolvedValue(null);

      await expect(downloadAndInstallUpdate()).rejects.toThrow('No update available');
    });

    it('should call progress callback with download progress', async () => {
      const mockDownloadAndInstall = vi.fn().mockImplementation(async (callback) => {
        // Simulate progress events
        callback({ event: 'Started', data: { contentLength: 1000 } });
        callback({ event: 'Progress', data: { chunkLength: 500 } });
        callback({ event: 'Progress', data: { chunkLength: 500 } });
        callback({ event: 'Finished' });
      });
      const mockUpdate = {
        version: '1.2.0',
        downloadAndInstall: mockDownloadAndInstall,
      };
      (check as Mock).mockResolvedValue(mockUpdate);
      (relaunch as Mock).mockResolvedValue(undefined);

      const progressCallback = vi.fn();
      await downloadAndInstallUpdate(progressCallback);

      expect(progressCallback).toHaveBeenCalledWith(500, 1000);
      expect(progressCallback).toHaveBeenCalledWith(1000, 1000);
      expect(relaunch).toHaveBeenCalled();
    });

    it('should handle missing contentLength in Started event', async () => {
      const mockDownloadAndInstall = vi.fn().mockImplementation(async (callback) => {
        callback({ event: 'Started', data: {} });
        callback({ event: 'Progress', data: { chunkLength: 500 } });
        callback({ event: 'Finished' });
      });
      const mockUpdate = {
        version: '1.2.0',
        downloadAndInstall: mockDownloadAndInstall,
      };
      (check as Mock).mockResolvedValue(mockUpdate);
      (relaunch as Mock).mockResolvedValue(undefined);

      const progressCallback = vi.fn();
      await downloadAndInstallUpdate(progressCallback);

      expect(progressCallback).toHaveBeenCalledWith(500, null);
    });
  });
});
