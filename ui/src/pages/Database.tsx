import { useState } from 'react';
import { Database as DbIcon, Play, RotateCcw, Plus, RefreshCw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';

export function Database() {
  const { bridgeState } = useAppStore();
  const [environment, setEnvironment] = useState('local');
  const [migrations] = useState({
    applied: 15,
    pending: 2,
    total: 17,
    pendingFiles: ['20240115_add_users_table.sql', '20240116_add_posts_table.sql'],
  });

  const isConnected = bridgeState === 'Running';

  return (
    <>
      <Header
        title="Database"
        subtitle="Manage database migrations"
        actions={
          <div className="flex items-center gap-2">
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="px-3 py-1.5 bg-bg-tertiary border border-border rounded-lg text-sm"
            >
              <option value="local">Local</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw size={16} />}
              disabled={!isConnected}
            >
              Refresh
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-success">
                <DbIcon size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Applied</p>
                <p className="text-2xl font-semibold">{migrations.applied}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-warning">
                <DbIcon size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Pending</p>
                <p className="text-2xl font-semibold">{migrations.pending}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-text-secondary">
                <DbIcon size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Total</p>
                <p className="text-2xl font-semibold">{migrations.total}</p>
              </div>
            </Card>
          </div>

          {/* Actions */}
          <Card>
            <CardHeader title="Actions" />
            <div className="flex flex-wrap gap-3">
              <Button icon={<Play size={16} />} disabled={!isConnected || migrations.pending === 0}>
                Apply Pending ({migrations.pending})
              </Button>
              <Button variant="secondary" icon={<RotateCcw size={16} />} disabled={!isConnected}>
                Rollback
              </Button>
              <Button variant="secondary" icon={<Plus size={16} />} disabled={!isConnected}>
                Create Migration
              </Button>
            </div>
          </Card>

          {/* Pending Migrations */}
          <Card>
            <CardHeader title="Pending Migrations" />
            {migrations.pendingFiles.length > 0 ? (
              <div className="space-y-2">
                {migrations.pendingFiles.map((file) => (
                  <div
                    key={file}
                    className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <StatusBadge status="pending" />
                      <span className="font-mono text-sm">{file}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-secondary text-center py-4">
                All migrations applied
              </p>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}
