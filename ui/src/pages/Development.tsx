import { useEffect, useState } from 'react';
import { Play, Square, RefreshCw, FileText, RotateCcw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import {
  getDevStatus,
  startDev,
  stopDev,
  restartDevService,
  getDevLogs,
  type ContainerStatus,
  type DevStatus,
} from '../api';

export function Development() {
  const { activeProject, bridgeState, addNotification } = useAppStore();
  const [devStatus, setDevStatus] = useState<DevStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [logsLoading, setLogsLoading] = useState(false);

  const isConnected = bridgeState === 'Running';

  useEffect(() => {
    if (isConnected && activeProject) {
      loadStatus();
    } else {
      setDevStatus(null);
    }
  }, [isConnected, activeProject]);

  useEffect(() => {
    if (selectedService && activeProject) {
      loadLogs(selectedService);
    }
  }, [selectedService, activeProject]);

  const loadStatus = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const status = await getDevStatus(activeProject.path);
      setDevStatus(status);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load dev status',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async (service: string) => {
    if (!activeProject) return;
    setLogsLoading(true);
    try {
      const result = await getDevLogs(activeProject.path, service, 100);
      setLogs(result.logs);
    } catch (error) {
      setLogs(`Error loading logs: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleStartAll = async () => {
    if (!activeProject) return;
    try {
      await startDev(activeProject.path);
      addNotification({ type: 'success', title: 'Started all services' });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to start services',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleStopAll = async () => {
    if (!activeProject) return;
    try {
      await stopDev(activeProject.path);
      addNotification({ type: 'success', title: 'Stopped all services' });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to stop services',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleStartService = async (service: string) => {
    if (!activeProject) return;
    try {
      await startDev(activeProject.path, service);
      addNotification({ type: 'success', title: `Started ${service}` });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: `Failed to start ${service}`,
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleStopService = async (service: string) => {
    if (!activeProject) return;
    try {
      await stopDev(activeProject.path, service);
      addNotification({ type: 'success', title: `Stopped ${service}` });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: `Failed to stop ${service}`,
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleRestartService = async (service: string) => {
    if (!activeProject) return;
    try {
      await restartDevService(activeProject.path, service);
      addNotification({ type: 'success', title: `Restarted ${service}` });
      loadStatus();
    } catch (error) {
      addNotification({
        type: 'error',
        title: `Failed to restart ${service}`,
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const getServiceStatus = (status: string): 'running' | 'stopped' | 'warning' => {
    if (status === 'running') return 'running';
    if (status === 'exited' || status === 'stopped') return 'stopped';
    return 'warning';
  };

  const services = devStatus?.services || [];

  return (
    <>
      <Header
        title="Development"
        subtitle={activeProject ? `Local development for ${activeProject.config.project.name}` : 'Manage local development environment'}
        actions={
          <div className="flex items-center gap-2">
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
            <Button
              size="sm"
              icon={<Play size={16} />}
              onClick={handleStartAll}
              disabled={!isConnected || !activeProject}
            >
              Start All
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {!activeProject && (
            <Card className="bg-warning/10 border-warning/30">
              <p className="text-text-primary">
                No project selected. Select a project from the sidebar to manage its development environment.
              </p>
            </Card>
          )}

          {activeProject && !devStatus && !loading && (
            <Card className="bg-bg-tertiary">
              <div className="text-center py-8">
                <p className="text-text-secondary mb-4">
                  No development configuration found for this project.
                </p>
                <p className="text-sm text-text-muted">
                  Make sure your project has a docker-compose.yml file and development settings in devflow.yml
                </p>
              </div>
            </Card>
          )}

          {/* Services */}
          {activeProject && (services.length > 0 || loading) && (
            <Card>
              <CardHeader
                title="Services"
                description={devStatus?.infrastructure_connected ? 'Connected to infrastructure' : 'Docker Compose services'}
                action={
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Square size={16} />}
                    onClick={handleStopAll}
                    disabled={!isConnected}
                  >
                    Stop All
                  </Button>
                }
              />
              {loading && services.length === 0 ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="animate-spin text-text-muted" size={24} />
                  <span className="ml-2 text-text-secondary">Loading services...</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {services.map((service: ContainerStatus) => (
                    <div
                      key={service.name}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedService === service.name
                          ? 'bg-accent/10 border border-accent/30'
                          : 'bg-bg-tertiary hover:bg-bg-tertiary/80'
                      }`}
                      onClick={() => setSelectedService(service.name)}
                    >
                      <div className="flex items-center gap-3">
                        <StatusBadge status={getServiceStatus(service.status)} />
                        <div>
                          <p className="font-medium">{service.name}</p>
                          <p className="text-sm text-text-muted">
                            {service.ports.length > 0 ? service.ports.join(', ') : 'No ports exposed'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {service.health && (
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              service.health === 'healthy'
                                ? 'bg-success/20 text-success'
                                : service.health === 'starting'
                                ? 'bg-warning/20 text-warning'
                                : 'bg-error/20 text-error'
                            }`}
                          >
                            {service.health}
                          </span>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<RotateCcw size={16} />}
                          title="Restart"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRestartService(service.name);
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<FileText size={16} />}
                          title="Logs"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedService(service.name);
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={
                            service.status === 'running' ? (
                              <Square size={16} />
                            ) : (
                              <Play size={16} />
                            )
                          }
                          title={service.status === 'running' ? 'Stop' : 'Start'}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (service.status === 'running') {
                              handleStopService(service.name);
                            } else {
                              handleStartService(service.name);
                            }
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* Logs */}
          {activeProject && (
            <Card>
              <CardHeader
                title="Logs"
                description={selectedService ? `Output from ${selectedService}` : 'Select a service to view logs'}
                action={
                  selectedService && (
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<RefreshCw size={16} />}
                      onClick={() => loadLogs(selectedService)}
                      loading={logsLoading}
                    >
                      Refresh
                    </Button>
                  )
                }
              />
              <div className="h-64 bg-bg-primary rounded-lg p-4 font-mono text-sm overflow-auto">
                {logsLoading ? (
                  <p className="text-text-muted">Loading logs...</p>
                ) : logs ? (
                  <pre className="whitespace-pre-wrap text-text-secondary">{logs}</pre>
                ) : (
                  <p className="text-text-muted">
                    {selectedService
                      ? 'No logs available'
                      : 'Select a service to view its logs...'}
                  </p>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
