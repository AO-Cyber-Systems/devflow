import { useEffect, useState } from 'react';
import { Key, RefreshCw, ArrowRightLeft, Check, AlertCircle } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import {
  listSecrets,
  syncSecrets,
  verifySecrets,
  getSecretProviders,
  type SecretsList,
  type SecretProvider,
} from '../api';

export function Secrets() {
  const { activeProject, bridgeState, addNotification } = useAppStore();
  const [secrets, setSecrets] = useState<SecretsList | null>(null);
  const [providers, setProviders] = useState<SecretProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const isConnected = bridgeState === 'Running';

  useEffect(() => {
    if (isConnected) {
      loadProviders();
      if (activeProject) {
        loadSecrets();
      }
    } else {
      setSecrets(null);
      setProviders([]);
    }
  }, [isConnected, activeProject]);

  const loadSecrets = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const result = await listSecrets(activeProject.path);
      setSecrets(result);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load secrets',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const result = await getSecretProviders();
      setProviders(result.providers || []);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const handleSync = async (from: string, to: string) => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await syncSecrets(activeProject.path, from, to);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Secrets synced',
          message: `Synced ${result.synced} secrets from ${from} to ${to}`,
        });
        loadSecrets();
      } else {
        throw new Error(`Failed to sync: ${result.failed} failed`);
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to sync secrets',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await verifySecrets(activeProject.path);
      if (result.success && result.out_of_sync === 0) {
        addNotification({
          type: 'success',
          title: 'Secrets verified',
          message: `All ${result.in_sync} secrets are in sync`,
        });
      } else {
        addNotification({
          type: 'warning',
          title: 'Secrets out of sync',
          message: `${result.out_of_sync} secrets need to be synced`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to verify secrets',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const secretsList = secrets?.secrets || [];

  return (
    <>
      <Header
        title="Secrets"
        subtitle={activeProject ? `Manage secrets for ${activeProject.config.project.name}` : 'Manage secrets across providers'}
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} />}
            onClick={loadSecrets}
            loading={loading}
            disabled={!isConnected || !activeProject}
          >
            Refresh
          </Button>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {!activeProject && (
            <Card className="bg-warning/10 border-warning/30">
              <p className="text-text-primary">
                No project selected. Select a project from the sidebar to manage its secrets.
              </p>
            </Card>
          )}

          {activeProject && !secrets && !loading && (
            <Card className="bg-bg-tertiary">
              <div className="text-center py-8">
                <Key size={40} className="mx-auto mb-4 text-text-muted" />
                <p className="text-text-secondary mb-2">
                  No secrets configuration found for this project.
                </p>
                <p className="text-sm text-text-muted">
                  Add a secrets section to your devflow.yml to manage secrets.
                </p>
              </div>
            </Card>
          )}

          {/* Sync Actions */}
          {activeProject && (
            <Card>
              <CardHeader title="Sync Actions" description="Sync secrets between providers" />
              <div className="flex flex-wrap gap-3">
                <Button
                  icon={<ArrowRightLeft size={16} />}
                  onClick={() => handleSync('1password', 'github')}
                  loading={actionLoading}
                  disabled={!isConnected}
                >
                  1Password to GitHub
                </Button>
                <Button
                  variant="secondary"
                  icon={<ArrowRightLeft size={16} />}
                  onClick={() => handleSync('1password', 'docker')}
                  loading={actionLoading}
                  disabled={!isConnected}
                >
                  1Password to Docker
                </Button>
                <Button
                  variant="secondary"
                  icon={<Check size={16} />}
                  onClick={handleVerify}
                  loading={actionLoading}
                  disabled={!isConnected}
                >
                  Verify All
                </Button>
              </div>
            </Card>
          )}

          {/* Secrets List */}
          {secrets && (
            <Card>
              <CardHeader
                title="Configured Secrets"
                description={`${secrets.total_count} secrets, ${secrets.mapped_count} mapped`}
              />
              {secretsList.length > 0 ? (
                <div className="space-y-2">
                  {secretsList.map((secret) => (
                    <div
                      key={secret.name}
                      className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Key size={18} className="text-text-muted" />
                        <div>
                          <p className="font-medium font-mono">{secret.name}</p>
                          <p className="text-sm text-text-muted">Source: {secret.source}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {secret.mapped_to.length > 0 ? (
                          secret.mapped_to.map((target) => (
                            <span
                              key={target}
                              className="text-xs px-2 py-1 rounded bg-success/20 text-success"
                            >
                              {target}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs px-2 py-1 rounded bg-warning/20 text-warning flex items-center gap-1">
                            <AlertCircle size={12} /> Not synced
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-text-secondary text-center py-4">
                  No secrets configured
                </p>
              )}
            </Card>
          )}

          {/* Providers */}
          <Card>
            <CardHeader title="Providers" description="Available secret providers" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {providers.length > 0 ? (
                providers.map((provider) => (
                  <div key={provider.name} className="p-3 bg-bg-tertiary rounded-lg text-center">
                    <p className="font-medium">{provider.name}</p>
                    <StatusBadge
                      status={provider.authenticated ? 'success' : provider.available ? 'warning' : 'error'}
                      label={provider.authenticated ? 'Connected' : provider.available ? 'Available' : 'Unavailable'}
                      size="sm"
                    />
                  </div>
                ))
              ) : (
                ['1Password', 'GitHub', 'Docker', 'Environment'].map((provider) => (
                  <div key={provider} className="p-3 bg-bg-tertiary rounded-lg text-center">
                    <p className="font-medium">{provider}</p>
                    <StatusBadge status="warning" label="Unknown" size="sm" />
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
