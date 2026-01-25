import { useEffect, useState, useCallback } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Stethoscope,
  Key,
  Package,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, CardHeader } from '../components/common';
import { useAppStore } from '../store';
import { runDoctor } from '../api';
import * as setupApi from '../api/setup';
import type {
  DoctorResult,
  DoctorCheck,
  ToolStatus,
  ToolCategory,
  PrerequisitesSummary,
  PlatformInfo,
  InstallResult,
} from '../types';

type TabId = 'prerequisites' | 'authentication' | 'diagnostics';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const TABS: Tab[] = [
  { id: 'prerequisites', label: 'Prerequisites', icon: <Package size={18} /> },
  { id: 'authentication', label: 'Authentication', icon: <Key size={18} /> },
  { id: 'diagnostics', label: 'Diagnostics', icon: <Stethoscope size={18} /> },
];

const CATEGORY_DISPLAY_NAMES: Record<ToolCategory, string> = {
  code_editor: 'Code Editors',
  runtime: 'Language Runtimes',
  container: 'Containers',
  database: 'Database Tools',
  secrets: 'Secrets Management',
  version_control: 'Version Control',
  cli_utility: 'CLI Utilities',
  shell: 'Shell & Terminal',
  infrastructure: 'Infrastructure',
};

const CATEGORY_DESCRIPTIONS: Record<ToolCategory, string> = {
  code_editor: 'AI-powered editors for modern development',
  runtime: 'Programming languages managed by Mise',
  container: 'Container runtimes for local development',
  database: 'Database clients and migration tools',
  secrets: 'Credential and secrets management',
  version_control: 'Git and collaboration tools',
  cli_utility: 'Essential command-line utilities',
  shell: 'Shell enhancements and customization',
  infrastructure: 'Local development infrastructure',
};

