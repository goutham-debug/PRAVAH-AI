import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { RoadEdge, RoadNode } from '../../types';
import { GitFork, MapPin, AlertTriangle, ShieldCheck, ArrowRight, Network, Split } from 'lucide-react';

export const RoadIntelligencePage: React.FC = () => {
  const [roads, setRoads] = useState<RoadEdge[]>([]);
  const [nodes, setNodes] = useState<RoadNode[]>([]);
  const [criticalLinks, setCriticalLinks] = useState<any[]>([]);
  const [connectivity, setConnectivity] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'CRITICAL' | 'ALL_ROADS' | 'TOPOLOGY'>('CRITICAL');

  useEffect(() => {
    const fetchRoads = async () => {
      setLoading(true);
      try {
        const [topoRes, critRes, netRes] = await Promise.all([
          api.getRoadTopology(),
          api.getRoadCriticalLinks(),
          api.getRoadNetworkAnalysis()
        ]);
        if (topoRes.success) {
          setRoads(topoRes.edges || []);
          setNodes(topoRes.nodes || []);
        }
        if (critRes.success) {
          setCriticalLinks(critRes.critical_links || []);
        }
        if (netRes.success) {
          setConnectivity(netRes.connectivity || null);
        }
      } catch (e) {
        console.warn("Failed fetching road intelligence data:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchRoads();
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
            Geographic Road Network Topology & Critical Corridors
          </h1>
          <p className="text-xs text-pravah-slate">
            NetworkX directed graph representation (Stage 3): intersections as nodes, segments as directed edges with flood elevation risks.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex gap-1.5 bg-white p-1 rounded-2xl border border-pravah-teal/20 text-xs font-bold shadow-sm">
          <button
            onClick={() => setActiveTab('CRITICAL')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'CRITICAL'
                ? 'bg-pravah-teal text-white shadow-sm'
                : 'text-pravah-navy hover:bg-pravah-aqua/50'
            }`}
          >
            Critical Links & Bridges
          </button>
          <button
            onClick={() => setActiveTab('ALL_ROADS')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'ALL_ROADS'
                ? 'bg-pravah-teal text-white shadow-sm'
                : 'text-pravah-navy hover:bg-pravah-aqua/50'
            }`}
          >
            All Road Segments
          </button>
          <button
            onClick={() => setActiveTab('TOPOLOGY')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              activeTab === 'TOPOLOGY'
                ? 'bg-pravah-teal text-white shadow-sm'
                : 'text-pravah-navy hover:bg-pravah-aqua/50'
            }`}
          >
            Graph Topology
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Intersections (Nodes)</div>
          <div className="text-2xl font-black text-pravah-navy mt-1">{nodes.length} Intersections</div>
          <div className="text-[11px] text-pravah-teal mt-0.5">Snapped with 3km threshold</div>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Road Segments (Edges)</div>
          <div className="text-2xl font-black text-pravah-navy mt-1">{roads.length} Segments</div>
          <div className="text-[11px] text-pravah-teal mt-0.5">Directed & one-way restrictions</div>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Topological Bridges</div>
          <div className="text-2xl font-black text-rose-600 mt-1">
            {connectivity?.bridge_count || 0} Cut-Edges
          </div>
          <div className="text-[11px] text-rose-700 mt-0.5">Loss splits network components</div>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Articulation Points</div>
          <div className="text-2xl font-black text-amber-600 mt-1">
            {connectivity?.articulation_point_count || 0} Cut-Vertices
          </div>
          <div className="text-[11px] text-amber-700 mt-0.5">Vital junction bottlenecks</div>
        </div>
      </div>

      {/* Tab 1: Critical Links & Bridges with Explanations */}
      {activeTab === 'CRITICAL' && (
        <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-black text-pravah-navy">
              Ranked Critical Road Corridors & Explainability
            </h2>
            <span className="text-xs text-pravah-slate">
              Ranked by topological bridge status, edge betweenness, and elevation risk
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400 animate-pulse">
              Analyzing road centrality and bridge dependencies...
            </div>
          ) : criticalLinks.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              No critical link records loaded.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                    <th className="py-3 px-3 font-bold">Rank & Road Name</th>
                    <th className="py-3 px-3 font-bold">Endpoints</th>
                    <th className="py-3 px-3 font-bold">Length</th>
                    <th className="py-3 px-3 font-bold">Bridge?</th>
                    <th className="py-3 px-3 font-bold">Betweenness</th>
                    <th className="py-3 px-3 font-bold">Criticality Score</th>
                    <th className="py-3 px-3 font-bold">Why Critical (Explainable Rationale)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {criticalLinks.map((link, idx) => (
                    <tr key={link.road_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-pravah-navy">
                          <span className="w-5 h-5 rounded-full bg-slate-100 text-pravah-slate text-[10px] font-bold inline-flex items-center justify-center mr-2">
                            {idx + 1}
                          </span>
                          {link.name}
                        </div>
                        <div className="text-[10px] text-slate-400 ml-7">{link.road_id}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-600">
                        <div>{link.source_name || link.source}</div>
                        <div className="text-slate-400 text-[10px]">⇄ {link.target_name || link.target}</div>
                      </td>
                      <td className="py-3 px-3 text-pravah-slate font-bold">{link.length_km} km</td>
                      <td className="py-3 px-3">
                        {link.is_bridge ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                            CUT-EDGE
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[10px]">Redundant</span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-bold text-pravah-navy">
                        {Math.round(link.betweenness_centrality * 1000) / 10}%
                      </td>
                      <td className="py-3 px-3 font-black text-rose-600 text-sm">
                        {link.criticality_score}
                      </td>
                      <td className="py-3 px-3 text-slate-700 max-w-md text-[11px] leading-relaxed">
                        {link.why_critical}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: All Road Segments */}
      {activeTab === 'ALL_ROADS' && (
        <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
          <h2 className="text-base font-black text-pravah-navy">
            All Monitored Road Segments & Flood Vulnerability
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                  <th className="py-3 px-3 font-bold">Road Name & ID</th>
                  <th className="py-3 px-3 font-bold">Source Node</th>
                  <th className="py-3 px-3 font-bold">Target Node</th>
                  <th className="py-3 px-3 font-bold">Length</th>
                  <th className="py-3 px-3 font-bold">Speed Limit</th>
                  <th className="py-3 px-3 font-bold">One-Way?</th>
                  <th className="py-3 px-3 font-bold">Base Flood Risk</th>
                  <th className="py-3 px-3 font-bold">Elevation Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {roads.map(r => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-bold text-pravah-navy">{r.name}</div>
                      <div className="text-[10px] text-slate-400">{r.id}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-600 font-semibold">{r.source}</td>
                    <td className="py-3 px-3 text-slate-600 font-semibold">{r.target}</td>
                    <td className="py-3 px-3 text-pravah-slate font-bold">{r.length_km} km</td>
                    <td className="py-3 px-3 text-slate-500">{r.speed_limit_kmh} km/h</td>
                    <td className="py-3 px-3">
                      {r.one_way ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">1-Way</span>
                      ) : (
                        <span className="text-slate-400 text-[10px]">2-Way</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        r.base_flood_risk === 'Severe'
                          ? 'bg-rose-100 text-rose-800'
                          : r.base_flood_risk === 'High'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {r.base_flood_risk}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-pravah-navy">{r.elevation_risk_score} / 100</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Graph Topology & Cut-Vertices */}
      {activeTab === 'TOPOLOGY' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-3">
            <h3 className="text-sm font-black text-pravah-navy flex items-center gap-2">
              <Split className="w-4 h-4 text-amber-600" />
              Articulation Points (Cut-Vertices)
            </h3>
            <p className="text-xs text-pravah-slate">
              Intersections whose failure disconnects two or more subgraphs:
            </p>
            <div className="space-y-2 pt-2">
              {(connectivity?.articulation_points || []).map((ap: any) => (
                <div key={ap.node_id} className="p-3 rounded-xl border border-amber-200 bg-amber-50/50 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-amber-950">{ap.name}</div>
                    <div className="text-[10px] text-amber-700">{ap.node_id} • Ward: {ap.neighbourhood_id || 'Cross-corridor'}</div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 text-[10px] font-bold">
                    Critical Junction
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-3">
            <h3 className="text-sm font-black text-pravah-navy flex items-center gap-2">
              <Network className="w-4 h-4 text-rose-600" />
              Topological Bridges (Cut-Edges)
            </h3>
            <p className="text-xs text-pravah-slate">
              Road segments without parallel detour paths in the topology:
            </p>
            <div className="space-y-2 pt-2">
              {(connectivity?.bridges || []).map((b: any) => (
                <div key={b.road_id} className="p-3 rounded-xl border border-rose-200 bg-rose-50/50 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-rose-950">{b.name}</div>
                    <div className="text-[10px] text-rose-700">{b.road_id} • {b.source} ⇄ {b.target} ({b.length_km} km)</div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-rose-200 text-rose-900 text-[10px] font-bold">
                    Bridge
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
