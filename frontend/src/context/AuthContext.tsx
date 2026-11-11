import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { User, UserRole } from '../types';
import { api } from '../api/client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  mustChangePassword: boolean;
  canWrite: boolean;
  login: (email: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  changePassword: (current: string, next: string) => Promise<{ ok: boolean; error?: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const ROLE_LABELS: Record<UserRole, string> = {
  SYSTEM_ADMIN: 'System Administrator',
  DISASTER_OFFICER: 'Disaster Management Officer',
  OPERATIONS_OFFICER: 'Operations Officer',
  DATA_MANAGER: 'Data Manager',
  READ_ONLY_ANALYST: 'Read-only Analyst',
};

// UI convenience only. The backend enforces permissions on every request.
const WRITE_ROLES: UserRole[] = ['SYSTEM_ADMIN', 'DISASTER_OFFICER', 'OPERATIONS_OFFICER'];

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const clear = useCallback(() => {
    localStorage.removeItem('pravah_token');
    setUser(null);
  }, []);

  useEffect(() => {
    const onUnauthorized = () => clear();
    const onPwdRequired = () => setUser(u => (u ? { ...u, must_change_password: true } : u));
    window.addEventListener('pravah:unauthorized', onUnauthorized);
    window.addEventListener('pravah:password-change-required', onPwdRequired);

    (async () => {
      if (localStorage.getItem('pravah_token')) {
        try {
          const res = await api.getMe();
          if (res.success && res.user) setUser(res.user);
          else clear();
        } catch {
          clear();
        }
      }
      setLoading(false);
    })();

    return () => {
      window.removeEventListener('pravah:unauthorized', onUnauthorized);
      window.removeEventListener('pravah:password-change-required', onPwdRequired);
    };
  }, [clear]);

  const login = async (email: string, password: string) => {
    try {
      const res = await api.login(email, password);
      if (res.success && res.token && res.user) {
        localStorage.setItem('pravah_token', res.token);
        setUser(res.user);
        return { ok: true };
      }
      return { ok: false, error: res.error || 'Sign-in failed.' };
    } catch {
      return { ok: false, error: 'Cannot reach the server. Check your connection and try again.' };
    }
  };

  const changePassword = async (current: string, next: string) => {
    try {
      const res = await api.changePassword(current, next);
      if (res.success && res.token && res.user) {
        localStorage.setItem('pravah_token', res.token);
        setUser(res.user);
        return { ok: true };
      }
      return { ok: false, error: res.error || 'Could not change password.' };
    } catch {
      return { ok: false, error: 'Cannot reach the server.' };
    }
  };

  const logout = async () => {
    try { await api.logout(); } catch { /* session is cleared locally regardless */ }
    clear();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        mustChangePassword: !!user?.must_change_password,
        canWrite: !!user && WRITE_ROLES.includes(user.role),
        login,
        changePassword,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
