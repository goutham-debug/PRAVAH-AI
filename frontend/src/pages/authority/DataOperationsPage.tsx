import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Database, Server, RefreshCw, Radio, AlertTriangle, Loader2 } from 'lucide-react';
import {
  api, DataOpsOverview, DatasetInventoryRow, IngestionEventView, IngestionRunView,
} from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { ClassificationBadge } from '../../components/common/ClassificationBadge';

const POLL_MS = 3000;
const fmt = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleString() : '—');

const statusColour = (s: string) =>
  ['UP', 'CONNECTED', 'REACHABLE', 'OK'].includes(s) ? 'text-emerald-700'
    : ['DOWN', 'UNREACHABLE', 'FAILED', 'INVALID', 'CONNECTED_INVALID_DATA'].includes(s) ? 'text-rose-700'
      : 'text-slate-600';

export const DataOperationsPage: React.FC = () => {
  const { user } = useAuth();
  const canRefresh = user?.role === 'SYSTEM_ADMIN' || user?.role === 'DATA_MANAGER';
  const [overview, setOverview] = useState<DataOpsOverview | null>(null);
  const [datasets, setDatasets] = useState<DatasetInventoryRow[]>([]);
  const [runs, setRuns] = useState<IngestionRunView[]>([]);
  const [events, setEvents] = useState<IngestionEventView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [probing, setProbing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const lastId = useRef(0);

  const load = useCallback(async (live = false) => {
    try {
      const [o, d, r, e] = await Promise.all([
        api.dataOpsOverview(live), api.dataOpsDatasets(), api.dataOpsRuns(15), api.dataOpsEvents(lastId.current),
      ]);
      if (!o.success) { setError((o as unknown as { error?: string }).error ?? 'Data Operations is not available to your role.'); return; }
      setError(null);
      setOverview(o);
      if (d.success) setDatasets(d.datasets);
      if (r.success) setRuns(r.runs);
      if (e.success && e.events.length) {
        setEvents(prev => (lastId.current === 0 ? e.events : [...prev, ...e.events]).slice(-200));
        lastId.current = e.last_id;
      }
    } catch {
      setError('Backend API is unreachable. No status can be shown.');
    }
  }, []);

  useEffect(() => {
    void load();
    const t = setInterval(() => void load(), POLL_MS);   // real polling of backend state/events
    return () => clearInterval(t);
  }, [load]);

  const refresh = async (key: string) => {
    setMessage(null);
    const res = await api.dataOpsRefresh(key);
    setMessage(res.success ? `Retrieval started for ${key} (run #${res.run_id}).` : (res.error ?? 'Could not start retrieval.'));
    void load();
  };
  const probe = async () => { setProbing(true); await load(true); setProbing(false); };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">Data Operations</h1>
          <p className="text-xs text-pravah-slate">
            Live backend status, provider connectivity and ingestion activity. Every value is read from the backend; nothing is simulated.
          </p>
        </div>
        <button onClick={probe} disabled={probing}
          className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-xl border border-pravah-teal/40 text-pravah-teal hover:bg-pravah-aqua/40 disabled:opacity-50">
          {probing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radio className="w-3.5 h-3.5" />} Run live connectivity probe
        </button>
      </div>

      {error && (
        <div role="alert" className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}
      {message && <div className="p-3 rounded-xl bg-white border border-slate-200 text-xs text-pravah-navy">{message}</div>}

      {!overview && !error && <Loader2 className="w-5 h-5 animate-spin text-pravah-slate" aria-label="Loading" />}

      {overview && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs space-y-1">
              <div className="flex items-center gap-2 font-bold text-pravah-navy"><Server className="w-4 h-4" /> Flask API</div>
              <div className={`font-black ${statusColour(overview.api.status)}`}>{overview.api.status}</div>
              <div className="text-pravah-slate">Environment: {overview.api.environment} · up {Math.floor(overview.api.uptime_seconds / 60)} min</div>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs space-y-1">
              <div className="flex items-center gap-2 font-bold text-pravah-navy"><Database className="w-4 h-4" /> Database</div>
              <div className={`font-black ${statusColour(overview.database.status)}`}>{overview.database.status}</div>
              <div className="text-pravah-slate">
                {overview.database.backend} {overview.database.server_version ?? ''} · {overview.database.latency_ms} ms
                {overview.database.postgis ? ` · PostGIS: ${overview.database.postgis}` : ''}
              </div>
              {overview.database.development_fallback && (
                <div className="text-amber-700 font-semibold">Development SQLite fallback — not production data.</div>
              )}
              {overview.database.error && <div className="text-rose-700">{overview.database.error}</div>}
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs space-y-1">
              <div className="font-bold text-pravah-navy">Ingestion</div>
              <div className="text-pravah-slate">Runs: {overview.ingestion.total_runs} · failed: {overview.ingestion.failed_runs} · running: {overview.ingestion.running}</div>
              <div className="text-pravah-slate">Last successful retrieval: {fmt(overview.ingestion.last_successful_retrieval)}</div>
              <div className="text-pravah-slate">Scheduler: {overview.ingestion.scheduler}</div>
            </div>
          </div>

          <section className="p-4 rounded-2xl bg-white border border-slate-200 space-y-3">
            <h2 className="text-sm font-black text-pravah-navy">Data registry & provider status</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[10px] uppercase text-pravah-slate">
                  <tr>
                    <th className="py-2 pr-3">Provider / dataset</th><th className="pr-3">Class</th><th className="pr-3">Connectivity</th>
                    <th className="pr-3">Last success</th><th className="pr-3">Observation</th><th className="pr-3">Validation</th><th />
                  </tr>
                </thead>
                <tbody>
                  {overview.sources.map(s => (
                    <tr key={s.key} className="border-t border-slate-100 align-top">
                      <td className="py-2 pr-3">
                        <div className="font-bold text-pravah-navy">{s.provider}</div>
                        <div className="text-pravah-slate">{s.name}</div>
                        <div className="text-[10px] text-slate-400">{s.licence}</div>
                        {!s.configured && (
                          <div className="text-[10px] text-amber-700 font-semibold">
                            Access required: set {s.missing_credentials.join(', ')}
                          </div>
                        )}
                        {s.last_error && <div className="text-[10px] text-rose-700">{s.last_error}</div>}
                      </td>
                      <td className="pr-3"><ClassificationBadge value={s.classification} /></td>
                      <td className={`pr-3 font-semibold ${statusColour(s.connectivity)}`}>
                        {s.connectivity.replace(/_/g, ' ')}
                        {s.probe_detail && <div className="font-normal text-[10px] text-slate-500">{s.probe_detail}</div>}
                      </td>
                      <td className="pr-3">{fmt(s.last_success_at)}</td>
                      <td className="pr-3">{s.observation_date ?? '—'}</td>
                      <td className="pr-3">
                        {s.validation_status}{s.record_count != null ? ` · ${s.record_count} rec.` : ''}
                        {(s.validation?.warnings ?? []).map((w, i) => <div key={i} className="text-[10px] text-amber-700">{w}</div>)}
                      </td>
                      <td>
                        {canRefresh && (
                          <button onClick={() => void refresh(s.key)} title="Retrieve now"
                            className="p-1.5 rounded-lg border border-slate-200 hover:bg-pravah-aqua/40">
                            <RefreshCw className="w-3.5 h-3.5 text-pravah-teal" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <section className="p-4 rounded-2xl bg-white border border-slate-200 space-y-3">
        <h2 className="text-sm font-black text-pravah-navy">Dataset availability & gaps</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="text-[10px] uppercase text-pravah-slate">
              <tr><th className="py-2 pr-3">Dataset</th><th className="pr-3">State</th><th className="pr-3">In use</th><th>Note</th></tr>
            </thead>
            <tbody>
              {datasets.map(d => (
                <tr key={d.id} className="border-t border-slate-100 align-top">
                  <td className="py-2 pr-3 font-bold text-pravah-navy">{d.label}</td>
                  <td className="pr-3"><ClassificationBadge value={d.state} /></td>
                  <td className="pr-3">{d.records_in_use}{d.unverified_records ? ` (${d.unverified_records} unverified)` : ''}</td>
                  <td className="text-pravah-slate">{d.note}</td>
                </tr>
              ))}
              {datasets.length === 0 && <tr><td colSpan={4} className="py-3 text-pravah-slate">No inventory available.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="p-4 rounded-2xl bg-white border border-slate-200 space-y-2">
          <h2 className="text-sm font-black text-pravah-navy">Recent ingestion runs</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px] text-left">
              <thead className="text-[10px] uppercase text-pravah-slate">
                <tr><th className="py-1 pr-2">#</th><th className="pr-2">Source</th><th className="pr-2">Status</th><th className="pr-2">HTTP</th><th className="pr-2">ms</th><th>Started</th></tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id} className="border-t border-slate-100" title={r.error ?? ''}>
                    <td className="py-1 pr-2">{r.id}</td><td className="pr-2">{r.source_key}</td>
                    <td className={`pr-2 font-semibold ${statusColour(r.status)}`}>{r.status}</td>
                    <td className="pr-2">{r.http_status ?? '—'}</td><td className="pr-2">{r.duration_ms ?? '—'}</td>
                    <td>{fmt(r.started_at)}</td>
                  </tr>
                ))}
                {runs.length === 0 && <tr><td colSpan={6} className="py-2 text-pravah-slate">No ingestion has run yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section className="p-4 rounded-2xl bg-pravah-navy text-slate-100 space-y-2">
          <h2 className="text-sm font-black">Backend execution events</h2>
          <div className="h-56 overflow-y-auto font-mono text-[11px] space-y-0.5" aria-live="polite">
            {events.map(e => (
              <div key={e.id} className={e.level === 'ERROR' ? 'text-rose-300' : e.level === 'WARN' ? 'text-amber-300' : ''}>
                <span className="text-slate-400">{new Date(e.at).toLocaleTimeString()}</span> [{e.source_key}] {e.message}
              </div>
            ))}
            {events.length === 0 && <div className="text-slate-400">No backend events recorded yet.</div>}
          </div>
        </section>
      </div>
    </div>
  );
};
