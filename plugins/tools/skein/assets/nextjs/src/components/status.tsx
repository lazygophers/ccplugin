// 状态元数据 + Badge 组件
import { cn } from "@/lib/utils";

export type TaskStatus = "planning" | "ready" | "research" | "active" | "check" | "finishing" | "done" | "failed";

export const ST_META: Record<string, { label: string; icon: string; colorVar: string }> = {
  planning:  { label: "规划中", icon: "fa-pencil-square-o", colorVar: "--st-planning" },
  ready:     { label: "待执行", icon: "fa-clock-o",        colorVar: "--st-ready" },
  research:  { label: "调研中", icon: "fa-search",          colorVar: "--st-research" },
  active:    { label: "执行中", icon: "fa-spinner",         colorVar: "--st-active" },
  check:     { label: "待验收", icon: "fa-eye",             colorVar: "--st-check" },
  finishing: { label: "收尾中", icon: "fa-flag-checkered",  colorVar: "--st-finishing" },
  done:      { label: "已完成", icon: "fa-check",           colorVar: "--st-done" },
  failed:    { label: "失败",   icon: "fa-times-circle",    colorVar: "--st-failed" },
};

// 看板列排序 = 生命周期时序: 规划 → 调研 → (就绪, 遗留兼容态) → 执行 → 验收 → 收尾 → 完成
export const ST_ORDER = ["planning", "research", "ready", "active", "check", "finishing", "done"];

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const meta = ST_META[status] || ST_META.planning;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap st-badge",
        className
      )}
      style={{
        backgroundColor: `var(${meta.colorVar})`,
        color: "#ffffff",
      }}
    >
      {meta.label}
    </span>
  );
}

export function StatusDot({ status, className }: { status: string; className?: string }) {
  const meta = ST_META[status] || ST_META.planning;
  return (
    <span
      className={cn("inline-block h-2 w-2 rounded-full flex-shrink-0", className)}
      style={{ backgroundColor: `var(${meta.colorVar})` }}
    />
  );
}
