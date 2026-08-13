"use client";

export function ProgressBar({ value, max = 100, colorVar = "--st-active", showLabel = true, className = "" }: {
  value: number | null | undefined;
  max?: number;
  colorVar?: string;
  showLabel?: boolean;
  className?: string;
}) {
  const pct = value != null ? Math.min(100, Math.max(0, Math.round((value / max) * 100))) : 0;
  const isDone = pct >= 100;
  const color = `var(${colorVar})`;
  const shimmerColor = `linear-gradient(90deg, ${color} 0%, color-mix(in srgb, ${color} 60%, #ffffff) 50%, ${color} 100%)`;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="progress-bar-track flex-1">
        <div
          className={`progress-bar-fill ${!isDone && pct > 0 ? "animated" : ""}`}
          style={{
            width: `${pct}%`,
            background: !isDone && pct > 0 ? shimmerColor : color,
          }}
        />
      </div>
      {showLabel && <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">{pct}%</span>}
    </div>
  );
}
