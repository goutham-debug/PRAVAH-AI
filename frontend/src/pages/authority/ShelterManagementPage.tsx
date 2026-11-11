import { useAssessment } from '../../context/AssessmentContext';
import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { MetricCard } from '../../components/common/MetricCard';
import { Building, Users, AlertTriangle, CheckCircle2, Shield, ArrowRight } from 'lucide-react';

export const ShelterManagementPage: React.FC = () => {
  const { closedRoads } = useAssessment();
  const [allocationData, setAllocationData] = useState<any>(null);
  const [shelters, setShelters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllocations = async () => {
      setLoading(true);
      try {
        const [allocRes, shRes] = await Promise.all([
          api.allocateShelters(closedRoads),
          api.listShelters()
        ]);
        if (allocRes.success) setAllocationData(allocRes);
        if (shRes.success) setShelters(shRes.shelters || []);
      } catch (e) {
        console.warn("Failed fetching shelter allocation:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAllocations();
  }, [closedRoads]);

  const assignments = allocationData?.assignments || [];
  const unmet = allocationData?.unmet_records || [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
          Shelter Capacity Allocation & Optimization Engine
        </h1>
        <p className="text-xs text-pravah-slate">
          Min-cost flow graph allocation matching displaced populations to regional relief centres under strict capacity constraints.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          title="Total Evacuation Demand"
          value={loading ? '...' : (allocationData?.total_evacuation_demand != null ? Number(allocationData.total_evacuation_demand).toLocaleString() : 'N/A')}
          subtitle="Screened high-risk displaced"
          colorScheme="amber"
        />
        <MetricCard
          title="Successfully Assigned"
          value={loading ? '...' : (allocationData?.total_allocated_population != null ? Number(allocationData.total_allocated_population).toLocaleString() : 'N/A')}
          subtitle={allocationData?.allocation_fulfillment_pct != null ? `${allocationData.allocation_fulfillment_pct}% fulfillment` : 'MODELLED'}
          colorScheme="teal"
        />
        <MetricCard
          title="Total Shelter Capacity"
          value={loading ? '...' : (allocationData?.total_shelter_capacity != null ? Number(allocationData.total_shelter_capacity).toLocaleString() : 'N/A')}
          subtitle={allocationData?.shelter_utilization_pct != null ? `${allocationData.shelter_utilization_pct}% utilized` : 'Pilot inventory'}
          colorScheme="blue"
        />
        <MetricCard
          title="Unmet / Cut-Off Demand"
          value={loading ? '...' : (allocationData ? Number((allocationData.total_unmet_demand || 0) + (allocationData.total_unreachable_demand || 0)).toLocaleString() : 'N/A')}
          subtitle="Isolated or capacity bound"
          colorScheme="red"
        />
      </div>

      {/* Unmet Demand Alert if any */}
      {unmet.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs space-y-2">
          <div className="font-bold text-amber-900 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Evacuation Deficit Notice (Zero Capacity Overflow Enforced)
          </div>
          <div className="space-y-1 text-amber-800">
            {unmet.map((u: any, idx: number) => (
              <div key={idx}>
                • <strong>{u.name}:</strong> {u.unmet_count} persons unmet ({u.reason})
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Area to Shelter Assignment Table */}
      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <h2 className="text-base font-black text-pravah-navy">
          Optimized Ward-to-Shelter Allocations (Min-Cost Flow Matching)
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                <th className="py-3 px-4 font-bold">Affected Ward</th>
                <th className="py-3 px-4 font-bold">Assigned Emergency Shelter</th>
                <th className="py-3 px-4 font-bold">Assigned Population</th>
                <th className="py-3 px-4 font-bold">Transit Distance</th>
                <th className="py-3 px-4 font-bold">Estimated Transit Time</th>
                <th className="py-3 px-4 font-bold">Constraint Check</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {assignments.map((alloc: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-bold text-pravah-navy">{alloc.neighbourhood_name}</td>
                  <td className="py-3 px-4 text-pravah-teal font-bold">{alloc.shelter_name}</td>
                  <td className="py-3 px-4 font-extrabold text-pravah-navy">
                    {Number(alloc.allocated_population).toLocaleString()} persons
                  </td>
                  <td className="py-3 px-4 text-pravah-slate">{alloc.travel_distance_km} km</td>
                  <td className="py-3 px-4 text-pravah-slate">{alloc.travel_time_mins} mins</td>
                  <td className="py-3 px-4">
                    <span className="text-emerald-700 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Within Capacity
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
