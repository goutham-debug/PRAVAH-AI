import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { FileText, Download, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';

export const SituationReportsPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [sitrep, setSitrep] = useState<any>(null);
  const [rainfallScenario, setRainfallScenario] = useState('HEAVY');
  const [loading, setLoading] = useState(true);

  const fetchSitrep = async (scen: string) => {
    setLoading(true);
    try {
      const res = await api.generateSitrep(scen, closedRoads);
      if (res.success && res.situation_report) {
        setSitrep(res.situation_report);
      }
    } catch (e) {
      console.warn("Failed generating situation report:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSitrep(rainfallScenario);
  }, [rainfallScenario]);

  const handleDownloadMarkdown = () => {
    if (!sitrep) return;
    const blob = new Blob([sitrep.markdown_content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `PRAVAH_AI_SITREP_${sitrep.report_id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
            Automated Operational Situation Reports (SITREPs)
          </h1>
          <p className="text-xs text-pravah-slate">
            Deterministic, grounded situation briefs generated strictly from executed scenario metrics and network audits.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={rainfallScenario}
            onChange={(e) => setRainfallScenario(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-pravah-navy bg-white focus:outline-none focus:border-pravah-teal shadow-sm"
          >
            <option value="NORMAL">Normal Scenario (25mm)</option>
            <option value="HEAVY">Heavy Monsoon Scenario (85mm)</option>
            <option value="EXTREME">Extreme Convective Storm (135mm)</option>
            <option value="CLOUDBURST">Cloudburst Emergency (195mm)</option>
          </select>

          <button
            onClick={handleDownloadMarkdown}
            disabled={!sitrep}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-pravah-teal text-white text-xs font-bold shadow-md hover:bg-pravah-teal-dark transition-all disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            Export Markdown
          </button>
        </div>
      </div>

      {sitrep && (
        <div className="p-8 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-6 font-sans">
          {/* Header metadata */}
          <div className="pb-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-pravah-teal">
                Official Incident Command Document
              </span>
              <h2 className="text-xl font-black text-pravah-navy">{sitrep.scenario_name}</h2>
              <div className="text-xs text-pravah-slate mt-0.5">
                Report ID: <strong>{sitrep.report_id}</strong> • Generated: {sitrep.timestamp}
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-pravah-teal/10 text-pravah-teal border border-pravah-teal/20 self-start sm:self-auto">
              MODELLED
            </span>
          </div>

          {/* Key Metrics Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-center">
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-pravah-slate font-bold uppercase">Network Integrity</div>
              <div className="text-xl font-extrabold text-pravah-navy mt-0.5">{sitrep.metrics?.network_integrity_pct}%</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-pravah-slate font-bold uppercase">Road Disruptions</div>
              <div className="text-xl font-extrabold text-rose-600 mt-0.5">{sitrep.metrics?.disruptions_count} segments</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-pravah-slate font-bold uppercase">Exposed Population</div>
              <div className="text-xl font-extrabold text-pravah-navy mt-0.5">{Number(sitrep.metrics?.exposed_population).toLocaleString()}</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="text-[10px] text-pravah-slate font-bold uppercase">Shelter Utilization</div>
              <div className="text-xl font-extrabold text-pravah-teal mt-0.5">{sitrep.metrics?.shelter_utilization_pct}%</div>
            </div>
          </div>

          {/* Narrative Executive Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-pravah-navy">
              Executive Operational Assessment
            </h3>
            <div className="p-4 rounded-2xl bg-pravah-aqua/30 border border-pravah-teal/20 text-xs text-pravah-navy leading-relaxed whitespace-pre-line font-medium">
              {sitrep.executive_summary}
            </div>
          </div>

          {/* Priority Interventions Table */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-pravah-navy">
              Recommended Tactical Interventions
            </h3>

            <div className="space-y-2">
              {(sitrep.recommendations || []).map((rec: any, idx: number) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                        rec.priority.includes('CRITICAL') ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {rec.priority}
                      </span>
                      <span className="font-bold text-pravah-navy">{rec.action}</span>
                    </div>
                    <div className="text-[11px] text-pravah-slate">
                      Target Corridor: <strong>{rec.target_zone}</strong>
                    </div>
                  </div>
                  <div className="text-[11px] text-pravah-teal font-semibold text-right sm:max-w-xs">
                    Impact: {rec.expected_impact}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
