"use client";

// 看板 DAG 节点类型: taskCard (普通 task) 和 taskGroup (supertask 容器)
// SubtaskCardNode (子任务 mini), DepTaskNode (依赖图)

import { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { PriorityBadge } from "@/components/priority";
import { ST_META } from "@/components/status";
import { cn } from "@/lib/utils";
import type { NormTask, NormSubtask } from "@/lib/model";

// ── 普通任务卡片 ──
export const TaskCardNode = memo(function TaskCardNode({ data, selected }: NodeProps) {
  const task = data.task as NormTask;
  const [hovered, setHovered] = useState(false);
  if (!task) return null;

  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;
  const subs = (task.subtasks || []) as NormSubtask[];
  const subDone = subs.filter(s => s.status === "done").length;

  return (
    <div
      className="dag-node-wrap relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0, top: 0 }} />
      <div
        className={cn(
          "flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md",
          selected && "ring-2 ring-primary",
          st === "active" && "dag-node-active",
        )}
        style={{
          borderColor: `var(${meta.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 20%, var(--card))`,
        }}
      >
        <span className="h-2 w-2 flex-shrink-0 rounded-full ml-2" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <div className="min-w-0 flex-1 pr-2">
          <div className="flex items-center gap-1.5">
            <div className="min-w-0 flex-1 truncate text-xs font-semibold leading-tight text-foreground">
              {task.title || task.name || "(未命名)"}
            </div>
            <PriorityBadge priority={task.priority} />
          </div>
          <div className="flex items-center text-[10px] leading-tight text-muted-foreground">
            <span className="truncate font-mono">#{task.id}</span>
            {subs.length > 0 && <span className="flex-shrink-0 ml-1">{subDone}/{subs.length}</span>}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, bottom: 0 }} />

      {/* Hover 悬浮卡片 */}
      {hovered && (
        <div className="pointer-events-none absolute left-0 top-full z-50 mt-2 w-80 rounded-lg border border-border/40 bg-card/95 p-4 shadow-xl backdrop-blur-md">
          <div className="mb-1.5 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
            <span className="text-xs font-semibold text-foreground">{task.title || task.name || task.id}</span>
            <span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium text-white" style={{ backgroundColor: `var(${meta.colorVar})` }}>{meta.label}</span>
          </div>
          <div className="mb-1.5 font-mono text-[10px] text-muted-foreground">#{task.id}</div>
          {(task.desc || task.description) && (
            <div className="mb-2 line-clamp-3 text-xs leading-relaxed text-muted-foreground">{task.desc || task.description}</div>
          )}
          {subs.length > 0 && (
            <div className="mb-1.5">
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>子任务进度</span>
                <span>{subDone}/{subs.length}</span>
              </div>
              <div className="mt-0.5 h-1 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full transition-all" style={{ width: `${subs.length ? Math.round(subDone / subs.length * 100) : 0}%`, backgroundColor: `var(${meta.colorVar})` }} />
              </div>
            </div>
          )}
          {(task.deps && task.deps.length > 0) && (
            <div className="text-[10px] text-muted-foreground">依赖: {task.deps.join(", ")}</div>
          )}
        </div>
      )}
    </div>
  );
});

// ── Supertask 容器节点 (分组框) ──
export const TaskGroupNode = memo(function TaskGroupNode({ data, selected }: NodeProps) {
  const task = data.task as NormTask;
  if (!task) return null;

  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;
  const subs = (task.subtasks || []) as NormSubtask[];
  const doneCount = subs.filter(c => c.status === "done").length;
  const pct = subs.length ? Math.round((doneCount / subs.length) * 100) : 0;

  return (
    <div
      className={cn(
        "dag-group-box flex flex-col rounded-lg border-2 border-dashed",
        selected && "ring-2 ring-primary",
      )}
      style={{
        borderColor: `var(${meta.colorVar})`,
        backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 6%, transparent)`,
        width: "100%",
        height: "100%",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0, top: 0 }} />
      <div
        className="dag-group-header flex cursor-pointer items-center gap-2 overflow-hidden rounded-t-md border-b px-2"
        style={{
          borderColor: `var(${meta.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 22%, var(--card))`,
        }}
      >
        <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <span className="truncate text-xs font-semibold text-foreground">
          {task.title || task.name || task.id}
        </span>
        <span className="ml-auto flex-shrink-0 font-mono text-[10px] text-muted-foreground">
          {doneCount}/{subs.length}
        </span>
        <div className="ml-1 h-1.5 w-12 flex-shrink-0 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: `var(${meta.colorVar})` }} />
        </div>
      </div>
      <div className="flex-1" />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, bottom: 0 }} />
    </div>
  );
});

// ── Subtask mini 卡片 (详情面板内嵌 + detail 页) ──
export const SubtaskCardNode = memo(function SubtaskCardNode({ data }: NodeProps) {
  const sub = data.sub as NormSubtask;
  if (!sub) return null;

  const sm = ST_META[sub.status] || ST_META.planning;

  return (
    <div>
      <Handle type="target" position={Position.Top} style={{ opacity: 0, top: 0 }} />
      <div
        className="flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md"
        style={{
          opacity: sub.status === "done" ? 0.5 : 1,
          borderColor: `var(${sm.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${sm.colorVar}) 20%, var(--card))`,
        }}
        title={sub.title || sub.name || sub.id}
      >
        <span className="ml-2 h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
        <div className="min-w-0 flex-1 pr-2">
          <div className="truncate text-xs font-semibold leading-tight text-foreground">{sub.title || sub.name || sub.id}</div>
          <div className="truncate text-[10px] leading-tight text-muted-foreground">{sm.label}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, bottom: 0 }} />
    </div>
  );
});

// ── 依赖图节点 (task detail 页上下游图) ──
export const DepTaskNode = memo(function DepTaskNode({ data }: NodeProps) {
  const task = data.task as NormTask;
  if (!task) return null;
  const meta = ST_META[task.status] || ST_META.planning;
  const isCenter = data.isCenter as boolean;

  return (
    <div>
      <Handle type="target" position={Position.Top} style={{ opacity: 0, top: 0 }} />
      <div
        className={cn(
          "flex items-center gap-2 rounded-md border px-2 py-1 transition-all hover:shadow-md",
          isCenter && "ring-2 ring-primary",
        )}
        style={{
          borderColor: `color-mix(in srgb, var(${meta.colorVar}) 30%, var(--border))`,
          backgroundColor: "var(--card)",
        }}
        title={task.title || task.name || task.id}
      >
        <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <span className="flex-1 truncate text-xs font-medium text-foreground">{task.title || task.name || task.id}</span>
        {isCenter && <span className="text-xs text-primary">★</span>}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, bottom: 0 }} />
    </div>
  );
});
