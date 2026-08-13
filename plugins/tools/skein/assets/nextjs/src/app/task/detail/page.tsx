"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useCallback, useMemo, useRef } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META } from "@/components/status";
import { api, ApiError } from "@/lib/api";
import { normalizeTask, normalizeTasks, type NormTask, type NormSubtask } from "@/lib/model";
import { PrioritySelect } from "@/components/priority";
import { subscribe } from "@/lib/live";
import { fmtRelative, fmtTime } from "@/lib/format";
import { AlertTriangle, Flag, Check, XCircle, CheckSquare, Square, History, Share2, Network, Link2, Settings as Cog, Target, FileText, FlaskConical, type LucideIcon } from "lucide-react";
import { renderMd } from "@/lib/md";
import { etaOf, etaText, fmtHours, actualOf, deltaText, type EtaResult } from "@/lib/eta";
import { layoutSubtaskDAG, layoutDepDAG } from "@/lib/elk-layout";
import { DagFlow, DagFlowProvider, SubtaskCardNode, DepTaskNode } from "@/components/dag";
import type { Node, Edge } from "@xyflow/react";
import { ProgressBar } from "@/components/progress-bar";
import { useToast } from "@/components/toast";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { IconApprove, IconFinish, IconTrash, IconCopyMini } from "@/components/icons";
import { cn } from "@/lib/utils";

// ── Timeline stages ──
// timeline (task.json 落盘的 TimelineEvent[]) 存在时按其渲染六段骨架 (对齐 TaskStatus 六态);
// 缺失/为空 (老 task 无该字段) 回落旧的按当前状态推算的四段渲染。
interface TimelineEvent { kind: "task" | "subtask"; status: string; at: number; sid: string | null; note: string; rollback: boolean }
interface Stage { key: string; label: string; desc: string; color: string; time: number | null; done: boolean; current: boolean; rounds?: number }

const STAGE_ORDER: Record<string, number> = { planning: 0, active: 1, check: 2, done: 3 };
const STAGE_COLORS: Record<string, string> = {
  created: "#74b9e8", started: "#237bb8", checked: "#c9a227", finished: "#48bb78",
};

// 六段骨架恒定 (kind=task 的六个 TaskStatus), 与后端 skeinlib/task/model.py TaskStatus 对齐
const STAGE_META: { key: string; label: string; desc: string; color: string }[] = [
  { key: "pending", label: "待处理", desc: "任务创建与规划", color: "#74b9e8" },
  { key: "research", label: "调研中", desc: "需求调研与方案设计", color: "#8e7cc3" },
  { key: "active", label: "执行中", desc: "任务执行中，子任务调度", color: "#237bb8" },
  { key: "check", label: "检查中", desc: "checkpoint 核对 + 场景自适应校验", color: "#c9a227" },
  { key: "finishing", label: "收尾中", desc: "验收通过，归档收尾", color: "#e08e45" },
  { key: "done", label: "已完成", desc: "任务完成，归档沉淀", color: "#48bb78" },
];

function buildStagesFromTimeline(task: NormTask, timeline: TimelineEvent[]): Stage[] {
  return STAGE_META.map((meta): Stage => {
    const events = timeline.filter(e => e.kind === "task" && e.status === meta.key);
    const occurred = events.length > 0;
    return {
      key: meta.key, label: meta.label, desc: meta.desc, color: meta.color,
      time: occurred ? events[0].at * 1000 : null,
      done: occurred,
      current: task.status === meta.key,
      rounds: events.length,
    };
  });
}

function buildStagesLegacy(task: NormTask): Stage[] {
  const st = task.status || "planning";
  const idx = STAGE_ORDER[st];
  const byTs = idx == null;
  return [
    { key: "planning", label: "规划中", desc: "任务规划与 PRD 编写", time: task.createdAt, done: idx > 0, current: idx === 0, color: STAGE_COLORS.created },
    { key: "started", label: "执行", desc: "任务执行中，子任务调度", time: task.startedAt, done: idx > 1, current: idx === 1, color: STAGE_COLORS.started },
    { key: "checked", label: "验收", desc: "checkpoint 核对 + 场景自适应校验", time: task.checkedAt, done: idx > 2, current: idx === 2, color: STAGE_COLORS.checked },
    { key: "finished", label: "完成", desc: "任务完成，归档沉淀", time: task.finishedAt, done: byTs ? !!task.finishedAt : idx >= 3, current: false, color: STAGE_COLORS.finished },
  ];
}

