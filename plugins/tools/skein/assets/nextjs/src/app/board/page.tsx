"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META, ST_ORDER } from "@/components/status";
import { api, ApiError, type Task } from "@/lib/api";
import { normalizeTasks, normalizeTask, normalizeStatus, applyTaskChangedBatch, type NormTask, type NormSubtask } from "@/lib/model";
import { PriorityBadge, PrioritySelect } from "@/components/priority";
import { subscribe } from "@/lib/live";
import { Archive, Network, List, CheckSquare, Square, Check, Link2, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { fmtRelative, fmtTime } from "@/lib/format";
import { renderMd } from "@/lib/md";
import { etaOf, etaText, fmtHours, actualOf, deltaText, overallSummary } from "@/lib/eta";
import { layoutBoardDAG, layoutSubtaskDAG } from "@/lib/elk-layout";
import { DagFlow, DagFlowProvider, TaskCardNode, TaskGroupNode, SubtaskCardNode } from "@/components/dag";
import { ProgressBar } from "@/components/progress-bar";
import { useToast } from "@/components/toast";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { IconApprove, IconFinish, IconRevert, IconDetail, IconTrash, IconClose, IconCopyMini } from "@/components/icons";
import type { Node, Edge } from "@xyflow/react";

const ALL_STATUSES = ["planning", "research", "active", "check", "finishing", "done"];
const DEFAULT_ACTIVE = ["planning", "research", "active", "check", "finishing"];  // 「全选/取消」基准 — 排除 done
const DEFAULT_FILTER = new Set(DEFAULT_ACTIVE);

// React Flow node types (stable ref)
const BOARD_NODE_TYPES = { taskCard: TaskCardNode, taskGroup: TaskGroupNode };

// ── Components ──

export default function BoardPage() {
  const toast = useToast();
  const [allTasks, setAllTasks] = useState<NormTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"dag" | "list">("dag");
  const [statusSet, setStatusSet] = useState<Set<string>>(new Set(DEFAULT_FILTER));
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailTask, setDetailTask] = useState<NormTask | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailRev, setDetailRev] = useState(0);  // bump to force detail refetch
  const [viewBox, setViewBox] = useState({ w: 1200, h: 800 });
  const wrapRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLDivElement>(null);
  const [confirmAction, setConfirmAction] = useState<{ type: "delete" | "finish" | "clean"; id: string; name: string } | null>(null);
  type PoolStats = { work: { limit: number; running: number }; gate: { limit: number; running: number } };
  const [pools, setPools] = useState<PoolStats | null>(null);

  useEffect(() => {
    api.data().then((r) => {
      const raw = r as unknown as Record<string, unknown>;
      const cards = (raw.cards || raw.tasks || []) as unknown as Record<string, unknown>[];
      const overview = (raw.overview as Record<string, unknown>) || {};
      const maxActive = (overview.maxActive as number) || 2;
      const tasks = normalizeTasks(cards).map(t => { (t as Record<string, unknown>).maxActive = maxActive; return t; });
      setAllTasks(tasks);
      if (overview.pools) setPools(overview.pools as PoolStats);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  // 逐 task 变更消息 → 局部更新卡片 (不整页重载); 全局 "reload"/"data" 兜底仍由 LiveBootstrap 处理整页刷。
  // 批量抗抖: 同一帧内收到的多条消息攒进 pending, 用 rAF 合并成一次 setAllTasks (一次重排),
  // 避免批量调度场景下每条消息各自触发一次昂贵的 DAG 布局重算。
  useEffect(() => {
    const pending: { id: string; card: Record<string, unknown> | null }[] = [];
    let flushHandle: number | null = null;
    const flush = () => {
      flushHandle = null;
      if (!pending.length) return;
      const batch = pending.splice(0, pending.length);
      setAllTasks(prev => {
        const maxActive = (prev[0] as Record<string, unknown> | undefined)?.maxActive ?? 2;
        return applyTaskChangedBatch(prev, batch, { maxActive });
      });
    };
    const unsub = subscribe((msg) => {
      if (msg.type !== "task-changed") return;
      pending.push(msg);
      if (flushHandle == null) flushHandle = requestAnimationFrame(flush);
    });
    return () => { unsub(); if (flushHandle != null) cancelAnimationFrame(flushHandle); };
  }, []);

  // Measure available canvas width
  useEffect(() => {
    function measure() {
      if (!wrapRef.current) return;
      const w = Math.max(400, wrapRef.current.clientWidth);
      const h = Math.max(600, wrapRef.current.clientHeight);
      setViewBox(prev => Math.abs(prev.w - w) > 40 || Math.abs(prev.h - h) > 40 ? { w, h } : prev);
    }
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [view, selectedId]);

  const countBy = useMemo(() => {
    const c: Record<string, number> = {};
    for (const t of allTasks) c[t.status] = (c[t.status] || 0) + 1;
    return c;
  }, [allTasks]);

  const summary = useMemo(() => overallSummary(allTasks, 2), [allTasks]);

  const selectedTask = detailTask;

  // 选中 task 变化 → 拉详情接口 (list 只含 DAG 必要字段, 详情需独立请求)
  useEffect(() => {
    if (!selectedId) { setDetailTask(null); return; }
    setDetailLoading(true);
    api.task(selectedId).then((raw) => {
      const r = raw as unknown as Record<string, unknown>;
      // 详情接口返回 {task: {...}, subtasks, timeline, prd, ...} — 合并到一层再 normalize
      const taskData = (r.task || {}) as Record<string, unknown>;
      const merged = { ...taskData, ...r } as Record<string, unknown>;
      delete merged.task;  // 去掉嵌套 task key
      const maxActive = (allTasks[0] as Record<string, unknown> | undefined)?.maxActive ?? 2;
      const t = normalizeTask(merged);
      (t as Record<string, unknown>).maxActive = maxActive;
      setDetailTask(t);
    }).catch(() => setDetailTask(null)).finally(() => setDetailLoading(false));
  }, [selectedId, detailRev]);

  const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
  const toggleStatus = (st: string) => {
    setStatusSet(prev => { const next = new Set(prev); if (next.has(st)) next.delete(st); else next.add(st); return next; });
  };
  const toggleAll = () => setStatusSet(allSelected ? new Set(DEFAULT_ACTIVE) : new Set(ALL_STATUSES));

  const cleanDone = () => setConfirmAction({ type: "clean", id: "", name: "" });

  // 页面直接改优先级: 复用白名单 exec 通道; 成功后本地乐观更新 (无需等 mtime 轮询), 失败给明确错误。
  // exec 端点 CLI 失败时仍返回 HTTP 200 (body.ok=false + stderr), 不会走 fetch 的 catch — 必须显式查 ok。
  const handlePriorityChange = async (id: string, val: string) => {
    try {
      await api.priority(id, val);
      setAllTasks(prev => prev.map(t => t.id === id ? { ...t, priority: val } : t));
      if (id === selectedId) setDetailRev(r => r + 1);
      toast("优先级已更新", "success");
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "优先级更新失败", "error");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-h-0 flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex flex-1 flex-col p-6 overflow-hidden">
          {/* Header row */}
          <div className="mb-4 flex flex-wrap items-center gap-3 flex-shrink-0">
            <div className="flex-shrink-0">
              <h1 className="mb-0.5 text-2xl font-bold text-foreground">任务看板</h1>
              <p className="text-xs text-muted-foreground">{allTasks.length} 个任务 · {ALL_STATUSES.filter(s => statusSet.has(s)).length} 个高亮</p>
              <div className="mt-1.5 flex items-center gap-2">
                <div className="h-1.5 w-28 overflow-hidden rounded-full bg-muted sm:w-44">
                  <div className="h-full bg-primary transition-all duration-500" style={{ width: `${summary.pct}%` }} />
                </div>
                <span className="whitespace-nowrap text-xs text-muted-foreground">整体 {summary.pct}% · 预计剩余 {summary.remainText}</span>
              </div>
            </div>
            {/* 两池占用 (design.md §3): work = exec+research 并发, gate = check+finishing 并发 */}
            {pools && (
              <div className="flex flex-shrink-0 flex-col gap-1 text-xs text-muted-foreground">
                {(["work", "gate"] as const).map(name => {
                  const p = pools[name];
                  const full = p.running >= p.limit;
                  return (
                    <div key={name} className="flex items-center gap-1.5">
                      <span className="w-8 font-mono uppercase">{name}</span>
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                        <div className="h-full transition-all duration-500"
                             style={{ width: `${Math.min(100, (p.running / Math.max(1, p.limit)) * 100)}%`,
                                      backgroundColor: `var(${name === "work" ? "--st-active" : "--st-check"})` }} />
                      </div>
                      <span className={cn("whitespace-nowrap font-mono", full && "text-foreground font-semibold")}>{p.running}/{p.limit}</span>
                    </div>
                  );
                })}
              </div>
            )}
            {/* Status filter */}
            <div className="flex flex-1 flex-wrap items-center gap-2">
              <button onClick={toggleAll} className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors", allSelected ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/50")}>
                全部
              </button>
              {ALL_STATUSES.map(st => (
                <button key={st} onClick={() => toggleStatus(st)} className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors", statusSet.has(st) ? "text-foreground" : "border-border text-muted-foreground opacity-50 hover:opacity-80")} style={statusSet.has(st) ? { borderColor: `var(${ST_META[st].colorVar})`, backgroundColor: `color-mix(in srgb, var(${ST_META[st].colorVar}) 25%, transparent)` } : {}}>
                  {ST_META[st].label} ({countBy[st] || 0})
                </button>
              ))}
            </div>
            {/* Tools */}
            <div className="flex flex-shrink-0 items-center gap-3">
              {countBy.done > 0 && (
                <button onClick={cleanDone} title="归档全部已完成任务" className="rounded-full border border-border bg-transparent px-3 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/30">
                  <Archive className="mr-1.5 inline h-3.5 w-3.5" />清理已完成
                </button>
              )}
              {/* View toggle */}
              <div className="flex items-center gap-1 rounded-lg border border-border bg-card/60 p-1">
                <button onClick={() => setView("dag")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-colors", view === "dag" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground")}><Network className="mr-1.5 inline h-3.5 w-3.5" />DAG</button>
                <button onClick={() => setView("list")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-colors", view === "list" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground")}><List className="mr-1.5 inline h-3.5 w-3.5" />列表</button>
              </div>
            </div>
          </div>

          {/* Main area: DAG/list + optional detail panel (absolute overlay, 不压缩 DAG 画布) */}
          <div ref={mainRef} className="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-border/30 bg-transparent">
            {/* DAG/List canvas — 始终占满容器，详情面板浮在其上 */}
            <div className={cn("absolute inset-0 board-dag-wrap", view === "list" ? "overflow-hidden" : "overflow-hidden")} ref={wrapRef}>
              {loading ? (
                <div className="py-16 text-center text-muted-foreground">加载中…</div>
              ) : view === "dag" ? (
                <DagFlowProvider>
                  <BoardDagCanvas tasks={allTasks} statusSet={statusSet} onSelect={setSelectedId} selectedId={selectedId} />
                </DagFlowProvider>
              ) : (
                <ListView tasks={allTasks} statusSet={statusSet} onSelect={setSelectedId} />
              )}
            </div>

            {/* Right: Detail panel */}
            {selectedId && !selectedTask && detailLoading && (
              <aside className="detail-panel absolute right-0 top-0 flex h-full w-[456px] items-center justify-center border-l border-border/30 bg-card/60 backdrop-blur-md rounded-r-lg z-10">
                <span className="text-sm text-muted-foreground">加载中…</span>
              </aside>
            )}
            {selectedTask && (
              <DetailPanel task={selectedTask} allTasks={allTasks} onClose={() => setSelectedId(null)}
                onConfirm={async (id) => { try { await api.confirm(id); toast("已确认规划", "success"); setDetailRev(r => r + 1); } catch (e) { toast(e instanceof ApiError ? e.message : "确认失败", "error"); } }}
                onRevert={async (id) => { try { await api.revert(id); toast("已回退到规划", "success"); setDetailRev(r => r + 1); } catch (e) { toast(e instanceof ApiError ? e.message : "回退失败", "error"); } }}
                onFinish={(id, name) => setConfirmAction({ type: "finish", id, name })}
                onDelete={(id, name) => setConfirmAction({ type: "delete", id, name })}
                onPriorityChange={handlePriorityChange}
                onSelectTask={setSelectedId}
              />
            )}
          </div>

          {/* Edge legend */}
          {view === "dag" && !loading && (
            <div className="mt-2 flex flex-shrink-0 flex-wrap items-center gap-3 text-xs text-muted-foreground">
              {[
                { color: "--st-done", label: "依赖已完成" },
                { color: "--st-active", label: "阻塞 · 上游可执行" },
                { color: "--st-failed", label: "阻塞 · 上游被卡" },
              ].map(e => (
                <span key={e.label} className="flex items-center gap-1">
                  <svg width="26" height="10"><path d="M 1 5 L 25 5" fill="none" stroke={`var(${e.color})`} strokeWidth={2} /></svg>
                  {e.label}
                </span>
              ))}
            </div>
          )}

          <ConfirmDialog
            open={!!confirmAction}
            title={confirmAction?.type === "delete" ? "删除任务" : confirmAction?.type === "finish" ? "强制完成" : "归档已完成任务"}
            message={confirmAction?.type === "delete"
              ? `确认删除 "${confirmAction?.name}"？删除后可从回收站恢复。`
              : confirmAction?.type === "finish"
              ? `确认强制完成 "${confirmAction?.name}"？将合并 worktree 并标记为已完成。`
              : `归档所有已完成任务？(等价 skein clean --days=0)`}
            confirmText={confirmAction?.type === "delete" ? "删除" : confirmAction?.type === "finish" ? "完成" : "归档"}
            destructive={confirmAction?.type === "delete" || confirmAction?.type === "clean"}
            onCancel={() => setConfirmAction(null)}
            onConfirm={async () => {
              if (!confirmAction) return;
              const { type, id } = confirmAction;
              setConfirmAction(null);
              try {
                if (type === "delete") { await api.del(id); setSelectedId(null); toast("已删除", "success"); }
                else if (type === "finish") { await api.finish(id, true); toast("已完成", "success"); setDetailRev(r => r + 1); }
                else { try { await api.clean(0); toast("清理完成", "success"); } catch (e) { toast(e instanceof ApiError ? e.message : "清理失败", "error"); } setTimeout(() => window.location.reload(), 500); }
              } catch (e) { toast(e instanceof ApiError ? e.message : "操作失败", "error"); }
            }}
          />
        </main>
      </div>
    </div>
  );
}

