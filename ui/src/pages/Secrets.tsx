import { useState } from 'react';
import { Key, RefreshCw, ArrowRightLeft, Check, AlertCircle } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader, StatusBadge } from '../components/common';
import { useAppStore } from '../store';

export function Secrets() {
  const { bridgeState } = useAppStore();
  const [secrets] = useState([
    { name: 'DATABASE_URL', source: '1password', synced: ['github', 'docker'] },
    { name: 'API_KEY', source: '1password', synced: ['github'] },
    { name: 'JWT_SECRET', source: 'env', synced: [] },
  ]);

  const isConnected = bridgeState === 'Running';

  return (
    <>
      <Header
        title="Secrets"
        subtitle="Manage secrets across providers"
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} />}
            disabled={!isConnected}
          >
            Refresh
          </Button>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Sync Actions */}
          <Card>
            <CardHeader title="Sync Actions" description="Sync secrets between providers" />
            <div className="flex flex-wrap gap-3">
              <Button icon={<ArrowRightLeft size={16} />} disabled={!isConnected}>
                1Password to GitHub
              </Button>
              <Button variant="secondary" icon={<ArrowRightLeft size={16} />} disabled={!isConnected}>
                1Password to Docker
              </Button>
              <Button variant="secondary" icon={<Check size={16} />} disabled={!isConnected}>
                Verify All
              </Button>
            </div>
          </Card>

          {/* Secrets List */}
          <Card>
            <CardHeader title="Configured Secrets" />
            <div className="space-y-2">
              {secrets.map((secret) => (
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
                    {secret.synced.length > 0 ? (
                      secret.synced.map((target) => (
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
          </Card>

          {/* Providers */}
          <Card>
            <CardHeader title="Providers" description="Available secret providers" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {['1Password', 'GitHub', 'Docker', 'Environment'].map((provider) => (
                <div key={provider} className="p-3 bg-bg-tertiary rounded-lg text-center">
                  <p className="font-medium">{provider}</p>
                  <StatusBadge status="success" label="Connected" size="sm" />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
