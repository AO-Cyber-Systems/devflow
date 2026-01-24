import { useEffect, useState } from 'react';
import { Server, Globe, Shield, Play, Square, RefreshCw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import { getInfraStatus, startInfra, stopInfra, regenerateCerts } from '../api';

export function Infrastructure() {
  const { infraStatus, setInfraStatus, bridgeState, addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);

  const isConnected = bridgeState === 'Running';

  const loadStatus = async () => {
    setLoading(true);
    try {
      const status = await getInfraStatus();
      setInfraStatus(status);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load infrastructure status',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isConnected) {
      loadStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected]);

  const handleStart = async () => {
    try {
      await startInfra();
      addNotification({ type: 'success', title: 'Infrastructure started' });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to start infrastructure',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleStop = async () => {
    try {
      await stopInfra();
      addNotification({ type: 'success', title: 'Infrastructure stopped' });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to stop infrastructure',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleRegenerateCerts = async () => {
    try {
      await regenerateCerts();
      addNotification({ type: 'success', title: 'Certificates regenerated' });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to regenerate certificates',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  return (
    <>
      <Header
        title="Infrastructure"
        subtitle="Traefik reverse proxy and shared network"
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} />}
            onClick={loadStatus}
            loading={loading}
            disabled={!isConnected}
          >
            Refresh
          </Button>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="flex items-center gap-4">
              <div className={`p-3 rounded-lg bg-bg-tertiary ${
                infraStatus?.network_exists ? 'text-success' : 'text-text-muted'
              }`}>
                <Globe size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Network</p>
                <p className="font-semibold">{infraStatus?.network_name || 'devflow-proxy'}</p>
                <StatusBadge
                  status={infraStatus?.network_exists ? 'running' : 'stopped'}
                  size="sm"
                />
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className={`p-3 rounded-lg bg-bg-tertiary ${
                infraStatus?.traefik_running ? 'text-success' : 'text-text-muted'
              }`}>
                <Server size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Traefik</p>
                <p className="font-semibold">{infraStatus?.traefik_running ? 'Running' : 'Stopped'}</p>
                <StatusBadge
                  status={infraStatus?.traefik_running ? 'running' : 'stopped'}
                  size="sm"
                />
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className={`p-3 rounded-lg bg-bg-tertiary ${
                infraStatus?.certificates_valid ? 'text-success' : 'text-warning'
              }`}>
                <Shield size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Certificates</p>
                <p className="font-semibold">{infraStatus?.certificates_valid ? 'Valid' : 'Not Found'}</p>
                <StatusBadge
                  status={infraStatus?.certificates_valid ? 'success' : 'warning'}
                  size="sm"
                />
              </div>
            </Card>
          </div>

          {/* Controls */}
          <Card>
            <CardHeader title="Controls" description="Start, stop, and manage infrastructure" />
            <div className="flex flex-wrap gap-3">
              {infraStatus?.traefik_running ? (
                <Button
                  variant="secondary"
                  icon={<Square size={16} />}
                  onClick={handleStop}
                  disabled={!isConnected}
                >
                  Stop Infrastructure
                </Button>
              ) : (
                <Button
                  icon={<Play size={16} />}
                  onClick={handleStart}
                  disabled={!isConnected}
                >
                  Start Infrastructure
                </Button>
              )}
              <Button
                variant="secondary"
                icon={<Shield size={16} />}
                onClick={handleRegenerateCerts}
                disabled={!isConnected}
              >
                Regenerate Certificates
              </Button>
            </div>
          </Card>

          {/* Registered Projects */}
          <Card>
            <CardHeader
              title="Registered Projects"
              description="Projects configured with infrastructure"
            />
            {infraStatus?.registered_projects && infraStatus.registered_projects.length > 0 ? (
              <div className="space-y-2">
                {infraStatus.registered_projects.map((project) => (
                  <div
                    key={project.path}
                    className="p-3 bg-bg-tertiary rounded-lg"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{project.name}</p>
                        <p className="text-sm text-text-muted">{project.path}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-text-secondary">
                          {project.domains.join(', ')}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-secondary text-center py-4">
                No projects registered with infrastructure
              </p>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}
