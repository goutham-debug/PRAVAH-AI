import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Loader2, FileText } from 'lucide-react';
import { api } from '../../api/client';
import { useAssessment } from '../../context/AssessmentContext';
import { PravahMap } from '../../components/map/PravahMap';
import { Legend } from '../../components/common/Legend';
import { RoadEdge, RoadNode, ScenarioComparisonResponse } from '../../types';

type Stage = 'baseline' | 'disrupted' | 'restored';

const RAINFALL = [
  { id: 'NORMAL', label: 'Normal', mm: 25 },
  { id: 'HEAVY', label: 'Heavy', mm: 85 },
  { id: 'EXTREME', label: 'Extreme', mm: 135 },
  { id: 'CLOUDBURST', label: 'Cloudburst', mm: 195 },
];

export const ScenarioSimulatorPage: React.FC = () => {
  const assessment = useAssessment();
  const [roads, setRoads] = useState<RoadEdge[]>([]);
  const [nodes, setNodes] = useState<RoadNode[]>([]);
  const [geoData, setGeoData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [rainfall, setRainfall] = useState('HEAVY');
  const [closed, setClosed] = useState<string[]>([]);
  const [restored, setRestored] = useState<string[]>([]);
  const [result, setResult] = useState<ScenarioComparisonResponse | null>(null);
  const [stage, setStage] = useState<Stage>('disrupted');
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState('');
  const [ranAt, setRanAt] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        const [cand, geo, topo] = await Promise.all([
          api.getCandidateDisruptions(), api.getNeighbourhoodsGeoJSON(), api.getRoadTopology(),
        ]);
        if (cand.success) setRoads(cand.candidate_roads || []);
        if (geo) setGeoData(geo);
        if (topo.success) setNodes(topo.nodes || []);
      } catch {
        setLoadError('Could not load road network.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const toggle = (list: string[], set: (v: string[]) => void, id: string) =>
    set(list.includes(id) ? list.filter(x => x !== id) : [...list, id]);

  const run = async () => {
    setRunError('');
    setRunning(true);
    try {
      const res = await api.compareScenarios({ rainfall_scenario: rainfall, closed_road_ids: closed, restored_road_ids: restored });
      if (res.success) {
        setResult(res);
        setStage('disrupted');
        setRanAt(new Date().toLocaleString());
      } else {
        setRunError(res.error || 'Analysis failed.');
      }
    } catch {
      setRunError('Cannot reach the server.');
    } finally {
      setRunning(false);
    }
  };

  const stageData = result?.stages[stage];
  const mapClosures = useMemo(() => {
    if (!result) return closed;
    if (stage === 'baseline') return [];
    if (stage === 'restored') return result.disruptions_applied.filter(r => !result.roads_restored.includes(r));
    return result.disruptions_applied;
  }, [result, stage, closed]);

  const riskDict: Record<string, any> = {};
  (stageData as any)?.neighbourhood_assessment?.forEach((n: any) => { riskDict[n.neighbourhood_id] = n; });
  const m = result?.comparison_matrix;

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-5 h-5 animate-spin text-pravah-slate" /></div>;
  if (loadError || roads.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 text-sm text-pravah-navy">
        <h1 className="font-bold text-base mb-1">Scenario Analysis</h1>
        <p className="text-pravah-slate">
          {loadError || 'No road network is loaded. Scenario analysis requires a road network dataset.'}
        </p>
      </div>
    );
  }

  const row = (label: string, a: React.ReactNode, b: React.ReactNode, c: React.ReactNode) => (
    <tr className="border-t border-slate-100">
      <td className="py-2 px-3 font-semibold text-pravah-navy">{label}</td>
      <td className="py-2 px-3">{a}</td><td className="py-2 px-3">{b}</td><td className="py-2 px-3">{c}</td>
    </tr>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-bold text-pravah-navy">Scenario Analysis</h1>
          <p className="text-xs text-pravah-slate">Compare baseline, selected closures and restoration. All results are MODELLED.</p>
        </div>
        {ranAt && <span className="text-[11px] text-pravah-slate">Computed {ranAt}</span>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          {result && (
            <div className="flex gap-1.5 text-xs" role="tablist" aria-label="Scenario stage">
              {([['baseline', 'Baseline'], ['disrupted', 'Closures'], ['restored', 'After restoration']] as [Stage, string][]).map(([id, label]) => (
                <button key={id} role="tab" aria-selected={stage === id} onClick={() => setStage(id)}
                  className={`px-3 py-1.5 rounded-lg font-semibold border ${stage === id ? 'bg-pravah-teal text-white border-pravah-teal' : 'bg-white text-pravah-navy border-slate-200 hover:bg-slate-50'}`}>
                  {label}
                </button>
              ))}
            </div>
          )}
          <PravahMap neighbourhoodsGeoJSON={geoData} riskAssessments={riskDict} roads={roads as any} nodes={nodes}
            closedRoadIds={mapClosures} height="520px" />
          <Legend />

          {m && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-pravah-slate">
                  <tr><th className="py-2 px-3">Measure (MODELLED)</th><th className="py-2 px-3">Baseline</th><th className="py-2 px-3">Closures</th><th className="py-2 px-3">Restored</th></tr>
                </thead>
                <tbody>
                  {row('Network integrity', `${m.network_integrity_pct.baseline}%`, `${m.network_integrity_pct.disrupted}%`, `${m.network_integrity_pct.restored}%`)}
                  {row('Isolated neighbourhoods', m.isolated_wards_count.baseline, m.isolated_wards_count.disrupted, m.isolated_wards_count.restored)}
                  {row('Unreachable facilities', m.unreachable_facilities.baseline, m.unreachable_facilities.disrupted, m.unreachable_facilities.restored)}
                  {row('Neighbourhoods without trauma access', m.wards_losing_trauma_access.baseline, m.wards_losing_trauma_access.disrupted, m.wards_losing_trauma_access.restored)}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-4">
            <fieldset>
              <legend className="text-xs font-bold text-pravah-navy mb-1.5">Rainfall assumption</legend>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                {RAINFALL.map(r => (
                  <button key={r.id} onClick={() => setRainfall(r.id)} aria-pressed={rainfall === r.id}
                    className={`py-1.5 px-2 rounded-lg text-left font-semibold border ${rainfall === r.id ? 'border-pravah-teal bg-pravah-aqua text-pravah-teal-dark' : 'border-slate-200 text-slate-700 hover:bg-slate-50'}`}>
                    {r.label} <span className="font-normal text-slate-500">{r.mm} mm</span>
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-pravah-slate mt-1">Assumed value, not an observation.</p>
            </fieldset>

            <fieldset>
              <legend className="text-xs font-bold text-pravah-navy mb-1.5">Road closures ({closed.length})</legend>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {roads.map(r => (
                  <label key={r.id} className={`flex items-start gap-2 p-1.5 rounded-lg border text-xs cursor-pointer ${closed.includes(r.id) ? 'border-rose-300 bg-rose-50' : 'border-slate-100 hover:bg-slate-50'}`}>
                    <input type="checkbox" checked={closed.includes(r.id)} onChange={() => toggle(closed, setClosed, r.id)} className="mt-0.5" />
                    <span><span className="font-semibold">{r.name}</span> <span className="text-slate-500">{r.length_km} km</span></span>
                  </label>
                ))}
              </div>
            </fieldset>

            {closed.length > 0 && (
              <fieldset>
                <legend className="text-xs font-bold text-pravah-navy mb-1.5">Restore (optional)</legend>
                <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                  {closed.map(id => {
                    const r = roads.find(x => x.id === id);
                    return (
                      <label key={id} className="flex items-center gap-2 text-xs">
                        <input type="checkbox" checked={restored.includes(id)} onChange={() => toggle(restored, setRestored, id)} />
                        {r?.name ?? id}
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            )}

            {runError && <p role="alert" className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-2">{runError}</p>}
            <button onClick={run} disabled={running || closed.length === 0}
              className="w-full py-2 rounded-lg bg-pravah-teal text-white font-semibold text-xs hover:bg-pravah-teal-dark disabled:opacity-50 flex items-center justify-center gap-2">
              {running ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Run analysis
            </button>
            {closed.length === 0 && <p className="text-[11px] text-pravah-slate">Select at least one closure.</p>}
          </div>

          {result && (
            <button
              onClick={() => assessment.apply(result.disruptions_applied.filter(r => !result.roads_restored.includes(r)), rainfall)}
              className="w-full py-2 rounded-lg border border-pravah-teal text-pravah-teal text-xs font-semibold hover:bg-pravah-aqua"
            >
              Apply closures to all modules
            </button>
          )}
          <Link to="/authority/sitrep" className="flex items-center gap-1.5 text-xs font-semibold text-pravah-teal hover:underline">
            <FileText className="w-3.5 h-3.5" /> Situation reports
          </Link>
        </div>
      </div>
    </div>
  );
};
