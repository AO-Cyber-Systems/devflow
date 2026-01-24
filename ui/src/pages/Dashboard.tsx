import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Server,
  FolderKanban,
  Database,
  Rocket,
  ArrowRight,
  Play,
  Square,
  RefreshCw,
} from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import { getInfraStatus, listProjects, startInfra, stopInfra } from '../api';

export function Dashboard() {
  const {
    infraStatus,
    setInfraStatus,
    projects,
    setProjects,
    bridgeState,
    addNotification,
  } = useAppStore();

  const isConnected = bridgeState === 'Running';

  const loadData = async () => {
    try {
      const [status, projectList] = await Promise.all([
        getInfraStatus(),
        listProjects(),
      ]);
      setInfraStatus(status);
      setProjects(projectList);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  useEffect(() => {
    if (isConnected) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected]);

  const handleStartInfra = async () => {
    try {
      await startInfra();
      addNotification({
        type: 'success',
        title: 'Infrastructure Started',
        message: 'Traefik and network are now running',
      });
      loadData();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to Start Infrastructure',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleStopInfra = async () => {
    try {
      await stopInfra();
      addNotification({
        type: 'success',
        title: 'Infrastructure Stopped',
      });
      loadData();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to Stop Infrastructure',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  return (
    <>
      <Header title="Dashboard" subtitle="Overview of your development environment" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Connection status */}
          {!isConnected && (
            <Card className="bg-warning/10 border-warning/30">
              <div className="flex items-center gap-3">
                <RefreshCw className="animate-spin text-warning" size={20} />
                <div>
                  <p className="font-medium text-text-primary">
                    Connecting to DevFlow...
                  </p>
                  <p className="text-sm text-text-secondary">
                    Waiting for bridge server to start
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={<Server size={24} />}
              label="Infrastructure"
              value={infraStatus?.traefik_running ? 'Running' : 'Stopped'}
              status={infraStatus?.traefik_running ? 'running' : 'stopped'}
            />
            <StatCard
              icon={<FolderKanban size={24} />}
              label="Projects"
              value={projects.length.toString()}
              status="success"
            />
            <StatCard
              icon={<Database size={24} />}
              label="Registered"
              value={infraStatus?.registered_projects.length.toString() || '0'}
              status="success"
            />
            <StatCard
              icon={<Rocket size={24} />}
              label="Certificates"
              value={infraStatus?.certificates_valid ? 'Valid' : 'Not Found'}
              status={infraStatus?.certificates_valid ? 'success' : 'warning'}
            />
          </div>

          {/* Infrastructure Panel */}
          <Card>
            <CardHeader
              title="Infrastructure"
              description="Traefik reverse proxy and shared network"
              action={
                <div className="flex items-center gap-2">
                  {infraStatus?.traefik_running ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Square size={16} />}
                      onClick={handleStopInfra}
                      disabled={!isConnected}
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<Play size={16} />}
                      onClick={handleStartInfra}
                      disabled={!isConnected}
                    >
                      Start
                    </Button>
                  )}
                </div>
              }
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 bg-bg-tertiary rounded-lg">
                <p className="text-sm text-text-secondary">Network</p>
                <p className="font-medium">
                  {infraStatus?.network_name || 'devflow-proxy'}
                </p>
                <StatusBadge
                  status={infraStatus?.network_exists ? 'running' : 'stopped'}
                  size="sm"
                />
              </div>
              <div className="p-3 bg-bg-tertiary rounded-lg">
                <p className="text-sm text-text-secondary">Traefik</p>
                <p className="font-medium">
                  {infraStatus?.traefik_url || 'Not running'}
                </p>
                <StatusBadge
                  status={infraStatus?.traefik_running ? 'running' : 'stopped'}
                  size="sm"
                />
              </div>
              <div className="p-3 bg-bg-tertiary rounded-lg">
                <p className="text-sm text-text-secondary">Certificates</p>
                <p className="font-medium">
                  {infraStatus?.certificates_path || 'Not configured'}
                </p>
                <StatusBadge
                  status={infraStatus?.certificates_valid ? 'success' : 'warning'}
                  size="sm"
                />
              </div>
            </div>
          </Card>

          {/* Recent Projects */}
          <Card>
            <CardHeader
              title="Recent Projects"
              description="Your registered DevFlow projects"
              action={
                <Link to="/projects">
                  <Button variant="ghost" size="sm">
                    View All <ArrowRight size={16} />
                  </Button>
                </Link>
              }
            />
            {projects.length > 0 ? (
              <div className="space-y-2">
                {projects.slice(0, 5).map((project) => (
                  <div
                    key={project.path}
                    className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{project.name}</p>
                      <p className="text-sm text-text-muted truncate max-w-md">
                        {project.path}
                      </p>
                    </div>
                    <StatusBadge
                      status={project.has_devflow_config ? 'success' : 'warning'}
                      label={project.has_devflow_config ? 'Configured' : 'No Config'}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-text-secondary">
                <FolderKanban size={40} className="mx-auto mb-2 opacity-50" />
                <p>No projects registered</p>
                <Link to="/projects">
                  <Button variant="ghost" size="sm" className="mt-2">
                    Add Project
                  </Button>
                </Link>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  status: 'running' | 'stopped' | 'success' | 'warning' | 'error';
}

function StatCard({ icon, label, value, status }: StatCardProps) {
  const statusColors = {
    running: 'text-success',
    success: 'text-success',
    stopped: 'text-text-muted',
    warning: 'text-warning',
    error: 'text-error',
  };

  return (
    <Card className="flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-bg-tertiary ${statusColors[status]}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-text-secondary">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </div>
    </Card>
  );
}
