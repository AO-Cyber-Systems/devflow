/**
 * UpdateChecker - Checks for app updates and displays a banner when available
 */

import { useState, useEffect, useCallback } from 'react';
import { Download, X, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../common';
import { checkForUpdates, downloadAndInstallUpdate, type UpdateCheckResult } from '../../api/updater';

type UpdateState = 'idle' | 'checking' | 'available' | 'downloading' | 'installing' | 'error';

export function UpdateChecker() {
  const [state, setState] = useState<UpdateState>('idle');
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResult | null>(null);
  const [progress, setProgress] = useState<{ downloaded: number; total: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const checkUpdate = useCallback(async () => {
    setState('checking');
    setError(null);
    try {
      const result = await checkForUpdates();
      setUpdateInfo(result);
      setState(result.available ? 'available' : 'idle');
    } catch (err) {
      console.error('Update check failed:', err);
      setState('idle');
    }
  }, []);

  // Check for updates on mount (with a small delay to not block app startup)
  useEffect(() => {
    const timer = setTimeout(() => {
      checkUpdate();
    }, 3000);
    return () => clearTimeout(timer);
  }, [checkUpdate]);

  const handleDownload = async () => {
    setState('downloading');
    setProgress({ downloaded: 0, total: null });
    setError(null);

    try {
      await downloadAndInstallUpdate((downloaded, total) => {
        setProgress({ downloaded, total });
      });
      setState('installing');
      // App will relaunch automatically
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Download failed';
      setError(message);
      setState('error');
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
  };

  // Don't render if dismissed or no update available
  if (dismissed || state === 'idle') {
    return null;
  }

  // Checking state - subtle indicator
  if (state === 'checking') {
    return null; // Don't show anything while checking
  }

  const progressPercent = progress?.total
    ? Math.round((progress.downloaded / progress.total) * 100)
    : 0;

  return (
    <div className="bg-accent-primary/10 border-b border-accent-primary/20 px-4 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {state === 'available' && (
            <>
              <div className="p-1.5 bg-accent-primary/20 rounded-full">
                <Download className="w-4 h-4 text-accent-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">
                  Update available: v{updateInfo?.version}
                </p>
                {updateInfo?.notes && (
                  <p className="text-xs text-text-secondary line-clamp-1 max-w-md">
                    {updateInfo.notes}
                  </p>
                )}
              </div>
            </>
          )}

          {state === 'downloading' && (
            <>
              <RefreshCw className="w-4 h-4 text-accent-primary animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-medium text-text-primary">
                  Downloading update...
                </p>
                <div className="mt-1 h-1.5 bg-bg-tertiary rounded-full overflow-hidden w-48">
                  <div
                    className="h-full bg-accent-primary transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
              <span className="text-xs text-text-secondary">
                {progressPercent}%
              </span>
            </>
          )}

          {state === 'installing' && (
            <>
              <CheckCircle className="w-4 h-4 text-success" />
              <p className="text-sm font-medium text-text-primary">
                Installing update... App will restart shortly.
              </p>
            </>
          )}

          {state === 'error' && (
            <>
              <AlertCircle className="w-4 h-4 text-error" />
              <div>
                <p className="text-sm font-medium text-text-primary">
                  Update failed
                </p>
                <p className="text-xs text-error">{error}</p>
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {state === 'available' && (
            <Button
              size="sm"
              onClick={handleDownload}
              icon={<Download size={14} />}
            >
              Install Update
            </Button>
          )}

          {state === 'error' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={checkUpdate}
              icon={<RefreshCw size={14} />}
            >
              Retry
            </Button>
          )}

          {(state === 'available' || state === 'error') && (
            <button
              onClick={handleDismiss}
              className="p-1 text-text-secondary hover:text-text-primary transition-colors"
              title="Dismiss"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
