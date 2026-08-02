"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useCallback, useMemo, useRef } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META } from "@/components/status";
import { api, ApiError } from "@/lib/api";
import { normalizeTask, normalizeTasks, PRIORITY_LABEL, type NormTask, type NormSubtask } from "@/lib/model";
import { subscribe } from "@/lib/live";
import { fmtRelative, fmtTime } from "@/lib/format";
import { renderMd } from "@/lib/md";
import { etaOf, etaText, fmtHours, actualOf, deltaText, type EtaResult } from "@/lib/eta";
import { drawEdgesPaths, buildDepDAG } from "@/lib/depdag";
import { ProgressBar } from "@/components/progress-bar";
import { useToast } from "@/components/toast";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { IconApprove, IconFinish, IconTrash, IconCopyMini } from "@/components/icons";
import { cn } from "@/lib/utils";

// ── Timeline stages (from old app.js buildTimeline) ──
const STAGE_ORDER: Record<string, number> = { planning: 0, active: 1, check: 2, done: 3 };
const STAGE_COLORS: Record<string, string> = {
  created: "#74b9e8", started: "#237bb8", checked: "#c9a227", finished: "#48bb78",
};

function buildStages(task: NormTask) {
  const st = task.status || "planning";
  const idx = STAGE_ORDER[st];
  const byTs = idx == null;
  const at = (i: number, ts: number | null) => byTs ? !!ts : idx > i;
  return [
    { key: "planning", label: "规划中", name: "规划中", desc: "任务规划与 PRD 编写", time: task.createdAt, done: idx > 0, current: idx === 0, color: STAGE_COLORS.created },
    { key: "started", label: "执行", name: "开始执行", desc: "任务执行中，子任务调度", time: task.startedAt, done: idx > 1, current: idx === 1, color: STAGE_COLORS.started },
    { key: "checked", label: "验收", name: "进入验收", desc: "checkpoint 核对 + 场景自适应校验", time: task.checkedAt, done: idx > 2, current: idx === 2, color: STAGE_COLORS.checked },
    { key: "finished", label: "完成", name: "已完成", desc: "任务完成，归档沉淀", time: task.finishedAt, done: byTs ? !!task.finishedAt : idx >= 3, current: false, color: STAGE_COLORS.finished },
  ];
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

  // 详情页订阅本 task 的逐条变更消息, 局部合并进 raw/task (不重跑 load, 不动 docs/prd/依赖等其余 state) ——
  // card 只是展示字段子集 (见 views.py _cards_signature), spread 合并保留 raw 里 card 没有的富字段
  // (docs/research/prd/parentTask/childTasks)。card 为空 = task 已归档/删除, 判定详情页不存在。
  // 合并基底必须是未 normalize 过的 raw, 不能是已 normalize 的 task —— task 上已有 normalizeTask 派生出
  // 的 title 字段, 若拿它做合并基底, 陈旧的 title 会盖掉 card 新来的 name (normalizeTask 优先取 title)。
  useEffect(() => {
    if (!id) return;
    // 订阅全局消息 (data) + 本 task 消息 (task-changed)
    const unsubGlobal = subscribe((msg) => {
      if (msg.type === "data") load(); // 整页刷新
    });
    const unsubTask = subscribe((msg) => {
      if (msg.type !== "task-changed") return;
      if (!msg.card) { setNotFound(true); setTask(null); return; }
      const card = msg.card;
      setRaw(prev => {
        const next = prev ? { ...prev, ...card } : card;
        setTask(normalizeTask(next));
        return next;
      });
    }, { taskId: id });
    return () => { unsubGlobal(); unsubTask(); };
  }, [id, load]);

  // 页面直接改优先级: 复用白名单 exec 通道; 成功后本地乐观更新, 失败给明确错误 (不静默失败)。
  // exec 端点 CLI 失败时仍返回 HTTP 200 (body.ok=false + stderr), 不会走 fetch 的 catch — 必须显式查 ok。
  const handlePriorityChange = async (val: string) => {
    if (!task) return;
    try {
      const r = await api.exec("priority", { id: task.id, set: val }) as { ok: boolean; stderr?: string };
      if (!r.ok) { toast(r.stderr?.trim() || "优先级更新失败", "error"); return; }
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
            <i className="fa fa-exclamation-triangle mb-3 text-4xl text-muted-foreground opacity-40" />
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
              <span className="opacity-40">/</span>
              <span className="text-foreground">{task.title || task.name || task.id}</span>
            </nav>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="mb-2 flex items-center gap-3">
                  <i className={`fa ${meta.icon} text-xl`} style={{ color: `var(${meta.colorVar})` }} />
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
                  <button onClick={async () => { try { await api.exec("confirm", { id: task.id }); toast("已确认规划", "success"); setTimeout(load, 500); } catch { toast("确认失败", "error"); } }} data-tip="确认规划 → 激活执行" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-2 text-primary hover:bg-primary/10">
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
                  <select value={task.priority} onChange={(e) => handlePriorityChange(e.target.value)}
                    className="rounded-md border border-border bg-card/60 px-2 py-1 text-sm text-foreground">
                    {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
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
              <Card title="生命周期时间线" icon="fa-history">
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
                          {s.key === "started" && subsOfTask.length > 0 && <span className="text-[10px] text-muted-foreground">{subDone}/{subsOfTask.length} 子任务</span>}
                        </div>
                        <div className="text-[10px] text-muted-foreground">{s.desc}</div>
                        {s.key === "started" && subsOfTask.length > 0 && <SubTimeline subs={subsOfTask} taskId={task.id} />}
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Subtask list */}
              {subs.length > 0 && (
                <Card title="子任务列表" icon="fa-tasks">
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
                <Card title={`依赖关系图 (${depTasks.length + dependents.length + 1})`} icon="fa-share-alt">
                  <DepDagView taskId={task.id} allTasks={depAll} />
                </Card>
              )}

              {/* Parent/Child relationship */}
              {(() => {
                const pt = raw?.parentTask as Record<string, unknown> | undefined;
                const ct = (raw?.childTasks || []) as Record<string, unknown>[];
                if (!pt && ct.length === 0) return null;
                return (
                <Card title="父子关系" icon="fa-sitemap">
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
                <Card title="前置依赖" icon="fa-link">
                  <div className="space-y-2">{depTasks.map(d => <DepLink key={d.id} task={d} />)}</div>
                </Card>
              )}
              {dependents.length > 0 && (
                <Card title="被依赖" icon="fa-share-alt">
                  <div className="space-y-2">{dependents.map(d => <DepLink key={d.id} task={d} />)}</div>
                </Card>
              )}

              {/* Actions */}
              <Card title="操作" icon="fa-cog">
                <div className="flex flex-wrap gap-2">
                  {st === "planning" && (
                    <button onClick={async () => { try { await api.exec("confirm", { id: task.id }); toast("已确认规划", "success"); setTimeout(load, 500); } catch { toast("确认失败", "error"); } }} className="w-full rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90">
                      <i className="fa fa-check mr-1.5" />确认规划 → 执行
                    </button>
                  )}
                  {st === "check" && (
                    <button onClick={() => setConfirmAction({ type: "finish" })} className="w-full rounded-md border border-primary px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/10">
                      <i className="fa fa-flag-checkered mr-1.5" />完成收尾
                    </button>
                  )}
                  <button onClick={() => setConfirmAction({ type: "delete" })} className="w-full rounded-md border border-destructive px-3 py-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10">
                    <i className="fa fa-times-circle mr-1.5" />删除任务
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

              {/* PRD sections */}
              {prd.map((sec, i) => (
                <Card key={i} title={`${sec.name}${sec.badge ? ` (${sec.badge[0]}/${sec.badge[1]})` : ""}`} icon={sec.name === "目标" ? "fa-bullseye" : sec.name === "验收标准" ? "fa-check-square-o" : "fa-file-text-o"}>
                  {sec.items && sec.items.length ? (
                    <div className="space-y-2">
                      {sec.items.map((item, j) => (
                        <div key={j} className="flex items-start gap-3 text-sm">
                          <i className={`fa ${item.done ? "fa-check-square" : "fa-square-o"} mt-0.5 flex-shrink-0`} style={{ color: item.done ? "var(--st-done)" : "var(--muted-foreground)" }} />
                          <span className={item.done ? "text-muted-foreground line-through" : "text-foreground"}>{item.text}</span>
                        </div>
                      ))}
                    </div>
                  ) : <p className="text-sm text-muted-foreground">—</p>}
                </Card>
              ))}

              {/* Contracts */}
              {task.contracts && task.contracts.length > 0 && (
                <Card title="契约" icon="fa-handshake-o">
                  <div className="space-y-3">
                    {task.contracts.map((c, i) => (
                      <div key={i} className="rounded-lg border border-border/40 bg-muted/20 p-3">
                        <div className="text-sm font-semibold text-foreground">{c.id}</div>
                        {c.desc && <div className="mt-1 text-xs text-muted-foreground">{c.desc}</div>}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Subtask DAG */}
              {subs.length >= 2 && <SubtaskDagCard subs={subs} />}

              {/* Design doc */}
              {docs.design && !isPlaceholder(docs.design) && (
                <Card title="详细设计" icon="fa-sitemap">
                  <div className="md-body text-xs leading-relaxed text-foreground" dangerouslySetInnerHTML={{ __html: renderMd(docs.design) }} />
                </Card>
              )}

              {/* Findings + research */}
              {(docs.findings || Object.entries(research).filter(([, b]) => !isPlaceholder(b)).length > 0) && (
                <Card title="调研" icon="fa-flask">
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
            if (type === "delete") { await api.exec("del", { id: task.id }); toast("已删除", "success"); setTimeout(() => { window.location.href = "/board/"; }, 800); }
            else if (type === "finish") { await api.finish(task.id); toast("已完成", "success"); setTimeout(load, 500); }
          } catch { toast("操作失败", "error"); }
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
                  <i className="fa fa-check" />
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

// ── Subtask DAG card ──
function SubtaskDagCard({ subs }: { subs: NormSubtask[] }) {
  const { layout } = useSubtaskLayout(subs);
  const { paths, markers } = useMemo(() => {
    if (!layout) return { paths: [] as ReturnType<typeof drawEdgesPaths>["paths"], markers: [] as ReturnType<typeof drawEdgesPaths>["markers"] };
    return drawEdgesPaths(layout.edges);
  }, [layout]);
  const wrapRef = useRef<HTMLDivElement>(null);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    const wrap = wrapRef.current; if (!wrap) return;
    if (e.target instanceof Element && e.target.closest("a, button")) return;
    const startX = e.clientX, startY = e.clientY, sl = wrap.scrollLeft, st = wrap.scrollTop;
    wrap.style.cursor = "grabbing";
    const move = (ev: MouseEvent) => { wrap.scrollLeft = sl - (ev.clientX - startX); wrap.scrollTop = st - (ev.clientY - startY); };
    const up = () => { wrap.style.cursor = "grab"; window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
    window.addEventListener("mousemove", move); window.addEventListener("mouseup", up);
    e.preventDefault();
  }, []);

  if (!layout || !layout.nodes.length) return null;

  return (
    <Card title="子任务 DAG" icon="fa-sitemap">
      <div className="overflow-auto" ref={wrapRef} onMouseDown={onMouseDown} style={{ cursor: "grab", maxHeight: "400px" }}>
        <div className="relative mx-auto" style={{ width: layout.width, height: layout.height }}>
          <svg className="pointer-events-none absolute inset-0" style={{ width: "100%", height: "100%" }}>
            <defs>
              {markers.map(m => <marker key={m.id} id={m.id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill={`var(--${m.color})`} /></marker>)}
            </defs>
            {paths.map((p, i) => <path key={i} d={p.d} fill="none" stroke={p.stroke} strokeWidth={p.strokeWidth} strokeOpacity={p.strokeOpacity} strokeDasharray={p.dashArray} markerEnd={p.markerEnd} />)}
          </svg>
          {layout.nodes.map(n => {
            const t = n.sub as NormSubtask; if (!t) return null;
            const sm = ST_META[t.status] || ST_META.planning;
            return (
              <div key={n.id} className={`absolute flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md ${t.status === "done" ? "opacity-50" : ""}`} style={{ left: n.x, top: n.y, width: n.w, height: n.h, borderColor: `var(${sm.colorVar})`, backgroundColor: `color-mix(in srgb, var(${sm.colorVar}) 20%, var(--card))` }} title={t.title || t.name || t.id}>
                <span className="ml-2 h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
                <div className="min-w-0 flex-1 pr-2">
                  <div className="truncate text-xs font-semibold leading-tight text-foreground">{t.title || t.name || t.id}</div>
                  <div className="truncate text-[10px] leading-tight text-muted-foreground hover:text-primary cursor-pointer" onClick={() => navigator.clipboard?.writeText(t.sid)} title="点击复制">{sm.label} · {t.sid}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

function useSubtaskLayout(subs: NormSubtask[]) {
  return useMemo(() => {
    if (!subs.length) return { layout: null };
    const byId = new Map(subs.map(s => [s.id, s]));
    const depsOf = (id: string) => (byId.get(id)?.deps || []).filter(d => byId.has(d));
    const s = { w: 148, h: 48, gapX: 16, gapY: 24, padX: 16, padY: 24 };
    const ids = [...byId.keys()];
    // simple tiered layout
    const lay = new Map<string, number>();
    const inSet = new Set(ids);
    const topo: string[] = [];
    const dmap = new Map(ids.map(id => [id, depsOf(id).filter(d => inSet.has(d))]));
    const left = new Map(ids.map(id => [id, dmap.get(id)!.length]));
    const succ = new Map(ids.map(id => [id, [] as string[]]));
    for (const id of ids) for (const d of dmap.get(id)!) succ.get(d)!.push(id);
    const q = ids.filter(id => left.get(id) === 0);
    const seen = new Set<string>();
    while (q.length) { const cur = q.shift()!; seen.add(cur); topo.push(cur); for (const nx of succ.get(cur)!) { left.set(nx, left.get(nx)! - 1); if (left.get(nx) === 0) q.push(nx); } }
    for (const id of ids) if (!seen.has(id)) topo.push(id);
    for (const id of topo) lay.set(id, Math.max(0, ...depsOf(id).map(d => (lay.get(d) ?? -1) + 1)));
    const tiers: string[][] = [];
    for (const id of topo) (tiers[lay.get(id)!] || (tiers[lay.get(id)!] = [])).push(id);
    const colW = s.w + s.gapX, rowH = s.h + s.gapY;
    const nodes: any[] = [];
    const nmap = new Map<string, any>();
    tiers.forEach((tier, ti) => tier.forEach((id, ri) => {
      const n = { id, x: s.padX + ti * colW, y: s.padY + ri * rowH, w: s.w, h: s.h, rowH: s.h, band: 0, sub: byId.get(id)! };
      nodes.push(n); nmap.set(id, n);
    }));
    const edges: any[] = [];
    for (const id of ids) for (const d of depsOf(id)) { const from = nmap.get(d), to = nmap.get(id); if (from && to) edges.push({ from, to, bends: [], cross: false, laneY: 0 }); }
    const width = s.padX * 2 + tiers.length * colW;
    const height = s.padY * 2 + Math.max(1, ...tiers.map(t => t.length)) * rowH;
    return { layout: { nodes, edges, width, height } };
  }, [subs]);
}

// ── Dep DAG view (from old depdag.js depDAGView) ──
function DepDagView({ taskId, allTasks }: { taskId: string; allTasks: NormTask[] }) {
  const dag = useMemo(() => buildDepDAG(taskId, allTasks), [taskId, allTasks]);
  const { paths, markers } = useMemo(() => drawEdgesPaths(dag.edges), [dag.edges]);

  // Hover chain highlight
  const [hoverId, setHoverId] = useState<string | null>(null);
  const chain = useMemo(() => {
    if (!hoverId) return null;
    const succ = new Map<string, string[]>(), pred = new Map<string, string[]>();
    for (const e of dag.edges) {
      if (!succ.has(e.from.id)) succ.set(e.from.id, []);
      if (!pred.has(e.to.id)) pred.set(e.to.id, []);
      succ.get(e.from.id)!.push(e.to.id);
      pred.get(e.to.id)!.push(e.from.id);
    }
    const seen = new Set([hoverId]);
    for (const adj of [succ, pred]) {
      const queue = [hoverId];
      while (queue.length) {
        for (const nx of adj.get(queue.shift()!) || []) {
          if (seen.has(nx)) continue;
          seen.add(nx);
          queue.push(nx);
        }
      }
    }
    return seen;
  }, [hoverId, dag.edges]);

  if (dag.nodes.length <= 1) return <div className="py-6 text-center text-xs text-muted-foreground">暂无上下游依赖</div>;

  return (
    <div className="overflow-x-auto">
      <div className="relative" style={{ width: dag.width, height: dag.height }}
        onMouseOver={(e) => { const link = (e.target as Element).closest("[data-node-id]"); setHoverId(link?.getAttribute("data-node-id") || null); }}
        onMouseLeave={() => setHoverId(null)}
      >
        {/* 父子包裹: 用容器框表达归属, 不画箭头边 (与看板同规则) */}
        {dag.groups.map(g => (
          <div key={g.id} className="pointer-events-none absolute rounded-lg border border-dashed border-primary/30 bg-primary/[0.03]" style={{ left: g.x, top: g.y, width: g.w, height: g.h }} />
        ))}
        <svg className="pointer-events-none absolute inset-0" style={{ width: "100%", height: "100%" }}>
          <defs>
            {markers.map(m => <marker key={m.id} id={m.id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill={`var(--${m.color})`} /></marker>)}
          </defs>
          {paths.map((p, i) => <path key={i} d={p.d} fill="none" stroke={p.stroke} strokeWidth={p.strokeWidth}
            strokeOpacity={chain ? (chain.has(p.fromId) && chain.has(p.toId) ? "0.95" : "0.1") : p.strokeOpacity}
            markerEnd={p.markerEnd} />)}
        </svg>
        {dag.nodes.map(n => {
          const meta = ST_META[n.task.status] || ST_META.planning;
          const inChain = chain?.has(n.id) ?? false;
          const isDim = chain ? !inChain : false;
          return (
            <Link key={n.id} prefetch={false} href={`/task/detail/?id=${n.id}`} data-node-id={n.id}
              className={`absolute flex items-center gap-2 rounded-md border px-2 py-1 transition-all hover:shadow-md ${n.isCenter ? "ring-2 ring-primary" : ""}`}
              style={{ left: n.x, top: n.y, width: n.w, height: n.h, opacity: isDim ? 0.15 : 1, borderColor: `color-mix(in srgb, var(${meta.colorVar}) 30%, var(--border))`, backgroundColor: "var(--card)" }}
              title={n.task.title || n.task.name || n.id}
            >
              <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
              <span className="flex-1 truncate text-xs font-medium text-foreground">{n.task.title || n.task.name || n.id}</span>
              {n.isCenter && <i className="fa fa-star text-xs text-primary" />}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// ── Shared components ──
function Card({ title, icon, children }: { title: string; icon?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card/60 p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
        {icon && <i className={`fa ${icon} text-primary`} />}
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
