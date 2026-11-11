import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, Link } from 'react-router-dom';
import { useAuth, ROLE_LABELS } from '../../context/AuthContext';
import { api, SystemStatus } from '../../api/client';
import { useAssessment } from '../../context/AssessmentContext';
import {
  LayoutDashboard,
  CloudRain,
  Activity,
  MapPin,
  HeartPulse,
  Navigation,
  Building,
  LifeBuoy,
  Sparkles,
  GitFork,
  FileText,
  ShieldAlert,
  Database,
  Bot,
  Terminal,
  LogOut,
  Loader2
} from 'lucide-react';

export const AuthorityLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const assessment = useAssessment();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusError, setStatusError] = useState(false);

  useEffect(() => {
    api.getSystemStatus().then(setStatus).catch(() => setStatusError(true));
  }, []);

  const canSeeDataOps = user?.role === 'SYSTEM_ADMIN' || user?.role === 'DATA_MANAGER' || user?.role === 'DISASTER_OFFICER';
  const navItems = [
    { to: '/authority/command', icon: <LayoutDashboard className="w-4 h-4" />, label: 'Command Centre' },
    { to: '/authority/flood', icon: <CloudRain className="w-4 h-4" />, label: 'Flood Intelligence' },
    { to: '/authority/impact', icon: <Activity className="w-4 h-4" />, label: 'Impact Analysis' },
    { to: '/authority/neighbourhoods', icon: <MapPin className="w-4 h-4" />, label: 'Neighbourhoods' },
    { to: '/authority/facilities', icon: <HeartPulse className="w-4 h-4" />, label: 'Hospital Access' },
    { to: '/authority/evacuation', icon: <Navigation className="w-4 h-4" />, label: 'Evacuation Routing' },
    { to: '/authority/shelters', icon: <Building className="w-4 h-4" />, label: 'Shelter Allocations' },
    { to: '/authority/rescue', icon: <LifeBuoy className="w-4 h-4" />, label: 'Rescue Operations' },
    { to: '/authority/scenario', icon: <Sparkles className="w-4 h-4" />, label: 'Scenario Analysis' },
    { to: '/authority/roads', icon: <GitFork className="w-4 h-4" />, label: 'Road Intelligence' },
    { to: '/authority/sitrep', icon: <FileText className="w-4 h-4" />, label: 'Situation Reports' },
    { to: '/authority/ai', icon: <Bot className="w-4 h-4" />, label: 'AI Assistant' },
    { to: '/authority/monitor', icon: <Terminal className="w-4 h-4" />, label: 'System Monitor' },
    ...(canSeeDataOps ? [{ to: '/authority/data-operations', icon: <Database className="w-4 h-4" />, label: 'Data Operations' }] : []),
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      {/* Professional Authority Operations Header */}
      <header className="bg-pravah-navy text-white border-b border-slate-800 sticky top-0 z-40">
        <div className="px-4 sm:px-6 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/authority/command" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-pravah-teal flex items-center justify-center text-white shadow-md">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-base tracking-tight">
                    PRAVAH <span className="text-pravah-teal">AI</span>
                  </span>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-pravah-teal/20 text-pravah-aqua border border-pravah-teal/40">
                    Operations
                  </span>
                </div>
                <div className="text-[10px] text-pravah-slate font-medium hidden sm:block">
                  {status?.zone ?? ''}
                </div>
              </div>
            </Link>
          </div>

          {/* Global Shared Assessment Context Indicator */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-slate-300 shadow-inner">
            <span className="text-[10px] uppercase font-bold text-pravah-teal">Assessment:</span>
            <span className="font-mono text-[11px] text-white">{assessment.assessmentId}</span>
            <span className="text-slate-600">|</span>
            <span className="text-[10px] text-slate-400">Precipitation:</span>
            <span className="font-bold text-[11px] text-amber-400">{assessment.rainfall}</span>
            {assessment.closedRoads.length > 0 && (
              <>
                <span className="text-slate-600">|</span>
                <span className="px-1.5 py-0.2 rounded bg-rose-900/60 text-[10px] text-rose-300 font-bold border border-rose-700/50">
                  {assessment.closedRoads.length} Closures Applied
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 pl-3 border-l border-slate-700 text-xs">
              <div className="w-7 h-7 rounded-full bg-pravah-teal/30 text-pravah-teal flex items-center justify-center font-bold text-xs">
                {user?.full_name?.charAt(0) ?? ''}
              </div>
              <span className="hidden lg:inline font-bold truncate max-w-[140px]">
                {user?.full_name}</span>
              <span className="hidden xl:inline text-[10px] text-slate-400">{user ? ROLE_LABELS[user.role] : ''}
              </span>
              <button
                onClick={() => { void logout(); }}
                className="p-1 text-slate-400 hover:text-white"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body with Sidebar + Dynamic Content Outlet */}
      <div className="flex flex-1 overflow-hidden">
        {/* Compact Desktop Sidebar */}
        <aside className="w-56 bg-white border-r border-slate-200 hidden md:flex flex-col justify-between py-4 px-3 flex-shrink-0 shadow-sm">
          <div className="space-y-1">
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-pravah-slate">
              Operational Modules
            </div>

            {navItems.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-pravah-teal text-white shadow-sm'
                      : 'text-pravah-navy hover:bg-pravah-aqua/50 hover:text-pravah-teal'
                  }`
                }
              >
                {item.icon}
                <span className="truncate">{item.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-pravah-pale border border-slate-200 text-xs space-y-1" aria-live="polite">
            <div className="text-[10px] text-pravah-slate font-bold uppercase">Data status</div>
            {!status && !statusError && <Loader2 className="w-3.5 h-3.5 animate-spin text-pravah-slate" />}
            {statusError && <div className="text-red-700 font-semibold">Unavailable</div>}
            {status && (
              <>
                <div className={`font-bold ${status.dataset_status === 'UNVERIFIED' ? 'text-amber-700' : 'text-pravah-navy'}`}>
                  {status.dataset_status}
                </div>
                <div className="text-[10px] text-pravah-slate">
                  Road network: {status.road_network.nodes} nodes, {status.road_network.edges} links
                </div>
                {status.unverified_records > 0 && (
                  <div className="text-[10px] text-pravah-slate">
                    {status.unverified_records} records not yet verified against an official source.
                  </div>
                )}
              </>
            )}
          </div>
        </aside>

        {/* Content View */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div className="mb-4 flex flex-wrap items-center gap-2 text-[11px] text-pravah-slate">
            <span className="font-bold uppercase tracking-wider">Assessment</span>
            <span className="px-2 py-0.5 rounded bg-white border border-slate-200 text-pravah-navy font-semibold">
              {assessment.closedRoads.length === 0 ? 'Baseline, no closures' : `${assessment.closedRoads.length} closure(s) applied`}
            </span>
            {assessment.closedRoads.length > 0 && (
              <button onClick={assessment.reset} className="text-pravah-teal hover:underline">Reset</button>
            )}
          </div>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
