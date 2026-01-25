/**
 * Setup Wizard - Full-screen blocking wizard for initial backend configuration
 *
 * This wizard runs before the main app and ensures a valid backend is configured.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Check, ChevronRight, Loader2, Server, Monitor, Container, Globe, AlertCircle, RefreshCw, Play, ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import { Button, Card } from '../components/common';
import {
  detectPrerequisites,
  getBackendConfig,
  saveBackendConfig,
  installBackendWithLogs,
  testBackendConnection,
  startBridgeWithConfig,
  getRecommendedBackend,
  createDefaultConfig,
  getBackendTypeName,
  getBackendTypeDescription,
  getWslDistrosDetailed,
  validateWslInstallation,
  startWslDistro,
  getWslIssueMessage,
  type InstallLogEntry,
} from '../api/backendSetup';
import type { BackendType, BackendConfig, PrerequisiteStatus, WizardStep, WslDistroStatus, WslInstallValidation } from '../types';

interface SetupWizardProps {
  onComplete: (config: BackendConfig) => void;
}

// Extended wizard step type to include validation
type ExtendedWizardStep = WizardStep | 'validating';

export function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState<ExtendedWizardStep>('welcome');
  const [prerequisites, setPrerequisites] = useState<PrerequisiteStatus | null>(null);
  const [selectedBackend, setSelectedBackend] = useState<BackendType | null>(null);
  const [recommendedBackend, setRecommendedBackend] = useState<BackendType | null>(null);
  const [config, setConfig] = useState<BackendConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [installMessage, setInstallMessage] = useState<string>('');

  // WSL-specific state
  const [wslDistros, setWslDistros] = useState<WslDistroStatus[]>([]);
  const [selectedDistro, setSelectedDistro] = useState<string | null>(null);
  const [wslValidation, setWslValidation] = useState<WslInstallValidation | null>(null);
  const [selectedPort, setSelectedPort] = useState<number>(9876);
  const [isStartingDistro, setIsStartingDistro] = useState(false);

  // Installation log state
  const [installLogs, setInstallLogs] = useState<InstallLogEntry[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Check for existing configuration on mount
  useEffect(() => {
    async function checkExisting() {
      try {
        const existing = await getBackendConfig();
        if (existing.configured && existing.default_backend) {
          // Already configured, try to connect
          setConfig(existing.default_backend);
          setStep('connecting');
          const connected = await testBackendConnection(existing.default_backend);
          if (connected) {
            await startBridgeWithConfig(existing.default_backend);
            onComplete(existing.default_backend);
          } else {
            // Connection failed, show wizard
            setStep('welcome');
          }
        }
      } catch {
        // No existing config, show wizard
      }
    }
    checkExisting();
  }, [onComplete]);

  // Detect prerequisites
  const runDetection = useCallback(async () => {
    setStep('detecting');
    setError(null);
    try {
      const [prereqs, recommended] = await Promise.all([
        detectPrerequisites(),
        getRecommendedBackend(),
      ]);
      setPrerequisites(prereqs);
      setRecommendedBackend(recommended);
      setSelectedBackend(recommended);

      // If WSL is available, fetch detailed distro information
      if (prereqs.wsl_available && prereqs.wsl_distros.length > 0) {
        try {
          const distros = await getWslDistrosDetailed();
          setWslDistros(distros);
          // Select the first running WSL2 distro, or first WSL2 distro, or first distro
          const runningWsl2 = distros.find(d => d.is_wsl2 && d.is_running);
          const anyWsl2 = distros.find(d => d.is_wsl2);
          const defaultDistro = runningWsl2 || anyWsl2 || distros[0];
          if (defaultDistro) {
            setSelectedDistro(defaultDistro.name);
          }
        } catch {
          // If detailed fetch fails, use basic distro list
          setWslDistros(prereqs.wsl_distros.map(name => ({
            name,
            is_wsl2: true, // Assume WSL2
            is_running: false,
            python_available: false,
            python_version: null,
            devflow_installed: false,
            devflow_version: null,
          })));
          setSelectedDistro(prereqs.wsl_distros[0] || null);
        }
      }

      setStep('selection');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect prerequisites');
      setStep('error');
    }
  }, []);

  // Install backend
  const runInstallation = useCallback(async () => {
    if (!selectedBackend) return;

    setStep('installing');
    setError(null);
    setInstallMessage('Preparing installation...');
    setInstallLogs([]);
    setShowLogs(false);

    let unlisten: UnlistenFn | null = null;

    try {
      const newConfig = createDefaultConfig(selectedBackend);
      // Apply WSL-specific settings
      if (selectedBackend === 'wsl2' && selectedDistro) {
        newConfig.wsl_distro = selectedDistro;
        newConfig.remote_port = selectedPort;
      }
      setConfig(newConfig);

      // Set up event listener for installation logs
      unlisten = await listen<InstallLogEntry>('install-log', (event) => {
        setInstallLogs((prev) => [...prev, event.payload]);
        // Update the main message with the latest log
        if (event.payload.level !== 'output') {
          setInstallMessage(event.payload.message);
        }
        // Auto-scroll to bottom
        if (logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
      });

      setInstallMessage(`Installing ${getBackendTypeName(selectedBackend)}...`);
      const message = await installBackendWithLogs(selectedBackend, newConfig);
      setInstallMessage(message);

      // Save the configuration
      await saveBackendConfig(newConfig);

      // Move to connection testing
      setStep('connecting');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
      setStep('error');
    } finally {
      // Clean up the event listener
      if (unlisten) {
        unlisten();
      }
    }
  }, [selectedBackend, selectedDistro, selectedPort]);

  // Validate WSL installation prerequisites
  const runValidation = useCallback(async () => {
    if (selectedBackend !== 'wsl2' || !selectedDistro) {
      // Skip validation for non-WSL backends
      return true;
    }

    setStep('validating');
    setError(null);
    setWslValidation(null);

    try {
      const validation = await validateWslInstallation(selectedDistro, selectedPort);
      setWslValidation(validation);
      return validation.can_install;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
      setStep('error');
      return false;
    }
  }, [selectedBackend, selectedDistro, selectedPort]);

  // Handle "Start Distro" button click
  const handleStartDistro = useCallback(async () => {
    if (!selectedDistro) return;

    setIsStartingDistro(true);
    try {
      await startWslDistro(selectedDistro);
      // Wait a moment for the distro to fully start
      await new Promise(resolve => setTimeout(resolve, 2000));
      // Re-validate
      await runValidation();
      // Refresh distro list
      const distros = await getWslDistrosDetailed();
      setWslDistros(distros);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start distribution');
    } finally {
      setIsStartingDistro(false);
    }
  }, [selectedDistro, runValidation]);

  // Proceed to installation (with validation for WSL)
  const proceedToInstall = useCallback(async () => {
    if (selectedBackend === 'wsl2') {
      const canInstall = await runValidation();
      if (!canInstall) {
        // Stay on validation step to show issues
        return;
      }
    }
    // Proceed to installation
    runInstallation();
  }, [selectedBackend, runValidation, runInstallation]);

  // Test connection and start bridge
  const runConnection = useCallback(async () => {
    if (!config) return;

    setStep('connecting');
    setError(null);

    try {
      // Give the backend a moment to start
      await new Promise(resolve => setTimeout(resolve, 2000));

      const connected = await testBackendConnection(config);
      if (!connected) {
        throw new Error('Backend is not responding. Please try again.');
      }

      // Start the bridge
      await startBridgeWithConfig(config);

      setStep('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      setStep('error');
    }
  }, [config]);

  // Auto-run connection test when reaching connecting step
  useEffect(() => {
    if (step === 'connecting' && config) {
      runConnection();
    }
  }, [step, config, runConnection]);

  // Finish wizard
  const finishWizard = useCallback(() => {
    if (config) {
      onComplete(config);
    }
  }, [config, onComplete]);

  // Get icon for backend type
  const getBackendIcon = (type: BackendType) => {
    switch (type) {
      case 'local_python':
        return <Monitor className="w-6 h-6" />;
      case 'docker':
        return <Container className="w-6 h-6" />;
      case 'wsl2':
        return <Server className="w-6 h-6" />;
      case 'remote':
        return <Globe className="w-6 h-6" />;
    }
  };

  // Check if backend type is available
  const isBackendAvailable = (type: BackendType): boolean => {
    if (!prerequisites) return false;
    switch (type) {
      case 'local_python':
        return prerequisites.python_available;
      case 'docker':
        return prerequisites.docker_available && prerequisites.docker_running;
      case 'wsl2':
        return prerequisites.wsl_available && prerequisites.wsl_distros.length > 0;
      case 'remote':
        return true; // Always available
    }
  };

  // Get availability message
  const getAvailabilityMessage = (type: BackendType): string | null => {
    if (!prerequisites) return null;
    switch (type) {
      case 'local_python':
        if (!prerequisites.python_available) return 'Python not found';
        if (prerequisites.devflow_installed) return `DevFlow ${prerequisites.devflow_version} installed`;
        return `Python ${prerequisites.python_version} available`;
      case 'docker':
        if (!prerequisites.docker_available) return 'Docker not installed';
        if (!prerequisites.docker_running) return 'Docker not running';
        return `Docker ${prerequisites.docker_version} running`;
      case 'wsl2':
        if (!prerequisites.wsl_available) return 'WSL2 not available';
        if (prerequisites.wsl_distros.length === 0) return 'No WSL distributions';
        return `${prerequisites.wsl_distros.length} distribution(s) available`;
      case 'remote':
        return 'Configure manually';
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        {/* Step indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-2 text-sm text-text-secondary">
            {(() => {
              // Include validation step only for WSL2
              const steps = selectedBackend === 'wsl2'
                ? ['Welcome', 'Detect', 'Select', 'Validate', 'Install', 'Connect', 'Done']
                : ['Welcome', 'Detect', 'Select', 'Install', 'Connect', 'Done'];
              const stepKeys = selectedBackend === 'wsl2'
                ? ['welcome', 'detecting', 'selection', 'validating', 'installing', 'connecting', 'complete']
                : ['welcome', 'detecting', 'selection', 'installing', 'connecting', 'complete'];

              return steps.map((label, idx) => {
                const stepIndex = stepKeys.indexOf(step as string);
                const isActive = idx === stepIndex;
                const isComplete = idx < stepIndex;
                const isError = step === 'error' && idx === stepIndex;

                return (
                  <div key={label} className="flex items-center">
                    {idx > 0 && <div className="w-8 h-px bg-border-primary mx-2" />}
                    <div
                      className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${
                        isError
                          ? 'bg-red-500 text-white'
                          : isComplete
                            ? 'bg-green-500 text-white'
                            : isActive
                              ? 'bg-accent-primary text-white'
                              : 'bg-bg-secondary text-text-secondary'
                      }`}
                    >
                      {isComplete ? <Check className="w-3 h-3" /> : idx + 1}
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>

        <Card className="p-8">
          {/* Welcome Step */}
          {step === 'welcome' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-accent-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <Server className="w-8 h-8 text-accent-primary" />
              </div>
              <h1 className="text-2xl font-bold text-text-primary mb-4">Welcome to DevFlow</h1>
              <p className="text-text-secondary mb-8 max-w-md mx-auto">
                DevFlow needs a backend service to manage your development environment.
                Let's set that up now.
              </p>
              <Button onClick={runDetection} className="inline-flex items-center">
                Get Started
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Detecting Step */}
          {step === 'detecting' && (
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-accent-primary animate-spin mx-auto mb-6" />
              <h2 className="text-xl font-semibold text-text-primary mb-2">Detecting Prerequisites</h2>
              <p className="text-text-secondary">
                Checking for Python, Docker, and other requirements...
              </p>
            </div>
          )}

          {/* Selection Step */}
          {step === 'selection' && prerequisites && (
            <div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">Choose Backend Type</h2>
              <p className="text-text-secondary mb-6">
                Select how you want to run the DevFlow backend service.
              </p>

              <div className="space-y-3 mb-6">
                {(['local_python', 'docker', 'wsl2', 'remote'] as BackendType[]).map((type) => {
                  const available = isBackendAvailable(type);
                  const isSelected = selectedBackend === type;
                  const isRecommended = recommendedBackend === type;

                  // Skip WSL2 on non-Windows
                  if (type === 'wsl2' && !prerequisites.wsl_available) {
                    return null;
                  }

                  return (
                    <div key={type}>
                      <button
                        onClick={() => available && setSelectedBackend(type)}
                        disabled={!available}
                        className={`w-full p-4 rounded-lg border-2 text-left transition-colors ${
                          isSelected
                            ? 'border-accent-primary bg-accent-primary/5'
                            : available
                              ? 'border-border-primary hover:border-accent-primary/50 bg-bg-secondary'
                              : 'border-border-primary bg-bg-secondary opacity-50 cursor-not-allowed'
                        }`}
                      >
                        <div className="flex items-start">
                          <div className={`mr-4 ${isSelected ? 'text-accent-primary' : 'text-text-secondary'}`}>
                            {getBackendIcon(type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center">
                              <span className={`font-medium ${isSelected ? 'text-accent-primary' : 'text-text-primary'}`}>
                                {getBackendTypeName(type)}
                              </span>
                              {isRecommended && (
                                <span className="ml-2 px-2 py-0.5 bg-green-500/10 text-green-500 text-xs rounded">
                                  Recommended
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-text-secondary mt-1">
                              {getBackendTypeDescription(type)}
                            </p>
                            <p className={`text-xs mt-2 ${available ? 'text-green-500' : 'text-red-500'}`}>
                              {getAvailabilityMessage(type)}
                            </p>
                          </div>
                          {isSelected && (
                            <Check className="w-5 h-5 text-accent-primary ml-4" />
                          )}
                        </div>
                      </button>

                      {/* WSL2 Distro Selection */}
                      {type === 'wsl2' && isSelected && wslDistros.length > 0 && (
                        <div className="mt-3 ml-10 p-4 bg-bg-secondary rounded-lg border border-border-primary">
                          <label className="block text-sm font-medium text-text-primary mb-2">
                            Select WSL Distribution
                          </label>
                          <div className="relative">
                            <select
                              value={selectedDistro || ''}
                              onChange={(e) => setSelectedDistro(e.target.value)}
                              className="w-full px-3 py-2 bg-bg-primary border border-border-primary rounded-md text-text-primary appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent-primary"
                            >
                              {wslDistros.map((distro) => (
                                <option key={distro.name} value={distro.name}>
                                  {distro.name}
                                  {!distro.is_wsl2 ? ' (WSL1)' : ''}
                                  {!distro.is_running ? ' (Stopped)' : ''}
                                  {distro.devflow_installed ? ' - DevFlow installed' : ''}
                                </option>
                              ))}
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
                          </div>

                          {/* Show selected distro status */}
                          {selectedDistro && (() => {
                            const distro = wslDistros.find(d => d.name === selectedDistro);
                            if (!distro) return null;
                            return (
                              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                                <div className="flex items-center">
                                  <div className={`w-2 h-2 rounded-full mr-2 ${distro.is_wsl2 ? 'bg-green-500' : 'bg-yellow-500'}`} />
                                  <span className="text-text-secondary">
                                    {distro.is_wsl2 ? 'WSL2' : 'WSL1 (upgrade needed)'}
                                  </span>
                                </div>
                                <div className="flex items-center">
                                  <div className={`w-2 h-2 rounded-full mr-2 ${distro.is_running ? 'bg-green-500' : 'bg-yellow-500'}`} />
                                  <span className="text-text-secondary">
                                    {distro.is_running ? 'Running' : 'Stopped'}
                                  </span>
                                </div>
                                <div className="flex items-center">
                                  <div className={`w-2 h-2 rounded-full mr-2 ${distro.python_available ? 'bg-green-500' : 'bg-red-500'}`} />
                                  <span className="text-text-secondary">
                                    Python {distro.python_version || 'Not found'}
                                  </span>
                                </div>
                                <div className="flex items-center">
                                  <div className={`w-2 h-2 rounded-full mr-2 ${distro.devflow_installed ? 'bg-green-500' : 'bg-gray-500'}`} />
                                  <span className="text-text-secondary">
                                    DevFlow {distro.devflow_installed ? distro.devflow_version : 'Not installed'}
                                  </span>
                                </div>
                              </div>
                            );
                          })()}

                          {/* Port selection */}
                          <div className="mt-3">
                            <label className="block text-xs font-medium text-text-secondary mb-1">
                              Service Port
                            </label>
                            <input
                              type="number"
                              value={selectedPort}
                              onChange={(e) => setSelectedPort(parseInt(e.target.value) || 9876)}
                              min={1024}
                              max={65535}
                              className="w-24 px-2 py-1 bg-bg-primary border border-border-primary rounded text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep('welcome')}>
                  Back
                </Button>
                <Button onClick={proceedToInstall} disabled={!selectedBackend || (selectedBackend === 'wsl2' && !selectedDistro)}>
                  Continue
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Validating Step (WSL2 only) */}
          {step === 'validating' && wslValidation && (
            <div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                {wslValidation.can_install ? 'Ready to Install' : 'Pre-Installation Check'}
              </h2>
              <p className="text-text-secondary mb-6">
                Checking requirements for {wslValidation.distro}...
              </p>

              {/* Show issues if any */}
              {wslValidation.issues.length > 0 && (
                <div className="space-y-3 mb-6">
                  {wslValidation.issues.map((issue, idx) => {
                    const { title, description, resolution } = getWslIssueMessage(issue);
                    const isDistroNotRunning = issue.type === 'distro_not_running';
                    const isPortInUse = issue.type === 'port_in_use';

                    return (
                      <div
                        key={idx}
                        className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg"
                      >
                        <div className="flex items-start">
                          <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <h4 className="font-medium text-red-500">{title}</h4>
                            <p className="text-sm text-text-secondary mt-1">{description}</p>
                            {resolution && (
                              <p className="text-xs text-text-secondary mt-2 font-mono bg-bg-secondary px-2 py-1 rounded">
                                {resolution}
                              </p>
                            )}
                            {/* Start distro button */}
                            {isDistroNotRunning && (
                              <Button
                                size="sm"
                                onClick={handleStartDistro}
                                disabled={isStartingDistro}
                                className="mt-3"
                              >
                                {isStartingDistro ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Starting...
                                  </>
                                ) : (
                                  <>
                                    <Play className="w-4 h-4 mr-2" />
                                    Start {selectedDistro}
                                  </>
                                )}
                              </Button>
                            )}
                            {/* Port selection for port in use */}
                            {isPortInUse && (
                              <div className="mt-3 flex items-center space-x-2">
                                <label className="text-sm text-text-secondary">Use port:</label>
                                <input
                                  type="number"
                                  value={selectedPort}
                                  onChange={(e) => setSelectedPort(parseInt(e.target.value) || 9876)}
                                  min={1024}
                                  max={65535}
                                  className="w-24 px-2 py-1 bg-bg-primary border border-border-primary rounded text-sm text-text-primary"
                                />
                                <Button size="sm" onClick={runValidation}>
                                  Re-check
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Show warnings if any */}
              {wslValidation.warnings.length > 0 && (
                <div className="space-y-2 mb-6">
                  {wslValidation.warnings.map((warning, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start"
                    >
                      <AlertCircle className="w-4 h-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-yellow-500">{warning}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Success state */}
              {wslValidation.can_install && (
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg mb-6">
                  <div className="flex items-center">
                    <Check className="w-5 h-5 text-green-500 mr-3" />
                    <p className="text-green-500 font-medium">
                      All checks passed. Ready to install DevFlow in {wslValidation.distro}.
                    </p>
                  </div>
                </div>
              )}

              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep('selection')}>
                  Back
                </Button>
                {wslValidation.can_install ? (
                  <Button onClick={runInstallation}>
                    Install
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Button onClick={runValidation}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Re-check
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Validating Step - Loading */}
          {step === 'validating' && !wslValidation && (
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-accent-primary animate-spin mx-auto mb-6" />
              <h2 className="text-xl font-semibold text-text-primary mb-2">Validating Prerequisites</h2>
              <p className="text-text-secondary">
                Checking requirements for {selectedDistro}...
              </p>
            </div>
          )}

          {/* Installing Step */}
          {step === 'installing' && (
            <div>
              <div className="text-center mb-6">
                <Loader2 className="w-12 h-12 text-accent-primary animate-spin mx-auto mb-6" />
                <h2 className="text-xl font-semibold text-text-primary mb-2">
                  Installing {selectedBackend && getBackendTypeName(selectedBackend)}
                </h2>
                <p className="text-text-secondary">{installMessage}</p>
              </div>

              {/* Collapsible Log Viewer */}
              {installLogs.length > 0 && (
                <div className="mt-6">
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="flex items-center justify-center w-full py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <Terminal className="w-4 h-4 mr-2" />
                    {showLogs ? 'Hide' : 'Show'} Installation Output
                    {showLogs ? (
                      <ChevronUp className="w-4 h-4 ml-2" />
                    ) : (
                      <ChevronDown className="w-4 h-4 ml-2" />
                    )}
                  </button>

                  {showLogs && (
                    <div
                      ref={logContainerRef}
                      className="mt-2 max-h-64 overflow-y-auto bg-bg-primary border border-border-primary rounded-lg p-3 font-mono text-xs"
                    >
                      {installLogs.map((log, idx) => (
                        <div
                          key={idx}
                          className={`py-0.5 ${
                            log.level === 'error'
                              ? 'text-red-500'
                              : log.level === 'warning'
                                ? 'text-yellow-500'
                                : log.level === 'success'
                                  ? 'text-green-500'
                                  : log.level === 'output'
                                    ? 'text-text-secondary opacity-75'
                                    : 'text-text-secondary'
                          }`}
                        >
                          {log.level !== 'output' && (
                            <span className="opacity-50">[{log.level.toUpperCase()}] </span>
                          )}
                          {log.message}
                          {log.output && (
                            <div className="ml-4 mt-1 whitespace-pre-wrap text-text-secondary opacity-60">
                              {log.output}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Connecting Step */}
          {step === 'connecting' && (
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-accent-primary animate-spin mx-auto mb-6" />
              <h2 className="text-xl font-semibold text-text-primary mb-2">Connecting to Backend</h2>
              <p className="text-text-secondary">Testing connection and starting the bridge...</p>
            </div>
          )}

          {/* Complete Step */}
          {step === 'complete' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <Check className="w-8 h-8 text-green-500" />
              </div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">Setup Complete</h2>
              <p className="text-text-secondary mb-8">
                DevFlow backend is configured and running. You're ready to go!
              </p>
              <Button onClick={finishWizard}>
                Start Using DevFlow
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Error Step */}
          {step === 'error' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">Something Went Wrong</h2>
              <p className="text-red-500 mb-6">{error}</p>
              <div className="flex justify-center space-x-4">
                <Button variant="secondary" onClick={() => setStep('selection')}>
                  Choose Different Backend
                </Button>
                <Button onClick={runDetection}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Prerequisites summary (shown during selection) */}
        {step === 'selection' && prerequisites && (
          <div className="mt-6 p-4 bg-bg-secondary rounded-lg">
            <h3 className="text-sm font-medium text-text-primary mb-3">System Status</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${prerequisites.python_available ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-text-secondary">
                  Python {prerequisites.python_version || 'Not found'}
                </span>
              </div>
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${prerequisites.devflow_installed ? 'bg-green-500' : 'bg-yellow-500'}`} />
                <span className="text-text-secondary">
                  DevFlow {prerequisites.devflow_installed ? prerequisites.devflow_version : 'Not installed'}
                </span>
              </div>
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${prerequisites.docker_running ? 'bg-green-500' : prerequisites.docker_available ? 'bg-yellow-500' : 'bg-red-500'}`} />
                <span className="text-text-secondary">
                  Docker {prerequisites.docker_running ? 'Running' : prerequisites.docker_available ? 'Stopped' : 'Not found'}
                </span>
              </div>
              {prerequisites.wsl_available && (
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${prerequisites.wsl_distros.length > 0 ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  <span className="text-text-secondary">
                    WSL2 {prerequisites.wsl_distros.length > 0 ? `(${prerequisites.wsl_distros[0]})` : 'No distros'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