// ── Board DAG Canvas (React Flow) ──
function BoardDagCanvas({ tasks, statusSet, onSelect, selectedId }: {
  tasks: NormTask[];
  statusSet: Set<string>;
  onSelect: (id: string) => void;
  selectedId: string | null;
}) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [layoutLoading, setLayoutLoading] = useState(true);

  useEffect(() => {
    if (!tasks.length) { setNodes([]); setEdges([]); setLayoutLoading(false); return; }
    setLayoutLoading(true);
    layoutBoardDAG(tasks, "compact").then(({ nodes, edges }) => {
      setNodes(nodes);
      setEdges(edges);
      setLayoutLoading(false);
    });
  }, [tasks]);

  const nodeStatusOf = useMemo(() => (node: Node) => {
    const task = node.data?.task as NormTask | undefined;
    return task?.status || "planning";
  }, []);

  if (layoutLoading) return <div className="py-16 text-center text-muted-foreground">布局计算中…</div>;
  if (!nodes.length) return <div className="py-16 text-center text-muted-foreground">暂无任务</div>;

  return (
    <DagFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={BOARD_NODE_TYPES}
      dimStatusSet={statusSet}
      selectedId={selectedId}
      onSelect={onSelect}
      nodeStatusOf={nodeStatusOf}
      enableHoverChain={true}
    />
  );
}

