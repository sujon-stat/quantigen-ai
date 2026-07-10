import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle, ChevronDown, ShieldCheck } from 'lucide-react';
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
  const [isOpen, setIsOpen] = useState(false);
  const safeAssumptions = assumptions || [];
  const allPassed = safeAssumptions.length === 0 || safeAssumptions.every((a) => a?.passed);

  return (
    <div className="glass-panel border-0 rounded-2xl relative overflow-hidden transition-all duration-300 shadow-md">
      {/* Top Status Banner Glow */}
      <div
        className={`absolute top-0 left-0 right-0 h-1.5 ${
          allPassed
            ? 'bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500'
            : 'bg-gradient-to-r from-amber-500 via-orange-500 to-amber-500'
        }`}
      />

      {/* Collapsible Trigger Header (Collapsed by Default) */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-900/90 hover:bg-slate-800/90 cursor-pointer transition-all select-none gap-3"
      >
        <div className="flex items-center gap-3">
          <QuantigenLogo size="sm" interactive={false} />
          <div className="flex items-center gap-2 flex-wrap">
            <ShieldCheck className={allPassed ? "w-5 h-5 text-emerald-400" : "w-5 h-5 text-amber-400"} />
            <span className="font-bold text-white text-sm">
              Assumption Shield: {allPassed ? 'All Prerequisites Satisfied' : 'Diagnostic Correction Active'}
            </span>
            <span className={allPassed ? 'badge-pass text-[11px]' : 'badge-warn text-[11px]'}>
              {safeAssumptions.length} Check{safeAssumptions.length !== 1 ? 's' : ''} Evaluated
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-sky-400 font-semibold sm:ml-auto">
          <span>{isOpen ? 'Hide Diagnostics' : 'Inspect Math & Diagnostics'}</span>
          <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {/* Collapsible Diagnostic Content */}
      {isOpen && (
        <div className="p-6 pt-4 border-t border-white/10 space-y-4 bg-slate-950/40 animate-fade-in">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="brand-subtitle text-xs text-slate-300">
                Evaluated prior to running <strong className="brand-title text-white">{methodName}</strong> to guarantee statistical reliability.
              </p>
            </div>
            <div className="shield-help-box text-xs text-slate-400 max-w-xs bg-slate-900/80 p-3 rounded-xl border border-white/5 flex items-start gap-2">
              <HelpCircle className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
              <span>
                If an assumption is violated, Quantigen automatically applies robust corrections (like Welch degrees of freedom or HC3 standard errors) so your inferences remain valid.
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {safeAssumptions.map((item, idx) => (
              <div
                key={idx}
                className={`shield-diag-card p-4 rounded-xl border flex items-start justify-between gap-4 transition-all ${
                  item.passed
                    ? 'bg-slate-900/60 border-white/5 hover:border-emerald-500/30'
                    : 'shield-diag-card-warn bg-amber-500/5 border-amber-500/30 shadow-md shadow-amber-500/5'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="shield-diag-title font-bold text-sm text-white flex items-center gap-2">
                      {item.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                      )}
                      {item.assumption_name}
                    </span>
                    <span className="shield-diag-test text-[11px] px-2 py-0.5 rounded bg-white/5 font-mono text-slate-300">
                      {item.test_name}
                    </span>
                  </div>
                  <p className="brand-subtitle text-xs text-slate-300 leading-relaxed">{item.explanation}</p>
                  {item.p_value !== undefined && item.p_value !== null && (
                    <div className="text-[11px] text-slate-400 pt-1 border-t border-white/5 flex items-center justify-between">
                      <span>Diagnostic p-value: <code className="brand-title text-slate-200">{item.p_value.toFixed(4)}</code></span>
                      <span>Test Stat: <code className="brand-title text-slate-200">{item.statistic?.toFixed(3) || 'N/A'}</code></span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
