import { useEffect, useState } from 'react';
import { Stethoscope, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader } from '../components/common';
import { useAppStore } from '../store';
import { runDoctor } from '../api';
import type { DoctorResult, DoctorCheck } from '../types';

export function Doctor() {
  const { bridgeState, addNotification } = useAppStore();
  const [result, setResult] = useState<DoctorResult | null>(null);
  const [loading, setLoading] = useState(false);

  const isConnected = bridgeState === 'Running';

  const runChecks = async () => {
    setLoading(true);
    try {
      const doctorResult = await runDoctor();
      setResult(doctorResult);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to run health checks',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isConnected) {
      runChecks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected]);

  const getStatusIcon = (status: DoctorCheck['status']) => {
    switch (status) {
      case 'ok':
        return <CheckCircle className="text-success" size={20} />;
      case 'warning':
        return <AlertCircle className="text-warning" size={20} />;
      case 'error':
        return <XCircle className="text-error" size={20} />;
      default:
        return <AlertCircle className="text-text-muted" size={20} />;
    }
  };

  const getStatusBg = (status: DoctorCheck['status']) => {
    switch (status) {
      case 'ok':
        return 'bg-success/10 border-success/30';
      case 'warning':
        return 'bg-warning/10 border-warning/30';
      case 'error':
        return 'bg-error/10 border-error/30';
      default:
        return 'bg-bg-tertiary border-border';
    }
  };

  const categorizeChecks = (checks: DoctorCheck[]) => {
    const categories: Record<string, DoctorCheck[]> = {
      'Required Tools': [],
      'Authentication': [],
      'Configuration': [],
      'Infrastructure': [],
      'Other': [],
    };

    checks.forEach((check) => {
      if (check.name.includes('docker') || check.name.includes('git') || check.name.includes('kubectl')) {
        categories['Required Tools'].push(check);
      } else if (check.name.includes('auth') || check.name.includes('login') || check.name.includes('token')) {
        categories['Authentication'].push(check);
      } else if (check.name.includes('config') || check.name.includes('settings')) {
        categories['Configuration'].push(check);
      } else if (check.name.includes('traefik') || check.name.includes('network') || check.name.includes('infra')) {
        categories['Infrastructure'].push(check);
      } else {
        categories['Other'].push(check);
      }
    });

    return Object.entries(categories).filter(([, checks]) => checks.length > 0);
  };

  const summary = result ? {
    total: result.checks.length,
    ok: result.checks.filter((c) => c.status === 'ok').length,
    warnings: result.checks.filter((c) => c.status === 'warning').length,
    errors: result.checks.filter((c) => c.status === 'error').length,
  } : null;

  return (
    <>
      <Header
        title="Doctor"
        subtitle="System health checks and diagnostics"
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} />}
            onClick={runChecks}
            loading={loading}
            disabled={!isConnected}
          >
            Run Checks
          </Button>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Summary */}
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-bg-tertiary text-text-secondary">
                  <Stethoscope size={24} />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Total</p>
                  <p className="text-2xl font-semibold">{summary.total}</p>
                </div>
              </Card>
              <Card className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-success/20 text-success">
                  <CheckCircle size={24} />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Passed</p>
                  <p className="text-2xl font-semibold">{summary.ok}</p>
                </div>
              </Card>
              <Card className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-warning/20 text-warning">
                  <AlertCircle size={24} />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Warnings</p>
                  <p className="text-2xl font-semibold">{summary.warnings}</p>
                </div>
              </Card>
              <Card className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-error/20 text-error">
                  <XCircle size={24} />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Errors</p>
                  <p className="text-2xl font-semibold">{summary.errors}</p>
                </div>
              </Card>
            </div>
          )}

          {/* Loading State */}
          {loading && !result && (
            <Card>
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="animate-spin text-text-muted" size={32} />
                <span className="ml-3 text-text-secondary">Running health checks...</span>
              </div>
            </Card>
          )}

          {/* Check Results by Category */}
          {result && categorizeChecks(result.checks).map(([category, checks]) => (
            <Card key={category}>
              <CardHeader title={category} />
              <div className="space-y-2">
                {checks.map((check) => (
                  <div
                    key={check.name}
                    className={`p-4 rounded-lg border ${getStatusBg(check.status)}`}
                  >
                    <div className="flex items-start gap-3">
                      {getStatusIcon(check.status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{check.name}</p>
                          <span className={`text-xs px-2 py-1 rounded ${
                            check.status === 'ok'
                              ? 'bg-success/20 text-success'
                              : check.status === 'warning'
                              ? 'bg-warning/20 text-warning'
                              : 'bg-error/20 text-error'
                          }`}>
                            {check.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-text-secondary mt-1">{check.message}</p>
                        {check.fix_hint && (
                          <p className="text-sm text-text-muted mt-2 italic">
                            Suggestion: {check.fix_hint}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}

          {/* No Results */}
          {!loading && !result && (
            <Card>
              <div className="text-center py-12">
                <Stethoscope className="mx-auto text-text-muted mb-4" size={48} />
                <p className="text-text-secondary mb-4">
                  Run health checks to diagnose your development environment
                </p>
                <Button
                  icon={<Stethoscope size={16} />}
                  onClick={runChecks}
                  disabled={!isConnected}
                >
                  Run Doctor
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
