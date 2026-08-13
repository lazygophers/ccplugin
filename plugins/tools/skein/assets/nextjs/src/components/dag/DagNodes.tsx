"use client";

// 看板 DAG 节点类型: taskCard (普通 task) 和 taskGroup (supertask 容器)
// SubtaskCardNode (子任务 mini), DepTaskNode (依赖图)

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { PriorityBadge } from "@/components/priority";
import { ST_META } from "@/components/status";
import { cn } from "@/lib/utils";
import type { NormTask, NormSubtask } from "@/lib/model";

// 四方向 Handle (隐藏, 供 RF 边路由分散用)
const HANDLES = (
  <>
    <Handle id="top" type="target" position={Position.Top} style={{ opacity: 0, top: 0 }} />
    <Handle id="bottom" type="source" position={Position.Bottom} style={{ opacity: 0, bottom: 0 }} />
    <Handle id="left" type="target" position={Position.Left} style={{ opacity: 0, left: 0 }} />
    <Handle id="right" type="source" position={Position.Right} style={{ opacity: 0, right: 0 }} />
  </>
);

// ── 普通任务卡片 ──
export const TaskCardNode = memo(function TaskCardNode({ data, selected }: NodeProps) {
  const task = data.task as NormTask;
  if (!task) return null;

  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;
  const subs = (task.subtasks || []) as NormSubtask[];
  const subDone = subs.filter(s => s.status === "done").length;

  return (
    <div className="dag-node-wrap group relative">
      {HANDLES}
      <div
        className={cn(
          "flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md",
          selected && "ring-2 ring-primary",
          st === "active" && "dag-node-active",
        )}
        style={{
          width: "280px",
          minHeight: "80px",
          borderColor: `var(${meta.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 20%, var(--card))`,
        }}
      >
        <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full ml-2.5" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <div className="min-w-0 flex-1 pr-2.5">
          <div className="flex items-center gap-1.5">
            <div className="min-w-0 flex-1 text-base font-semibold leading-tight text-foreground break-words">
              {task.title || task.name || task.id}
            </div>
            <PriorityBadge priority={task.priority} />
          </div>
          <div className="flex items-center text-base leading-tight text-muted-foreground">
            <span className="font-mono">#{task.id}</span>
            {subs.length > 0 && <span className="flex-shrink-0 ml-1">{subDone}/{subs.length}</span>}
          </div>
        </div>
      </div>

      {/* Hover 悬浮卡片 — CSS group-hover */}
      <div className="pointer-events-none absolute left-0 top-full z-[9999] mt-2 w-96 rounded-lg border border-border/40 bg-card/95 p-5 shadow-xl backdrop-blur-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-150">
        <div className="mb-2 flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
          <span className="text-base font-semibold text-foreground">{task.title || task.name || task.id}</span>
          <span className="ml-auto rounded px-2 py-0.5 text-base font-medium text-white" style={{ backgroundColor: `var(${meta.colorVar})` }}>{meta.label}</span>
        </div>
        <div className="mb-2 font-mono text-base text-muted-foreground">#{task.id}</div>
        {(task.desc || task.description) && (
          <div className="mb-2 line-clamp-3 text-base leading-relaxed text-muted-foreground">{task.desc || task.description}</div>
        )}
        {subs.length > 0 && (
          <div className="mb-2">
            <div className="flex items-center justify-between text-base text-muted-foreground">
              <span>子任务进度</span>
              <span>{subDone}/{subs.length}</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full transition-all" style={{ width: `${subs.length ? Math.round(subDone / subs.length * 100) : 0}%`, backgroundColor: `var(${meta.colorVar})` }} />
            </div>
          </div>
        )}
        {(task.deps && task.deps.length > 0) && (
          <div className="text-base text-muted-foreground">依赖: {task.deps.join(", ")}</div>
        )}
      </div>
    </div>
  );
});

