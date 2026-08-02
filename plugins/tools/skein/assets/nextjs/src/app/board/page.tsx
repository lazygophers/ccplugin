"use client";

import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META, ST_ORDER } from "@/components/status";
import { api, ApiError, type Task } from "@/lib/api";
import { normalizeTasks, normalizeStatus, applyTaskChangedBatch, PRIORITY_LABEL, PRIORITY_COLOR_VAR, type NormTask, type NormSubtask } from "@/lib/model";
import { subscribe } from "@/lib/live";
import { cn } from "@/lib/utils";
import { fmtRelative, fmtTime } from "@/lib/format";
import { renderMd } from "@/lib/md";
import { etaOf, etaText, fmtHours, actualOf, deltaText, overallSummary } from "@/lib/eta";
import { drawEdgesPaths, buildDepDAG, type DagEdge } from "@/lib/depdag";
import { layoutTiered, layoutDAG, type LayoutNode, type GroupBox, type Density } from "@/lib/board-layout";
import { ProgressBar } from "@/components/progress-bar";
import { useToast } from "@/components/toast";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { IconApprove, IconFinish, IconDetail, IconTrash, IconClose, IconCopyMini } from "@/components/icons";

const ALL_STATUSES = ["planning", "ready", "active", "check", "done"];
const DEFAULT_FILTER = new Set(["planning", "ready", "active", "check"]);

// ── Sugiyama layout (ported from old board.js) ──
interface LayoutEdge extends DagEdge {}

interface SugiOpts { colW: number; rowH: number; padX: number; padY: number; gapX: number; gapY: number; }

