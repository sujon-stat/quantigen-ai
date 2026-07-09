import React from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';
import type { AssumptionResult } from '../../types/statmind';
import { QuantigenLogo } from '../common/QuantigenLogo';

interface AssumptionShieldProps {
  assumptions: AssumptionResult[];
  methodName: string;
}

export const AssumptionShield: React.FC<AssumptionShieldProps> = ({
  assumptions = [],
  methodName,
}) => {
  const safeAssumptions = assumptions || [];
  const allPassed = safeAssumptions.length === 0 || safeAssumptions.every((a) => a?.passed);

  return (
    <div className="glass-panel p-6 border-0 rounded-3xl relative overflow-hidden transition-all duration-300">
      {/* Top Status Banner Glow */}
      <div
        className={`absolute top-0 left-0 right-0 h-1.5 ${
          allPassed
            ? 'bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500'
            : 'bg-gradient-to-r from-amber-500 via-orange-500 to-amber-500'
        }`}
      />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <QuantigenLogo size="md" interactive={true} />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">Quantigen Assumption Diagnostic Shield</h3>
              <span className={allPassed ? 'badge-pass' : 'badge-warn'}>
                {allPassed ? 'All Prerequisites Satisfied' : 'Diagnostic Warning & Correction Active'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Evaluated prior to running <strong className="text-white">{methodName}</strong> to guarantee statistical reliability.
            </p>
          </div>
        </div>

        <div className="text-xs text-slate-400 max-w-xs bg-slate-900/60 p-3 rounded-xl border border-white/5 flex items-start gap-2">
          <HelpCircle className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
          <span>
            If an assumption is violated, Quantigen automatically applies robust corrections (like Welch degrees of freedom or HC3 standard errors) so your inferences remain valid.
          </span>
        </div>
      </div>

      {/* Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {safeAssumptions.map((item, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-xl border flex items-start justify-between gap-4 transition-all ${
              item.passed
                ? 'bg-slate-900/60 border-white/5 hover:border-emerald-500/30'
                : 'bg-amber-500/5 border-amber-500/30 shadow-md shadow-amber-500/5'
            }`}
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-white flex items-center gap-2">
                  {item.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                  )}
                  {item.assumption_name}
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-white/5 font-mono text-slate-300">
                  {item.test_name}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{item.explanation}</p>
              {item.p_value !== undefined && item.p_value !== null && (
                <div className="text-[11px] text-slate-400 pt-1 border-t border-white/5 flex items-center justify-between">
                  <span>Diagnostic p-value: <code className="text-slate-200">{item.p_value.toFixed(4)}</code></span>
                  <span>Test Stat: <code className="text-slate-200">{item.statistic?.toFixed(3) || 'N/A'}</code></span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
