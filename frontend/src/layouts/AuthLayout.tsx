import { Link, Outlet } from 'react-router-dom';
import { Activity } from 'lucide-react';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col">
      {/* Header */}
      <header className="h-16 flex items-center justify-center">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-[#1e3a5f] flex items-center justify-center">
            <Activity size={24} className="text-white" />
          </div>
          <span className="text-[#1e3a5f] font-bold text-xl">MediLens AI</span>
        </Link>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center">
        <p className="text-sm text-slate-500">
          MediLens AI provides educational health information only.
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Not a substitute for professional medical advice, diagnosis, or treatment.
        </p>
      </footer>
    </div>
  );
}
