import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const AuthShell: React.FC<{ title: string; subtitle?: string; children: React.ReactNode }> = ({ title, subtitle, children }) => (
  <div className="min-h-screen bg-pravah-pale flex flex-col">
    <div className="h-1.5 bg-pravah-teal" />
    <main className="flex-1 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-pravah-teal flex items-center justify-center text-white">
            <ShieldAlert className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="font-extrabold text-lg text-pravah-navy leading-tight">
              PRAVAH <span className="text-pravah-teal">AI</span>
            </div>
            <div className="text-xs text-pravah-slate">Urban Flood Impact Intelligence</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
          <h1 className="text-lg font-bold text-pravah-navy">{title}</h1>
          {subtitle && <p className="text-sm text-pravah-slate mt-1">{subtitle}</p>}
          <div className="mt-5">{children}</div>
        </div>
        <p className="text-[11px] text-pravah-slate text-center mt-4">
          Authorised personnel only. Access is logged.
        </p>
      </div>
    </main>
  </div>
);
