import { useState } from 'react';
import { Rocket, RefreshCw, RotateCcw, FileText, AlertTriangle } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';

export function Deploy() {
  const { bridgeState } = useAppStore();
  const [environment, setEnvironment] = useState('staging');
  const [services] = useState([
    { name: 'web', image: 'myapp/web:v1.2.3', replicas: '3/3', status: 'running' },
    { name: 'api', image: 'myapp/api:v1.2.3', replicas: '2/2', status: 'running' },
    { name: 'worker', image: 'myapp/worker:v1.2.3', replicas: '1/1', status: 'running' },
  ]);

  const isConnected = bridgeState === 'Running';

  return (
    <>
      <Header
        title="Deploy"
        subtitle="Manage production deployments"
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
              disabled={!isConnected}
            >
              Refresh
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Warning for production */}
          {environment === 'production' && (
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
          <Card>
            <CardHeader
              title="Deploy Actions"
              description={`Deploy to ${environment}`}
            />
            <div className="flex flex-wrap gap-3">
              <Button
                icon={<Rocket size={16} />}
                disabled={!isConnected}
                variant={environment === 'production' ? 'danger' : 'primary'}
              >
                Deploy All Services
              </Button>
              <Button variant="secondary" icon={<RotateCcw size={16} />} disabled={!isConnected}>
                Rollback
              </Button>
              <Button variant="secondary" icon={<FileText size={16} />} disabled={!isConnected}>
                View Logs
              </Button>
            </div>
          </Card>

          {/* Services */}
          <Card>
            <CardHeader title="Services" description={`Running on ${environment}`} />
            <div className="space-y-2">
              {services.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between p-3 bg-bg-tertiary rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <StatusBadge status={service.status === 'running' ? 'running' : 'stopped'} />
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
                      <Button variant="ghost" size="sm" icon={<Rocket size={16} />} title="Deploy" />
                      <Button variant="ghost" size="sm" icon={<RotateCcw size={16} />} title="Rollback" />
                      <Button variant="ghost" size="sm" icon={<FileText size={16} />} title="Logs" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
