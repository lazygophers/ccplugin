// 状态元数据 + Badge 组件
import { cn } from "@/lib/utils";
import { Pencil, Search, Loader2, Eye, Flag, Check, XCircle, type LucideIcon } from "lucide-react";

export type TaskStatus = "planning" | "research" | "active" | "check" | "finishing" | "done" | "failed";

export const ST_META: Record<string, { label: string; icon: LucideIcon; colorVar: string }> = {
  // 标签对齐 model.py PHASE_OF: pending=plan(计划中) / active=exec(进行中)
  planning:  { label: "计划中", icon: Pencil,      colorVar: "--st-planning" },
  research:  { label: "调研中", icon: Search,      colorVar: "--st-research" },
  active:    { label: "进行中", icon: Loader2,     colorVar: "--st-active" },
  check:     { label: "待验收", icon: Eye,         colorVar: "--st-check" },
  finishing: { label: "收尾中", icon: Flag,        colorVar: "--st-finishing" },
  done:      { label: "已完成", icon: Check,       colorVar: "--st-done" },
  failed:    { label: "失败",   icon: XCircle,     colorVar: "--st-failed" },
};

// 看板列排序 = 生命周期时序: 规划 → 调研 → 执行 → 验收 → 收尾 → 完成
export const ST_ORDER = ["planning", "research", "active", "check", "finishing", "done"];

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
