// 优先级 Badge + Select — 唯一呈现单元, 看板卡片/详情页/看板抽屉共用同一映射来源 (lib/model.ts)
import { PRIORITY_LABEL, PRIORITY_COLOR_VAR } from "@/lib/model";
import { cn } from "@/lib/utils";

// 描边小标签: 文字色+边框色同色, 无底色 — 优先级是辅助信息, 不与状态徽章抢视觉权重
export function PriorityBadge({ priority, className }: { priority: string; className?: string }) {
  const colorVar = PRIORITY_COLOR_VAR[priority] || "--muted-foreground";
  const label = PRIORITY_LABEL[priority] || priority || "中";
  return (
    <span
      className={cn("flex-shrink-0 rounded border px-1 text-[9px] font-medium leading-tight", className)}
      style={{ color: `var(${colorVar})`, borderColor: `var(${colorVar})` }}
    >
      {label}
    </span>
  );
}

export function PrioritySelect({ value, onChange, className }: { value: string; onChange: (val: string) => void; className?: string }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={cn("rounded-md border border-border bg-card/60 px-2 py-1 text-sm text-foreground", className)}
    >
      {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  );
}