// ── Supertask 容器节点 (分组框) ──
export const TaskGroupNode = memo(function TaskGroupNode({ data, selected }: NodeProps) {
  const task = data.task as NormTask;
  if (!task) return null;

  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;

  // 优先用 data.childDone/childTotal (布局层传入的子 task 完成统计)
  // 回退到 subtask 统计
  const childDone = (data.childDone as number) ?? 0;
  const childTotal = (data.childTotal as number) ?? 0;
  const subs = (task.subtasks || []) as NormSubtask[];
  const doneCount = childTotal > 0 ? childDone : subs.filter(c => c.status === "done").length;
  const totalCount = childTotal > 0 ? childTotal : subs.length;
  const pct = totalCount ? Math.round((doneCount / totalCount) * 100) : 0;

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
        pointerEvents: "none",
      }}
    >
      <div
        className="dag-group-header flex cursor-pointer items-center gap-2 overflow-hidden rounded-t-md border-b px-2"
        style={{
          borderColor: `var(${meta.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 22%, var(--card))`,
          pointerEvents: "auto",
        }}
      >
        <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <span className="truncate text-base font-semibold text-foreground">
          {task.title || task.name || task.id}
        </span>
        <span className="ml-auto flex-shrink-0 font-mono text-base text-muted-foreground">
          {doneCount}/{totalCount}
        </span>
        <div className="ml-1 h-1.5 w-12 flex-shrink-0 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: `var(${meta.colorVar})` }} />
        </div>
      </div>
    </div>
  );
});

// ── Subtask mini 卡片 (详情面板内嵌 + detail 页) ──
export const SubtaskCardNode = memo(function SubtaskCardNode({ data }: NodeProps) {
  const sub = data.sub as NormSubtask;
  if (!sub) return null;

  const sm = ST_META[sub.status] || ST_META.planning;

  return (
    <div className="group relative">
      {HANDLES}
      <div
        className={cn(
          "flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md",
          // running subtask 归一化后就是 active, 和 task 卡共用同一套脉冲动效
          sub.status === "active" && "dag-node-active",
        )}
        style={{
          width: "260px",
          minHeight: "72px",
          opacity: sub.status === "done" ? 0.5 : 1,
          borderColor: `var(${sm.colorVar})`,
          backgroundColor: `color-mix(in srgb, var(${sm.colorVar}) 20%, var(--card))`,
        }}
      >
        <span className="ml-2.5 h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
        <div className="min-w-0 flex-1 pr-2.5">
          <div className="text-base font-semibold leading-tight text-foreground break-words">{sub.title || sub.name || sub.id}</div>
          <div className="text-base leading-tight text-muted-foreground">{sm.label}</div>
        </div>
      </div>

      {/* Hover 悬浮卡片 */}
      <div className="pointer-events-none absolute left-0 top-full z-[9999] mt-2 w-96 rounded-lg border border-border/40 bg-card/95 p-5 shadow-xl backdrop-blur-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-150">
        <div className="mb-2 flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
          <span className="text-base font-semibold text-foreground">{sub.title || sub.name || sub.id}</span>
          <span className="ml-auto rounded px-2 py-0.5 text-base font-medium text-white" style={{ backgroundColor: `var(${sm.colorVar})` }}>{sm.label}</span>
        </div>
        <div className="mb-2 font-mono text-base text-muted-foreground">{sub.sid}</div>
        {sub.desc && <div className="mb-2 line-clamp-3 text-base leading-relaxed text-muted-foreground">{sub.desc}</div>}
        {sub.estimate && <div className="text-base text-muted-foreground">预估: {sub.estimate}h</div>}
      </div>
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
    <div className="group relative">
      {HANDLES}
      <div
        className={cn(
          "flex items-center gap-2 rounded-md border px-2 py-1 transition-all hover:shadow-md",
          isCenter && "ring-2 ring-primary",
          task.status === "active" && "dag-node-active",
        )}
        style={{
          width: "200px",
          minHeight: "48px",
          borderColor: `color-mix(in srgb, var(${meta.colorVar}) 30%, var(--border))`,
          backgroundColor: "var(--card)",
        }}
      >
        <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
        <span className="flex-1 text-base font-medium text-foreground break-words">{task.title || task.name || task.id}</span>
        {isCenter && <span className="text-base text-primary">★</span>}
      </div>
    </div>
  );
});
