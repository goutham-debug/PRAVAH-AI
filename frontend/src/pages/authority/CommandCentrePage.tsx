import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { PravahMap } from '../../components/map/PravahMap';
import { MetricCard } from '../../components/common/MetricCard';
import { Legend } from '../../components/common/Legend';
import { RiskBadge } from '../../components/common/RiskBadge';
import {
  ShieldAlert,
  AlertTriangle,
  Building,
  HeartPulse,
  LifeBuoy,
  GitFork,
  Radio,
  ArrowRight,
  TrendingDown,
  RefreshCw
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const CommandCentrePage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [geoData, setGeoData] = useState<any>(null);
  const [roads, setRoads] = useState<any[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);
  const [shelters, setShelters] = useState<any[]>([]);
  const [rescueTeams, setRescueTeams] = useState<any[]>([]);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [scenarioRes, setScenarioRes] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const pct = (v: any) => (typeof v === 'number' ? `${v}%` : 'n/a');
  const num = (v: any) => (typeof v === 'number' ? v.toLocaleString() : 'n/a');

  const loadData = async () => {
    setLoading(true);
    try {
      const [geo, topo, facRes, shRes, rtRes, incRes, scenRes] = await Promise.all([
        api.getNeighbourhoodsGeoJSON(),
        api.getRoadTopology(),
        api.getFacilities(),
        api.listShelters(),
        api.listRescueTeams(),
        api.listIncidents(),
        api.simulateScenario({
          rainfall_scenario: 'HEAVY',
          active_disruptions: closedRoads,
          scenario_name: 'Baseline overview'
        })
      ]);

      if (geo) setGeoData(geo);
      if (topo.success) {
        setRoads(topo.edges || []);
        setNodes(topo.nodes || []);
      }
      if (facRes.success) setFacilities(facRes.facilities || []);
      if (shRes.success) setShelters(shRes.shelters || []);
      if (rtRes.success) setRescueTeams(rtRes.teams || []);
      if (incRes.success) setIncidents(incRes.incidents || []);
      if (scenRes.success) setScenarioRes(scenRes.scenario);
    } catch (e) {
      console.warn("Failed loading command centre data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const riskDict: Record<string, any> = {};
  if (scenarioRes?.neighbourhood_assessment) {
    scenarioRes.neighbourhood_assessment.forEach((item: any) => {
      riskDict[item.neighbourhood_id] = item;
    });
  }

  return (
    <div className="space-y-5">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
            Command Centre
          </h1>
          <p className="text-xs text-pravah-slate">
            Road connectivity, facility access and assessment summary.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-pravah-navy hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-pravah-teal ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link
            to="/authority/scenario"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-pravah-teal text-white text-xs font-bold shadow-md hover:bg-pravah-teal-dark transition-colors"
          >
            Scenario analysis
          </Link>
        </div>
      </div>

      {/* KPI strip: every value comes from the backend assessment; "n/a" when not returned */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard title="Network Integrity" value={pct(scenarioRes?.connectivity?.network_integrity_pct)}
          subtitle="MODELLED" colorScheme="teal" />
        <MetricCard title="Road Closures Applied" value={closedRoads.length} subtitle="Current assessment"
          colorScheme={closedRoads.length ? 'red' : 'slate'} />
        <MetricCard title="Exposed Population" value={num(scenarioRes?.total_exposed_population)}
          subtitle="Unverified population data" colorScheme="amber" />
        <MetricCard title="Isolated Neighbourhoods" value={num(scenarioRes?.connectivity?.isolated_neighbourhood_ids?.length)}
          subtitle="MODELLED"
          colorScheme={scenarioRes?.connectivity?.isolated_neighbourhood_ids?.length ? 'red' : 'teal'} />
        <MetricCard title="Hospital Access" value={pct(scenarioRes?.facility_accessibility?.overall_accessibility_pct)}
          subtitle="Road reachability only" colorScheme="blue" />
        <MetricCard title="Response Teams" value={rescueTeams.length || 'n/a'} subtitle="Registered" colorScheme="slate" />
      </div>

      {/* Main Map + Right Intelligence Console */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Large Central Map */}
        <div className="lg:col-span-3 space-y-3">
          <PravahMap
            neighbourhoodsGeoJSON={geoData}
            riskAssessments={riskDict}
            roads={roads}
            nodes={nodes}
            closedRoadIds={closedRoads}
            facilities={facilities}
            shelters={shelters}
            rescueTeams={rescueTeams}
            incidents={incidents}
            height="590px"
          />

          <div className="flex flex-wrap items-center gap-4 p-3 rounded-xl bg-white border border-slate-200 text-xs text-pravah-slate">
            <span>Neighbourhoods: <strong>{geoData?.features?.length ?? 0}</strong></span>
            <span>Facilities: <strong>{facilities.length}</strong></span>
            <span>Shelters: <strong>{shelters.length}</strong></span>
            <span>Incidents: <strong>{incidents.length}</strong></span>
          </div>
        </div>

        {/* Right Intelligence Panel */}
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-pravah-navy uppercase tracking-wider flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-pravah-slate" /> Closures applied
              </span>
              <span className="text-[10px] font-bold text-pravah-slate">{closedRoads.length}</span>
            </div>
            {closedRoads.length === 0 ? (
              <p className="text-xs text-pravah-slate">None. Baseline network shown. Apply verified closures from Scenario Analysis.</p>
            ) : (
              <ul className="space-y-1 text-xs">
                {closedRoads.map((id: string) => (
                  <li key={id} className="p-2 rounded-lg bg-rose-50 border border-rose-100 font-semibold text-rose-900">
                    {roads.find((r: any) => r.id === id)?.name ?? id}
                  </li>
                ))}
              </ul>
            )}
            <Link to="/authority/scenario" className="text-xs font-bold text-pravah-teal hover:underline flex items-center justify-between pt-1">
              <span>Scenario analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Quick SITREP Highlights */}
          {scenarioRes?.situation_report && (
            <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold uppercase tracking-wider text-pravah-navy">
                  Summary
                </span>
                <span className="text-[10px] text-pravah-slate">MODELLED</span>
              </div>
              <p className="text-xs text-pravah-slate leading-relaxed">
                {scenarioRes.situation_report.executive_summary?.slice(0, 220)}...
              </p>
              <Link
                to="/authority/sitrep"
                className="inline-flex items-center gap-1 text-xs font-bold text-pravah-teal hover:underline"
              >
                Open situation report <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Map Legend */}
          <Legend />
        </div>
      </div>
    </div>
  );
};
