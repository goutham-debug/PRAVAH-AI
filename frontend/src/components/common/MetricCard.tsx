import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: string;
  trendPositive?: boolean;
  colorScheme?: 'teal' | 'red' | 'amber' | 'blue' | 'slate';
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendPositive,
  colorScheme = 'teal',
  badge,
}) => {
  const schemeStyles = {
    teal: 'border-pravah-teal/20 bg-white hover:border-pravah-teal/50',
    red: 'border-rose-200 bg-rose-50/40 hover:border-rose-400',
    amber: 'border-amber-200 bg-amber-50/40 hover:border-amber-400',
    blue: 'border-blue-200 bg-blue-50/40 hover:border-blue-400',
    slate: 'border-slate-200 bg-white hover:border-slate-400',
  }[colorScheme];

  return (
    <div className={`p-4 rounded-xl border transition-all shadow-sm ${schemeStyles}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-pravah-slate truncate">
          {title}
        </span>
        {icon && <div className="text-pravah-teal">{icon}</div>}
      </div>
      <div className="flex items-baseline justify-between gap-2">
        <div className="text-2xl font-extrabold text-pravah-navy tracking-tight">{value}</div>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-pravah-teal/10 text-pravah-teal font-semibold">
            {badge}
          </span>
        )}
      </div>
      {(subtitle || trend) && (
        <div className="mt-1 flex items-center justify-between text-xs text-pravah-slate">
          {subtitle && <span>{subtitle}</span>}
          {trend && (
            <span className={trendPositive ? 'text-emerald-600 font-semibold' : 'text-rose-600 font-semibold'}>
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
