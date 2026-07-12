import React, { useState, useEffect } from 'react';

interface QuantigenLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  interactive?: boolean;
  showText?: boolean;
  className?: string;
  onClick?: () => void;
}

type LogoMode = 'gaussian' | 'regression' | 'scatter';

export const QuantigenLogo: React.FC<QuantigenLogoProps> = ({
  size = 'md',
  interactive = true,
  showText = false,
  className = '',
  onClick,
}) => {
  const [mode, setMode] = useState<LogoMode>('gaussian');
  const [isHovered, setIsHovered] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });
  const [isScanning, setIsScanning] = useState(false);

  // Auto-cycle through statistical representation modes every 6 seconds when not hovered
  useEffect(() => {
    if (!interactive || isHovered) return;
    const interval = setInterval(() => {
      setMode((prev) => {
        if (prev === 'gaussian') return 'regression';
        if (prev === 'regression') return 'scatter';
        return 'gaussian';
      });
    }, 6000);
    return () => clearInterval(interval);
  }, [interactive, isHovered]);

  const handleLogoClick = () => {
    setIsScanning(true);
    setTimeout(() => setIsScanning(false), 900);
    setMode((prev) => {
      if (prev === 'gaussian') return 'regression';
      if (prev === 'regression') return 'scatter';
      return 'gaussian';
    });
    if (onClick) onClick();
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!interactive) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.max(10, Math.min(90, ((e.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(10, Math.min(90, ((e.clientY - rect.top) / rect.height) * 100));
    setMousePos({ x, y });
  };

  const sizeDimensions = {
    sm: { container: 'w-9 h-9', svg: 36, title: 'text-base', sub: 'text-[9px]' },
    md: { container: 'w-12 h-12', svg: 48, title: 'text-xl', sub: 'text-xs' },
    lg: { container: 'w-16 h-16', svg: 64, title: 'text-2xl', sub: 'text-sm' },
    xl: { container: 'w-24 h-24', svg: 96, title: 'text-3xl', sub: 'text-base' },
  }[size];

  const modeDiagnostics = {
    gaussian: {
      title: 'NORM / SHAPIRO-WILK',
      stat: 'W = 0.984 • p = .642 (PASSED)',
      color: 'from-sky-400 to-blue-500',
      text: 'text-sky-300',
      border: 'border-sky-400/40',
    },
    regression: {
      title: 'OLS / HC3 ROBUST FIT',
      stat: 'R² = .894 • F(3,48) = 42.1 (p < .001)',
      color: 'from-indigo-400 to-purple-500',
      text: 'text-indigo-300',
      border: 'border-indigo-400/40',
    },
    scatter: {
      title: 'UNIVARIATE DISTRIBUTION',
      stat: 'n = 54,600 OBS • 0 MISSING',
      color: 'from-emerald-400 to-teal-500',
      text: 'text-emerald-300',
      border: 'border-emerald-400/40',
    },
  }[mode];

  return (
    <div
      className={`relative inline-flex items-center gap-3.5 select-none ${
        interactive ? 'cursor-pointer group' : ''
      } ${className}`}
      onMouseEnter={() => interactive && setIsHovered(true)}
      onMouseLeave={() => interactive && setIsHovered(false)}
      onMouseMove={handleMouseMove}
      onClick={interactive ? handleLogoClick : undefined}
      title={interactive ? 'Click to cycle statistical engines (Gaussian Curve ↔ OLS Regression ↔ Raw Observations)' : undefined}
    >
      {/* Outer Scan Wave Effect on Click */}
      {isScanning && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-sky-400 via-indigo-500 to-emerald-400 opacity-60 animate-ping pointer-events-none z-0" />
      )}

      {/* Main Living Statistical Core Container */}
      <div
        className={`q-core-badge relative ${sizeDimensions.container} rounded-2xl flex items-center justify-center overflow-hidden transition-all duration-500 transform ${
          isHovered
            ? 'scale-105 shadow-2xl shadow-sky-500/40 bg-gradient-to-br from-slate-900 via-indigo-950/90 to-slate-900 border-sky-400/80'
            : 'shadow-lg shadow-sky-950/60 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/80 border-white/15 hover:border-white/30'
        } border z-10`}
      >
        {/* Ambient Statistical Grid Background */}
        <svg className="absolute inset-0 w-full h-full opacity-15 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="statGrid" width="8" height="8" patternUnits="userSpaceOnUse">
              <path d="M 8 0 L 0 0 0 8" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-sky-300" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#statGrid)" />
        </svg>

        {/* Orbiting Dual Engine Badges [R] & [Py] around perimeter */}
        <div className={`absolute top-1 left-1 px-1 py-0.2 rounded bg-sky-500/20 border border-sky-400/40 text-[7px] font-mono font-bold text-sky-300 tracking-tighter transition-opacity duration-300 ${isHovered ? 'opacity-100' : 'opacity-60'}`}>
          R
        </div>
        <div className={`absolute bottom-1 right-1 px-1 py-0.2 rounded bg-emerald-500/20 border border-emerald-400/40 text-[7px] font-mono font-bold text-emerald-300 tracking-tighter transition-opacity duration-300 ${isHovered ? 'opacity-100' : 'opacity-60'}`}>
          Py
        </div>

        {/* Living SVG Statistical Nexus (The Q-Engine) */}
        <svg
          width={sizeDimensions.svg}
          height={sizeDimensions.svg}
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10 overflow-visible"
        >
          <defs>
            {/* Multi-Spectrum Brand Gradient */}
            <linearGradient id="qCoreGrad" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#38bdf8" /> {/* Sky */}
              <stop offset="50%" stopColor="#818cf8" /> {/* Indigo */}
              <stop offset="100%" stopColor="#34d399" /> {/* Emerald */}
            </linearGradient>

            {/* Area Under Curve Shading */}
            <linearGradient id="curveAreaGrad" x1="50" y1="20" x2="50" y2="80" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.05" />
            </linearGradient>

            <filter id="laserGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* ==================== THE LETTER 'Q' SHIELD RING ==================== */}
          <circle
            cx="48"
            cy="46"
            r="35"
            stroke="url(#qCoreGrad)"
            strokeWidth={isHovered ? "4.5" : "3.8"}
            strokeDasharray={isHovered ? "8 3" : "none"}
            className="transition-all duration-700"
            style={{
              filter: isHovered ? 'drop-shadow(0px 0px 5px rgba(56, 189, 248, 0.7))' : 'none',
              transformOrigin: '48px 46px',
              transform: isHovered ? 'rotate(-45deg)' : 'rotate(0deg)',
            }}
          />

          {/* Precision Tail of 'Q' crossing the lower right border */}
          <path
            d="M 68 66 L 90 88"
            stroke="url(#qCoreGrad)"
            strokeWidth={isHovered ? "6.5" : "5.5"}
            strokeLinecap="round"
            className="transition-all duration-500"
            style={{
              filter: isHovered ? 'drop-shadow(0px 0px 6px rgba(52, 211, 153, 0.8))' : 'none',
            }}
          />

          {/* ==================== STATE 1: GAUSSIAN PROBABILITY CURVE ==================== */}
          <g
            className={`transition-all duration-500 transform ${
              mode === 'gaussian' ? 'opacity-100 scale-100' : 'opacity-0 scale-90 pointer-events-none'
            }`}
            style={{ transformOrigin: '48px 46px' }}
          >
            {/* Shaded Area Under the Curve (Confidence Region) */}
            <path
              d="M 18 64 Q 31 64 39 42 Q 48 14 57 42 Q 65 64 78 64 L 78 68 L 18 68 Z"
              fill="url(#curveAreaGrad)"
            />
            {/* Main Bell Curve Line */}
            <path
              d="M 18 64 Q 31 64 39 42 Q 48 14 57 42 Q 65 64 78 64"
              stroke="#38bdf8"
              strokeWidth="3.2"
              strokeLinecap="round"
              fill="none"
              filter="url(#laserGlow)"
            />
            {/* Mean Parameter Node (Peak) */}
            <circle cx="48" cy="14" r="3.5" fill="#38bdf8" />
            <circle cx="48" cy="14" r="1.5" fill="#ffffff" />
            {/* Standard Deviation Inflection Marks */}
            <line x1="39" y1="42" x2="39" y2="66" stroke="#818cf8" strokeWidth="1" strokeDasharray="2 2" />
            <line x1="57" y1="42" x2="57" y2="66" stroke="#34d399" strokeWidth="1" strokeDasharray="2 2" />
          </g>

          {/* ==================== STATE 2: OLS ROBUST REGRESSION FIT ==================== */}
          <g
            className={`transition-all duration-500 transform ${
              mode === 'regression' ? 'opacity-100 scale-100' : 'opacity-0 scale-90 pointer-events-none'
            }`}
            style={{ transformOrigin: '48px 46px' }}
          >
            {/* 95% Confidence Band Shading */}
            <path
              d="M 22 66 L 74 24 L 74 36 L 22 74 Z"
              fill="url(#curveAreaGrad)"
              opacity="0.6"
            />
            {/* Regression Trendline */}
            <line
              x1="20"
              y1="68"
              x2="76"
              y2="28"
              stroke="#818cf8"
              strokeWidth="3.2"
              strokeLinecap="round"
              filter="url(#laserGlow)"
            />
            {/* Data Observations Scatter around the Fit */}
            <circle cx="26" cy="62" r="2.5" fill="#38bdf8" />
            <circle cx="36" cy="58" r="2.5" fill="#34d399" />
            <circle cx="48" cy="46" r="3" fill="#ffffff" filter="url(#laserGlow)" />
            <circle cx="58" cy="38" r="2.5" fill="#38bdf8" />
            <circle cx="68" cy="34" r="2.5" fill="#a855f7" />
            {/* Residual Distance Indicator */}
            <line x1="36" y1="58" x2="36" y2="56" stroke="#fb7185" strokeWidth="1.2" />
          </g>

          {/* ==================== STATE 3: UNIVARIATE SCATTER CLOUD ==================== */}
          <g
            className={`transition-all duration-500 transform ${
              mode === 'scatter' ? 'opacity-100 scale-100' : 'opacity-0 scale-90 pointer-events-none'
            }`}
            style={{ transformOrigin: '48px 46px' }}
          >
            {/* Cluster of Data Coordinates */}
            <circle cx="30" cy="52" r="3" fill="#38bdf8" className="animate-pulse" />
            <circle cx="38" cy="36" r="2.5" fill="#34d399" />
            <circle cx="44" cy="58" r="3.2" fill="#818cf8" />
            <circle cx="52" cy="32" r="2.8" fill="#38bdf8" />
            <circle cx="58" cy="48" r="3.5" fill="#a855f7" />
            <circle cx="66" cy="40" r="2.5" fill="#34d399" />
            <circle cx="48" cy="45" r="4" fill="#ffffff" filter="url(#laserGlow)" />
            {/* Inter-node Distance Links (Statistical Cluster) */}
            <line x1="38" y1="36" x2="48" y2="45" stroke="#38bdf8" strokeWidth="0.8" strokeOpacity="0.5" />
            <line x1="58" y1="48" x2="48" y2="45" stroke="#818cf8" strokeWidth="0.8" strokeOpacity="0.5" />
            <line x1="52" y1="32" x2="48" y2="45" stroke="#34d399" strokeWidth="0.8" strokeOpacity="0.5" />
          </g>

          {/* ==================== INTERACTIVE LASER CROSSHAIR (ON HOVER) ==================== */}
          {isHovered && (
            <g className="pointer-events-none transition-all duration-75">
              {/* Vertical Crosshair Line */}
              <line
                x1={mousePos.x}
                y1="16"
                x2={mousePos.x}
                y2="76"
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="2 2"
                strokeOpacity="0.8"
              />
              {/* Horizontal Crosshair Line */}
              <line
                x1="16"
                y1={mousePos.y}
                x2="80"
                y2={mousePos.y}
                stroke="#34d399"
                strokeWidth="1"
                strokeDasharray="2 2"
                strokeOpacity="0.8"
              />
              {/* Active Intersection Target Dot */}
              <circle
                cx={mousePos.x}
                cy={mousePos.y}
                r="3"
                fill="#ffffff"
                stroke="#38bdf8"
                strokeWidth="1.5"
                filter="url(#laserGlow)"
              />
            </g>
          )}
        </svg>

        {/* Real-Time Telemetry HUD Overlay (Appears on Hover) */}
        {interactive && isHovered && (
          <div className="absolute inset-x-0 bottom-0 py-0.5 px-1.5 bg-slate-950/95 border-t border-sky-400/40 text-[7px] font-mono font-semibold text-sky-200 flex items-center justify-between tracking-tight z-20 animate-fade-in">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              <span>{modeDiagnostics.title}</span>
            </span>
            <span className="text-slate-400">
              x:{Math.round(mousePos.x)}, y:{Math.round(100 - mousePos.y)}
            </span>
          </div>
        )}
      </div>

      {/* Brand Typography & Active Software Telemetry */}
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className={`font-extrabold ${sizeDimensions.title} tracking-tight brand-title-gradient group-hover:from-sky-200 group-hover:to-emerald-300 transition-all duration-300`}>
              StatAid Studio
            </span>
            <span className="brand-pill-sky text-[10px] px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-300 font-medium font-mono group-hover:border-sky-400 transition-all flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ENGINE: {mode.toUpperCase()}</span>
            </span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`brand-pill-stat text-[11px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border ${modeDiagnostics.border} ${modeDiagnostics.text} font-medium transition-all`}>
              {modeDiagnostics.stat}
            </span>
            <span className="text-[11px] text-slate-400 hidden sm:inline">
              • Research-First Transparency
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
