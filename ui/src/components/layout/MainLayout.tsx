import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Notifications } from '../common/Notifications';

export function MainLayout() {
  return (
    <div className="flex h-screen bg-bg-primary">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
      <Notifications />
    </div>
  );
}
