// 状态元数据 + Badge 组件
import { cn } from "@/lib/utils";

export type TaskStatus = "planning" | "ready" | "active" | "check" | "done" | "failed";

export const ST_META: Record<string, { label: string; icon: string; colorVar: string }> = {
  planning: { label: "规划中", icon: "fa-pencil-square-o", colorVar: "--st-planning" },
  ready:    { label: "待执行", icon: "fa-clock-o",        colorVar: "--st-ready" },
  active:   { label: "执行中", icon: "fa-spinner",         colorVar: "--st-active" },
  check:    { label: "待验收", icon: "fa-eye",             colorVar: "--st-check" },
  done:     { label: "已完成", icon: "fa-check",           colorVar: "--st-done" },
  failed:   { label: "失败",   icon: "fa-times-circle",    colorVar: "--st-failed" },
};

export const ST_ORDER = ["planning", "ready", "active", "check", "done"];

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const meta = ST_META[status] || ST_META.planning;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap",
        className
      )}
      style={{
        backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 16%, transparent)`,
        color: `var(${meta.colorVar})`,
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
