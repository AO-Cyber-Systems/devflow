import { useEffect, useState } from 'react';
import { Database as DbIcon, Play, RotateCcw, Plus, RefreshCw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import {
  getMigrationStatus,
  runMigrations,
  rollbackMigrations,
  createMigration,
  type MigrationStatus,
} from '../api';

export function Database() {
  const { activeProject, bridgeState, addNotification } = useAppStore();
  const [environment, setEnvironment] = useState('local');
  const [migrations, setMigrations] = useState<MigrationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newMigrationName, setNewMigrationName] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const isConnected = bridgeState === 'Running';

  const loadStatus = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const status = await getMigrationStatus(activeProject.path, environment);
      setMigrations(status);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load migration status',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isConnected && activeProject) {
      loadStatus();
    } else {
      setMigrations(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected, activeProject, environment]);

  const handleApplyMigrations = async () => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await runMigrations(activeProject.path, environment);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Migrations applied',
          message: `Applied ${result.applied} migrations`,
        });
        loadStatus();
      } else {
        throw new Error(result.error || 'Migration failed');
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to apply migrations',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await rollbackMigrations(activeProject.path, environment, 1);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Rollback complete',
          message: `Rolled back ${result.rolled_back} migrations`,
        });
        loadStatus();
      } else {
        throw new Error('Rollback failed');
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to rollback',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateMigration = async () => {
    if (!activeProject || !newMigrationName.trim()) return;
    setActionLoading(true);
    try {
      const result = await createMigration(activeProject.path, newMigrationName);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Migration created',
          message: `Created ${result.file}`,
        });
        setNewMigrationName('');
        setShowCreateDialog(false);
        loadStatus();
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to create migration',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <>
      <Header
        title="Database"
        subtitle={activeProject ? `Manage migrations for ${activeProject.config.project.name}` : 'Manage database migrations'}
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
              onClick={loadStatus}
              loading={loading}
              disabled={!isConnected || !activeProject}
            >
              Refresh
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {!activeProject && (
            <Card className="bg-warning/10 border-warning/30">
              <p className="text-text-primary">
                No project selected. Select a project from the sidebar to manage its database migrations.
              </p>
            </Card>
          )}

          {activeProject && !migrations && !loading && (
            <Card className="bg-bg-tertiary">
              <div className="text-center py-8">
                <DbIcon size={40} className="mx-auto mb-4 text-text-muted" />
                <p className="text-text-secondary mb-2">
                  No database configuration found for this project.
                </p>
                <p className="text-sm text-text-muted">
                  Add a database section to your devflow.yml to manage migrations.
                </p>
              </div>
            </Card>
          )}

          {/* Status */}
          {migrations && (
            <>
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
                  <div className={`p-3 rounded-lg bg-bg-tertiary ${migrations.pending > 0 ? 'text-warning' : 'text-text-muted'}`}>
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
                  <Button
                    icon={<Play size={16} />}
                    onClick={handleApplyMigrations}
                    loading={actionLoading}
                    disabled={!isConnected || migrations.pending === 0}
                  >
                    Apply Pending ({migrations.pending})
                  </Button>
                  <Button
                    variant="secondary"
                    icon={<RotateCcw size={16} />}
                    onClick={handleRollback}
                    loading={actionLoading}
                    disabled={!isConnected || migrations.applied === 0}
                  >
                    Rollback
                  </Button>
                  <Button
                    variant="secondary"
                    icon={<Plus size={16} />}
                    onClick={() => setShowCreateDialog(true)}
                    disabled={!isConnected}
                  >
                    Create Migration
                  </Button>
                </div>
              </Card>

              {/* Create Migration Dialog */}
              {showCreateDialog && (
                <Card>
                  <CardHeader title="Create New Migration" />
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newMigrationName}
                      onChange={(e) => setNewMigrationName(e.target.value)}
                      placeholder="e.g., add_users_table"
                      className="flex-1 px-4 py-2 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      onKeyDown={(e) => e.key === 'Enter' && handleCreateMigration()}
                    />
                    <Button
                      onClick={handleCreateMigration}
                      loading={actionLoading}
                      disabled={!newMigrationName.trim()}
                    >
                      Create
                    </Button>
                    <Button variant="secondary" onClick={() => setShowCreateDialog(false)}>
                      Cancel
                    </Button>
                  </div>
                </Card>
              )}

              {/* Pending Migrations */}
              <Card>
                <CardHeader title="Pending Migrations" />
                {migrations.pending_files.length > 0 ? (
                  <div className="space-y-2">
                    {migrations.pending_files.map((file) => (
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
            </>
          )}
        </div>
      </div>
    </>
  );
}
