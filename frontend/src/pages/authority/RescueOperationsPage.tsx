import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { LifeBuoy, AlertTriangle, Shield, CheckCircle2, Phone, ArrowRight } from 'lucide-react';

export const RescueOperationsPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [coordination, setCoordination] = useState<any>(null);
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRescue = async () => {
      setLoading(true);
      try {
        const [coordRes, teamRes] = await Promise.all([
          api.coordinateRescue(closedRoads),
          api.listRescueTeams()
        ]);
        if (coordRes.success) setCoordination(coordRes);
        if (teamRes.success) setTeams(teamRes.teams || []);
      } catch (e) {
        console.warn("Failed fetching rescue operations:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchRescue();
  }, [closedRoads]);

  const assignments = coordination?.assignments || [];
  const unassigned = coordination?.unassigned_incidents || [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
          Tactical Rescue Operations & Resource Coordination
        </h1>
        <p className="text-xs text-pravah-slate">
          Capability-based matching allocating SDRF boat squads, BBMP de-watering pump units, and NDRF medical ambulances to priority incidents.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Active Incidents Triaged</div>
          <div className="text-2xl font-black text-pravah-navy mt-1">
            {loading ? '...' : (coordination?.total_incidents_evaluated != null ? coordination.total_incidents_evaluated : 0)}
          </div>
          <div className="text-[11px] text-pravah-teal mt-0.5 font-semibold">Priority rank weighted</div>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Squads Dispatched</div>
          <div className="text-2xl font-black text-emerald-600 mt-1">
            {loading ? '...' : (coordination?.dispatched_count != null ? coordination.dispatched_count : 0)}
          </div>
          <div className="text-[11px] text-emerald-700 mt-0.5 font-semibold">Zero duplicate assignment</div>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-pravah-teal/20 shadow-sm">
          <div className="text-xs uppercase font-bold text-pravah-slate">Idle Reserve Teams</div>
          <div className="text-2xl font-black text-blue-600 mt-1">
            {loading ? '...' : (coordination?.remaining_idle_teams_count != null ? coordination.remaining_idle_teams_count : teams.length)}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Staged for escalation</div>
        </div>
      </div>

      {/* Dispatched Missions Table */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <h2 className="text-base font-black text-pravah-navy">
          Active Emergency Mission Deployments
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                <th className="py-3 px-3 font-bold">Report ID</th>
                <th className="py-3 px-3 font-bold">Severity</th>
                <th className="py-3 px-3 font-bold">Incident Type</th>
                <th className="py-3 px-3 font-bold">Assigned Rescue Unit</th>
                <th className="py-3 px-3 font-bold">Squad Capability</th>
                <th className="py-3 px-3 font-bold">Transit Dist</th>
                <th className="py-3 px-3 font-bold">ETA</th>
                <th className="py-3 px-3 font-bold">Commander Contact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {assignments.map((m: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-3 font-bold text-pravah-navy">{m.tracking_id}</td>
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      m.severity === 'SEVERE' ? 'bg-rose-100 text-rose-800' : 'bg-orange-100 text-orange-800'
                    }`}>
                      {m.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-semibold text-pravah-navy">{m.incident_type}</td>
                  <td className="py-3 px-3 font-bold text-pravah-teal">{m.assigned_team_name}</td>
                  <td className="py-3 px-3 text-[11px] text-slate-600">{m.team_type}</td>
                  <td className="py-3 px-3 text-slate-600">{m.response_distance_km} km</td>
                  <td className="py-3 px-3 font-bold text-emerald-700">{m.estimated_arrival_mins} mins</td>
                  <td className="py-3 px-3 text-slate-600">{m.contact_commander || 'Duty Officer'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
