import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { MetricCard } from '../../components/common/MetricCard';
import { RiskBadge } from '../../components/common/RiskBadge';
import { Activity, Users, AlertTriangle, GitFork, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ImpactAnalysisPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [scenarioRes, setScenarioRes] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchImpact = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.simulateScenario({
          rainfall_scenario: 'HEAVY',
          active_disruptions: closedRoads
        });
        if (res.success) {
          setScenarioRes(res.scenario);
        } else {
          setError("Failed retrieving scenario impact data.");
        }
      } catch (e: any) {
        console.warn("Failed fetching impact analysis:", e);
        setError(e?.message || "Error connecting to impact analysis service.");
      } finally {
        setLoading(false);
      }
    };
    fetchImpact();
  }, [closedRoads]);

  const nbs = scenarioRes?.neighbourhood_assessment || [];
  const conn = scenarioRes?.connectivity;

  // Real aggregate population metrics from backend response
  const totalMonitoredPop = nbs.reduce((acc: number, n: any) => acc + (n.population || 0), 0);
  const totalExposedPop = nbs.reduce((acc: number, n: any) => acc + (n.exposed_population || 0), 0);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
          Neighbourhood Impact & Population Exposure Analysis
        </h1>
        <p className="text-xs text-pravah-slate">
          Network disruption impact on administrative ward accessibility and census population exposure (MODELLED).
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Dynamic Aggregate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          title="Monitored Ward Population"
          value={loading ? "..." : Number(totalMonitoredPop).toLocaleString()}
          subtitle="Sum of monitored BBMP wards"
          colorScheme="teal"
        />
        <MetricCard
          title="Directly Exposed Population"
          value={loading ? "..." : Number(totalExposedPop).toLocaleString()}
          subtitle="High & Severe risk zones"
          colorScheme="amber"
        />
        <MetricCard
          title="Network Graph Components"
          value={loading ? "..." : (conn?.num_connected_components || 1)}
          subtitle={conn?.num_connected_components > 1 ? "Graph split into disconnected islands" : "Single unified component"}
          colorScheme={conn?.num_connected_components > 1 ? 'red' : 'teal'}
        />
        <MetricCard
          title="Isolated Ward Enclaves"
          value={loading ? "..." : (conn?.isolated_neighbourhood_ids?.length || 0)}
          subtitle="Complete loss of road egress"
          colorScheme={conn?.isolated_neighbourhood_ids?.length ? 'red' : 'teal'}
        />
      </div>

      {/* Ward Cards */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-black text-pravah-navy">
            Population Exposure by Ward Polygon
          </h2>
          <span className="text-xs text-pravah-slate">
            {loading ? 'Evaluating...' : `${nbs.length} Monitored Wards`}
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400 animate-pulse">
            Analyzing graph connectivity and ward exposure...
          </div>
        ) : nbs.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No neighbourhood exposure data available.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {nbs.map((nb: any) => (
              <div
                key={nb.neighbourhood_id}
                className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-pravah-navy">{nb.name}</span>
                  <RiskBadge level={nb.classification} size="sm" />
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between text-pravah-slate">
                    <span>Total Population:</span>
                    <span className="font-bold text-pravah-navy">{Number(nb.population).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-pravah-slate">
                    <span>Estimated Exposed:</span>
                    <span className="font-bold text-rose-600">{Number(nb.exposed_population).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-pravah-slate">
                    <span>Exposure Ratio:</span>
                    <span className="font-semibold text-pravah-navy">
                      {Math.round((nb.exposed_population / Math.max(1, nb.population)) * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-pravah-slate">
                    <span>Vulnerability Score (R):</span>
                    <span className="font-bold text-pravah-navy">{nb.risk_score}</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200 text-[11px] text-pravah-slate truncate">
                  Elevation: {nb.elevation_m}m • {nb.lake_proximity || 'Elevated plateau'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
