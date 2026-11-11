import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { PravahMap } from '../../components/map/PravahMap';
import { Navigation, MapPin, AlertTriangle, Play, CheckCircle2, Shield, GitBranch, Compass, Info } from 'lucide-react';

export const EvacuationPlanningPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [nodes, setNodes] = useState<any[]>([]);
  const [roads, setRoads] = useState<any[]>([]);
  const [startNode, setStartNode] = useState('');
  const [destNode, setDestNode] = useState('');
  const [algorithm, setAlgorithm] = useState<'dijkstra' | 'astar'>('dijkstra');
  const [routeRes, setRouteRes] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const topo = await api.getRoadTopology();
        if (topo.success) {
          const list = topo.nodes || [];
          setNodes(list);
          setRoads(topo.edges || []);
          if (list.length > 1) {
            setStartNode(prev => prev || list[0].id);
            setDestNode(prev => prev || list[list.length - 1].id);
          }
        }
      } catch (e) {
        console.warn("Failed fetching road topology:", e);
      }
    };
    fetchTopology();
  }, []);

  const handleRunRouting = async () => {
    setLoading(true);
    setErrorMsg(null);
    setRouteRes(null);
    const origin = nodes.find(n => n.id === startNode);
    const dest = nodes.find(n => n.id === destNode);

    if (!origin || !dest) {
      setLoading(false);
      return;
    }

    try {
      const res = await api.planJourney({
        start_lat: origin.lat,
        start_lon: origin.lon,
        dest_lat: dest.lat,
        dest_lon: dest.lon,
        avoid_roads: closedRoads,
        algorithm: algorithm
      });
      if (res.success) {
        setRouteRes(res);
      } else {
        setErrorMsg(res.error || "Route could not be calculated.");
        setRouteRes(res);
      }
    } catch (e: any) {
      console.warn("Evacuation routing failed:", e);
      setErrorMsg(e?.message || "Failed connecting to routing engine.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (nodes.length > 0 && startNode && destNode) {
      handleRunRouting();
    }
  }, [nodes, startNode, destNode, algorithm, closedRoads]);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
            Intelligent Evacuation Routing & Corridor Analysis
          </h1>
          <p className="text-xs text-pravah-slate">
            Topological evacuation pathfinding on directed road network (Stage 4) using Dijkstra and A* algorithms, avoiding confirmed road cuts.
          </p>
        </div>

        {/* Algorithm Selector */}
        <div className="flex items-center gap-1.5 bg-white p-1 rounded-2xl border border-pravah-teal/20 text-xs font-bold shadow-sm">
          <span className="text-[10px] text-slate-400 px-2 uppercase tracking-wider font-extrabold">Algorithm:</span>
          <button
            onClick={() => setAlgorithm('dijkstra')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              algorithm === 'dijkstra'
                ? 'bg-pravah-teal text-white shadow-sm'
                : 'text-pravah-navy hover:bg-pravah-aqua/50'
            }`}
          >
            Dijkstra
          </button>
          <button
            onClick={() => setAlgorithm('astar')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              algorithm === 'astar'
                ? 'bg-pravah-teal text-white shadow-sm'
                : 'text-pravah-navy hover:bg-pravah-aqua/50'
            }`}
          >
            A* (Heuristic)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-pravah-teal-dark flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5" />
              Evacuation Corridor Generator
            </h3>

            <div>
              <label className="block text-xs font-bold text-pravah-navy mb-1">Evacuation Origin (Vulnerable Ward Hub)</label>
              <select
                value={startNode}
                onChange={(e) => setStartNode(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-pravah-teal bg-white font-medium"
              >
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name} ({n.id})</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-pravah-navy mb-1">Designated Egress Hub / High-Ground Shelter</label>
              <select
                value={destNode}
                onChange={(e) => setDestNode(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-pravah-teal bg-white font-medium"
              >
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name} ({n.id})</option>)}
              </select>
            </div>

            <button
              onClick={handleRunRouting}
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-pravah-teal text-white font-bold text-xs shadow-md hover:bg-pravah-teal-dark transition-all disabled:opacity-50"
            >
              {loading ? 'Solving Graph Route...' : `Compute Optimal Route (${algorithm.toUpperCase()})`}
            </button>
          </div>

          {/* Area Isolation Warning if no path found */}
          {errorMsg && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 space-y-2">
              <div className="font-bold flex items-center gap-1.5 text-rose-900">
                <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                CORRIDOR BLOCKED / TOPOLOGICAL ISOLATION
              </div>
              <p className="leading-relaxed">{errorMsg}</p>
              {closedRoads.length > 0 && (
                <div className="text-[11px] text-rose-700 pt-1">
                  Active closures affecting path: {closedRoads.join(', ')}
                </div>
              )}
            </div>
          )}

          {/* Primary Route Details */}
          {routeRes?.primary_route && (
            <div className="p-5 rounded-2xl bg-white border border-pravah-teal/20 shadow-md space-y-3 text-xs">
              <div className="flex items-center justify-between font-bold text-pravah-navy">
                <span>Calculated Primary Route</span>
                <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  {routeRes.primary_route.total_distance_km} km • {routeRes.primary_route.travel_time_mins} mins
                </span>
              </div>

              {routeRes.primary_route.route_explanation && (
                <p className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100 leading-relaxed">
                  {routeRes.primary_route.route_explanation}
                </p>
              )}

              {/* Alternative Route Summary if available */}
              {routeRes.alternative_route && (
                <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200/60 text-indigo-900 space-y-1">
                  <div className="font-bold flex items-center gap-1 text-[11px]">
                    <GitBranch className="w-3.5 h-3.5 text-indigo-600" />
                    Alternative Detour Corridor Available
                  </div>
                  <div className="text-[11px] text-indigo-700">
                    {routeRes.alternative_route.total_distance_km} km • {routeRes.alternative_route.travel_time_mins} mins (via {routeRes.alternative_route.road_names.slice(0, 2).join(', ')})
                  </div>
                </div>
              )}

              <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-pravah-slate pt-1">
                  Turn-by-Turn Waypoints:
                </div>
                {routeRes.primary_route.turn_by_turn.map((step: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-2 text-slate-700">
                    <span className="w-4 h-4 rounded-full bg-pravah-teal/20 text-pravah-teal text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="leading-snug">{step}</span>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center gap-1">
                <Info className="w-3 h-3 flex-shrink-0" />
                <span>Speed model: 25 km/h emergency transit crawl. No live traffic API active.</span>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-3">
          <PravahMap
            roads={roads}
            nodes={nodes}
            closedRoadIds={closedRoads}
            routeCoordinates={routeRes?.primary_route?.coordinates}
            alternativeRouteCoordinates={routeRes?.alternative_route?.coordinates}
            height="560px"
          />
        </div>
      </div>
    </div>
  );
};