// ── List View ──
function ListView({ tasks, statusSet, onSelect }: { tasks: NormTask[]; statusSet: Set<string>; onSelect: (id: string) => void }) {
  const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
  return (
    <div className="grid h-full grid-cols-1 gap-4 overflow-hidden p-2 md:grid-cols-2 xl:grid-cols-3">
      {ALL_STATUSES.map(st => {
        const list = tasks.filter(t => (t.status || "planning") === st);
        const meta = ST_META[st];
        const isDimmed = !allSelected && !statusSet.has(st);
        return (
          <div key={st} className={cn("flex max-h-full flex-col rounded-lg border border-border/30 bg-card/40 p-4", isDimmed && "opacity-40")}>
            <div className="mb-4 flex flex-shrink-0 items-center gap-2">
              <span className="h-3 w-3 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
              <span className="text-sm font-semibold text-foreground">{meta.label}</span>
              <span className="ml-auto text-xs text-muted-foreground">{list.length}</span>
            </div>
            <div className="min-h-0 flex-1 space-y-2 overflow-y-auto">
              {list.length ? list.map(t => (
                <div key={t.id} onClick={() => onSelect(t.id)} className={cn("flex cursor-pointer items-center gap-2 rounded-lg p-2 transition-colors hover:bg-muted/30", st === "active" && "dag-node-active")}>
                  {(() => { const Icon = meta.icon; return <Icon className="h-3 w-3" style={{ color: `var(${meta.colorVar})` }} />; })()}
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-foreground">{t.title || t.name || "(未命名)"}</div>
                    <div className="truncate font-mono text-xs text-muted-foreground">#{t.id}</div>
                  </div>
                  <PriorityBadge priority={t.priority} />
                </div>
              )) : <div className="py-6 text-center text-xs text-muted-foreground">暂无</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Detail Panel ──
function DetailPanel({ task, allTasks, onClose, onConfirm, onRevert, onFinish, onDelete, onPriorityChange, onSelectTask }: {
  task: NormTask; allTasks: NormTask[]; onClose: () => void;
  onConfirm: (id: string) => void; onRevert: (id: string) => void; onFinish: (id: string, name: string) => void; onDelete: (id: string, name: string) => void;
  onPriorityChange: (id: string, val: string) => void; onSelectTask: (id: string) => void;
}) {
  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;
  const maxActive = ((task as Record<string, unknown>).maxActive as number) || 2;
  const eta = etaText(task as unknown as Parameters<typeof etaText>[0], maxActive);
  const subs = (task.subtasks || []) as NormSubtask[];
  const subDone = subs.filter(s => s.status === "done").length;

  return (
    <aside className="detail-panel absolute right-0 top-0 flex h-full w-[456px] flex-col border-l border-border/30 bg-card/60 backdrop-blur-md rounded-r-lg overflow-hidden shadow-xl z-10">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <StatusBadge status={st} />
            <CopyableId id={task.id} />
          </div>
          <h3 className="text-base font-semibold leading-tight text-foreground" style={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{task.title || task.name || "(未命名)"}</h3>
        </div>
        <div className="flex items-center gap-1.5">
          {st === "planning" && (
            <button onClick={() => onConfirm(task.id)} data-tip="确认规划 → 激活执行" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-1.5 text-primary hover:bg-primary/10"><IconApprove /></button>
          )}
          {st === "check" && (
            <button onClick={() => onRevert(task.id)} data-tip="回退到规划" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-1.5 text-primary hover:bg-primary/10"><IconRevert /></button>
          )}
          {(st === "active" || st === "check") && (
            <button onClick={() => onFinish(task.id, task.title || task.name || task.id)} data-tip="强制完成" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-1.5 text-primary hover:bg-primary/10"><IconFinish /></button>
          )}
          <Link href={`/task/detail/?id=${task.id}`} prefetch={false} data-tip="打开详情页" className="icon-btn flex items-center justify-center rounded-md border border-border p-1.5 text-muted-foreground hover:bg-muted/30 hover:text-foreground"><IconDetail /></Link>
          <button onClick={() => onDelete(task.id, task.title || task.name || task.id)} data-tip="删除任务" className="icon-btn flex items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-1.5 text-destructive hover:bg-destructive/20"><IconTrash /></button>
          <button onClick={onClose} data-tip="关闭" className="icon-btn flex items-center justify-center rounded-md p-1.5 text-muted-foreground hover:bg-muted/30 hover:text-foreground"><IconClose /></button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {/* Basic info */}
        <DetailCard title="基本信息">
          <InfoRow label="优先级" value={
            <PrioritySelect value={task.priority} onChange={(val) => onPriorityChange(task.id, val)} />
          } />
          <InfoRow label="预估工时" value={task.estimate ? `${task.estimate} h` : "—"} />
          <InfoRow label="进度" value={<ProgressBar value={Number((task as Record<string, unknown>).spct ?? task.progress ?? (st === "done" ? 100 : 0))} colorVar={meta.colorVar} />} />
          {st === "done" ? (() => { const a = actualOf(task as unknown as Parameters<typeof actualOf>[0]); if (!a) return null; const dt = deltaText(a.delta); return <InfoRow label="实际耗时" value={`${fmtHours(a.hours)}${dt ? ` (${dt})` : ""}`} />; })()
            : <InfoRow label="预计剩余" value={eta ? eta.main : "—"} />}
        </DetailCard>

        {/* Description */}
        <DetailCard title="任务描述">
          <p className="whitespace-pre-wrap text-sm text-foreground">{task.description || task.desc || "暂无描述"}</p>
        </DetailCard>

        {/* ETA detail */}
        {eta?.detail && <div className="text-xs text-muted-foreground">{eta.detail}</div>}

        {/* PRD sections */}
        {(() => {
          const prdData = ((task as Record<string, unknown>).prd) as { name: string; items?: { text: string; done?: boolean; kind?: string }[]; badge?: [number, number] }[] | undefined;
          if (!prdData?.length) return null;
          return prdData.map((sec, i) => (
            <DetailCard key={i} title={`${sec.name}${sec.badge ? ` (${sec.badge[0]}/${sec.badge[1]})` : ""}`}>
              {sec.items?.length ? (
                <div className="space-y-1.5">
                  {sec.items.map((item, j) => (
                    <div key={j} className="flex items-start gap-2 text-sm">
                      {item.done ? <CheckSquare className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--st-done)" }} /> : <Square className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />}
                      <span className={item.done ? "text-muted-foreground line-through" : "text-foreground"}>{item.text}</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-muted-foreground">—</p>}
            </DetailCard>
          ));
        })()}

        {/* Parent/Child relationship */}
        {(() => {
          const parentId = (task.parent as string | null) || null;
          const parent = parentId ? allTasks.find(t => t.id === parentId) : null;
          const children = allTasks.filter(t => (t.parent as string | null) === task.id);
          if (!parentId && children.length === 0) return null;
          return (
            <DetailCard title="父子关系">
              {parentId && (
                <div className="mb-2">
                  <div className="mb-1 text-xs text-muted-foreground">父任务</div>
                  {parent ? (
                    <div onClick={() => onSelectTask(parent.id)} className="flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                      <StatusDot status={parent.status} className="mt-0.5" />
                      <span className="truncate text-sm text-foreground">{parent.title || parent.name || parent.id}</span>
                    </div>
                  ) : (
                    <Link href={`/task/detail/?id=${parentId}`} prefetch={false} className="flex items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                      <span className="truncate text-sm text-muted-foreground">{parentId}</span>
                    </Link>
                  )}
                </div>
              )}
              {children.length > 0 && (
                <div>
                  <div className="mb-1 text-xs text-muted-foreground">子任务 ({children.length})</div>
                  <div className="space-y-1">
                    {children.map(c => (
                      <div key={c.id} onClick={() => onSelectTask(c.id)} className="flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                        <StatusDot status={c.status} className="mt-0.5" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm text-foreground">{c.title || c.name || c.id}</div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-foreground">{ST_META[c.status]?.label || c.status}</span>
                            <div className="flex-1"><ProgressBar value={Number((c as Record<string, unknown>).spct ?? c.progress ?? 0)} colorVar={(ST_META[c.status] || ST_META.planning).colorVar} showLabel={false} /></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </DetailCard>
          );
        })()}

        {/* Subtask DAG */}
        {subs.length >= 2 && (
          <DetailCard title="子任务 DAG">
            <SubtaskDag subs={subs} />
          </DetailCard>
        )}

        {/* Dep links (upstream/downstream) */}
        {(() => {
          const depIds = (task.deps || []) as string[];
          const depNames = ((task as Record<string, unknown>).depNames || []) as string[];
          const upstream = depIds.map((id, i) => {
            const found = allTasks.find(t => t.id === id);
            return found || { id, name: depNames[i] || id, title: depNames[i] || id, status: "done" } as NormTask;
          });
          const downstream = allTasks.filter(t => (t.deps || []).includes(task.id));
          if (!upstream.length && !downstream.length) return null;
          return (
            <DetailCard title="依赖关系">
              {upstream.length > 0 && (
                <div className="mb-3">
                  <div className="mb-1.5 flex items-center gap-1 text-xs text-muted-foreground"><Link2 className="h-3 w-3" />前置依赖</div>
                  <div className="space-y-1">
                    {upstream.map(d => {
                      const live = allTasks.find(t => t.id === d.id);
                      return live ? (
                        <div key={d.id} onClick={() => onSelectTask(d.id)} className="flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                          <StatusDot status={d.status} className="mt-0.5" />
                          <span className="truncate text-sm text-foreground">{d.title || d.name || d.id}</span>
                        </div>
                      ) : (
                        <Link key={d.id} href={`/task/detail/?id=${d.id}`} prefetch={false} className="flex items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                          <span className="truncate text-sm text-muted-foreground">{d.title || d.name || d.id}</span>
                          <span className="text-[10px] text-muted-foreground/60">(已归档)</span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
              {downstream.length > 0 && (
                <div>
                  <div className="mb-1.5 flex items-center gap-1 text-xs text-muted-foreground"><Share2 className="h-3 w-3" />被依赖</div>
                  <div className="space-y-1">
                    {downstream.map(d => (
                      <div key={d.id} onClick={() => onSelectTask(d.id)} className="flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/30">
                        <StatusDot status={d.status} className="mt-0.5" />
                        <span className="truncate text-sm text-foreground">{d.title || d.name || d.id}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </DetailCard>
          );
        })()}

        {/* Timeline */}
        <DetailCard title="生命周期时间线">
          <TaskTimeline task={task} eta={eta} subs={subs} />
        </DetailCard>
      </div>
    </aside>
  );
}

function DetailCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/30 bg-card/60 p-4">
      <h4 className="mb-3 text-sm font-semibold text-primary">{title}</h4>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-3 py-1.5">
      <span className="w-20 flex-shrink-0 text-sm text-muted-foreground">{label}</span>
      <div className="flex-1 text-sm text-foreground">{value || "—"}</div>
    </div>
  );
}

function CopyableId({ id, label }: { id: string; label?: string }) {
  const toast = useToast();
  return (
    <span
      onClick={() => { navigator.clipboard?.writeText(id); toast(`已复制 ${label || "ID"}: ${id}`, "success"); }}
      className="copyable-id group inline-flex cursor-pointer items-center gap-1 font-mono text-xs text-muted-foreground transition-colors hover:text-primary"
      title={`点击复制 ${label || "ID"}: ${id}`}
    >
      <span>#{id}</span>
      <IconCopyMini className="opacity-0 transition-opacity group-hover:opacity-100" />
    </span>
  );
}

// ── Task Timeline (buildTimeline port) ──
const STAGE_ORDER: Record<string, number> = { planning: 0, active: 1, check: 2, done: 3 };
const STAGE_COLORS: Record<string, string> = {
  created: "#74b9e8", started: "#237bb8", checked: "#c9a227", finished: "#48bb78",
};

function TaskTimeline({ task, eta, subs }: { task: NormTask; eta: { main: string; detail: string } | null; subs: NormSubtask[] }) {
  const st = task.status || "planning";
  const idx = STAGE_ORDER[st];
  const byTs = idx == null;
  const at = (i: number, ts: number | null) => byTs ? !!ts : idx > i;
  const stages = [
    { key: "planning", label: "规划中", desc: "任务规划与 PRD 编写", time: task.createdAt, done: idx > 0, current: idx === 0, color: STAGE_COLORS.created },
    { key: "started", label: "执行", desc: "任务执行中", time: task.startedAt, done: idx > 1, current: idx === 1, color: STAGE_COLORS.started },
    { key: "checked", label: "验收", desc: "checkpoint 核对", time: task.checkedAt, done: idx > 2, current: idx === 2, color: STAGE_COLORS.checked },
    { key: "finished", label: "完成", desc: "任务完成", time: task.finishedAt, done: byTs ? !!task.finishedAt : idx >= 3, current: false, color: STAGE_COLORS.finished },
  ];

  return (
    <div>
      {eta && <div className="mb-3 text-xs text-muted-foreground">{eta.main}{eta.detail ? ` · ${eta.detail}` : ""}</div>}
      <div className="relative pl-4">
        <div className="absolute left-[5px] top-0 h-full w-px bg-border" />
        {stages.map((s) => {
          const done = s.done;
          const current = s.current;
          return (
            <div key={s.key} className="relative mb-3 last:mb-0">
              <span className={cn("absolute -left-4 top-1 h-2.5 w-2.5 rounded-full border-2 border-background", current && "tl-dot-active")} style={{ backgroundColor: done || current ? s.color : "var(--muted)", color: s.color }} />
              <div className="flex items-center gap-2">
                <span className={cn("text-xs font-medium text-foreground", current && "tl-label-active")}>{s.label}</span>
                <span className={cn("text-[10px]", done ? "text-muted-foreground" : "text-muted-foreground/60")}>
                  {done ? fmtTime(s.time) : current ? "当前" : "待执行"}
                </span>
              </div>
              <div className="text-[10px] text-muted-foreground">{s.desc}</div>
              {s.key === "started" && subs.length > 0 && (
                <details open className="mt-1 ml-2">
                  <summary className="cursor-pointer select-none text-[10px] text-muted-foreground">子任务</summary>
                  <div className="mt-1 space-y-1 border-l border-border/30 pl-3">
                    {[...subs].sort((a, b) => {
                      // done 按 finishedAt 降序排最前; 其余按原序在后
                      const ad = a.status === "done" ? 0 : 1;
                      const bd = b.status === "done" ? 0 : 1;
                      if (ad !== bd) return ad - bd;
                      if (ad === 0) return (b.finishedAt || 0) - (a.finishedAt || 0);
                      return 0;
                    }).map(sub => {
                      const sm = ST_META[sub.status] || ST_META.planning;
                      const isDone = sub.status === "done";
                      return (
                        <div key={sub.sid} className="flex items-start gap-2">
                          {isDone ? (
                            <span className="mt-0.5 flex h-3.5 w-3.5 flex-shrink-0 items-center justify-center rounded-full text-[8px] text-white" style={{ backgroundColor: `var(${sm.colorVar})` }}>
                              <Check className="h-2.5 w-2.5" />
                            </span>
                          ) : (
                            <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
                          )}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-[11px] text-foreground">{sub.title || sub.name || sub.sid}</span>
                              <span onClick={() => navigator.clipboard?.writeText(sub.sid)} className="cursor-pointer flex-shrink-0 font-mono text-[9px] text-muted-foreground/60 hover:text-primary" title={`点击复制: ${sub.sid}`}>{sub.sid}</span>
                              {sub.status === "active" && <span className="h-1 w-1 flex-shrink-0 rounded-full bg-primary tl-dot-active" style={{ position: "relative" }} />}
                            </div>
                            <div className="text-[10px] text-muted-foreground">{sm.label}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Subtask DAG (React Flow mini) ──
const SUBTASK_NODE_TYPES = { subtaskCard: SubtaskCardNode };

function SubtaskDag({ subs }: { subs: NormSubtask[] }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    if (!subs.length) return;
    layoutSubtaskDAG(subs).then(({ nodes, edges }) => {
      setNodes(nodes);
      setEdges(edges);
    });
  }, [subs]);

  if (!subs.length) return <div className="py-4 text-center text-xs text-muted-foreground">暂无子任务</div>;

  return (
    <div style={{ height: "250px" }}>
      <DagFlowProvider>
        <DagFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={SUBTASK_NODE_TYPES}
          minHeight={200}
          enableHoverChain={false}
          showControls={false}
        />
      </DagFlowProvider>
    </div>
  );
}