function buildStages(task: NormTask): Stage[] {
  const timeline = task.timeline as TimelineEvent[] | undefined;
  if (Array.isArray(timeline) && timeline.length > 0) return buildStagesFromTimeline(task, timeline);
  return buildStagesLegacy(task);
}

function isPlaceholder(src: string): boolean {
  if (!src) return true;
  return !String(src).split("\n").some(l => {
    const s = l.trim();
    if (!s) return false;
    if (/^#{1,6}\s/.test(s)) return false;
    if (/^>/.test(s)) return false;
    if (/[:：]$/.test(s)) return false;
    return true;
  });
}

function TaskDetailContent() {
  const toast = useToast();
  const params = useSearchParams();
  const id = params.get("id") || "";
  const [task, setTask] = useState<NormTask | null>(null);
  const [raw, setRaw] = useState<Record<string, unknown> | null>(null);
  const [depTasks, setDepTasks] = useState<NormTask[]>([]);
  const [dependents, setDependents] = useState<NormTask[]>([]);
  const [docs, setDocs] = useState<{ prd?: string; design?: string; findings?: string }>({});
  const [research, setResearch] = useState<Record<string, string>>({});
  const [prd, setPrd] = useState<{ name: string; items?: { text: string; done?: boolean; kind?: string }[]; badge?: [number, number] }[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{ type: "delete" | "finish" } | null>(null);

  const load = useCallback(() => {
    if (!id) return;
    api.task(id).then((r) => {
      const resp = r as unknown as Record<string, unknown>;
      const taskRaw = resp.task
        ? {
            ...(resp.task as Record<string, unknown>), docs: resp.docs, research: resp.research,
            prd: resp.prd, progress: resp.progress, stage: resp.stage,
            parentTask: resp.parentTask, childTasks: resp.childTasks,
          }
        : (resp.card || resp);
      setRaw(taskRaw as Record<string, unknown>);
      setTask(normalizeTask(taskRaw as Record<string, unknown>));
      setDepTasks(normalizeTasks((resp.depTasks || []) as Record<string, unknown>[]));
      setDependents(normalizeTasks((resp.dependents || []) as Record<string, unknown>[]));
      const d = resp.docs as Record<string, string> | undefined;
      if (d) setDocs({ prd: d.prd, design: d.design, findings: d.findings });
      setResearch((resp.research as Record<string, string>) || {});
      const p = resp.prd as { name: string; items?: { text: string; done?: boolean; kind?: string }[]; badge?: [number, number] }[] | undefined;
      setPrd(p || []);
    }).catch(() => setNotFound(true));
  }, [id]);

  useEffect(() => { load(); }, [load]);

  // 详情页订阅本 task 的变更消息 → 触发 load() 重拉完整数据 (含 docs/prd/subtask/契约/依赖)。
  // 不做局部 card 合并: card 只携带看板卡片展示字段 (见 views.py _cards_signature), 缺 docs/research/prd
  // 等详情页富内容 —— 仅 spread 合并会让 prd.md / design.md / research/ 的编辑在前端永远不刷新
  // (典型「前端不刷新」bug)。load() 一次完整 GET /__skein__/task 是 O(单 task) 的, 详情页只看一个 task,
  // 重拉开销可接受。抗抖: 多条 task-changed 攒到一起一次 load (批量调度场景)。
  // card 为空 = task 已归档/删除, 直接判定详情页不存在。
  useEffect(() => {
    if (!id) return;
    let pending = false;
    const flush = () => { pending = false; load(); };
    const unsubGlobal = subscribe((msg) => {
      if (msg.type === "data") load();
    });
    const unsubTask = subscribe((msg) => {
      if (msg.type !== "task-changed") return;
      if (!msg.card) { setNotFound(true); setTask(null); return; }
      if (!pending) { pending = true; requestAnimationFrame(flush); }
    }, { taskId: id });
    return () => { unsubGlobal(); unsubTask(); };
  }, [id, load]);

  // 页面直接改优先级: 复用白名单 exec 通道; 成功后本地乐观更新, 失败给明确错误 (不静默失败)。
  // exec 端点 CLI 失败时仍返回 HTTP 200 (body.ok=false + stderr), 不会走 fetch 的 catch — 必须显式查 ok。
  const handlePriorityChange = async (val: string) => {
    if (!task) return;
    try {
      await api.priority(task.id, val);
      setTask(prev => prev ? { ...prev, priority: val } : prev);
      setRaw(prev => prev ? { ...prev, priority: val } : prev);
      toast("优先级已更新", "success");
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "优先级更新失败", "error");
    }
  };

  const depAll = useMemo(() => task ? [task, ...depTasks, ...dependents] : [], [task, depTasks, dependents]);

  if (notFound) return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="py-16 text-center">
            <AlertTriangle className="mb-3 h-10 w-10 text-muted-foreground opacity-40" />
            <h2 className="text-lg font-semibold text-foreground">任务不存在</h2>
            <p className="mt-1 text-sm text-muted-foreground">ID: {id}</p>
            <Link prefetch={false} href="/tasks/" className="mt-3 inline-block text-sm text-primary hover:underline">返回任务列表</Link>
          </div>
        </main>
      </div>
    </div>
  );

  if (!task) return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6"><div className="py-16 text-center text-muted-foreground">加载中…</div></main>
      </div>
    </div>
  );

  const st = task.status || "planning";
  const meta = ST_META[st] || ST_META.planning;
  const subs = task.subtasks || [];
  const subDone = subs.filter(s => s.status === "done").length;
  const maxActive = (raw?.maxActive as number) || 2;
  const eta = etaText(task as unknown as Parameters<typeof etaText>[0], maxActive);
  const stages = buildStages(task);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          {/* Breadcrumb + Title */}
          <div className="mb-6">
            <nav className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Link prefetch={false} href="/dashboard/" className="hover:text-foreground">概览</Link>
              <span className="opacity-40">/</span>
              <Link prefetch={false} href="/board/" className="hover:text-foreground">看板</Link>
              {(() => {
                const pt = raw?.parentTask as Record<string, unknown> | undefined;
                if (!pt?.id) return null;
                return (
                  <>
                    <span className="opacity-40">/</span>
                    <Link prefetch={false} href={`/task/detail/?id=${pt.id}`} className="hover:text-foreground">{pt.name as string || pt.id as string}</Link>
                  </>
                );
              })()}
              <span className="opacity-40">/</span>
              <span className="text-foreground">{task.title || task.name || task.id}</span>
            </nav>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="mb-2 flex items-center gap-3">
                  {(() => { const Icon = meta.icon; return <Icon className="h-5 w-5" style={{ color: `var(${meta.colorVar})` }} />; })()}
                  <h1 className="text-3xl font-bold text-foreground">{task.title || task.name || "(未命名)"}</h1>
                </div>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span className="copyable-id group inline-flex cursor-pointer items-center gap-1 font-mono text-muted-foreground transition-colors hover:text-primary" onClick={() => { navigator.clipboard?.writeText(task.id); toast(`已复制: ${task.id}`, "success"); }} title="点击复制">
                    #{task.id}
                    <IconCopyMini className="opacity-0 transition-opacity group-hover:opacity-100" />
                  </span>
                  {task.createdAt && <><span className="opacity-40">·</span><span>创建于 {fmtRelative(task.createdAt)}</span></>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {st === "planning" && (
                  <button onClick={async () => { try { await api.confirm(task.id); toast("已确认规划", "success"); setTimeout(load, 500); } catch (e) { toast(e instanceof ApiError ? e.message : "确认失败", "error"); } }} data-tip="确认规划 → 激活执行" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-2 text-primary hover:bg-primary/10">
                    <IconApprove size={18} />
                  </button>
                )}
                {st === "check" && (
                  <button onClick={() => setConfirmAction({ type: "finish" })} data-tip="完成收尾" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-2 text-primary hover:bg-primary/10">
                    <IconFinish size={18} />
                  </button>
                )}
                <StatusBadge status={st} className="px-4 py-1 text-base" />
                <button onClick={() => setConfirmAction({ type: "delete" })} data-tip="删除任务" className="icon-btn flex items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-2 text-destructive hover:bg-destructive/20">
                  <IconTrash size={18} />
                </button>
              </div>
            </div>
          </div>

          {/* Two-column layout: left=meta, right=content */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            {/* Left: meta info */}
            <div className="min-w-0 space-y-4">
              {/* Basic info */}
              <Card title="基本信息">
                <InfoRow label="优先级" value={
                  <PrioritySelect value={task.priority} onChange={handlePriorityChange} />
                } />
                {task.assignee ? <InfoRow label="负责人" value={String(task.assignee)} /> : null}
                <InfoRow label="预估工时" value={task.estimate ? `${task.estimate} 小时` : "—"} />
                <InfoRow label="进度" value={<ProgressBar value={Number(task.progress ?? (st === "done" ? 100 : 0))} colorVar={meta.colorVar} />} />
                {st === "done" ? (() => {
                  const a = actualOf(task as unknown as Parameters<typeof actualOf>[0]);
                  if (!a) return null;
                  const dt = deltaText(a.delta);
                  return <InfoRow label="实际耗时" value={`${fmtHours(a.hours)}${dt ? ` (${dt})` : ""}`} />;
                })() : <InfoRow label="预计剩余" value={eta ? eta.main : "—"} />}
              </Card>

              {/* Timeline */}
              <Card title="生命周期时间线" icon={History}>
                {eta && <div className="mb-3 text-xs text-muted-foreground">{eta.main}{eta.detail ? ` · ${eta.detail}` : ""}</div>}
                <div className="relative pl-4">
                  <div className="absolute left-[5px] top-0 h-full w-px bg-border" />
                  {stages.map((s) => {
                    const done = s.done;
                    const current = s.current;
                    const subsOfTask = subs;
                    return (
                      <div key={s.key} className="relative mb-3 last:mb-0">
                        <span className={cn("absolute -left-4 top-1 h-2.5 w-2.5 rounded-full border-2 border-background", current && "tl-dot-active")} style={{ backgroundColor: done || current ? s.color : "var(--muted)", color: s.color }} />
                        <div className="flex items-center gap-2">
                          <span className={cn("text-xs font-medium text-foreground", current && "tl-label-active")}>{s.label}</span>
                          <span className={`text-[10px] ${done ? "text-muted-foreground" : "text-muted-foreground/60"}`}>
                            {done ? fmtTime(s.time) : current ? "当前" : "待执行"}
                          </span>
                          {done && (s.rounds || 0) > 1 && <span className="text-[10px] text-muted-foreground" title={`经历 ${s.rounds} 次该阶段 (含回滚重入)`}>↺{s.rounds}轮</span>}
                          {(s.key === "started" || s.key === "active") && subsOfTask.length > 0 && <span className="text-[10px] text-muted-foreground">{subDone}/{subsOfTask.length} 子任务</span>}
                        </div>
                        <div className="text-[10px] text-muted-foreground">{s.desc}</div>
                        {(s.key === "started" || s.key === "active") && subsOfTask.length > 0 && <SubTimeline subs={subsOfTask} taskId={task.id} />}
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Subtask list */}
              {subs.length > 0 && (
                <Card title="子任务列表" icon={CheckSquare}>
                  <div className="space-y-2">
                    {subs.map(s => (
                      <div key={s.sid} className="flex items-start gap-3 rounded-md p-2 transition-colors hover:bg-muted/30">
                        <StatusDot status={s.status} className="mt-1.5" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate text-xs font-medium text-foreground">{s.title || s.name || s.sid}</span>
                            <span className="cursor-pointer font-mono text-[10px] text-muted-foreground hover:text-primary transition-colors" onClick={() => { navigator.clipboard?.writeText(s.sid); toast(`已复制: ${s.sid}`, "success"); }} title="点击复制">{s.sid}</span>
                          </div>
                          {s.desc && <div className="mt-0.5 break-words text-[11px] text-muted-foreground overflow-hidden">{s.desc}</div>}
                          <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                            <span>{ST_META[s.status]?.label || s.status}</span>
                            {s.estimate ? <span>预估 {s.estimate}h</span> : null}
                            {s.dependsOn && s.dependsOn.length > 0 && (
                              <span className="flex items-center gap-0.5" title={`依赖: ${s.dependsOn.join(", ")}`}>
                                <Link2 className="h-2.5 w-2.5" />
                                {s.dependsOn.map(d => {
                                  const dep = subs.find(x => x.sid === d);
                                  return dep?.title || dep?.name || d;
                                }).join(", ")}
                              </span>
                            )}
                          </div>
                        </div>
                        {s.progress != null && <span className="text-[10px] text-muted-foreground">{s.progress}%</span>}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Dep DAG */}
              {(depTasks.length > 0 || dependents.length > 0) && (
                <Card title={`依赖关系图 (${depTasks.length + dependents.length + 1})`} icon={Share2}>
                  <DepDagView taskId={task.id} allTasks={depAll} />
                </Card>
              )}

              {/* Parent/Child relationship */}
              {(() => {
                const pt = raw?.parentTask as Record<string, unknown> | undefined;
                const ct = (raw?.childTasks || []) as Record<string, unknown>[];
                if (!pt && ct.length === 0) return null;
                return (
                <Card title="父子关系" icon={Network}>
                  {pt && (
                    <div className="mb-2">
                      <div className="mb-1 text-[10px] text-muted-foreground">父任务</div>
                      <Link prefetch={false} href={`/task/detail/?id=${pt.id}`} className="flex items-start gap-2 rounded-md p-2 transition-colors hover:bg-muted/30">
                        <StatusDot status={pt.status as string} className="mt-1.5" />
                        <div className="min-w-0 flex-1">
                          <div className="text-sm text-foreground">{pt.name as string}</div>
                          <div className="text-[10px] text-muted-foreground">{ST_META[pt.status as string]?.label || (pt.status as string)}</div>
                        </div>
                      </Link>
                    </div>
                  )}
                  {ct.length > 0 && (
                    <div>
                      <div className="mb-1 text-[10px] text-muted-foreground">子任务 ({ct.length})</div>
                      <div className="space-y-1">
                        {ct.map(c => (
                          <Link key={c.id as string} prefetch={false} href={`/task/detail/?id=${c.id}`} className="flex items-start gap-2 rounded-md p-2 transition-colors hover:bg-muted/30">
                            <StatusDot status={c.status as string} className="mt-1.5" />
                            <div className="min-w-0 flex-1">
                              <div className="text-sm text-foreground">{c.name as string}</div>
                              <div className="flex items-center gap-2">
                                <div className="text-[10px] text-muted-foreground">{ST_META[c.status as string]?.label || (c.status as string)}</div>
                                <div className="flex-1"><ProgressBar value={Number(c.progress) || 0} colorVar={(ST_META[c.status as string] || ST_META.planning).colorVar} showLabel={false} /></div>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
                );
              })()}

              {/* Dep links */}
              {depTasks.length > 0 && (
                <Card title="前置依赖" icon={Link2}>
                  <div className="space-y-2">{depTasks.map(d => <DepLink key={d.id} task={d} />)}</div>
                </Card>
              )}
              {dependents.length > 0 && (
                <Card title="被依赖" icon={Share2}>
                  <div className="space-y-2">{dependents.map(d => <DepLink key={d.id} task={d} />)}</div>
                </Card>
              )}

              {/* Actions */}
              <Card title="操作" icon={Cog}>
                <div className="flex flex-wrap gap-2">
                  {st === "planning" && (
                    <button onClick={async () => { try { await api.confirm(task.id); toast("已确认规划", "success"); setTimeout(load, 500); } catch (e) { toast(e instanceof ApiError ? e.message : "确认失败", "error"); } }} className="w-full rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90">
                      <Check className="mr-1.5 inline h-3.5 w-3.5" />确认规划 → 执行
                    </button>
                  )}
                  {st === "check" && (
                    <button onClick={() => setConfirmAction({ type: "finish" })} className="w-full rounded-md border border-primary px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/10">
                      <Flag className="mr-1.5 inline h-3.5 w-3.5" />完成收尾
                    </button>
                  )}
                  <button onClick={() => setConfirmAction({ type: "delete" })} className="w-full rounded-md border border-destructive px-3 py-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10">
                    <XCircle className="mr-1.5 inline h-3.5 w-3.5" />删除任务
                  </button>
                </div>
              </Card>
            </div>

            {/* Right: full content */}
            <div className="min-w-0 space-y-4 lg:col-span-3">
              {task.description && (
                <Card title="任务描述">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{task.description}</p>
                </Card>
              )}

              {/* PRD sections — 三段固定渲染: 缺文件/空章节也亮卡片, 空态引导编辑 */}
              {PRD_FIXED.map((sec) => (
                <PrdSectionCard key={sec.name} taskId={task.id} sec={sec} data={prd.find(p => p.name === sec.name)} onSaved={load} />
              ))}

              {/* Subtask DAG */}
              {subs.length >= 2 && <SubtaskDagCard subs={subs} />}

              {/* Design doc — 恒渲染 (无文件/占位也亮卡), 可直接编辑全文 */}
              <DesignCard taskId={task.id} content={docs.design} onSaved={load} />

              {/* Findings + research */}
              {(docs.findings || Object.entries(research).filter(([, b]) => !isPlaceholder(b)).length > 0) && (
                <Card title="调研" icon={FlaskConical}>
                  {docs.findings && !isPlaceholder(docs.findings) ? (
                    <div className="md-body text-xs leading-relaxed text-foreground" dangerouslySetInnerHTML={{ __html: renderMd(docs.findings) }} />
                  ) : <p className="text-sm text-muted-foreground">无收敛结论</p>}
                  {Object.entries(research).filter(([, b]) => !isPlaceholder(b)).map(([name, body]) => (
                    <details key={name} className="mt-3 rounded-lg border border-border/40">
                      <summary className="cursor-pointer select-none px-3 py-2 text-sm text-foreground">{name}</summary>
                      <div className="px-3 pb-3"><div className="md-body text-xs leading-relaxed text-foreground" dangerouslySetInnerHTML={{ __html: renderMd(body) }} /></div>
                    </details>
                  ))}
                </Card>
              )}
            </div>
          </div>
        </main>
      </div>
      <ConfirmDialog
        open={!!confirmAction}
        title={confirmAction?.type === "delete" ? "删除任务" : "完成收尾"}
        message={confirmAction?.type === "delete"
          ? `确认删除 "${task?.title || task?.name || id}"？删除后可从回收站恢复。`
          : `确认完成 "${task?.title || task?.name || id}" 的收尾？将合并 worktree 并标记为已完成。`}
        confirmText={confirmAction?.type === "delete" ? "删除" : "完成"}
        destructive={confirmAction?.type === "delete"}
        onCancel={() => setConfirmAction(null)}
        onConfirm={async () => {
          const type = confirmAction?.type;
          setConfirmAction(null);
          if (!task) return;
          try {
            if (type === "delete") { await api.del(task.id); toast("已删除", "success"); setTimeout(() => { window.location.href = "/board/"; }, 800); }
            else if (type === "finish") { await api.finish(task.id, true); toast("已完成", "success"); setTimeout(load, 500); }
          } catch (e) { toast(e instanceof ApiError ? e.message : "操作失败", "error"); }
        }}
      />
    </div>
  );
}

// ── Sub-task execution timeline (from old app.js subTimelineView) ──
function SubTimeline({ subs, taskId }: { subs: NormSubtask[]; taskId: string }) {
  const [open, setOpen] = useState(true);
  const ordered = [...subs].sort((a, b) => {
    // done 按 finishedAt 降序排最前; 其余按 startedAt 升序在后
    const ad = a.status === "done" ? 0 : 1;
    const bd = b.status === "done" ? 0 : 1;
    if (ad !== bd) return ad - bd;
    if (ad === 0) return (b.finishedAt || 0) - (a.finishedAt || 0);
    return (a.startedAt || Infinity) - (b.startedAt || Infinity);
  });
  return (
    <details className="mt-1" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary className="cursor-pointer select-none text-[10px] text-muted-foreground">子任务执行过程</summary>
      <div className="mt-1 space-y-1">
        {ordered.map(s => {
          const st = s.status || "planning";
          const meta = ST_META[st] || ST_META.planning;
          let dur = "";
          const est = (typeof s.estimate === "number" && s.estimate > 0) ? s.estimate : 0;
          if (s.startedAt && s.finishedAt) {
            const act = (s.finishedAt - s.startedAt) / 3600000;
            const dt = est ? deltaText(act / est - 1) : null;
            dur = `实际 ${fmtHours(act)}` + (est ? ` / 预估 ${fmtHours(est)}` : "") + (dt ? ` (${dt})` : "");
          } else if (est) { dur = `预估 ${fmtHours(est)}`; }
          const isDone = st === "done";
          return (
            <div key={s.sid} className="flex items-start gap-2">
              {isDone ? (
                <span className="mt-0.5 flex h-3.5 w-3.5 flex-shrink-0 items-center justify-center rounded-full text-[8px] text-white" style={{ backgroundColor: `var(${meta.colorVar})` }}>
                  <Check className="h-2.5 w-2.5" />
                </span>
              ) : (
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-xs text-foreground">{s.title || s.name || s.sid}</span>
                  <span className="cursor-pointer font-mono text-[10px] text-muted-foreground hover:text-primary transition-colors" onClick={() => navigator.clipboard?.writeText(s.sid)} title="点击复制">{s.sid}</span>
                </div>
                <div className="text-[10px] text-muted-foreground">
                  {[meta.label, s.startedAt ? `起 ${fmtTime(s.startedAt)}` : null, s.finishedAt ? `止 ${fmtTime(s.finishedAt)}` : null, dur || null].filter(Boolean).join(" · ")}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </details>
  );
}

// ── Subtask DAG card (React Flow) ──
const SUBTASK_NODE_TYPES = { subtaskCard: SubtaskCardNode };

function SubtaskDagCard({ subs }: { subs: NormSubtask[] }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    if (!subs.length) return;
    layoutSubtaskDAG(subs).then(({ nodes, edges }) => {
      setNodes(nodes);
      setEdges(edges);
    });
  }, [subs]);

  if (!subs.length) return null;

  return (
    <Card title="子任务 DAG" icon={Network}>
      <div style={{ height: "300px" }}>
        <DagFlowProvider>
          <DagFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={SUBTASK_NODE_TYPES}
            minHeight={200}
            enableHoverChain={false}
            showControls={true}
          />
        </DagFlowProvider>
      </div>
    </Card>
  );
}

// ── Dep DAG view (React Flow) ──
const DEP_NODE_TYPES = { depTaskCard: DepTaskNode };

function DepDagView({ taskId, allTasks }: { taskId: string; allTasks: NormTask[] }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [centerId, setCenterId] = useState<string>("");

  useEffect(() => {
    layoutDepDAG(taskId, allTasks).then(({ nodes, edges, centerId }) => {
      setNodes(nodes);
      setEdges(edges);
      setCenterId(centerId);
    });
  }, [taskId, allTasks]);

  if (nodes.length <= 1) return <div className="py-6 text-center text-xs text-muted-foreground">暂无上下游依赖</div>;

  return (
    <div style={{ height: "300px" }}>
      <DagFlowProvider>
        <DagFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={DEP_NODE_TYPES}
          minHeight={200}
          enableHoverChain={true}
          showControls={true}
        />
      </DagFlowProvider>
    </div>
  );
}

// ── PRD 三段固定顺序 (与后端 PRD_SECTIONS 对齐); type 是 CLI 章节名 ──
const PRD_FIXED: { name: string; type: string; icon: LucideIcon }[] = [
  { name: "目标", type: "goal", icon: Target },
  { name: "边界", type: "scope", icon: FileText },
  { name: "验收标准", type: "acceptance", icon: CheckSquare },
];

// PRD 章节卡: 浏览态 checklist + 编辑态 textarea (一行一条, 整章重建 — 增/删/改一条都是改全文后 write)
function PrdSectionCard({ taskId, sec, data, onSaved }: {
  taskId: string;
  sec: { name: string; type: string; icon: LucideIcon };
  data?: { name: string; items?: { text: string; done?: boolean; kind?: string }[]; badge?: [number, number] };
  onSaved: () => void;
}) {
  const toast = useToast();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const items = data?.items;
  const Icon = sec.icon;

  const save = async () => {
    setBusy(true);
    try {
      await api.prd(taskId, "write", sec.type, text);
      toast(`${sec.name} 已保存`, "success");
      setEditing(false);
      onSaved();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "保存失败", "error");
    } finally { setBusy(false); }
  };

  return (
    <Card title={`${sec.name}${data?.badge ? ` (${data.badge[0]}/${data.badge[1]})` : ""}`} icon={Icon}>
      {editing ? (
        <div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.max(4, text.split("\n").length + 1)}
            className="w-full rounded-md border border-border bg-background p-2 font-mono text-xs leading-relaxed text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="一行一条，留空保存即清空本章"
            autoFocus
          />
          <p className="mt-1 text-[10px] text-muted-foreground">保存整章重建，勾选态将重置（勾选归 check 阶段）</p>
          <div className="mt-2 flex gap-2">
            <button onClick={save} disabled={busy} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{busy ? "保存中…" : "保存"}</button>
            <button onClick={() => setEditing(false)} className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted/50">取消</button>
          </div>
        </div>
      ) : (
        <div>
          {items && items.length ? (
            <div className="space-y-2">
              {items.map((item, j) => (
                <div key={j} className="flex items-start gap-3 text-sm">
                  {item.done ? <CheckSquare className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--st-done)" }} /> : <Square className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />}
                  <span className={item.done ? "text-muted-foreground line-through" : "text-foreground"}>{item.text}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted-foreground">暂无条目 — 点「编辑」添加</p>}
          <button onClick={() => { setText((items || []).map(i => i.text).join("\n")); setEditing(true); }} className="mt-3 rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground">编辑</button>
        </div>
      )}
    </Card>
  );
}

// 详细设计卡: design.md 全文; 浏览态渲染 markdown, 编辑态 textarea 直写全文
function DesignCard({ taskId, content, onSaved }: { taskId: string; content?: string; onSaved: () => void }) {
  const toast = useToast();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await api.designSave(taskId, text);
      toast("详细设计已保存", "success");
      setEditing(false);
      onSaved();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "保存失败", "error");
    } finally { setBusy(false); }
  };

  return (
    <Card title="详细设计" icon={Network}>
      {editing ? (
        <div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={16}
            className="w-full rounded-md border border-border bg-background p-2 font-mono text-xs leading-relaxed text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="# 架构 / 数据流 / 取舍 / 技术选型 / 测试接缝 (seam) / 可能性分支"
            autoFocus
          />
          <div className="mt-2 flex gap-2">
            <button onClick={save} disabled={busy} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{busy ? "保存中…" : "保存"}</button>
            <button onClick={() => setEditing(false)} className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted/50">取消</button>
          </div>
        </div>
      ) : (
        <div>
          {content ? (
            <>
              {isPlaceholder(content) && <p className="mb-2 text-xs text-muted-foreground">尚未填写，以下为模板占位</p>}
              <div className="md-body text-xs leading-relaxed text-foreground" dangerouslySetInnerHTML={{ __html: renderMd(content) }} />
            </>
          ) : <p className="text-sm text-muted-foreground">暂无详细设计 — 点「编辑」撰写</p>}
          <button onClick={() => { setText(content || ""); setEditing(true); }} className="mt-3 rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground">编辑</button>
        </div>
      )}
    </Card>
  );
}

// ── Shared components ──
function Card({ title, icon: Icon, children }: { title: string; icon?: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card/60 p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
        {Icon && <Icon className="h-4 w-4 text-primary" />}
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-3 py-1.5">
      <span className="w-20 flex-shrink-0 text-xs text-muted-foreground">{label}</span>
      <div className="flex-1 text-xs text-foreground">{value || "—"}</div>
    </div>
  );
}

function DepLink({ task }: { task: NormTask }) {
  return (
    <Link prefetch={false} href={`/task/detail/?id=${task.id}`} className="flex items-start gap-2 rounded-md p-2 transition-colors hover:bg-muted/30">
      <StatusDot status={task.status} className="mt-1.5" />
      <div className="min-w-0 flex-1">
        <div className="text-sm text-foreground">{task.title || task.name || task.id}</div>
      </div>
    </Link>
  );
}

export default function TaskDetailPage() {
  return (
    <Suspense fallback={<div className="py-16 text-center text-muted-foreground">加载中…</div>}>
      <TaskDetailContent />
    </Suspense>
  );
}