export function Setup() {
  const { bridgeState, addNotification } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabId>('prerequisites');
  const [doctorResult, setDoctorResult] = useState<DoctorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [toolStatuses, setToolStatuses] = useState<ToolStatus[]>([]);
  const [summary, setSummary] = useState<PrerequisitesSummary | null>(null);
  const [platformInfo, setPlatformInfo] = useState<PlatformInfo | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<ToolCategory>>(new Set());
  const [installingTools, setInstallingTools] = useState<Set<string>>(new Set());

  const isConnected = bridgeState === 'Running';

  const loadPrerequisites = useCallback(async () => {
    setLoading(true);
    try {
      const [statuses, prereqSummary, platform] = await Promise.all([
        setupApi.detectAllTools(),
        setupApi.getPrerequisitesSummary(),
        setupApi.getPlatformInfo(),
      ]);
      setToolStatuses(statuses);
      setSummary(prereqSummary);
      setPlatformInfo(platform);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load prerequisites',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  const runDoctorChecks = useCallback(async () => {
    setLoading(true);
    try {
      const result = await runDoctor();
      setDoctorResult(result);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to run health checks',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    if (isConnected) {
      if (activeTab === 'prerequisites') {
        loadPrerequisites();
      } else if (activeTab === 'diagnostics') {
        runDoctorChecks();
      }
    }
  }, [isConnected, activeTab, loadPrerequisites, runDoctorChecks]);

  const handleInstallTool = async (toolId: string) => {
    setInstallingTools((prev) => new Set(prev).add(toolId));
    try {
      const result: InstallResult = await setupApi.installTool(toolId);
      if (result.success) {
        addNotification({
          type: 'success',
          title: 'Installation complete',
          message: result.message,
        });
        // Refresh the tool status
        const updatedStatus = await setupApi.detectTool(toolId);
        setToolStatuses((prev) =>
          prev.map((t) => (t.tool_id === toolId ? updatedStatus : t))
        );
      } else {
        addNotification({
          type: 'error',
          title: 'Installation failed',
          message: result.error_details || result.message,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Installation failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setInstallingTools((prev) => {
        const next = new Set(prev);
        next.delete(toolId);
        return next;
      });
    }
  };

  const toggleCategory = (category: ToolCategory) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const getToolsByCategory = (category: ToolCategory): ToolStatus[] => {
    return toolStatuses.filter((t) => t.category === category);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'installed':
        return <CheckCircle className="text-success" size={18} />;
      case 'not_installed':
        return <Download className="text-text-muted" size={18} />;
      case 'outdated':
        return <AlertCircle className="text-warning" size={18} />;
      case 'installing':
        return <RefreshCw className="text-primary animate-spin" size={18} />;
      case 'failed':
        return <XCircle className="text-error" size={18} />;
      default:
        return <AlertCircle className="text-text-muted" size={18} />;
    }
  };

  const getDoctorStatusIcon = (status: DoctorCheck['status']) => {
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

  const getDoctorStatusBg = (status: DoctorCheck['status']) => {
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

  const categorizeDoctorChecks = (checks: DoctorCheck[]) => {
    const categories: Record<string, DoctorCheck[]> = {
      Tools: [],
      Authentication: [],
      Configuration: [],
      Infrastructure: [],
    };

    checks.forEach((check) => {
      if (check.category === 'tool') {
        categories['Tools'].push(check);
      } else if (check.category === 'auth') {
        categories['Authentication'].push(check);
      } else if (check.category === 'config') {
        categories['Configuration'].push(check);
      } else if (check.category === 'infrastructure') {
        categories['Infrastructure'].push(check);
      }
    });

    return Object.entries(categories).filter(([, checks]) => checks.length > 0);
  };

  const renderPrerequisites = () => {
    const categories = Object.keys(CATEGORY_DISPLAY_NAMES) as ToolCategory[];
    const categoriesWithTools = categories.filter(
      (cat) => getToolsByCategory(cat).length > 0
    );

    return (
      <div className="space-y-6">
        {/* Platform Info */}
        {platformInfo && (
          <Card>
            <CardHeader title="Platform Information" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-text-secondary">Operating System</p>
                <p className="font-medium capitalize">
                  {platformInfo.os}
                  {platformInfo.distro && ` (${platformInfo.distro})`}
                </p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Architecture</p>
                <p className="font-medium">{platformInfo.architecture}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">WSL</p>
                <p className="font-medium">{platformInfo.is_wsl ? 'Yes' : 'No'}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Package Managers</p>
                <p className="font-medium">
                  {platformInfo.package_managers.slice(0, 3).join(', ')}
                  {platformInfo.package_managers.length > 3 && '...'}
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Summary */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-text-secondary">
                <Package size={24} />
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
                <p className="text-sm text-text-secondary">Installed</p>
                <p className="text-2xl font-semibold">{summary.installed}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-text-muted">
                <Download size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Not Installed</p>
                <p className="text-2xl font-semibold">{summary.not_installed}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-warning/20 text-warning">
                <AlertCircle size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Outdated</p>
                <p className="text-2xl font-semibold">{summary.outdated}</p>
              </div>
            </Card>
          </div>
        )}

        {/* Tool Categories */}
        {categoriesWithTools.map((category) => {
          const tools = getToolsByCategory(category);
          const isExpanded = expandedCategories.has(category);
          const installedCount = tools.filter(
            (t) => t.status === 'installed' || t.status === 'outdated'
          ).length;

          return (
            <Card key={category}>
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between p-1 hover:bg-bg-tertiary/50 rounded-lg transition-colors"
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown size={20} className="text-text-muted" />
                  ) : (
                    <ChevronRight size={20} className="text-text-muted" />
                  )}
                  <div className="text-left">
                    <h3 className="font-medium">{CATEGORY_DISPLAY_NAMES[category]}</h3>
                    <p className="text-sm text-text-secondary">
                      {CATEGORY_DESCRIPTIONS[category]}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-secondary">
                    {installedCount} / {tools.length} installed
                  </span>
                  {installedCount === tools.length ? (
                    <CheckCircle className="text-success" size={18} />
                  ) : installedCount > 0 ? (
                    <AlertCircle className="text-warning" size={18} />
                  ) : (
                    <Download className="text-text-muted" size={18} />
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="mt-4 space-y-2">
                  {tools.map((tool) => {
                    const isInstalling = installingTools.has(tool.tool_id);
                    const effectiveStatus = isInstalling ? 'installing' : tool.status;

                    return (
                      <div
                        key={tool.tool_id}
                        className="flex items-center justify-between p-3 bg-bg-tertiary/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          {getStatusIcon(effectiveStatus)}
                          <div>
                            <p className="font-medium">{tool.name}</p>
                            <p className="text-sm text-text-secondary">
                              {tool.version || 'Not installed'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {tool.status === 'not_installed' && (
                            <Button
                              size="sm"
                              variant="secondary"
                              icon={<Download size={14} />}
                              onClick={() => handleInstallTool(tool.tool_id)}
                              loading={isInstalling}
                              disabled={isInstalling}
                            >
                              Install
                            </Button>
                          )}
                          {tool.status === 'outdated' && (
                            <Button
                              size="sm"
                              variant="secondary"
                              icon={<RefreshCw size={14} />}
                              onClick={() => handleInstallTool(tool.tool_id)}
                              loading={isInstalling}
                              disabled={isInstalling}
                            >
                              Update
                            </Button>
                          )}
                          {tool.install_methods.length > 0 && (
                            <span className="text-xs text-text-muted">
                              via {tool.install_methods[0]}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          );
        })}

        {/* Loading State */}
        {loading && toolStatuses.length === 0 && (
          <Card>
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="animate-spin text-text-muted" size={32} />
              <span className="ml-3 text-text-secondary">Detecting tools...</span>
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderAuthentication = () => {
    // Filter auth-related checks from doctor results
    const authChecks = doctorResult?.checks.filter((c) => c.category === 'auth') || [];

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader title="Authentication Status" />
          {authChecks.length > 0 ? (
            <div className="space-y-2">
              {authChecks.map((check) => (
                <div
                  key={check.name}
                  className={`p-4 rounded-lg border ${getDoctorStatusBg(check.status)}`}
                >
                  <div className="flex items-start gap-3">
                    {getDoctorStatusIcon(check.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{check.name}</p>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            check.status === 'ok'
                              ? 'bg-success/20 text-success'
                              : check.status === 'warning'
                              ? 'bg-warning/20 text-warning'
                              : 'bg-error/20 text-error'
                          }`}
                        >
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
          ) : (
            <div className="text-center py-8">
              <Key className="mx-auto text-text-muted mb-4" size={48} />
              <p className="text-text-secondary">
                Run diagnostics to check authentication status
              </p>
              <Button
                className="mt-4"
                variant="secondary"
                icon={<RefreshCw size={16} />}
                onClick={runDoctorChecks}
                loading={loading}
              >
                Run Checks
              </Button>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Quick Links" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <a
              href="https://cli.github.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-bg-tertiary/50 rounded-lg hover:bg-bg-tertiary transition-colors"
            >
              <ExternalLink size={18} className="text-text-muted" />
              <div>
                <p className="font-medium">GitHub CLI</p>
                <p className="text-sm text-text-secondary">Authenticate with GitHub</p>
              </div>
            </a>
            <a
              href="https://1password.com/downloads/command-line/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-bg-tertiary/50 rounded-lg hover:bg-bg-tertiary transition-colors"
            >
              <ExternalLink size={18} className="text-text-muted" />
              <div>
                <p className="font-medium">1Password CLI</p>
                <p className="text-sm text-text-secondary">Manage secrets securely</p>
              </div>
            </a>
          </div>
        </Card>
      </div>
    );
  };

  const renderDiagnostics = () => {
    const doctorSummary = doctorResult
      ? {
          total: doctorResult.checks.length,
          ok: doctorResult.checks.filter((c) => c.status === 'ok').length,
          warnings: doctorResult.checks.filter((c) => c.status === 'warning').length,
          errors: doctorResult.checks.filter((c) => c.status === 'error').length,
        }
      : null;

    return (
      <div className="space-y-6">
        {/* Summary */}
        {doctorSummary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-bg-tertiary text-text-secondary">
                <Stethoscope size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Total</p>
                <p className="text-2xl font-semibold">{doctorSummary.total}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-success/20 text-success">
                <CheckCircle size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Passed</p>
                <p className="text-2xl font-semibold">{doctorSummary.ok}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-warning/20 text-warning">
                <AlertCircle size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Warnings</p>
                <p className="text-2xl font-semibold">{doctorSummary.warnings}</p>
              </div>
            </Card>
            <Card className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-error/20 text-error">
                <XCircle size={24} />
              </div>
              <div>
                <p className="text-sm text-text-secondary">Errors</p>
                <p className="text-2xl font-semibold">{doctorSummary.errors}</p>
              </div>
            </Card>
          </div>
        )}

        {/* Loading State */}
        {loading && !doctorResult && (
          <Card>
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="animate-spin text-text-muted" size={32} />
              <span className="ml-3 text-text-secondary">Running health checks...</span>
            </div>
          </Card>
        )}

        {/* Check Results by Category */}
        {doctorResult &&
          categorizeDoctorChecks(doctorResult.checks).map(([category, checks]) => (
            <Card key={category}>
              <CardHeader title={category} />
              <div className="space-y-2">
                {checks.map((check) => (
                  <div
                    key={check.name}
                    className={`p-4 rounded-lg border ${getDoctorStatusBg(check.status)}`}
                  >
                    <div className="flex items-start gap-3">
                      {getDoctorStatusIcon(check.status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{check.name}</p>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              check.status === 'ok'
                                ? 'bg-success/20 text-success'
                                : check.status === 'warning'
                                ? 'bg-warning/20 text-warning'
                                : 'bg-error/20 text-error'
                            }`}
                          >
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
        {!loading && !doctorResult && (
          <Card>
            <div className="text-center py-12">
              <Stethoscope className="mx-auto text-text-muted mb-4" size={48} />
              <p className="text-text-secondary mb-4">
                Run health checks to diagnose your development environment
              </p>
              <Button
                icon={<Stethoscope size={16} />}
                onClick={runDoctorChecks}
                disabled={!isConnected}
              >
                Run Doctor
              </Button>
            </div>
          </Card>
        )}
      </div>
    );
  };

  const getRefreshAction = () => {
    if (activeTab === 'prerequisites') {
      return (
        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw size={16} />}
          onClick={loadPrerequisites}
          loading={loading}
          disabled={!isConnected}
        >
          Refresh
        </Button>
      );
    }
    return (
      <Button
        variant="secondary"
        size="sm"
        icon={<RefreshCw size={16} />}
        onClick={runDoctorChecks}
        loading={loading}
        disabled={!isConnected}
      >
        Run Checks
      </Button>
    );
  };

  return (
    <>
      <Header
        title="Setup & Health"
        subtitle="Prerequisites, authentication, and system diagnostics"
        actions={getRefreshAction()}
      />
      <div className="flex-1 overflow-auto">
        {/* Tabs */}
        <div className="border-b border-border px-6">
          <nav className="flex gap-4" aria-label="Tabs">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary hover:border-border'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          <div className="max-w-4xl mx-auto">
            {activeTab === 'prerequisites' && renderPrerequisites()}
            {activeTab === 'authentication' && renderAuthentication()}
            {activeTab === 'diagnostics' && renderDiagnostics()}
          </div>
        </div>
      </div>
    </>
  );
}
