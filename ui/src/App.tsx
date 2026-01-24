import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar, Notifications } from './components/layout';
import {
  Dashboard,
  Projects,
  Config,
  Infrastructure,
  Development,
  Database,
  Secrets,
  Deploy,
  Doctor,
} from './pages';
import { useAppStore } from './store';
import { startBridge, getGlobalConfig, listProjects } from './api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
    },
  },
});

function AppContent() {
  const { setBridgeState, setGlobalConfig, setProjects, addNotification } = useAppStore();

  const initializeApp = async () => {
    setBridgeState('Starting');

    try {
      // Start the Python bridge
      // In development, the bridge is at ../bridge relative to ui/
      // In production, it would be bundled with the app
      // Use environment variable or fallback to hardcoded path for development
      const devflowRoot = import.meta.env.VITE_DEVFLOW_ROOT || '/home/justin/aocyber/devflow';

      console.log('Starting bridge with devflow root:', devflowRoot);
      await startBridge('bridge.main', devflowRoot);
      setBridgeState('Running');

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
      setBridgeState('Error');
      addNotification({
        type: 'error',
        title: 'Connection failed',
        message: error instanceof Error ? error.message : 'Failed to start bridge',
      });
    }
  };

  useEffect(() => {
    initializeApp();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen bg-bg-primary text-text-primary">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
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
          <Route path="/doctor" element={<Doctor />} />
        </Routes>
      </main>
      <Notifications />
    </div>
  );
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
