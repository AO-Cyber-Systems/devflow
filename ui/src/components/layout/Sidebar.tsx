import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  Settings,
  Database,
  Server,
  Code2,
  Key,
  Rocket,
  Wrench,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAppStore } from '../../store';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
  { to: '/projects', icon: <FolderKanban size={20} />, label: 'Projects' },
  { to: '/config', icon: <Settings size={20} />, label: 'Configuration' },
  { to: '/infrastructure', icon: <Server size={20} />, label: 'Infrastructure' },
  { to: '/development', icon: <Code2 size={20} />, label: 'Development' },
  { to: '/database', icon: <Database size={20} />, label: 'Database' },
  { to: '/secrets', icon: <Key size={20} />, label: 'Secrets' },
  { to: '/deploy', icon: <Rocket size={20} />, label: 'Deploy' },
  { to: '/setup', icon: <Wrench size={20} />, label: 'Setup & Health' },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={`flex flex-col bg-bg-secondary border-r border-border transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-56'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center h-14 px-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          {!sidebarCollapsed && (
            <span className="font-semibold text-lg">DevFlow</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-accent text-white'
                      : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                  }`
                }
                title={sidebarCollapsed ? item.label : undefined}
              >
                {item.icon}
                {!sidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border p-2">
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 rounded-lg text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <ChevronRight size={20} />
          ) : (
            <ChevronLeft size={20} />
          )}
        </button>
      </div>
    </aside>
  );
}
