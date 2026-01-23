import { Circle } from 'lucide-react';

type Status = 'running' | 'stopped' | 'error' | 'warning' | 'pending' | 'success' | 'unknown';

interface StatusBadgeProps {
  status: Status;
  label?: string;
  size?: 'sm' | 'md';
}

const statusColors: Record<Status, string> = {
  running: 'text-success',
  success: 'text-success',
  stopped: 'text-text-muted',
  error: 'text-error',
  warning: 'text-warning',
  pending: 'text-warning',
  unknown: 'text-text-muted',
};

const statusLabels: Record<Status, string> = {
  running: 'Running',
  success: 'Success',
  stopped: 'Stopped',
  error: 'Error',
  warning: 'Warning',
  pending: 'Pending',
  unknown: 'Unknown',
};

export function StatusBadge({ status, label, size = 'md' }: StatusBadgeProps) {
  const displayLabel = label || statusLabels[status];
  const dotSize = size === 'sm' ? 6 : 8;

  return (
    <span className={`inline-flex items-center gap-1.5 ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>
      <Circle
        size={dotSize}
        className={`fill-current ${statusColors[status]}`}
      />
      <span className="text-text-secondary">{displayLabel}</span>
    </span>
  );
}
