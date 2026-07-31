// ---- 剩余工时预估 (ETA) — 纯函数, 无 DOM 无副作用 ----
//
// 单独成文件的理由: app.js 一被 import 就自启动 (boot/wireTheme 直接碰 document), 于是这段纯
// 数学没法在浏览器外验证。抽出来后 node 里直接 import 就能跑, 改算法能当场验 (见 tests/)。
//
// 综合五路输入: ① subtask 逐项预估工时 ② 各 subtask 当前百分比 ③ subtask DAG 排序 (关键路径)
//   ④ 并发上限 (并行墙钟下界) ⑤ 已完成 subtask 的实际耗时 / 预估比 (校准因子)。
// 口径 = **墙钟** (人时经并发折算后), 非人力工时累加, 也不含等待/空档。

// ---- 剩余工时预估 (ETA) ----
// 综合五路输入: ① subtask 逐项预估工时 ② 各 subtask 当前百分比 ③ subtask DAG 排序 (关键路径)
//   ④ 并发上限 (并行墙钟下界) ⑤ 已完成 subtask 的实际耗时 / 预估比 (校准因子)。
// 口径 = 工时 (人时经并发折算后的墙钟), 非日历时间 — 不含等待/空档。
//
// task 自身开销 = task.estimate - Σ subtask.estimate (即 plan/grill/check/finish),
// 按阶段剩余系数折算: 越靠后剩得越少。
const OWN_LEFT = { planning: 1, ready: 0.85, active: 0.6, check: 0.25, done: 0, failed: 0.6 };

function subRemain(s, fallbackEst) {
  if (s.status === 'done') return 0;
  const est = (typeof s.estimate === 'number' && s.estimate > 0) ? s.estimate : fallbackEst;
  if (!est) return 0;
  const pct = Math.min(100, Math.max(0, Number(s.progress ?? s.pct ?? 0)));
  return est * (1 - pct / 100);
}

// DAG 最长加权路径 (权 = 节点剩余工时)。成环时断边, 不死循环。
// 节点键取 `sid || id`、依赖取 `dependsOn || deps` — 所以 subtask 级 (sid/dependsOn) 与
// task 级 (id/deps) 都能直接喂进来, 聚合 ETA 靠的就是这个通用性。
export function criticalPath(subs, remOf) {
  const byId = new Map(subs.map(s => [s.sid || s.id, s]));
  const memo = new Map(), inStack = new Set();
  const walk = (id) => {
    if (memo.has(id)) return memo.get(id);
    if (inStack.has(id)) return 0;               // 成环: 断掉这条边
    const s = byId.get(id);
    if (!s) return 0;
    inStack.add(id);
    const deps = s.dependsOn || s.deps || [];
    const best = deps.reduce((m, d) => Math.max(m, walk(d)), 0);
    inStack.delete(id);
    const v = best + remOf(s);
    memo.set(id, v);
    return v;
  };
  return subs.reduce((m, s) => Math.max(m, walk(s.sid || s.id)), 0);
}

// 校准因子: 已完成 subtask 的 Σ实际耗时 / Σ预估。样本不足或离谱 (超 [0.25,4]) 则不校准。
function calibration(subs) {
  let act = 0, est = 0;
  for (const s of subs) {
    if (s.status !== 'done' || !s.startedAt || !s.finishedAt) continue;
    if (!(typeof s.estimate === 'number' && s.estimate > 0)) continue;
    act += (s.finishedAt - s.startedAt) / 3600000;
    est += s.estimate;
  }
  if (!est || !act) return 1;
  const r = act / est;
  return (r < 0.25 || r > 4) ? 1 : r;
}

// 返回 {hours, calib, own, work, critical} 或 null (已完成 / 无任何工时数据)。
export function etaOf(task, maxActive) {
  const st = task.status || 'planning';
  if (st === 'done' || st === 'archived' || st === 'cancelled') return null;
  const subs = task.subtasks || [];
  const withEst = subs.filter(s => typeof s.estimate === 'number' && s.estimate > 0);
  // 老数据无 subtask 工时: 用同 task 已填项均值兜底; 全无则整体退回 task.estimate 按进度折算
  const fallbackEst = withEst.length
    ? withEst.reduce((a, s) => a + s.estimate, 0) / withEst.length : 0;
  const remOf = (s) => subRemain(s, fallbackEst);
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
  const critical = criticalPath(subs, remOf);
  // 并行墙钟下界: 关键路径压不动, 其余按并发摊
  const wall = Math.max(critical, work / n);
  return { hours: (wall + own) * calib, calib, own, work, critical };
}


