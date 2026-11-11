import React from 'react';

export const Legend: React.FC = () => {
  return (
    <div className="bg-white/95 backdrop-blur border border-pravah-teal/20 p-3 rounded-xl shadow-lg text-xs space-y-2.5 max-w-xs">
      <div className="font-bold text-pravah-navy uppercase tracking-wider text-[11px] pb-1 border-b border-pravah-pale">
        Map Intelligence Legend
      </div>

      <div>
        <div className="font-semibold text-pravah-slate mb-1">Ward Flood Risk Index (R)</div>
        <div className="grid grid-cols-2 gap-1.5">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500 inline-block opacity-75"></span>
            <span>Low (&lt;30)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-400 inline-block opacity-75"></span>
            <span>Moderate (30-55)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-orange-500 inline-block opacity-75"></span>
            <span>High (55-75)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-rose-600 inline-block opacity-75"></span>
            <span>Severe (&gt;75)</span>
          </div>
        </div>
      </div>

      <div className="pt-1 border-t border-pravah-pale">
        <div className="font-semibold text-pravah-slate mb-1">Road Network & Transit</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-4 h-1 bg-[#167F83] rounded"></span>
            <span>Open Arterial Road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-1 bg-rose-600 rounded"></span>
            <span>Disrupted / Closed Road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-1.5 bg-blue-500 rounded border border-white"></span>
            <span>Safe Evacuation Route</span>
          </div>
        </div>
      </div>

      <div className="pt-1 border-t border-pravah-pale">
        <div className="font-semibold text-pravah-slate mb-1">Critical Facilities</div>
        <div className="grid grid-cols-2 gap-1.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 border border-white shadow-sm"></span>
            <span>Hospital</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 border border-white shadow-sm"></span>
            <span>Relief Shelter</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600 border border-white shadow-sm"></span>
            <span>Rescue Team</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-600 border border-white shadow-sm"></span>
            <span>Incident Point</span>
          </div>
        </div>
      </div>
    </div>
  );
};
