import { useEffect, useState } from 'react';
import { Rocket, RefreshCw, RotateCcw, FileText, AlertTriangle } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import {
  getDeployStatus,
  deploy,
  rollbackDeploy,
  getDeployLogs,
  type DeployStatus,
  type ServiceStatus,
} from '../api';

export function Deploy() {
  const { activeProject, bridgeState, addNotification } = useAppStore();
  const [environment, setEnvironment] = useState('staging');
  const [deployStatus, setDeployStatus] = useState<DeployStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [logsLoading, setLogsLoading] = useState(false);

  const isConnected = bridgeState === 'Running';

  useEffect(() => {
    if (isConnected && activeProject) {
      loadStatus();
    } else {
      setDeployStatus(null);
    }
  }, [isConnected, activeProject, environment]);

  const loadStatus = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const status = await getDeployStatus(activeProject.path, environment);
      setDeployStatus(status);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load deploy status',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async (service?: string) => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await deploy(activeProject.path, environment, service, false, false);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Deployment started',
          message: `Deployed ${result.deployed} services`,
        });
        loadStatus();
      } else if (result.requires_approval) {
        addNotification({
          type: 'warning',
          title: 'Approval required',
          message: 'Production deployments require approval',
        });
      } else {
        throw new Error('Deployment failed');
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to deploy',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRollback = async (service?: string) => {
    if (!activeProject) return;
    setActionLoading(true);
    try {
      const result = await rollbackDeploy(activeProject.path, environment, service);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Rollback complete',
          message: `Rolled back ${result.rolled_back} services`,
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

  const handleViewLogs = async (service: string) => {
    if (!activeProject) return;
    setSelectedService(service);
    setLogsLoading(true);
    try {
      const result = await getDeployLogs(activeProject.path, environment, service, 100);
      setLogs(result.logs);
    } catch (error) {
      setLogs(`Error loading logs: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLogsLoading(false);
    }
  };

  const getServiceStatus = (status: string): 'running' | 'stopped' | 'warning' => {
    if (status === 'running') return 'running';
    if (status === 'stopped' || status === 'unknown') return 'stopped';
    return 'warning';
  };

  const services = deployStatus?.services || [];

  return (
    <>
      <Header
        title="Deploy"
        subtitle={activeProject ? `Manage deployments for ${activeProject.config.project.name}` : 'Manage production deployments'}
        actions={
          <div className="flex items-center gap-2">
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="px-3 py-1.5 bg-bg-tertiary border border-border rounded-lg text-sm"
            >
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
                No project selected. Select a project from the sidebar to manage its deployments.
              </p>
            </Card>
          )}

          {activeProject && !deployStatus && !loading && (
            <Card className="bg-bg-tertiary">
              <div className="text-center py-8">
                <Rocket size={40} className="mx-auto mb-4 text-text-muted" />
                <p className="text-text-secondary mb-2">
                  No deployment configuration found for this project.
                </p>
                <p className="text-sm text-text-muted">
                  Add a deployment section to your devflow.yml to manage deployments.
                </p>
              </div>
            </Card>
          )}

          {/* Warning for production */}
          {activeProject && environment === 'production' && (
            <Card className="bg-warning/10 border-warning/30">
              <div className="flex items-center gap-3">
                <AlertTriangle className="text-warning" size={20} />
                <p className="text-text-primary">
                  Production deployments require approval. Changes will be reviewed before applying.
                </p>
              </div>
            </Card>
          )}

          {/* Actions */}
          {deployStatus && (
            <>
              <Card>
                <CardHeader
                  title="Deploy Actions"
                  description={deployStatus.host ? `Host: ${deployStatus.host}` : `Deploy to ${environment}`}
                />
                <div className="flex flex-wrap gap-3">
                  <Button
                    icon={<Rocket size={16} />}
                    onClick={() => handleDeploy()}
                    loading={actionLoading}
                    disabled={!isConnected}
                    variant={environment === 'production' ? 'danger' : 'primary'}
                  >
                    Deploy All Services
                  </Button>
                  <Button
                    variant="secondary"
                    icon={<RotateCcw size={16} />}
                    onClick={() => handleRollback()}
                    loading={actionLoading}
                    disabled={!isConnected}
                  >
                    Rollback
                  </Button>
                </div>
              </Card>

              {/* Services */}
              <Card>
                <CardHeader title="Services" description={`Running on ${environment}`} />
                {services.length > 0 ? (
                  <div className="space-y-2">
                    {services.map((service: ServiceStatus) => (
                      <div
                        key={service.name}
                        className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <StatusBadge status={getServiceStatus(service.status)} />
                          <div>
                            <p className="font-medium">{service.name}</p>
                            <p className="text-sm text-text-muted font-mono">{service.image}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-text-secondary">
                            Replicas: {service.replicas}
                          </span>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<Rocket size={16} />}
                              title="Deploy"
                              onClick={() => handleDeploy(service.name)}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<RotateCcw size={16} />}
                              title="Rollback"
                              onClick={() => handleRollback(service.name)}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<FileText size={16} />}
                              title="Logs"
                              onClick={() => handleViewLogs(service.name)}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-text-secondary text-center py-4">
                    No services configured for deployment
                  </p>
                )}
              </Card>

              {/* Logs */}
              {selectedService && (
                <Card>
                  <CardHeader
                    title="Logs"
                    description={`Output from ${selectedService} on ${environment}`}
                    action={
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<RefreshCw size={16} />}
                        onClick={() => handleViewLogs(selectedService)}
                        loading={logsLoading}
                      >
                        Refresh
                      </Button>
                    }
                  />
                  <div className="h-64 bg-bg-primary rounded-lg p-4 font-mono text-sm overflow-auto">
                    {logsLoading ? (
                      <p className="text-text-muted">Loading logs...</p>
                    ) : logs ? (
                      <pre className="whitespace-pre-wrap text-text-secondary">{logs}</pre>
                    ) : (
                      <p className="text-text-muted">No logs available</p>
                    )}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
