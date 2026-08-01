// ETA 剩余工时预估 — 纯函数移植 (无 DOM 无副作用)

const OWN_LEFT: Record<string, number> = { planning: 1, ready: 0.85, active: 0.6, check: 0.25, done: 0, failed: 0.6 };

interface SubLike { sid?: string; id?: string; status?: string; estimate?: number | null; progress?: number | null; pct?: number; dependsOn?: string[]; deps?: string[]; startedAt?: number | null; finishedAt?: number | null; }
interface TaskLike { id: string; status?: string; estimate?: number | null; progress?: number | null; deps?: string[]; subtasks?: SubLike[]; startedAt?: number | null; finishedAt?: number | null; createdAt?: number | null; [key: string]: unknown; }

function subRemain(s: SubLike, fallbackEst: number): number {
  if (s.status === "done" || s.status === "已完成") return 0;
  const est = typeof s.estimate === "number" && s.estimate > 0 ? s.estimate : fallbackEst;
  if (!est) return 0;
  const pct = Math.min(100, Math.max(0, Number(s.progress ?? s.pct ?? 0)));
  return est * (1 - pct / 100);
}

export function criticalPath<T extends { id: string; sid?: string; deps?: string[]; dependsOn?: string[] }>(subs: T[], remOf: (n: T) => number): number {
  const byId = new Map(subs.map(s => [(s.sid || s.id), s]));
  const memo = new Map<string, number>();
  const inStack = new Set<string>();
  const walk = (id: string): number => {
    if (memo.has(id)) return memo.get(id)!;
    if (inStack.has(id)) return 0;
    const s = byId.get(id) as T | undefined;
    if (!s) return 0;
    inStack.add(id);
    const deps = (s as Record<string, unknown>).dependsOn as string[] || s.deps || [];
    const best = deps.reduce((m: number, d: string) => Math.max(m, walk(d)), 0);
    inStack.delete(id);
    const v = best + remOf(s);
    memo.set(id, v);
    return v;
  };
  return subs.reduce((m, s) => Math.max(m, walk(s.sid || s.id)), 0);
}

function calibration(subs: SubLike[]): number {
  let act = 0, est = 0;
  for (const s of subs) {
    if (s.status !== "done" || !s.startedAt || !s.finishedAt) continue;
    if (!(typeof s.estimate === "number" && s.estimate > 0)) continue;
    act += (s.finishedAt - s.startedAt) / 3600000;
    est += s.estimate;
  }
  if (!est || !act) return 1;
  const r = act / est;
  return r < 0.25 || r > 4 ? 1 : r;
}

export interface EtaResult { hours: number; calib: number; own: number; work: number; critical: number; }

export function etaOf(task: TaskLike, maxActive: number): EtaResult | null {
  const st = task.status || "planning";
  if (["done", "archived", "cancelled"].includes(st)) return null;
  const subs = task.subtasks || [];
  const withEst = subs.filter(s => typeof s.estimate === "number" && s.estimate > 0);
  const fallbackEst = withEst.length ? withEst.reduce((a, s) => a + (s.estimate as number), 0) / withEst.length : 0;
  const remOf = (s: SubLike) => subRemain(s, fallbackEst);
  const work = subs.reduce((a, s) => a + remOf(s), 0);
  const subSum = subs.reduce((a, s) => a + (Number(s.estimate) || 0), 0);
  const taskEst = Number(task.estimate) || 0;
  const own = Math.max(0, taskEst - subSum) * (OWN_LEFT[st] ?? 0.6);
  if (!work && !own) {
    if (!taskEst) return null;
    const pct = Math.min(100, Math.max(0, Number(task.progress) || 0));
    return { hours: taskEst * (1 - pct / 100), calib: 1, own: 0, work: 0, critical: 0 };
  }
  const calib = calibration(subs);
  const n = Math.max(1, Number(maxActive) || 1);
  const critical = criticalPath(subs as { id: string; sid?: string; deps?: string[] }[], remOf as (n: { id: string; sid?: string; deps?: string[] }) => number);
  const wall = Math.max(critical, work / n);
  return { hours: (wall + own) * calib, calib, own, work, critical };
}

