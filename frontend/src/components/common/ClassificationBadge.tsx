import React from 'react';
import { Classification } from '../../api/client';

const STYLE: Record<Classification, string> = {
  OBSERVED: 'bg-emerald-50 text-emerald-800 border-emerald-300',
  OFFICIAL: 'bg-emerald-50 text-emerald-800 border-emerald-300',
  FORECAST: 'bg-blue-50 text-blue-800 border-blue-300',
  MODELLED: 'bg-indigo-50 text-indigo-800 border-indigo-300',
  UNVERIFIED: 'bg-amber-50 text-amber-800 border-amber-300',
  STALE: 'bg-orange-50 text-orange-800 border-orange-300',
  UNAVAILABLE: 'bg-rose-50 text-rose-800 border-rose-300',
  NOT_ASSESSED: 'bg-slate-100 text-slate-700 border-slate-300',
};

export const ClassificationBadge: React.FC<{ value: Classification }> = ({ value }) => (
  <span className={`inline-block text-[10px] font-bold tracking-wide px-2 py-0.5 rounded border ${STYLE[value] ?? STYLE.NOT_ASSESSED}`}>
    {value.replace('_', ' ')}
  </span>
);
