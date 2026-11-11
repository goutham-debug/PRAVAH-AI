import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Facility } from '../../types';
import { HeartPulse, AlertTriangle, ShieldCheck, MapPin, Building, Phone, Link2 } from 'lucide-react';

export const CriticalFacilitiesPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [accessData, setAccessData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFacilities = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getFacilityAccessibility(closedRoads);
        if (res.success) {
          setAccessData(res);
        } else {
          setError("Failed to retrieve facility accessibility metrics.");
        }
      } catch (e: any) {
        console.warn("Failed fetching facility accessibility:", e);
        setError(e?.message || "Error connecting to facility accessibility service.");
      } finally {
        setLoading(false);
      }
    };
    fetchFacilities();
  }, [closedRoads]);

  const facilities: any[] = accessData?.facility_status || [];
  const traumaAtRisk = accessData?.wards_with_zero_trauma_access || [];
  const criticalAccessRoads: any[] = accessData?.critical_facility_dependency_roads || [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
          Critical Healthcare Facility Accessibility Engine
        </h1>
        <p className="text-xs text-pravah-slate">
          Network accessibility audits evaluating road reachability from all monitored wards to Tertiary Trauma Centres and emergency wards (Stage 3).
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Disconnection Warning if any wards lose trauma care */}
      {traumaAtRisk.length > 0 && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 shadow-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5 animate-bounce" />
          <div className="text-xs space-y-1">
            <div className="font-bold text-rose-900">
              CRITICAL TRAUMA DISCONNECTION DETECTED ({traumaAtRisk.length} Wards)
            </div>
            <p className="text-rose-700 leading-relaxed">
              The following neighbourhood(s) have lost road network connectivity to all Level-1 Tertiary Trauma Centres (Vydehi & Sakra):
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {traumaAtRisk.map((w: any) => (
                <span key={w.neighbourhood_id} className="px-2.5 py-0.5 rounded-full bg-rose-200 text-rose-900 font-bold text-xs">
                  {w.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Critical Facility Dependency Roads */}
      {criticalAccessRoads.length > 0 && (
        <div className="p-5 rounded-3xl bg-amber-50/70 border border-amber-200 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-950 uppercase tracking-wider">
            <Link2 className="w-4 h-4 text-amber-700" />
            Critical Facility Access Dependency Roads
          </div>
          <p className="text-xs text-amber-900">
            Road segments carrying vital ambulance and emergency ingress routes for multiple facilities:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 text-xs">
            {criticalAccessRoads.slice(0, 4).map((car: any) => (
              <div key={car.road_id} className="p-3 bg-white rounded-xl border border-amber-200/80">
                <span className="font-bold text-pravah-navy">{car.road_id}</span>
                <span className="text-[11px] text-amber-800 ml-2">({car.dependent_facility_routes_count} hospital routes)</span>
                <div className="text-[11px] text-slate-600 mt-0.5">{car.criticality_explanation}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Facilities Table */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-black text-pravah-navy">
            Facility Road Network Reachability Matrix
          </h2>
          <span className="text-xs text-pravah-slate">
            {loading ? 'Evaluating paths...' : `${accessData?.reachable_facilities ?? 0} of ${accessData?.total_facilities ?? 0} facilities reachable (${accessData?.overall_accessibility_pct ?? 0}%)`}
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400 animate-pulse">
            Computing network reachability matrices to all facilities...
          </div>
        ) : facilities.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No registered health facilities found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                  <th className="py-3 px-3 font-bold">Facility Name</th>
                  <th className="py-3 px-3 font-bold">Classification</th>
                  <th className="py-3 px-3 font-bold">Beds / ICU</th>
                  <th className="py-3 px-3 font-bold">Emergency Ward</th>
                  <th className="py-3 px-3 font-bold">Network Reachability</th>
                  <th className="py-3 px-3 font-bold">Connected Wards</th>
                  <th className="py-3 px-3 font-bold">Emergency Contact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {facilities.map(fac => {
                  const isTrauma = fac.subtype === 'TERTIARY_TRAUMA';
                  return (
                    <tr key={fac.facility_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-pravah-navy">{fac.name}</div>
                        <div className="text-[10px] text-slate-400">{fac.facility_id} • {fac.address || 'Whitefield'}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] ${
                          isTrauma ? 'bg-purple-100 text-purple-900' : 'bg-blue-50 text-blue-700'
                        }`}>
                          {fac.subtype || fac.type}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-pravah-slate font-semibold">
                        {fac.capacity_beds > 0 ? `${fac.capacity_beds} beds` : 'N/A'}
                      </td>
                      <td className="py-3 px-3">
                        {fac.has_emergency_ward ? (
                          <span className="text-emerald-700 font-bold flex items-center gap-1">
                            <ShieldCheck className="w-3.5 h-3.5" /> 24x7 Active
                          </span>
                        ) : (
                          <span className="text-slate-400">Regular</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        {fac.is_network_accessible ? (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                            Reachable {fac.min_travel_time_mins !== null ? `(${fac.min_travel_time_mins} mins)` : ''}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold text-[10px]">
                            Access Blocked
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-pravah-slate">
                        {fac.connected_wards_count} of {fac.total_wards_count} wards
                      </td>
                      <td className="py-3 px-3 font-semibold text-pravah-navy">
                        {fac.phone || 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
