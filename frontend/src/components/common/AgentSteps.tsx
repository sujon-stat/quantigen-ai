import React from 'react';
import { CheckCircle2, Loader2, AlertTriangle, ShieldCheck } from 'lucide-react';

export type StepStatus = 'pending' | 'running' | 'success' | 'warning' | 'error';

export interface AgentStep {
  id: string;
  label: string;
  status: StepStatus;
  detail?: string;
}

interface AgentStepsProps {
  steps: AgentStep[];
  title?: string;
  subtitle?: string;
}

export const AgentSteps: React.FC<AgentStepsProps> = ({
  steps,
  title = 'Quantigen Agentic Engine Working...',
  subtitle = 'Assumption-First Diagnostic & Statistical Execution Pipeline',
}) => {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="bg-slate-950/90 border-2 border-sky-500/30 rounded-2xl p-6 mb-6 font-mono shadow-2xl shadow-sky-500/10 backdrop-blur-xl animate-fade-in transition-all">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <h4 className="font-sans font-bold text-white text-base tracking-wide flex items-center gap-2">
              <span>{title}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-400/30 font-mono tracking-wider font-semibold">
                AGENTIC v0.1
              </span>
            </h4>
            <p className="font-sans text-xs text-slate-400 mt-0.5">{subtitle}</p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-sans font-semibold">
          <ShieldCheck className="w-4 h-4" />
          <span>Patent-Pending Shield Active</span>
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-3.5 pl-1">
        {steps.map((step, index) => {
          const isRunning = step.status === 'running';
          const isSuccess = step.status === 'success';
          const isWarning = step.status === 'warning';
          const isError = step.status === 'error';
          const isPending = step.status === 'pending';

          return (
            <div
              key={step.id}
              className={`flex items-start gap-3.5 p-3 rounded-xl transition-all ${
                isRunning
                  ? 'bg-sky-500/10 border border-sky-400/40 shadow-lg shadow-sky-500/5 translate-x-1'
                  : isWarning
                  ? 'bg-amber-500/10 border border-amber-400/40 shadow-lg shadow-amber-500/5'
                  : isSuccess
                  ? 'bg-slate-900/60 border border-white/5'
                  : 'opacity-60'
              }`}
            >
              {/* Step Index & Status Icon */}
              <div className="flex-shrink-0 mt-0.5 flex items-center justify-center">
                {isPending && (
                  <div className="w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500 text-xs font-bold">
                    {index + 1}
                  </div>
                )}
                {isRunning && (
                  <div className="w-6 h-6 rounded-lg bg-sky-500/20 border border-sky-400/50 flex items-center justify-center text-sky-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                )}
                {isSuccess && (
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/20 border border-emerald-400/50 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                )}
                {isWarning && (
                  <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-400/50 flex items-center justify-center text-amber-300">
                    <AlertTriangle className="w-4 h-4 animate-pulse" />
                  </div>
                )}
                {isError && (
                  <div className="w-6 h-6 rounded-lg bg-rose-500/20 border border-rose-400/50 flex items-center justify-center text-rose-400">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`text-sm font-sans tracking-wide ${
                      isRunning
                        ? 'text-white font-bold'
                        : isWarning
                        ? 'text-amber-200 font-bold'
                        : isSuccess
                        ? 'text-slate-200 font-semibold'
                        : isError
                        ? 'text-rose-300 font-bold'
                        : 'text-slate-500 font-medium'
                    }`}
                  >
                    {step.label}
                  </span>

                  {/* Status Pill */}
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded uppercase font-mono tracking-wider font-bold ${
                      isRunning
                        ? 'bg-sky-500/20 text-sky-300 border border-sky-400/30'
                        : isWarning
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-400/30'
                        : isSuccess
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/30'
                        : isError
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-400/30'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {step.status}
                  </span>
                </div>

                {/* Step Detail Explanation */}
                {step.detail && (
                  <div
                    className={`mt-1.5 p-2 rounded-lg font-mono text-xs leading-relaxed ${
                      isWarning
                        ? 'bg-amber-950/60 border border-amber-400/30 text-amber-200 font-semibold'
                        : isSuccess
                        ? 'bg-slate-950/80 border border-white/5 text-sky-300'
                        : isRunning
                        ? 'bg-sky-950/40 border border-sky-400/20 text-sky-200 animate-pulse'
                        : 'text-slate-400'
                    }`}
                  >
                    {isWarning && <strong className="text-amber-400 uppercase tracking-wider block text-[10px] mb-0.5">⚡ Assumption Shield Intervention:</strong>}
                    {step.detail}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