// ── 跨 task 聚合 (看板总览用) ────────────────────────────────────────────────
// 与单 task 内部同构: 关键路径压不动, 其余按并发摊, 取两者较大者作墙钟下界。
// 为什么不是简单累加: max_active 缺省 2, 两个数差一倍; 「还要多久」问的是墙钟, 不是人力工时。
export function aggregateEta(tasks, maxActive) {
  const live = (tasks || []).filter(t => {
    const st = t.status || 'planning';
    return st !== 'done' && st !== 'archived' && st !== 'cancelled';
  });
  if (!live.length) return { hours: 0, work: 0, critical: 0, unknown: 0 };
  let work = 0, unknown = 0;
  const remOf = (t) => {
    const e = etaOf(t, maxActive);
    if (!e) { unknown += 1; return 0; }   // 无任何工时数据的 task: 记数, 不瞎猜
    return e.hours;
  };
  const rem = new Map(live.map(t => [t.id, remOf(t)]));
  for (const v of rem.values()) work += v;
  // task 级依赖只在「前置未完成」时才真的串行; 已完成的前置不构成等待
  const liveIds = new Set(live.map(t => t.id));
  const nodes = live.map(t => ({ id: t.id, deps: (t.deps || []).filter(d => liveIds.has(d)) }));
  const critical = criticalPath(nodes, (n) => rem.get(n.id) || 0);
  const n = Math.max(1, Number(maxActive) || 1);
  return { hours: Math.max(critical, work / n), work, critical, unknown };
}

// 整体进度: 按工时加权的完成度。无工时的 task 退化为等权 —— 一个 40h 的 task 和一个 1h 的
// 不该各占一半分母, 但也不能因为没填工时就不计入。
export function overallProgress(tasks) {
  const live = (tasks || []).filter(t => (t.status || '') !== 'archived');
  if (!live.length) return 0;
  const w = (t) => {
    const e = Number(t.estimate);
    return (isFinite(e) && e > 0) ? e : 1;
  };
  const pct = (t) => {
    const st = t.status || 'planning';
    if (st === 'done') return 100;
    const p = Number(t.progress);
    return isFinite(p) ? Math.min(100, Math.max(0, p)) : 0;
  };
  const tot = live.reduce((a, t) => a + w(t), 0);
  return tot ? Math.round(live.reduce((a, t) => a + w(t) * pct(t), 0) / tot) : 0;
}

// 工时 → 人话。<1h 出分钟, <16h 出小时, 否则按 8h/人日 出天。
export function fmtHours(h) {
  if (h == null || !isFinite(h) || h <= 0) return '—';
  if (h < 1) return Math.max(1, Math.round(h * 60)) + ' 分钟';
  if (h < 16) return (h < 10 ? h.toFixed(1) : Math.round(h)) + ' 小时';
  const d = h / 8;
  return (d < 10 ? d.toFixed(1) : Math.round(d)) + ' 人日';
}

// 已完成的实际耗时 (墙钟: 起始→完成)。返回 {hours, est, delta} 或 null。
// 起始优先 startedAt (真正开工), 缺则退回 createdAt。delta = 实际/预估 - 1。
export function actualOf(task) {
  const end = task.finishedAt, start = task.startedAt || task.createdAt;
  if (!end || !start || end <= start) return null;
  const hours = (end - start) / 3600000;
  const est = Number(task.estimate) || 0;
  return { hours, est, delta: est ? hours / est - 1 : null };
}

// 偏差人话: "+35%" / "-12%"; 5% 以内算准, 返回 null。
function deltaText(d) {
  if (d == null || Math.abs(d) < 0.05) return null;
  return (d > 0 ? '超出 +' : '提前 ') + Math.round(Math.abs(d) * 100) + '%';
}

// 一行摘要: 未完成出 "剩余约 3.5 小时 (关键路径 2h · ...)"; 已完成出 "实际耗时 X (预估 Y · 超出 +30%)"
export function etaText(task, maxActive) {
  const st = task.status || 'planning';
  if (st === 'done' || st === 'archived') {
    const a = actualOf(task);
    if (!a) return null;
    const parts = [];
    if (a.est) parts.push(`预估 ${fmtHours(a.est)}`);
    const dt = deltaText(a.delta);
    if (dt) parts.push(dt);
    return { main: `实际耗时 ${fmtHours(a.hours)}`, detail: parts.join(' · '), actual: a };
  }
  const e = etaOf(task, maxActive);
  if (!e) return null;
  const parts = [];
  if (e.critical) parts.push(`关键路径 ${fmtHours(e.critical)}`);
  if (e.own) parts.push(`自身开销 ${fmtHours(e.own)}`);
  if (Math.abs(e.calib - 1) > 0.05) parts.push(`实测校准 ×${e.calib.toFixed(2)}`);
  return { main: `剩余约 ${fmtHours(e.hours)}`, detail: parts.join(' · '), eta: e };
}
