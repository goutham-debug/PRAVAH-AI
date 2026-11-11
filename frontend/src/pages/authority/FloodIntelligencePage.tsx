import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { RiskBadge } from '../../components/common/RiskBadge';
import { CloudRain, Sliders, Info, HelpCircle, CheckCircle2, AlertTriangle, Database } from 'lucide-react';

export const FloodIntelligencePage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [rainfallScenario, setRainfallScenario] = useState('HEAVY');
  const [results, setResults] = useState<any[]>([]);
  const [formulaMeta, setFormulaMeta] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssessment = async (scen: string) => {
    setLoading(true);
    setError(null);
    try {
      const [assessRes, metaRes] = await Promise.all([
        api.assessFlood(scen, closedRoads),
        api.getFloodFormula()
      ]);
      if (assessRes.success) {
        setResults(assessRes.results || []);
      } else {
        setError("Failed to retrieve flood assessment results from backend.");
      }
      if (metaRes.success) setFormulaMeta(metaRes);
    } catch (e: any) {
      console.warn("Failed fetching flood assessment:", e);
      setError(e?.message || "Failed connecting to flood assessment service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment(rainfallScenario);
  }, [rainfallScenario, closedRoads]);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
            Deterministic Flood Intelligence Engine
          </h1>
          <p className="text-xs text-pravah-slate">
            Explainable flood susceptibility screening index (MODELLED). Not a 1D/2D hydrodynamic water depth simulation.
          </p>
        </div>

        {/* Rainfall Selector Buttons */}
        <div className="flex gap-1.5 bg-white p-1 rounded-2xl border border-pravah-teal/20 text-xs font-bold shadow-sm">
          {['NORMAL', 'HEAVY', 'EXTREME', 'CLOUDBURST'].map(scen => (
            <button
              key={scen}
              onClick={() => setRainfallScenario(scen)}
              className={`px-3 py-1.5 rounded-xl transition-all ${
                rainfallScenario === scen
                  ? 'bg-pravah-teal text-white shadow-sm'
                  : 'text-pravah-navy hover:bg-pravah-aqua/50'
              }`}
            >
              {scen}
            </button>
          ))}
        </div>
      </div>

      {/* Formula & Explainability Banner */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-pravah-teal">
              Deterministic Screening Equation (Stage 2)
            </span>
            <div className="text-2xl font-black text-pravah-navy tracking-tight mt-0.5">
              R = 0.35P + 0.20E + 0.25H + 0.20D
            </div>
            <p className="text-xs text-pravah-slate mt-1 max-w-xl">
              Normalized index (0 to 100). Combines dynamic rainfall intensity (P), terrain elevation vulnerability (E), empirical historical flood history (H), and stormwater drainage deficit/disruptions (D).
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2.5 rounded-xl bg-pravah-aqua/50 border border-pravah-teal/20">
              <div className="font-extrabold text-pravah-teal-dark">P (35%)</div>
              <div className="text-[11px] text-pravah-slate font-medium">Rainfall Intensity</div>
            </div>
            <div className="p-2.5 rounded-xl bg-pravah-aqua/50 border border-pravah-teal/20">
              <div className="font-extrabold text-pravah-teal-dark">E (20%)</div>
              <div className="text-[11px] text-pravah-slate font-medium">Elevation Vuln.</div>
            </div>
            <div className="p-2.5 rounded-xl bg-pravah-aqua/50 border border-pravah-teal/20">
              <div className="font-extrabold text-pravah-teal-dark">H (25%)</div>
              <div className="text-[11px] text-pravah-slate font-medium">Historical Flood</div>
            </div>
            <div className="p-2.5 rounded-xl bg-pravah-aqua/50 border border-pravah-teal/20">
              <div className="font-extrabold text-pravah-teal-dark">D (20%)</div>
              <div className="text-[11px] text-pravah-slate font-medium">Drainage Deficit</div>
            </div>
          </div>
        </div>

        {/* Risk Classification Scale & Data Source Provenance */}
        <div className="flex flex-wrap items-center justify-between text-xs gap-3 pt-1">
          <div className="flex items-center gap-3">
            <span className="font-bold text-pravah-navy">Classification Tiers:</span>
            <div className="flex flex-wrap gap-2.5">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Low (&lt;30)</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Moderate (30–55)</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span> High (55–75)</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-600"></span> Severe (&gt;75)</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
            <Database className="w-3.5 h-3.5 text-pravah-teal" />
            <span>Authorised Sources: Open-Meteo • CartoDEM/SRTM • BBMP Inundation Register</span>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Ward Ranking Table */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-black text-pravah-navy">
            Ward Vulnerability Rankings ({rainfallScenario} Downpour)
          </h2>
          <span className="text-xs text-pravah-slate">
            {loading ? 'Computing scores...' : `Ranked by deterministic score R (${results.length} wards)`}
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400 animate-pulse">
            Calculating weighted flood susceptibility metrics...
          </div>
        ) : results.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No neighbourhood records found for assessment.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                  <th className="py-3 px-3">Rank & Ward</th>
                  <th className="py-3 px-3">Tier</th>
                  <th className="py-3 px-3 font-extrabold">Score (R)</th>
                  <th className="py-3 px-2">Rain (P) [35%]</th>
                  <th className="py-3 px-2">Elevation (E) [20%]</th>
                  <th className="py-3 px-2">Hazard (H) [25%]</th>
                  <th className="py-3 px-2">Drain (D) [20%]</th>
                  <th className="py-3 px-3">Primary Driver</th>
                  <th className="py-3 px-3">Exposed Pop</th>
                  <th className="py-3 px-3">Catchment Feature</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {results.map((item, idx) => (
                  <tr key={item.neighbourhood_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-3 font-bold text-pravah-navy">
                      <span className="w-5 h-5 rounded-full bg-slate-100 text-pravah-slate text-[10px] font-bold inline-flex items-center justify-center mr-2">
                        {idx + 1}
                      </span>
                      {item.name}
                    </td>
                    <td className="py-3 px-3">
                      <RiskBadge level={item.classification} size="sm" />
                    </td>
                    <td className="py-3 px-3 font-black text-sm text-pravah-navy">
                      {item.risk_score !== null && item.risk_score !== undefined ? item.risk_score : 'N/A'}
                    </td>
                    <td className="py-3 px-2 text-pravah-slate">
                      {item.components?.P?.value} <span className="text-[10px] text-slate-400">({item.components?.P?.weighted_contribution})</span>
                    </td>
                    <td className="py-3 px-2 text-pravah-slate">
                      {item.components?.E?.value} <span className="text-[10px] text-slate-400">({item.components?.E?.weighted_contribution})</span>
                    </td>
                    <td className="py-3 px-2 text-pravah-slate">
                      {item.components?.H?.value} <span className="text-[10px] text-slate-400">({item.components?.H?.weighted_contribution})</span>
                    </td>
                    <td className="py-3 px-2 text-pravah-slate">
                      {item.components?.D?.value} <span className="text-[10px] text-slate-400">({item.components?.D?.weighted_contribution})</span>
                    </td>
                    <td className="py-3 px-3 font-semibold text-pravah-teal-dark text-[11px]">
                      {item.primary_driver?.name ? (
                        <span>{item.primary_driver.name.split(' ')[0]} ({item.primary_driver.pct_of_total}%)</span>
                      ) : 'Balanced'}
                    </td>
                    <td className="py-3 px-3 font-bold text-rose-600">
                      {Number(item.exposed_population || 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-pravah-slate text-[11px] truncate max-w-xs">
                      {item.lake_proximity || `${item.elevation_m}m elevated plateau`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
