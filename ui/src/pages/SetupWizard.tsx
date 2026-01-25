/**
 * Setup Wizard - Full-screen blocking wizard for initial backend configuration
 *
 * This wizard runs before the main app and ensures a valid backend is configured.
 */

import { useState, useEffect, useCallback } from 'react';
import { Check, ChevronRight, Loader2, Server, Monitor, Container, Globe, AlertCircle, RefreshCw } from 'lucide-react';
import { Button, Card } from '../components/common';
import {
  detectPrerequisites,
  getBackendConfig,
  saveBackendConfig,
  installBackend,
  testBackendConnection,
  startBridgeWithConfig,
  getRecommendedBackend,
  createDefaultConfig,
  getBackendTypeName,
  getBackendTypeDescription,
} from '../api/backendSetup';
import type { BackendType, BackendConfig, PrerequisiteStatus, WizardStep } from '../types';

interface SetupWizardProps {
  onComplete: (config: BackendConfig) => void;
}

export function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState<WizardStep>('welcome');
  const [prerequisites, setPrerequisites] = useState<PrerequisiteStatus | null>(null);
  const [selectedBackend, setSelectedBackend] = useState<BackendType | null>(null);
  const [recommendedBackend, setRecommendedBackend] = useState<BackendType | null>(null);
  const [config, setConfig] = useState<BackendConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [installMessage, setInstallMessage] = useState<string>('');

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

    try {
      const newConfig = createDefaultConfig(selectedBackend);
      setConfig(newConfig);

      setInstallMessage(`Installing ${getBackendTypeName(selectedBackend)}...`);
      const message = await installBackend(selectedBackend, newConfig);
      setInstallMessage(message);

      // Save the configuration
      await saveBackendConfig(newConfig);

      // Move to connection testing
      setStep('connecting');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
      setStep('error');
    }
  }, [selectedBackend]);

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
            {['Welcome', 'Detect', 'Select', 'Install', 'Connect', 'Done'].map((label, idx) => {
              const stepIndex = ['welcome', 'detecting', 'selection', 'installing', 'connecting', 'complete'].indexOf(step);
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
            })}
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
                    <button
                      key={type}
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
                  );
                })}
              </div>

              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep('welcome')}>
                  Back
                </Button>
                <Button onClick={runInstallation} disabled={!selectedBackend}>
                  Continue
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Installing Step */}
          {step === 'installing' && (
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-accent-primary animate-spin mx-auto mb-6" />
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                Installing {selectedBackend && getBackendTypeName(selectedBackend)}
              </h2>
              <p className="text-text-secondary">{installMessage}</p>
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
