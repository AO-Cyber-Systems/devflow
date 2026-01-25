import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

export interface UpdateCheckResult {
  available: boolean;
  version?: string;
  notes?: string;
  date?: string;
}

export async function checkForUpdates(): Promise<UpdateCheckResult> {
  try {
    const update = await check();
    if (update) {
      return {
        available: true,
        version: update.version,
        notes: update.body ?? undefined,
        date: update.date ?? undefined,
      };
    }
    return { available: false };
  } catch (error) {
    console.error('Update check failed:', error);
    return { available: false };
  }
}

export async function installUpdate(): Promise<void> {
  const update = await check();
  if (update) {
    await update.downloadAndInstall();
    await relaunch();
  }
}

export async function downloadAndInstallUpdate(
  onProgress?: (downloaded: number, total: number | null) => void
): Promise<void> {
  const update = await check();
  if (!update) {
    throw new Error('No update available');
  }

  let downloaded = 0;
  let contentLength: number | null = null;

  await update.downloadAndInstall((event) => {
    switch (event.event) {
      case 'Started':
        contentLength = event.data.contentLength ?? null;
        break;
      case 'Progress':
        downloaded += event.data.chunkLength;
        if (onProgress) {
          onProgress(downloaded, contentLength);
        }
        break;
      case 'Finished':
        break;
    }
  });

  await relaunch();
}
