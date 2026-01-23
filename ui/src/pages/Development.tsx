import { useState } from 'react';
import { Play, Square, RefreshCw, Terminal, FileText } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';

export function Development() {
  const { activeProject, bridgeState } = useAppStore();
  const [services] = useState([
    { name: 'web', status: 'running', ports: ['3000:3000'], health: 'healthy' },
    { name: 'api', status: 'running', ports: ['8080:8080'], health: 'healthy' },
    { name: 'db', status: 'running', ports: ['5432:5432'], health: null },
  ]);

  const isConnected = bridgeState === 'Running';

  return (
    <>
      <Header
        title="Development"
        subtitle="Docker Compose services for local development"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw size={16} />}
              disabled={!isConnected}
            >
              Refresh
            </Button>
            <Button size="sm" icon={<Play size={16} />} disabled={!isConnected}>
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
                No project selected. Select a project to manage its development environment.
              </p>
            </Card>
          )}

          {/* Services */}
          <Card>
            <CardHeader
              title="Services"
              description="Docker Compose services"
              action={
                <Button variant="secondary" size="sm" icon={<Square size={16} />}>
                  Stop All
                </Button>
              }
            />
            <div className="space-y-2">
              {services.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <StatusBadge
                      status={service.status === 'running' ? 'running' : 'stopped'}
                    />
                    <div>
                      <p className="font-medium">{service.name}</p>
                      <p className="text-sm text-text-muted">
                        {service.ports.join(', ')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {service.health && (
                      <span className={`text-xs px-2 py-1 rounded ${
                        service.health === 'healthy'
                          ? 'bg-success/20 text-success'
                          : 'bg-warning/20 text-warning'
                      }`}>
                        {service.health}
                      </span>
                    )}
                    <Button variant="ghost" size="sm" icon={<Terminal size={16} />} title="Shell" />
                    <Button variant="ghost" size="sm" icon={<FileText size={16} />} title="Logs" />
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={service.status === 'running' ? <Square size={16} /> : <Play size={16} />}
                      title={service.status === 'running' ? 'Stop' : 'Start'}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Logs */}
          <Card>
            <CardHeader title="Logs" description="Service output logs" />
            <div className="h-64 bg-bg-primary rounded-lg p-4 font-mono text-sm overflow-auto">
              <p className="text-text-muted">Select a service to view logs...</p>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
