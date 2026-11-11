import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthShell } from './AuthShell';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated, loading } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [forgot, setForgot] = useState(false);

  if (!loading && isAuthenticated) {
    const from = (location.state as { from?: string } | null)?.from || '/authority/command';
    return <Navigate to={from} replace />;
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setBusy(true);
    const res = await login(email.trim(), password);
    setBusy(false);
    if (!res.ok) setError(res.error || 'Sign-in failed.');
  };

  return (
    <AuthShell title="Sign in" subtitle="Use your authorised account.">
      <form onSubmit={submit} noValidate className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-xs font-semibold text-pravah-navy mb-1">Email</label>
          <input
            id="email" type="email" autoComplete="username" autoFocus value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pravah-teal"
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="password" className="block text-xs font-semibold text-pravah-navy">Password</label>
            <button type="button" onClick={() => setForgot(f => !f)} className="text-xs text-pravah-teal hover:underline">
              Forgot password?
            </button>
          </div>
          <div className="relative">
            <input
              id="password" type={show ? 'text' : 'password'} autoComplete="current-password" value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full pl-3 pr-10 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pravah-teal"
            />
            <button
              type="button" onClick={() => setShow(s => !s)}
              aria-label={show ? 'Hide password' : 'Show password'}
              className="absolute inset-y-0 right-0 px-3 text-slate-500 hover:text-pravah-navy"
            >
              {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {forgot && (
          <p className="text-xs text-pravah-navy bg-pravah-aqua border border-pravah-teal/30 rounded-lg p-3">
            Password resets are issued by your System Administrator. Ask them to reset your account; you will be
            asked to choose a new password at your next sign-in.
          </p>
        )}
        {error && (
          <p role="alert" className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{error}</p>
        )}

        <button
          type="submit" disabled={busy}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-pravah-teal text-white text-sm font-semibold hover:bg-pravah-teal-dark disabled:opacity-60"
        >
          {busy && <Loader2 className="w-4 h-4 animate-spin" />}
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </AuthShell>
  );
};
