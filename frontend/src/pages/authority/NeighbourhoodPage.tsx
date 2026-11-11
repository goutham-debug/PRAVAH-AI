import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Neighbourhood } from '../../types';
import { MapPin, Users, Maximize2, Shield, Layers, AlertTriangle } from 'lucide-react';

export const NeighbourhoodPage: React.FC = () => {
  const [neighbourhoods, setNeighbourhoods] = useState<Neighbourhood[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNbs = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getNeighbourhoods();
        if (res.success) {
          setNeighbourhoods(res.neighbourhoods || []);
        } else {
          setError("Failed to load neighbourhood records.");
        }
      } catch (e: any) {
        console.warn("Failed fetching neighbourhoods:", e);
        setError(e?.message || "Error connecting to neighbourhood registry service.");
      } finally {
        setLoading(false);
      }
    };
    fetchNbs();
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy">
          Neighbourhood & Administrative Ward Registry
        </h1>
        <p className="text-xs text-pravah-slate">
          Monitored BBMP administrative ward boundaries, census population, topographic elevation, and hydrological hazard factors.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="p-6 rounded-3xl bg-white border border-pravah-teal/20 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-black text-pravah-navy">
            Ward Inventory & Topographic Hazard Baseline
          </h2>
          <span className="text-xs text-pravah-slate">
            {loading ? 'Loading...' : `${neighbourhoods.length} Monitored Wards`}
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400 animate-pulse">
            Loading administrative ward records...
          </div>
        ) : neighbourhoods.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No neighbourhood records loaded.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-pravah-slate uppercase text-[10px] tracking-wider bg-slate-50">
                  <th className="py-3 px-3 font-bold">Ward Name & ID</th>
                  <th className="py-3 px-3 font-bold">BBMP Ward #</th>
                  <th className="py-3 px-3 font-bold">Census Population</th>
                  <th className="py-3 px-3 font-bold">Area (sq km)</th>
                  <th className="py-3 px-3 font-bold">Elevation (m MSL)</th>
                  <th className="py-3 px-3 font-bold">Historical Hazard (H)</th>
                  <th className="py-3 px-3 font-bold">Drainage Factor (D)</th>
                  <th className="py-3 px-3 font-bold">Lake / Rajakaluve Corridor</th>
                  <th className="py-3 px-3 font-bold">Data Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {neighbourhoods.map(nb => (
                  <tr key={nb.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-bold text-pravah-navy">{nb.name}</div>
                      <div className="text-[10px] text-slate-400">{nb.id}</div>
                    </td>
                    <td className="py-3 px-3 text-pravah-navy font-semibold">{nb.ward_no || 'N/A'}</td>
                    <td className="py-3 px-3 font-bold text-pravah-teal">{Number(nb.population).toLocaleString()}</td>
                    <td className="py-3 px-3 text-pravah-slate">{nb.area_sqkm} km²</td>
                    <td className="py-3 px-3 text-pravah-slate font-semibold">{nb.elevation_m}m</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        nb.hazard_factor >= 70 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {nb.hazard_factor} / 100
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-600 font-semibold">
                      {nb.drainage_factor || 50} / 100
                    </td>
                    <td className="py-3 px-3 text-slate-600 truncate max-w-xs">{nb.lake_proximity || 'Elevated plateau buffer'}</td>
                    <td className="py-3 px-3 text-emerald-700 font-semibold text-[11px]">{nb.verification_status}</td>
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
