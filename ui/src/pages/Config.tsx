import { useEffect, useState } from 'react';
import { Header } from '../components/layout';
import { Button, Card } from '../components/common';
import { Save, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import Editor from '@monaco-editor/react';
import * as yaml from 'js-yaml';
import { useAppStore } from '../store';
import {
  getGlobalConfig,
  getProjectConfig,
  updateGlobalConfig,
  updateProjectConfig,
  validateConfig,
  type DevflowConfig,
} from '../api';

export function Config() {
  const { activeProject, bridgeState, addNotification } = useAppStore();
  const [activeTab, setActiveTab] = useState<'global' | 'project'>('global');
  const [configContent, setConfigContent] = useState<string>('');
  const [originalContent, setOriginalContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);

  const isConnected = bridgeState === 'Running';
  const hasChanges = configContent !== originalContent;

  useEffect(() => {
    if (isConnected) {
      loadConfig();
    } else {
      setConfigContent('');
      setOriginalContent('');
    }
  }, [isConnected, activeTab, activeProject]);

  const loadConfig = async () => {
    setLoading(true);
    setValidationErrors([]);
    setValidationWarnings([]);
    try {
      let config;
      if (activeTab === 'global') {
        config = await getGlobalConfig();
      } else {
        if (!activeProject) {
          setConfigContent('# No project selected\n# Select a project from the sidebar to edit its configuration.');
          setOriginalContent('');
          setLoading(false);
          return;
        }
        config = await getProjectConfig(activeProject.path);
      }
      const yamlContent = yaml.dump(config, {
        indent: 2,
        lineWidth: 120,
        noRefs: true,
        sortKeys: false,
      });
      setConfigContent(yamlContent);
      setOriginalContent(yamlContent);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addNotification({
        type: 'error',
        title: `Failed to load ${activeTab} config`,
        message,
      });
      setConfigContent(`# Error loading configuration\n# ${message}`);
      setOriginalContent('');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Parse YAML to validate it
      const parsed = yaml.load(configContent);
      if (typeof parsed !== 'object' || parsed === null) {
        throw new Error('Invalid configuration: must be an object');
      }

      if (activeTab === 'global') {
        // For global config, we need to update it section by section
        // The API expects key/value pairs
        const config = parsed as Record<string, unknown>;
        for (const [key, value] of Object.entries(config)) {
          if (key !== 'version') {
            await updateGlobalConfig(key, value);
          }
        }
      } else {
        if (!activeProject) {
          throw new Error('No project selected');
        }
        await updateProjectConfig(activeProject.path, parsed as DevflowConfig);
      }

      addNotification({
        type: 'success',
        title: 'Configuration saved',
        message: `${activeTab === 'global' ? 'Global' : 'Project'} configuration has been updated.`,
      });

      // Reload to get the canonical format
      await loadConfig();

      // Validate after save
      await handleValidate();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addNotification({
        type: 'error',
        title: 'Failed to save configuration',
        message,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async () => {
    try {
      const result = await validateConfig(activeTab === 'project' ? activeProject?.path : undefined);
      setValidationErrors(result.errors);
      setValidationWarnings(result.warnings);
      if (result.valid) {
        addNotification({
          type: 'success',
          title: 'Configuration valid',
          message: result.warnings.length > 0
            ? `Valid with ${result.warnings.length} warning(s)`
            : 'No issues found',
        });
      } else {
        addNotification({
          type: 'error',
          title: 'Configuration invalid',
          message: `Found ${result.errors.length} error(s)`,
        });
      }
    } catch (error) {
      console.error('Validation error:', error);
    }
  };

  const handleTabChange = (tab: 'global' | 'project') => {
    if (hasChanges) {
      if (!confirm('You have unsaved changes. Discard them?')) {
        return;
      }
    }
    setActiveTab(tab);
  };

  return (
    <>
      <Header
        title="Configuration"
        subtitle={activeTab === 'global'
          ? 'Edit global DevFlow settings'
          : activeProject
            ? `Edit configuration for ${activeProject.config.project.name}`
            : 'Edit project configuration'
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw size={16} />}
              onClick={loadConfig}
              loading={loading}
              disabled={!isConnected}
            >
              Reload
            </Button>
            <Button
              size="sm"
              icon={<Save size={16} />}
              onClick={handleSave}
              loading={saving}
              disabled={!isConnected || !hasChanges || (activeTab === 'project' && !activeProject)}
            >
              Save Changes
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => handleTabChange('global')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'global'
                  ? 'bg-accent text-white'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
              }`}
            >
              Global Config
            </button>
            <button
              onClick={() => handleTabChange('project')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'project'
                  ? 'bg-accent text-white'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
              }`}
            >
              Project Config
            </button>
          </div>

          {/* Status indicators */}
          {hasChanges && (
            <div className="flex items-center gap-2 text-warning text-sm">
              <AlertCircle size={16} />
              <span>You have unsaved changes</span>
            </div>
          )}

          {/* Validation Results */}
          {(validationErrors.length > 0 || validationWarnings.length > 0) && (
            <Card className="space-y-2">
              {validationErrors.map((error, i) => (
                <div key={`error-${i}`} className="flex items-center gap-2 text-error text-sm">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              ))}
              {validationWarnings.map((warning, i) => (
                <div key={`warning-${i}`} className="flex items-center gap-2 text-warning text-sm">
                  <AlertCircle size={16} />
                  <span>{warning}</span>
                </div>
              ))}
              {validationErrors.length === 0 && validationWarnings.length === 0 && (
                <div className="flex items-center gap-2 text-success text-sm">
                  <CheckCircle size={16} />
                  <span>Configuration is valid</span>
                </div>
              )}
            </Card>
          )}

          {/* No project warning */}
          {activeTab === 'project' && !activeProject && (
            <Card className="bg-warning/10 border-warning/30">
              <p className="text-text-primary">
                No project selected. Select a project from the sidebar to edit its configuration.
              </p>
            </Card>
          )}

          {/* Editor */}
          <Card padding="none" className="overflow-hidden">
            <div className="h-[600px]">
              {loading ? (
                <div className="flex items-center justify-center h-full text-text-muted">
                  Loading configuration...
                </div>
              ) : (
                <Editor
                  height="100%"
                  defaultLanguage="yaml"
                  value={configContent}
                  onChange={(value) => setConfigContent(value || '')}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    padding: { top: 16, bottom: 16 },
                    readOnly: !isConnected || (activeTab === 'project' && !activeProject),
                  }}
                />
              )}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
