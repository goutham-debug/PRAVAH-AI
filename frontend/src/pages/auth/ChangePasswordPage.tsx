import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthShell } from './AuthShell';

export const ChangePasswordPage: React.FC = () => {
  const { changePassword, logout, user } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (next !== confirm) return setError('New passwords do not match.');
    if (next.length < 12) return setError('Password must be at least 12 characters.');
    setBusy(true);
    const res = await changePassword(current, next);
    setBusy(false);
    if (!res.ok) setError(res.error || 'Could not change password.');
  };

  const field = (id: string, label: string, value: string, set: (v: string) => void, auto: string) => (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-pravah-navy mb-1">{label}</label>
      <input
        id={id} type="password" autoComplete={auto} value={value} onChange={e => set(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pravah-teal"
      />
    </div>
  );

  return (
    <AuthShell title="Set a new password" subtitle={`Signed in as ${user?.email}. A new password is required before you continue.`}>
      <form onSubmit={submit} className="space-y-4">
        {field('cur', 'Current (temporary) password', current, setCurrent, 'current-password')}
        {field('new', 'New password', next, setNext, 'new-password')}
        {field('conf', 'Confirm new password', confirm, setConfirm, 'new-password')}
        <p className="text-[11px] text-pravah-slate">
          At least 12 characters, using three of: lowercase, uppercase, digits, symbols.
        </p>
        {error && <p role="alert" className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{error}</p>}
        <button type="submit" disabled={busy}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-pravah-teal text-white text-sm font-semibold hover:bg-pravah-teal-dark disabled:opacity-60">
          {busy && <Loader2 className="w-4 h-4 animate-spin" />}
          Update password
        </button>
        <button type="button" onClick={logout} className="w-full text-xs text-pravah-slate hover:underline">Sign out</button>
      </form>
    </AuthShell>
  );
};
