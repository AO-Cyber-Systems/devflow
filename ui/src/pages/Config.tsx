import { useState } from 'react';
import { Header } from '../components/layout';
import { Button, Card } from '../components/common';
import { Save, RefreshCw } from 'lucide-react';
import Editor from '@monaco-editor/react';

export function Config() {
  const [activeTab, setActiveTab] = useState<'global' | 'project'>('global');
  const [configContent, setConfigContent] = useState(`# DevFlow Configuration
version: "1"

git:
  user_name: null
  user_email: null
  co_author_enabled: true
  co_author_name: Claude
  co_author_email: noreply@anthropic.com

defaults:
  secrets_provider: null
  network_name: devflow-proxy
  registry: null

infrastructure:
  auto_start: false
  traefik_http_port: 80
  traefik_https_port: 443
  traefik_dashboard_port: 8088
`);

  return (
    <>
      <Header
        title="Configuration"
        subtitle="Edit global and project configuration"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" icon={<RefreshCw size={16} />}>
              Reload
            </Button>
            <Button size="sm" icon={<Save size={16} />}>
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
              onClick={() => setActiveTab('global')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'global'
                  ? 'bg-accent text-white'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
              }`}
            >
              Global Config
            </button>
            <button
              onClick={() => setActiveTab('project')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'project'
                  ? 'bg-accent text-white'
                  : 'bg-bg-secondary text-text-secondary hover:text-text-primary'
              }`}
            >
              Project Config
            </button>
          </div>

          {/* Editor */}
          <Card padding="none" className="overflow-hidden">
            <div className="h-[600px]">
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
                }}
              />
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