export function aggregateEta(tasks: TaskLike[], maxActive: number): { hours: number; work: number; critical: number; unknown: number } {
  const live = (tasks || []).filter(t => { const st = t.status || "planning"; return !["done", "archived", "cancelled"].includes(st); });
  if (!live.length) return { hours: 0, work: 0, critical: 0, unknown: 0 };
  let work = 0, unknown = 0;
  const remOf = (t: TaskLike) => { const e = etaOf(t, maxActive); if (!e) { unknown += 1; return 0; } return e.hours; };
  const rem = new Map(live.map(t => [t.id, remOf(t)]));
  for (const v of rem.values()) work += v;
  const liveIds = new Set(live.map(t => t.id));
  const nodes = live.map(t => ({ id: t.id, deps: (t.deps || []).filter(d => liveIds.has(d)) }));
  const critical = criticalPath(nodes, (n) => rem.get(n.id) || 0);
  const n = Math.max(1, Number(maxActive) || 1);
  return { hours: Math.max(critical, work / n), work, critical, unknown };
}

export function overallProgress(tasks: TaskLike[]): number {
  const live = (tasks || []).filter(t => (t.status || "") !== "archived");
  if (!live.length) return 0;
  const w = (t: TaskLike) => { const e = Number(t.estimate); return isFinite(e) && e > 0 ? e : 1; };
  const pct = (t: TaskLike) => { const st = t.status || "planning"; if (st === "done") return 100; const p = Number(t.progress); return isFinite(p) ? Math.min(100, Math.max(0, p)) : 0; };
  const tot = live.reduce((a, t) => a + w(t), 0);
  return tot ? Math.round(live.reduce((a, t) => a + w(t) * pct(t), 0) / tot) : 0;
}

export function fmtHours(h: number | null | undefined): string {
  if (h == null || !isFinite(h) || h <= 0) return "—";
  if (h < 1) return `${Math.max(1, Math.round(h * 60))} 分钟`;
  if (h < 16) return `${h < 10 ? h.toFixed(1) : Math.round(h)} 小时`;
  const d = h / 8;
  return `${d < 10 ? d.toFixed(1) : Math.round(d)} 人日`;
}

// 已完成实际耗时 (墙钟)
export function actualOf(task: TaskLike): { hours: number; est: number; delta: number | null } | null {
  const end = task.finishedAt, start = task.startedAt || task.createdAt;
  if (!end || !start || end <= start) return null;
  const hours = (end - start) / 3600000;
  const est = Number(task.estimate) || 0;
  return { hours, est, delta: est ? hours / est - 1 : null };
}

export function deltaText(d: number | null): string | null {
  if (d == null || Math.abs(d) < 0.05) return null;
  return (d > 0 ? "超出 +" : "提前 ") + Math.round(Math.abs(d) * 100) + "%";
}

export function etaText(task: TaskLike, maxActive: number): { main: string; detail: string; eta?: EtaResult } | null {
  const st = task.status || "planning";
  if (st === "done" || st === "archived") {
    const a = actualOf(task);
    if (!a) return null;
    const parts: string[] = [];
    if (a.est) parts.push(`预估 ${fmtHours(a.est)}`);
    const dt = deltaText(a.delta);
    if (dt) parts.push(dt);
    return { main: `实际耗时 ${fmtHours(a.hours)}`, detail: parts.join(" · ") };
  }
  const e = etaOf(task, maxActive);
  if (!e) return null;
  const parts: string[] = [];
  if (e.critical) parts.push(`关键路径 ${fmtHours(e.critical)}`);
  if (e.own) parts.push(`自身开销 ${fmtHours(e.own)}`);
  if (Math.abs(e.calib - 1) > 0.05) parts.push(`实测校准 ×${e.calib.toFixed(2)}`);
  return { main: `剩余约 ${fmtHours(e.hours)}`, detail: parts.join(" · "), eta: e };
}

export function overallSummary(tasks: TaskLike[], maxActive: number): { pct: number; remainText: string; remainHint: string } {
  const all = (tasks || []).filter(t => (t.status || "") !== "archived");
  const pct = overallProgress(all);
  if (!all.length) return { pct: 0, remainText: "暂无任务", remainHint: "" };
  const live = all.filter(t => { const st = t.status || "planning"; return st !== "done" && st !== "cancelled"; });
  if (!live.length) return { pct, remainText: "全部完成", remainHint: "" };
  const agg = aggregateEta(all, maxActive);
  if (agg.unknown === live.length) return { pct, remainText: "未知", remainHint: `${agg.unknown} 个未估工时` };
  const n = Math.max(1, Number(maxActive) || 1);
  const hints = [`总工时 ${fmtHours(agg.work)}`, `并发 ${n}`];
  if (agg.unknown) hints.push(`${agg.unknown} 个未估工时`);
  return { pct, remainText: fmtHours(agg.hours), remainHint: hints.join(" · ") };
}
