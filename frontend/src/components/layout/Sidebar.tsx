import React from 'react';
import { ShieldAlert, BookOpen, Code2, FileCheck2, Lightbulb } from 'lucide-react';

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-full md:w-72 flex-shrink-0 space-y-4">
      {/* Principle 1 Card */}
      <div className="glass-panel p-4 space-y-2 border-l-4 border-l-sky-400">
        <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
          <ShieldAlert className="w-4 h-4" />
          <span>Reliability Over Intelligence</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          A correct simple answer beats a wrong sophisticated answer. StatAid Studio evaluates data distributions before calculating statistics.
        </p>
      </div>

      {/* Principle 2 Card */}
      <div className="glass-panel p-4 space-y-2 border-l-4 border-l-amber-400">
        <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
          <BookOpen className="w-4 h-4" />
          <span>Assumption-First Shield</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Before showing any <code className="text-sky-300">p</code>-value, our engine tests Shapiro-Wilk normality and Levene homogeneity, applying Welch's or HC3 robust corrections when needed.
        </p>
      </div>

      {/* Principle 3 Card */}
      <div className="glass-panel p-4 space-y-2 border-l-4 border-l-indigo-400">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
          <Code2 className="w-4 h-4" />
          <span>Full R & Python Transparency</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Every calculation provides the exact, reproducible <code className="text-indigo-300">.R</code> and <code className="text-indigo-300">.py</code> code blocks so you can verify results independently.
        </p>
      </div>

      {/* Principle 4 Card */}
      <div className="glass-panel p-4 space-y-2 border-l-4 border-l-emerald-400">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
          <FileCheck2 className="w-4 h-4" />
          <span>APA 7th Edition Reporting</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Generate publication-ready APA citation strings and download high-resolution (300 DPI) static PNG charts for manuscript attachments.
        </p>
      </div>

      {/* Quick Tip Box */}
      <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/90 border border-white/10 rounded-xl p-4 text-xs space-y-2">
        <div className="flex items-center gap-2 text-sky-300 font-medium">
          <Lightbulb className="w-4 h-4 text-amber-400" />
          <span>Pro Tip: Natural Language</span>
        </div>
        <p className="text-slate-400">
          Not sure which test to run? Just type your research question in the <strong className="text-white">AI Consultant</strong> tab and we'll pick the exact verified method for your variables!
        </p>
      </div>
    </aside>
  );
};
