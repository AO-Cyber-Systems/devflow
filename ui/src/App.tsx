import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar, Notifications, UpdateChecker } from './components/layout';
import {
  Dashboard,
  Projects,
  Config,
  Infrastructure,
  Development,
  Database,
  Secrets,
  Deploy,
  Setup,
  SetupWizard,
} from './pages';
import { useAppStore } from './store';
import { getGlobalConfig, listProjects } from './api';
import { getBackendConfig, startBridgeWithConfig, testBackendConnection } from './api/backendSetup';
import type { BackendConfig } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
    },
  },
});

/**
 * Loading screen shown while checking backend configuration
 */
function LoadingScreen() {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-accent-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-secondary">Loading DevFlow...</p>
      </div>
    </div>
  );
}

/**
 * Main application content - shown after backend is configured
 */
function MainApp() {
  const { setGlobalConfig, setProjects, addNotification } = useAppStore();

  const loadInitialData = async () => {
    try {
      // Load initial data
      const [config, projects] = await Promise.all([
        getGlobalConfig().catch(() => null),
        listProjects().catch(() => []),
      ]);

      if (config) {
        setGlobalConfig(config);
      }
      setProjects(projects);

      addNotification({
        type: 'success',
        title: 'Connected',
        message: 'DevFlow bridge is running',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Load failed',
        message: error instanceof Error ? error.message : 'Failed to load data',
      });
    }
  };

  useEffect(() => {
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen bg-bg-primary text-text-primary">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <UpdateChecker />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/config" element={<Config />} />
          <Route path="/infrastructure" element={<Infrastructure />} />
          <Route path="/development" element={<Development />} />
          <Route path="/database" element={<Database />} />
          <Route path="/secrets" element={<Secrets />} />
          <Route path="/deploy" element={<Deploy />} />
          <Route path="/setup" element={<Setup />} />
          {/* Redirect old doctor route to setup */}
          <Route path="/doctor" element={<Navigate to="/setup" replace />} />
        </Routes>
      </main>
      <Notifications />
    </div>
  );
}

/**
 * App content with backend configuration check
 */
function AppContent() {
  const { setBackendConfigured, setBackendConfig, setBridgeState } = useAppStore();
  const [showWizard, setShowWizard] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkBackendConfig() {
      try {
        const config = await getBackendConfig();

        if (!config.configured || !config.default_backend) {
          // No configuration, show wizard
          setShowWizard(true);
          return;
        }

        // Configuration exists, try to start the backend
        setBackendConfig(config.default_backend);
        setBridgeState('Starting');

        try {
          // For Docker/WSL2/Remote, test connection first
          if (config.default_backend.backend_type !== 'local_python') {
            const connected = await testBackendConnection(config.default_backend);
            if (!connected) {
              // Backend not responding, show wizard for reconfiguration
              console.warn('Backend not responding, showing wizard');
              setShowWizard(true);
              return;
            }
          }

          // Start the bridge with the saved configuration
          await startBridgeWithConfig(config.default_backend);
          setBackendConfigured(true);
          setBridgeState('Running');
          setShowWizard(false);
        } catch (error) {
          console.error('Failed to connect to backend:', error);
          // Show wizard for reconfiguration
          setShowWizard(true);
        }
      } catch (error) {
        console.error('Failed to load backend config:', error);
        // Show wizard on any error
        setShowWizard(true);
      }
    }

    checkBackendConfig();
  }, [setBackendConfigured, setBackendConfig, setBridgeState]);

  const handleWizardComplete = async (config: BackendConfig) => {
    setBackendConfig(config);
    setBackendConfigured(true);
    setBridgeState('Running');
    setShowWizard(false);
  };

  // Loading state
  if (showWizard === null) {
    return <LoadingScreen />;
  }

  // Show wizard if backend not configured
  if (showWizard) {
    return <SetupWizard onComplete={handleWizardComplete} />;
  }

  // Show main app
  return <MainApp />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