function sugiyama(ids: string[], depsOf: (id: string) => string[], opt: SugiOpts & { maxWidth?: number; viewH?: number }) {
  const { colW, rowH, padX, padY, gapX, gapY } = opt;
  const maxWidth = opt.maxWidth || 1200;
  const viewH = opt.viewH || 800;
  const idSet = new Set(ids);
  const deps = new Map<string, string[]>(), succ = new Map<string, string[]>();
  for (const id of ids) { deps.set(id, []); succ.set(id, []); }
  for (const id of ids) {
    const seen = new Set<string>();
    for (const d of depsOf(id)) {
      if (!idSet.has(d) || d === id || seen.has(d)) continue;
      seen.add(d); deps.get(id)!.push(d); succ.get(d)!.push(id);
    }
  }
  // 1. rank
  const rank = new Map<string, number>();
  const indeg = new Map(ids.map(i => [i, deps.get(i)!.length]));
  let frontier = ids.filter(i => indeg.get(i) === 0);
  let settled = 0;
  while (frontier.length) {
    const next: string[] = [];
    for (const id of frontier) {
      settled++;
      let r = 0;
      for (const d of deps.get(id)!) r = Math.max(r, (rank.has(d) ? rank.get(d)! : -1) + 1);
      rank.set(id, r);
      for (const s of succ.get(id)!) { indeg.set(s, indeg.get(s)! - 1); if (indeg.get(s) === 0) next.push(s); }
    }
    frontier = next;
  }
  if (settled < ids.length) {
    for (const id of ids) { if (rank.has(id)) continue; let r = 0; for (const d of deps.get(id)!) if (rank.has(d)) r = Math.max(r, rank.get(d)! + 1); rank.set(id, r); }
  }
  // sink compact
  for (const id of ids.slice().sort((a, b) => rank.get(b)! - rank.get(a)!)) {
    const ss = succ.get(id)!; if (!ss.length) continue;
    let m = Infinity; for (const s of ss) m = Math.min(m, rank.get(s)!);
    if (m - 1 > rank.get(id)!) rank.set(id, m - 1);
  }
  const usedRanks = [...new Set(ids.map(i => rank.get(i)!))].sort((a, b) => a - b);
  const remap = new Map(usedRanks.map((r, i) => [r, i] as [number, number]));
  for (const id of ids) rank.set(id, remap.get(rank.get(id)!)!);
  const L = usedRanks.length;
  // 2. edges + dummy nodes
  const layers: { id: string; rank: number; dummy: boolean; x: number; y: number; y0: number; band: number }[][] = Array.from({ length: L }, () => []);
  const nodeOf = new Map<string, any>();
  for (const id of ids) { const n = { id, rank: rank.get(id)!, dummy: false, x: 0, y: 0, y0: 0, band: 0 }; nodeOf.set(id, n); layers[n.rank].push(n); }
  const edges: { from: any; to: any; chain: any[] }[] = [];
  let dseq = 0;
  for (const id of ids) {
    for (const d of deps.get(id)!) {
      const from = nodeOf.get(d), to = nodeOf.get(id);
      const chain: any[] = [];
      for (let r = from.rank + 1; r < to.rank; r++) { const dn = { id: `~d${dseq++}`, rank: r, dummy: true, x: 0, y: 0, y0: 0, band: 0 }; layers[r].push(dn); chain.push(dn); }
      edges.push({ from, to, chain });
    }
  }
  const adjUp = new Map<any, any[]>(), adjDown = new Map<any, any[]>();
  const link = (a: any, b: any) => { if (!adjDown.has(a)) adjDown.set(a, []); if (!adjUp.has(b)) adjUp.set(b, []); adjDown.get(a)!.push(b); adjUp.get(b)!.push(a); };
  for (const e of edges) { let prev = e.from; for (const dn of e.chain) { link(prev, dn); prev = dn; } link(prev, e.to); }
  // 3. cross min
  const posIn = new Map<any, number>();
  const reindex = () => { for (const l of layers) l.forEach((n, i) => posIn.set(n, i)); };
  reindex();
  const medianOf = (n: any, adj: Map<any, any[]>) => { const ps: number[] = (adj.get(n) || []).map((m: any) => posIn.get(m)).filter((v: any): v is number => v != null); if (!ps.length) return -1; const mid = ps.length >> 1; return ps.length % 2 ? ps[mid] : (ps[mid - 1] + ps[mid]) / 2; };
  const crossOf = (a: any, b: any, adj: Map<any, any[]>) => { const pa: number[] = (adj.get(a) || []).map((m: any) => posIn.get(m)).filter((v: any): v is number => v != null); const pb: number[] = (adj.get(b) || []).map((m: any) => posIn.get(m)).filter((v: any): v is number => v != null); let c = 0; for (const x of pa) for (const y of pb) if (y < x) c++; return c; };
  const idxs = layers.map((_, i) => i);
  for (let it = 0; it < 6; it++) {
    const down = it % 2 === 0;
    const seq = down ? idxs.slice(1) : idxs.slice(0, -1).reverse();
    const adj = down ? adjUp : adjDown;
    for (const li of seq) {
      const layer = layers[li];
      const med = new Map<any, number>();
      layer.forEach((n, i) => { const m = medianOf(n, adj); med.set(n, m < 0 ? i : m); });
      layer.sort((a, b) => med.get(a)! - med.get(b)!);
      reindex();
      if (layer.length <= 200) {
        for (let round = 0; round < 4; round++) {
          let improved = false;
          for (let i = 0; i + 1 < layer.length; i++) {
            const a = layer[i], b = layer[i + 1];
            if (crossOf(a, b, adj) > crossOf(b, a, adj)) { layer[i] = b; layer[i + 1] = a; posIn.set(b, i); posIn.set(a, i + 1); improved = true; }
          }
          if (!improved) break;
        }
      }
    }
    reindex();
  }
  // 4. fold bands
  const K = Math.max(1, Math.floor((maxWidth - padX * 2) / colW));
  const bandH = Math.max(4, Math.floor((viewH || 800) / rowH)) * rowH;
  const DUMMY_H = 28;
  const hOf = (n: any) => (n.dummy ? DUMMY_H : rowH);
  const seat: { band: number; col: number; cols: number }[] = [];
  let curBand = 0, curCol = 0;
  for (const l of layers) {
    const need = l.reduce((a, n) => a + hOf(n), 0);
    const cols = Math.min(K, Math.max(1, Math.ceil(need / bandH)));
    if (curCol + cols > K && curCol > 0) { curBand++; curCol = 0; }
    seat.push({ band: curBand, col: curCol, cols });
    curCol += cols;
  }
  const bands = curBand + 1;
  const bandOf = (li: number) => seat[li].band;
  // 5. coords
  layers.forEach((l, li) => {
    const st = seat[li]; let col = 0, acc = 0;
    for (const n of l) {
      const nh = hOf(n);
      if (acc + nh > bandH && acc > 0 && col < st.cols - 1) { col++; acc = 0; }
      n.x = (st.col + col) * colW; n.y = acc; n.y0 = acc; n.band = st.band; acc += nh;
    }
  });
  const SLACK = 3 * rowH;
  for (let pass = 0; pass < 3; pass++) {
    const seq = pass % 2 === 0 ? idxs : idxs.slice().reverse();
    const adj = pass % 2 === 0 ? adjUp : adjDown;
    for (const li of seq) {
      if (seat[li].cols > 1) continue;
      const layer = layers[li]; const band = bandOf(li);
      let prev = -Infinity;
      for (const n of layer) {
        const ns = (adj.get(n) || []).filter((m: any) => m.band === band);
        let want = n.y;
        if (ns.length) { const ys = ns.map((m: any) => m.y).sort((a: number, b: number) => a - b); const mid = ys.length >> 1; want = ys.length % 2 ? ys[mid] : (ys[mid - 1] + ys[mid]) / 2; }
        want = Math.max(n.y0 - SLACK, Math.min(n.y0 + SLACK, want));
        n.y = Math.max(want, prev);
        prev = n.y + hOf(n);
      }
    }
  }
  const span = Array.from({ length: bands }, () => ({ lo: Infinity, hi: -Infinity }));
  let usedCols = 1;
  layers.forEach((l, li) => {
    const s = span[seat[li].band]; usedCols = Math.max(usedCols, seat[li].col + seat[li].cols);
    for (const n of l) { s.lo = Math.min(s.lo, n.y); s.hi = Math.max(s.hi, n.y + hOf(n)); }
  });
  const bandTop: { top: number; shift: number }[] = [];
  const bandsInfo: { top: number; bottom: number }[] = [];
  let accY = 0;
  for (const s of span) {
    if (s.lo === Infinity) { s.lo = 0; s.hi = 0; }
    bandTop.push({ top: accY, shift: -s.lo });
    bandsInfo.push({ top: accY + padY, bottom: accY + (s.hi - s.lo) + padY });
    accY += (s.hi - s.lo) + rowH;
  }
  const all = layers.flat();
  for (const n of all) { const bt = bandTop[n.band]; n.x += padX; n.y += bt.shift + bt.top + padY; }
  const maxY = all.reduce((m, n) => Math.max(m, n.y + (n.dummy ? 0 : rowH - gapY)), 0);
  return { layers, edges, bandCols: usedCols, bandsInfo, width: usedCols * colW + padX * 2, height: maxY + padY };
}

