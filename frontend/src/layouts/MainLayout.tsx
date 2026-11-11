import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  FileText,
  MessageSquare,
  GitCompare,
  FileHeart,
  Shield,
  Settings,
  Menu,
  X,
  LogOut,
  Activity,
} from 'lucide-react';
import { useState } from 'react';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  phase?: number;
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard', phase: 2 },
  { to: '/upload', icon: <Upload size={20} />, label: 'Upload Report', phase: 3 },
  { to: '/reports', icon: <FileText size={20} />, label: 'Report Library', phase: 3 },
  { to: '/chat', icon: <MessageSquare size={20} />, label: 'AI Chat', phase: 9 },
  { to: '/compare', icon: <GitCompare size={20} />, label: 'Compare Reports', phase: 10 },
  { to: '/summary', icon: <FileHeart size={20} />, label: 'Doctor Summary', phase: 10 },
  { to: '/privacy', icon: <Shield size={20} />, label: 'Privacy Center', phase: 10 },
  { to: '/settings', icon: <Settings size={20} />, label: 'Settings', phase: 2 },
];

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-[#1e3a5f] transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-white/10">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#0d9488] flex items-center justify-center">
              <Activity size={20} className="text-white" />
            </div>
            <span className="text-white font-semibold text-lg">MediLens AI</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-white/70 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive(item.to)
                  ? 'bg-white/15 text-white'
                  : 'text-white/70 hover:bg-white/10 hover:text-white'
              }`}
            >
              {item.icon}
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
          <button className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors">
            <LogOut size={20} />
            <span className="text-sm font-medium">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg"
          >
            <Menu size={20} />
          </button>

          <div className="hidden lg:block" />

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-900">Demo User</p>
              <p className="text-xs text-slate-500">demo@medilens.ai</p>
            </div>
            <div className="w-9 h-9 rounded-full bg-[#0d9488] flex items-center justify-center text-white font-medium text-sm">
              DU
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
