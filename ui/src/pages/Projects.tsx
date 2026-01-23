import { useEffect, useState } from 'react';
import { FolderPlus, Folder, ExternalLink, Trash2, RefreshCw } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, StatusBadge } from '../components/common';
import { useAppStore } from '../store';
import {
  listProjects,
  addProject,
  removeProject,
  openProjectFolder,
} from '../api';

export function Projects() {
  const { projects, setProjects, bridgeState, addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [newProjectPath, setNewProjectPath] = useState('');

  const isConnected = bridgeState === 'Running';

  useEffect(() => {
    if (isConnected) {
      loadProjects();
    }
  }, [isConnected]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const projectList = await listProjects();
      setProjects(projectList);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to load projects',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddProject = async () => {
    if (!newProjectPath.trim()) return;

    try {
      await addProject(newProjectPath);
      setNewProjectPath('');
      addNotification({
        type: 'success',
        title: 'Project Added',
        message: `Added ${newProjectPath}`,
      });
      loadProjects();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to add project',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleRemoveProject = async (path: string) => {
    try {
      await removeProject(path);
      addNotification({
        type: 'success',
        title: 'Project Removed',
      });
      loadProjects();
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to remove project',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  const handleOpenFolder = async (path: string) => {
    try {
      await openProjectFolder(path);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Failed to open folder',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  };

  return (
    <>
      <Header
        title="Projects"
        subtitle="Manage your DevFlow projects"
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={16} />}
            onClick={loadProjects}
            loading={loading}
            disabled={!isConnected}
          >
            Refresh
          </Button>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Add Project */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">Add Project</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={newProjectPath}
                onChange={(e) => setNewProjectPath(e.target.value)}
                placeholder="/path/to/project"
                className="flex-1 px-4 py-2 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                onKeyDown={(e) => e.key === 'Enter' && handleAddProject()}
              />
              <Button
                icon={<FolderPlus size={16} />}
                onClick={handleAddProject}
                disabled={!isConnected || !newProjectPath.trim()}
              >
                Add
              </Button>
            </div>
          </Card>

          {/* Project List */}
          <Card padding="none">
            <div className="p-4 border-b border-border">
              <h3 className="text-lg font-semibold">
                Registered Projects ({projects.length})
              </h3>
            </div>
            {projects.length > 0 ? (
              <div className="divide-y divide-border">
                {projects.map((project) => (
                  <div
                    key={project.path}
                    className="flex items-center justify-between p-4 hover:bg-bg-tertiary/50"
                  >
                    <div className="flex items-center gap-3">
                      <Folder className="text-text-muted" size={20} />
                      <div>
                        <p className="font-medium">{project.name}</p>
                        <p className="text-sm text-text-muted">{project.path}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <StatusBadge
                        status={project.has_devflow_config ? 'success' : 'warning'}
                        label={
                          project.has_devflow_config ? 'Configured' : 'No Config'
                        }
                      />
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<ExternalLink size={16} />}
                          onClick={() => handleOpenFolder(project.path)}
                          title="Open in file manager"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 size={16} />}
                          onClick={() => handleRemoveProject(project.path)}
                          className="text-error hover:text-error"
                          title="Remove from registry"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-text-secondary">
                <Folder size={40} className="mx-auto mb-2 opacity-50" />
                <p>No projects registered</p>
                <p className="text-sm mt-1">
                  Add a project path above to get started
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}
