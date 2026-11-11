import { Link } from 'react-router-dom';
import { LogIn, Clock } from 'lucide-react';
import { Card, Button, Input } from '../components';

export default function LoginPage() {
  return (
    <Card>
      <div className="text-center mb-8">
        <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-gradient-to-br from-[#1e3a5f] to-[#0d9488] flex items-center justify-center">
          <LogIn size={24} className="text-white" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Welcome Back</h1>
        <p className="text-slate-600 mt-1">Sign in to your MediLens AI account</p>
      </div>

      {/* Coming soon notice */}
      <div className="mb-6 p-4 rounded-lg bg-amber-50 border border-amber-200">
        <div className="flex items-center gap-2 text-amber-800">
          <Clock size={18} />
          <span className="text-sm font-medium">Authentication coming in Phase 2</span>
        </div>
        <p className="text-sm text-amber-700 mt-1">
          User accounts and secure login will be implemented in the next development phase.
        </p>
      </div>

      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <Input
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          disabled
        />
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          disabled
        />
        <Button className="w-full" size="lg" disabled>
          Sign In
        </Button>
      </form>

      <p className="text-center text-sm text-slate-600 mt-6">
        Don't have an account?{' '}
        <Link to="/register" className="text-[#0d9488] font-medium hover:underline">
          Create one
        </Link>
      </p>
    </Card>
  );
}