// ── Components ──

export default function BoardPage() {
  const toast = useToast();
  const [allTasks, setAllTasks] = useState<NormTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"dag" | "list">("dag");
  const [statusSet, setStatusSet] = useState<Set<string>>(new Set(DEFAULT_FILTER));
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const density: Density = "compact";
  const [viewBox, setViewBox] = useState({ w: 1200, h: 800 });
  const wrapRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLDivElement>(null);
  const [confirmAction, setConfirmAction] = useState<{ type: "delete" | "finish" | "clean"; id: string; name: string } | null>(null);

  useEffect(() => {
    api.data().then((r) => {
      const raw = r as unknown as Record<string, unknown>;
      const cards = (raw.cards || raw.tasks || []) as unknown as Record<string, unknown>[];
      const maxActive = ((raw.overview as Record<string, unknown>)?.maxActive as number) || 2;
      const tasks = normalizeTasks(cards).map(t => { (t as Record<string, unknown>).maxActive = maxActive; return t; });
      setAllTasks(tasks);
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

  useEffect(() => {}, []); // placeholder removed

  const countBy = useMemo(() => {
    const c: Record<string, number> = {};
    for (const t of allTasks) c[t.status] = (c[t.status] || 0) + 1;
    return c;
  }, [allTasks]);

  const summary = useMemo(() => overallSummary(allTasks, 2), [allTasks]);

  const layout = useMemo(() => view === "dag" ? layoutDAG(allTasks, viewBox, density) : null, [allTasks, viewBox, density, view]);

  const selectedTask = selectedId ? allTasks.find(t => t.id === selectedId) || null : null;

  const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
  const toggleStatus = (st: string) => {
    setStatusSet(prev => { const next = new Set(prev); if (next.has(st)) next.delete(st); else next.add(st); return next; });
  };
  const toggleAll = () => setStatusSet(allSelected ? new Set(["planning", "ready", "active", "check"]) : new Set(ALL_STATUSES));

  const cleanDone = () => setConfirmAction({ type: "clean", id: "", name: "" });

  // 页面直接改优先级: 复用白名单 exec 通道; 成功后本地乐观更新 (无需等 mtime 轮询), 失败给明确错误。
  // exec 端点 CLI 失败时仍返回 HTTP 200 (body.ok=false + stderr), 不会走 fetch 的 catch — 必须显式查 ok。
  const handlePriorityChange = async (id: string, val: string) => {
    try {
      const r = await api.exec("priority", { id, set: val }) as { ok: boolean; stderr?: string };
      if (!r.ok) { toast(r.stderr?.trim() || "优先级更新失败", "error"); return; }
      setAllTasks(prev => prev.map(t => t.id === id ? { ...t, priority: val } : t));
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
                  <i className="fa fa-archive mr-1.5" />清理已完成
                </button>
              )}
              {/* View toggle */}
              <div className="flex items-center gap-1 rounded-lg border border-border bg-card/60 p-1">
                <button onClick={() => setView("dag")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-colors", view === "dag" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground")}><i className="fa fa-sitemap mr-1.5" />DAG</button>
                <button onClick={() => setView("list")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-colors", view === "list" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground")}><i className="fa fa-list mr-1.5" />列表</button>
              </div>
            </div>
          </div>

          {/* Main area: DAG/list + optional detail panel (absolute overlay, 不压缩 DAG 画布) */}
          <div ref={mainRef} className="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-border/30 bg-transparent">
            {/* DAG/List canvas — 始终占满容器，详情面板浮在其上 */}
            <div className={cn("absolute inset-0 board-dag-wrap", view === "list" ? "overflow-hidden" : "overflow-auto")} ref={wrapRef}
              onMouseDown={(e) => {
                if (e.target instanceof Element && e.target.closest(".dag-node-wrap, button, a")) return;
                const wrap = wrapRef.current; if (!wrap) return;
                const startX = e.clientX, startY = e.clientY, startSL = wrap.scrollLeft, startST = wrap.scrollTop;
                wrap.style.cursor = "grabbing";
                const move = (ev: MouseEvent) => { wrap.scrollLeft = startSL - (ev.clientX - startX); wrap.scrollTop = startST - (ev.clientY - startY); };
                const up = () => { wrap.style.cursor = "grab"; window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
                window.addEventListener("mousemove", move); window.addEventListener("mouseup", up);
                e.preventDefault();
              }}
              style={{ cursor: view === "dag" ? "grab" : "default" } as React.CSSProperties}
            >
              {loading ? (
                <div className="py-16 text-center text-muted-foreground">加载中…</div>
              ) : view === "dag" && layout ? (
                <DagCanvas layout={layout} statusSet={statusSet} onSelect={setSelectedId} selectedId={selectedId} />
              ) : (
                <ListView tasks={allTasks} statusSet={statusSet} onSelect={setSelectedId} />
              )}
            </div>

            {/* Right: Detail panel */}
            {selectedTask && (
              <DetailPanel task={selectedTask} allTasks={allTasks} onClose={() => setSelectedId(null)}
                onConfirm={async (id) => { try { await api.exec("confirm", { id }); toast("已确认规划", "success"); } catch { toast("确认失败", "error"); } }}
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
                if (type === "delete") { await api.exec("del", { id }); setSelectedId(null); toast("已删除", "success"); }
                else if (type === "finish") { await api.exec("finish", { id }); toast("已完成", "success"); }
                else { await api.exec("clean", { days: 0 }); toast("已归档", "success"); setTimeout(() => window.location.reload(), 500); }
              } catch { toast("操作失败", "error"); }
            }}
          />
        </main>
      </div>
    </div>
  );
}

// ── DAG Canvas ──
function DagCanvas({ layout, statusSet, onSelect, selectedId }: {
  layout: { nodes: LayoutNode[]; edges: DagEdge[]; groups: GroupBox[]; width: number; height: number; density: Density };
  statusSet: Set<string>;
  onSelect: (id: string) => void;
  selectedId: string | null;
}) {
  const { nodes, edges, groups, width, height, density } = layout;
  const { paths, markers } = useMemo(() => drawEdgesPaths(edges, (e) => ({
    dimmed: !(statusSet.has((e.from as LayoutNode).task?.status || "planning") && statusSet.has((e.to as LayoutNode).task?.status || "planning")),
  })), [edges, statusSet]);

  // Hover chain highlight
  const [hoverId, setHoverId] = useState<string | null>(null);
  const chain = useMemo(() => {
    if (!hoverId) return null;
    const succ = new Map<string, string[]>(), pred = new Map<string, string[]>();
    for (const e of edges) { if (!succ.has(e.from.id)) succ.set(e.from.id, []); if (!pred.has(e.to.id)) pred.set(e.to.id, []); succ.get(e.from.id)!.push(e.to.id); pred.get(e.to.id)!.push(e.from.id); }
    const seen = new Set([hoverId]);
    for (const adj of [succ, pred]) { const queue = [hoverId]; while (queue.length) { for (const nx of adj.get(queue.shift()!) || []) { if (seen.has(nx)) continue; seen.add(nx); queue.push(nx); } } }
    return seen;
  }, [hoverId, edges]);

  if (!nodes.length) return <div className="py-16 text-center text-muted-foreground">暂无任务</div>;

  return (
    <div className="relative dag-canvas" style={{ width, height, minWidth: "100%" }}
      onMouseOver={(e) => { const card = (e.target as Element).closest("[data-node-id]"); setHoverId(card?.getAttribute("data-node-id") || null); }}
      onMouseLeave={() => setHoverId(null)}
    >
      <svg className="pointer-events-none absolute inset-0 dag-edges" style={{ width: "100%", height: "100%" }} aria-hidden="true">
        <defs>
          {markers.map(m => (
            <marker key={m.id} id={m.id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill={`var(--${m.color})`} />
            </marker>
          ))}
        </defs>
        {paths.map((p, i) => (
          <path key={i} d={p.d} fill="none" stroke={p.stroke} strokeWidth={p.strokeWidth}
            strokeOpacity={chain ? (chain.has(p.fromId) && chain.has(p.toId) ? "0.95" : "0.1") : p.strokeOpacity}
            strokeDasharray={p.dashArray}
            markerEnd={p.markerEnd}
            className="dag-edge"
            data-from={p.fromId} data-to={p.toId}
          />
        ))}
      </svg>
      {groups.map(g => {
        const st = g.parent.status || "planning";
        const meta = ST_META[st] || ST_META.planning;
        const doneCount = g.children.filter(c => c.status === "done").length;
        const pct = g.children.length ? Math.round((doneCount / g.children.length) * 100) : 0;
        return (
          <div key={g.id} className="dag-group-box absolute rounded-lg border-2 border-dashed"
            style={{ left: g.x, top: g.y, width: g.w, height: g.h, borderColor: `var(${meta.colorVar})`, backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 6%, transparent)` }}>
            <div
              onClick={(e) => { e.preventDefault(); onSelect(g.id); }}
              className={cn("dag-group-header flex cursor-pointer items-center gap-2 overflow-hidden rounded-t-md border-b px-2", selectedId === g.id && "ring-2 ring-primary")}
              style={{ height: g.headerH, borderColor: `var(${meta.colorVar})`, backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 22%, var(--card))` }}
            >
              <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
              <span className="truncate text-xs font-semibold text-foreground">{g.parent.title || g.parent.name || g.id}</span>
              <span className="ml-auto flex-shrink-0 font-mono text-[10px] text-muted-foreground">{doneCount}/{g.children.length}</span>
              <div className="ml-1 h-1.5 w-12 flex-shrink-0 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: `var(${meta.colorVar})` }} />
              </div>
            </div>
          </div>
        );
      })}
      {nodes.map(n => {
        const t = n.task; if (!t) return null;
        const st = t.status || "planning";
        const meta = ST_META[st] || ST_META.planning;
        const dimmed = !statusSet.has(st);
        const inChain = chain?.has(n.id) ?? false;
        const isDim = chain ? !inChain : false;
        const mini = density === "mini";
        const subs = (t.subtasks || []) as NormSubtask[];
        const subDone = subs.filter(s => s.status === "done").length;
        return (
          <div key={n.id} className="dag-node-wrap absolute" data-node-id={n.id}
            style={{ left: n.x, top: n.y, width: n.w, opacity: dimmed ? 0.4 : (isDim ? 0.15 : 1), transition: "opacity 0.15s" }}>
            <div
              onClick={(e) => { e.preventDefault(); onSelect(n.id); }}
              data-task-id={n.id}
              className={cn("flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md", selectedId === n.id && "ring-2 ring-primary", st === "active" && "dag-node-active")}
              style={{ height: n.h, borderColor: `var(${meta.colorVar})`, backgroundColor: `color-mix(in srgb, var(${meta.colorVar}) 20%, var(--card))` }}
            >
              <span className="h-2 w-2 flex-shrink-0 rounded-full ml-2" style={{ backgroundColor: `var(${meta.colorVar})` }} />
              <div className="min-w-0 flex-1 pr-2">
                {mini ? (
                  <div className="truncate text-xs leading-none text-foreground">{t.title || t.name || t.id}</div>
                ) : (
                  <>
                    <div className="flex items-center gap-1.5">
                      <div className="min-w-0 flex-1 truncate text-xs font-semibold leading-tight text-foreground">{t.title || t.name || "(未命名)"}</div>
                      <span className="flex-shrink-0 rounded border px-1 text-[9px] font-medium leading-tight" style={{ color: `var(${PRIORITY_COLOR_VAR[t.priority] || "--muted-foreground"})`, borderColor: `var(${PRIORITY_COLOR_VAR[t.priority] || "--muted-foreground"})` }}>{PRIORITY_LABEL[t.priority] || t.priority || "中"}</span>
                    </div>
                    <div className="flex items-center text-[10px] leading-tight text-muted-foreground">
                      <span className="truncate font-mono">#{t.id}</span>
                      {subs.length > 0 && <span className="flex-shrink-0 ml-1">{subDone}/{subs.length}</span>}
                    </div>
                  </>
                )}
              </div>
            </div>
            {/* Hover 悬浮卡片 */}
            {hoverId === n.id && (
              <div className="pointer-events-none absolute left-0 top-full z-50 mt-2 w-80 rounded-lg border border-border/40 bg-card/95 p-4 shadow-xl backdrop-blur-md">
                <div className="mb-1.5 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
                  <span className="text-xs font-semibold text-foreground">{t.title || t.name || t.id}</span>
                  <span className="ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium text-white" style={{ backgroundColor: `var(${meta.colorVar})` }}>{meta.label}</span>
                </div>
                <div className="mb-1.5 font-mono text-[10px] text-muted-foreground">#{t.id}</div>
                {(t.desc || t.description) && (
                  <div className="mb-2 line-clamp-3 text-xs leading-relaxed text-muted-foreground">{t.desc || t.description}</div>
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
                {(t.deps && t.deps.length > 0) && (
                  <div className="text-[10px] text-muted-foreground">依赖: {t.deps.join(", ")}</div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
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
                  <i className={`fa ${meta.icon} text-xs`} style={{ color: `var(${meta.colorVar})` }} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-foreground">{t.title || t.name || "(未命名)"}</div>
                    <div className="truncate font-mono text-xs text-muted-foreground">#{t.id}</div>
                  </div>
                  <span className="flex-shrink-0 rounded border px-1 text-[9px] font-medium" style={{ color: `var(${PRIORITY_COLOR_VAR[t.priority] || "--muted-foreground"})`, borderColor: `var(${PRIORITY_COLOR_VAR[t.priority] || "--muted-foreground"})` }}>{PRIORITY_LABEL[t.priority] || t.priority || "中"}</span>
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
function DetailPanel({ task, allTasks, onClose, onConfirm, onFinish, onDelete, onPriorityChange, onSelectTask }: {
  task: NormTask; allTasks: NormTask[]; onClose: () => void;
  onConfirm: (id: string) => void; onFinish: (id: string, name: string) => void; onDelete: (id: string, name: string) => void;
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
            <button onClick={() => onConfirm(task.id)} data-tip="确认规划 → 进就绪" className="icon-btn flex items-center justify-center rounded-md border border-primary/40 p-1.5 text-primary hover:bg-primary/10"><IconApprove /></button>
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
            <select value={task.priority} onChange={(e) => onPriorityChange(task.id, e.target.value)}
              className="rounded-md border border-border bg-card/60 px-2 py-1 text-sm text-foreground">
              {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
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
                      <i className={`fa ${item.done ? "fa-check-square" : "fa-square-o"} mt-0.5 flex-shrink-0`} style={{ color: item.done ? "var(--st-done)" : "var(--muted-foreground)" }} />
                      <span className={item.done ? "text-muted-foreground line-through" : "text-foreground"}>{item.text}</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-muted-foreground">—</p>}
            </DetailCard>
          ));
        })()}

        {/* Contracts */}
        {task.contracts?.length > 0 && (
          <DetailCard title="契约">
            <div className="space-y-2">
              {task.contracts.map((c, i) => (
                <div key={i} className="rounded border border-border/40 bg-muted/20 p-2">
                  <div className="text-sm font-medium text-foreground">{c.id}</div>
                  {c.desc && <div className="mt-1 text-xs text-muted-foreground">{c.desc}</div>}
                </div>
              ))}
            </div>
          </DetailCard>
        )}

        {/* Subtask DAG */}
        {subs.length >= 2 && (
          <DetailCard title="子任务 DAG">
            <SubtaskDag subs={subs} />
          </DetailCard>
        )}

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
const STAGE_ORDER: Record<string, number> = { planning: 0, ready: 1, active: 2, check: 3, done: 4 };
const STAGE_COLORS: Record<string, string> = {
  created: "#74b9e8", ready: "#429cd1", started: "#237bb8", checked: "#c9a227", finished: "#48bb78",
};

function TaskTimeline({ task, eta, subs }: { task: NormTask; eta: { main: string; detail: string } | null; subs: NormSubtask[] }) {
  const st = task.status || "planning";
  const idx = STAGE_ORDER[st];
  const byTs = idx == null;
  const at = (i: number, ts: number | null) => byTs ? !!ts : idx > i;
  const stages = [
    { key: "planning", label: "规划中", desc: "任务规划与 PRD 编写", time: task.createdAt, done: idx > 0, current: idx === 0, color: STAGE_COLORS.created },
    { key: "ready", label: "就绪", desc: "规划完成，等待开始执行", time: task.confirmedAt, done: idx > 1, current: idx === 1, color: STAGE_COLORS.ready },
    { key: "started", label: "执行", desc: "任务执行中", time: task.startedAt, done: idx > 2, current: idx === 2, color: STAGE_COLORS.started },
    { key: "checked", label: "验收", desc: "checkpoint 核对", time: task.checkedAt, done: idx > 3, current: idx === 3, color: STAGE_COLORS.checked },
    { key: "finished", label: "完成", desc: "任务完成", time: task.finishedAt, done: byTs ? !!task.finishedAt : idx >= 4, current: false, color: STAGE_COLORS.finished },
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
                              <i className="fa fa-check" />
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

// ── Subtask DAG (mini, draggable pan, same style as task DAG) ──
function SubtaskDag({ subs }: { subs: NormSubtask[] }) {
  const layout = useMemo(() => {
    const byId = new Map(subs.map(s => [s.id, s]));
    const s = { colW: 160, rowH: 60, padX: 16, padY: 24, gapX: 16, gapY: 24 };
    const depsOf = (id: string) => (byId.get(id)?.deps || []).filter(d => byId.has(d));
    return layoutTiered([...byId.keys()], depsOf, { w: s.colW - s.gapX, h: s.rowH - s.gapY, gapX: s.gapX, gapY: s.gapY, padX: s.padX, padY: s.padY }, 580, (id) => ({ sub: byId.get(id)! }));
  }, [subs]);

  const { paths, markers } = useMemo(() => drawEdgesPaths(layout.edges), [layout.edges]);
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

  if (!layout.nodes.length) return <div className="py-4 text-center text-xs text-muted-foreground">暂无子任务</div>;

  return (
    <div className="overflow-auto" ref={wrapRef} onMouseDown={onMouseDown} style={{ cursor: "grab", maxHeight: "400px" }}>
      <div className="relative mx-auto" style={{ width: layout.width, height: layout.height }}>
        <svg className="pointer-events-none absolute inset-0" style={{ width: "100%", height: "100%" }}>
          <defs>
            {markers.map(m => <marker key={m.id} id={m.id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill={`var(--${m.color})`} /></marker>)}
          </defs>
          {paths.map((p, i) => <path key={i} d={p.d} fill="none" stroke={p.stroke} strokeWidth={p.strokeWidth} strokeOpacity={p.strokeOpacity} strokeDasharray={p.dashArray} markerEnd={p.markerEnd} />)}
        </svg>
        {layout.nodes.map(n => {
          const sub = (n as any).sub as NormSubtask; if (!sub) return null;
          const sm = ST_META[sub.status] || ST_META.planning;
          return (
            <div key={n.id} className="absolute flex cursor-pointer items-center gap-2 overflow-hidden rounded-md border transition-all hover:shadow-md" style={{ left: n.x, top: n.y, width: n.w, height: n.h, opacity: sub.status === "done" ? 0.5 : 1, borderColor: `var(${sm.colorVar})`, backgroundColor: `color-mix(in srgb, var(${sm.colorVar}) 20%, var(--card))` }} title={sub.title || sub.name || sub.id}>
              <span className="ml-2 h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: `var(${sm.colorVar})` }} />
              <div className="min-w-0 flex-1 pr-2">
                <div className="truncate text-xs font-semibold leading-tight text-foreground">{sub.title || sub.name || sub.id}</div>
                <div className="truncate text-[10px] leading-tight text-muted-foreground">{sm.label}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
