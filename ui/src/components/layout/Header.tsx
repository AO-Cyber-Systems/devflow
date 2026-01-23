import { Circle, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store';
import type { BridgeState } from '../../types';

function getBridgeStatusColor(state: BridgeState): string {
  switch (state) {
    case 'Running':
      return 'text-success';
    case 'Starting':
      return 'text-warning';
    case 'Error':
      return 'text-error';
    default:
      return 'text-text-muted';
  }
}

function getBridgeStatusText(state: BridgeState): string {
  switch (state) {
    case 'Running':
      return 'Connected';
    case 'Starting':
      return 'Connecting...';
    case 'Error':
      return 'Connection Error';
    default:
      return 'Disconnected';
  }
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  const { bridgeState, infraStatus, activeProject } = useAppStore();

  return (
    <header className="h-14 border-b border-border bg-bg-secondary flex items-center justify-between px-6">
      {/* Left side - Title */}
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">{title}</h1>
          {subtitle && (
            <p className="text-sm text-text-secondary">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Right side - Status and actions */}
      <div className="flex items-center gap-4">
        {/* Infrastructure status */}
        {infraStatus && (
          <div className="flex items-center gap-2 text-sm">
            <Circle
              size={8}
              className={`fill-current ${
                infraStatus.traefik_running ? 'text-success' : 'text-text-muted'
              }`}
            />
            <span className="text-text-secondary">
              {infraStatus.traefik_running ? 'Traefik Running' : 'Traefik Stopped'}
            </span>
          </div>
        )}

        {/* Active project */}
        {activeProject && (
          <div className="flex items-center gap-2 text-sm px-3 py-1 bg-bg-tertiary rounded-md">
            <span className="text-text-secondary">Project:</span>
            <span className="text-text-primary font-medium">
              {activeProject.config.project.name}
            </span>
          </div>
        )}

        {/* Bridge status */}
        <div className="flex items-center gap-2 text-sm">
          {bridgeState === 'Starting' ? (
            <RefreshCw size={14} className="animate-spin text-warning" />
          ) : (
            <Circle
              size={8}
              className={`fill-current ${getBridgeStatusColor(bridgeState)}`}
            />
          )}
          <span className="text-text-secondary">
            {getBridgeStatusText(bridgeState)}
          </span>
        </div>

        {/* Custom actions */}
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}
