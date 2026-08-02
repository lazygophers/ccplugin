// 依赖关系图 (以任一 task 为中心的上下游) + 通用 DAG 连线渲染
// 从旧 depdag.js 移植, TypeScript 化

import type { NormTask } from "./model";

const ST_COLOR: Record<string, string> = {
  planning: "st-planning",
  active: "st-active", check: "st-check",
  done: "st-done", failed: "st-failed",
};

export const EDGE_KIND: Record<string, { color: string; label: string }> = {
  ready:   { color: "st-done",   label: "依赖已完成" },
  blocked: { color: "st-active", label: "阻塞 · 上游可执行" },
  stuck:   { color: "st-failed", label: "阻塞 · 上游被卡" },
};

export interface DagNode {
  id: string;
  x: number; y: number;
  w: number; h: number;
  rowH?: number;
  band?: number;
  task?: NormTask;
  sub?: Record<string, unknown>;
  [key: string]: unknown;
}
export interface DagEdge {
  from: DagNode;
  to: DagNode;
  bends: { x: number; y: number }[];
  cross: boolean;
  laneY: number;
}

export function edgeKinds(edges: DagEdge[]): (e: DagEdge) => string {
  const item = new Map<string, Record<string, unknown>>();
  for (const e of edges) for (const n of [e.from, e.to]) item.set(n.id, (n.task || n.sub || {}) as Record<string, unknown>);
  const stOf = (id: string): string => item.has(id) ? ((item.get(id)!.status as string) || "planning") : "done";
  return (e: DagEdge): string => {
    if (stOf(e.from.id) === "done") return "ready";
    const f = item.get(e.from.id) || {};
    const deps = (f.deps || f.dependsOn || []) as string[];
    return deps.every((d: string) => stOf(d) === "done") ? "blocked" : "stuck";
  };
}

// ---- orthPath: 正交折点 → 圆角直角 path ----
function orthPath(raw: { x: number; y: number }[]): string {
  const pts: { x: number; y: number }[] = [];
  for (const p of raw) {
    const last = pts[pts.length - 1];
    if (last && Math.abs(last.x - p.x) < 0.5 && Math.abs(last.y - p.y) < 0.5) continue;
    pts.push(p);
  }
  if (pts.length < 2) return "";
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const pv = pts[i - 1], p = pts[i], nx = pts[i + 1];
    const inLen = Math.abs(p.x - pv.x) + Math.abs(p.y - pv.y);
    const outLen = Math.abs(nx.x - p.x) + Math.abs(nx.y - p.y);
    const r = Math.min(10, inLen / 2, outLen / 2);
    d += ` L ${p.x - Math.sign(p.x - pv.x) * r} ${p.y - Math.sign(p.y - pv.y) * r}`;
    d += ` Q ${p.x} ${p.y} ${p.x + Math.sign(nx.x - p.x) * r} ${p.y + Math.sign(nx.y - p.y) * r}`;
  }
  const end = pts[pts.length - 1];
  return d + ` L ${end.x} ${end.y}`;
}

// ---- bundleTrunks: 边捆绑 ----
function bundleTrunks(edges: DagEdge[]): Map<string, { x: number; set: Set<DagEdge> }> {
  const byTo = new Map<string, DagEdge[]>();
  for (const e of edges) {
    if (e.cross || Math.abs(e.to.y - e.from.y) <= (e.from.rowH || e.from.h)) continue;
    if (!byTo.has(e.to.id)) byTo.set(e.to.id, []);
    byTo.get(e.to.id)!.push(e);
  }
  const trunks = new Map<string, { x: number; set: Set<DagEdge> }>();
  for (const [id, group] of byTo) {
    if (group.length >= 3) trunks.set(id, { x: group[0].to.x - 16, set: new Set(group) });
  }
  return trunks;
}

// ---- drawEdges: SVG 连线 → React 元素数组 ----
export interface EdgeRenderInfo { dimmed?: boolean }

export function drawEdgesPaths(edges: DagEdge[], getEdgeInfo?: (e: DagEdge) => EdgeRenderInfo): {
  paths: { d: string; stroke: string; strokeWidth: number; strokeOpacity: string; dashArray?: string; markerEnd: string; fromId: string; toId: string }[];
  markers: { id: string; color: string }[];
} {
  if (!edges.length) return { paths: [], markers: [] };
  const kindOf = edgeKinds(edges);
  const usedKinds = new Set<string>();
  const markers: { id: string; color: string }[] = [];
  for (const e of edges) {
    const k = kindOf(e);
    if (usedKinds.has(k)) continue;
    usedKinds.add(k);
    markers.push({ id: `arrow-${k}`, color: EDGE_KIND[k].color });
  }

  const lanes = new Map<string, number>();
  const chan = (v: number, axis: string): number => {
    const k = axis + Math.round(v / 10);
    const n = lanes.get(k) || 0;
    lanes.set(k, n + 1);
    return v + (n % 5) * 7 - 14;
  };
  const trunks = bundleTrunks(edges);

  const paths = edges.map(e => {
    const trunk = trunks.get(e.to.id);
    const bundled = !!trunk && trunk.set.has(e);
    const vert = !bundled && Math.abs(e.to.x - e.from.x) < e.from.w && e.to.y > e.from.y + e.from.h / 2;
    const bx = bundled ? trunk!.x : e.to.x + e.to.w / 2;
    const rightward = bx >= e.from.x + e.from.w / 2;
    const downward = e.to.y >= e.from.y;
    const x1 = vert ? e.from.x + e.from.w / 2 : (rightward ? e.from.x + e.from.w : e.from.x);
    const y1 = vert ? (downward ? e.from.y + e.from.h : e.from.y) : e.from.y + e.from.h / 2;
    const x2 = vert ? e.to.x + e.to.w / 2 : (bundled || rightward ? e.to.x : e.to.x + e.to.w);
    const y2 = vert ? (downward ? e.to.y : e.to.y + e.to.h) : e.to.y + e.to.h / 2;
    const kind = kindOf(e);
    const dimmed = getEdgeInfo ? !!getEdgeInfo(e).dimmed : false;
    const pts: { x: number; y: number }[] = [{ x: x1, y: y1 }];
    if (bundled) {
      const sx = x1 + (rightward ? 16 : -16), yc = e.from.y + (e.from.rowH || e.from.h) + 10;
      pts.push({ x: sx, y: y1 }, { x: sx, y: yc }, { x: trunk!.x, y: yc }, { x: trunk!.x, y: y2 });
    } else if (e.cross) {
      const sx = chan(x1 + (rightward ? 30 : -30), "x");
      const ex = chan(x2 + (rightward ? -30 : 30), "x");
      const yc = chan(e.laneY, "y");
      pts.push({ x: sx, y: y1 }, { x: sx, y: yc }, { x: ex, y: yc }, { x: ex, y: y2 });
    } else if (vert) {
      let px = x1, py = y1;
      for (const m of [...(e.bends || []), { x: x2, y: y2 }]) {
        const cy = chan((py + m.y) / 2, "y");
        pts.push({ x: px, y: cy }, { x: m.x, y: cy });
        px = m.x; py = m.y;
      }
    } else {
      let px = x1, py = y1;
      for (const m of [...(e.bends || []), { x: x2, y: y2 }]) {
        const cx = chan((px + m.x) / 2, "x");
        pts.push({ x: cx, y: py }, { x: cx, y: m.y });
        px = m.x; py = m.y;
      }
    }
    pts.push({ x: x2, y: y2 });
    const d = orthPath(pts);
    const opacity = dimmed ? "0.12" : (e.cross ? "0.4" : "0.55");
    return {
      d, stroke: `var(--${EDGE_KIND[kind].color})`,
      strokeWidth: 2, strokeOpacity: opacity,
      dashArray: e.cross ? "7 5" : undefined,
      markerEnd: `url(#arrow-${kind})`,
      fromId: e.from.id, toId: e.to.id,
    };
  });
  return { paths, markers };
}

// ---- buildDepDAG: 以当前 task 为中心的上下游图 (含父子关系) ----
export function buildDepDAG(taskId: string, allTasks: NormTask[]) {
  const byId = new Map(allTasks.map(t => [t.id, t]));
  const task = byId.get(taskId);
  if (!task) return { nodes: [] as DepDagNode[], edges: [] as DagEdge[], groups: [] as DepDagGroup[], width: 0, height: 0, centerId: taskId };

  const visited = new Set<string>([taskId]);
  const upstream: string[] = [];
  const downstream: string[] = [];
  const downstreamOf = new Map<string, string[]>();
  for (const t of allTasks) {
    for (const d of t.deps || []) {
      if (!downstreamOf.has(d)) downstreamOf.set(d, []);
      downstreamOf.get(d)!.push(t.id);
    }
  }

  let queue = [...(task.deps || [])];
  while (queue.length) {
    const id = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id); upstream.push(id);
    const t = byId.get(id);
    if (t && t.deps) queue.push(...t.deps.filter(d => !visited.has(d)));
  }
  queue = downstreamOf.get(taskId) || [];
  while (queue.length) {
    const id = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id); downstream.push(id);
    const next = downstreamOf.get(id) || [];
    queue.push(...next.filter(d => !visited.has(d)));
  }

  // 父子关系纳入图: 当前 task 的 parent + parent 的其他 child; 若是 supertask 则纳入其 child
  const parentId = task.parent;
  if (parentId && byId.has(parentId) && !visited.has(parentId)) {
    visited.add(parentId);
    upstream.push(parentId);
  }
  // supertask 的 child 全部纳入
  if (task.kind === "supertask") {
    for (const t of allTasks) {
      if (t.parent === taskId && !visited.has(t.id)) {
        visited.add(t.id);
        downstream.push(t.id);
      }
    }
  }
  // 若当前 task 有 parent, 把兄弟 (同 parent 的其他 child) 也纳入
  if (parentId) {
    for (const t of allTasks) {
      if (t.parent === parentId && t.id !== taskId && !visited.has(t.id)) {
        visited.add(t.id);
        downstream.push(t.id);
      }
    }
  }

  const layerOf = new Map<string, number>();
  layerOf.set(taskId, 0);
  let upQueue = [taskId], upLayer = 0;
  while (upQueue.length) {
    upLayer--;
    const next: string[] = [];
    for (const id of upQueue) {
      const t = byId.get(id);
      if (!t) continue;
      for (const d of t.deps || []) {
        if (!visited.has(d)) continue;
        if (layerOf.has(d) && layerOf.get(d)! >= upLayer) continue;
        layerOf.set(d, upLayer); next.push(d);
      }
      // parent 在上游层
      if (t.parent && visited.has(t.parent)) {
        if (!layerOf.has(t.parent) || layerOf.get(t.parent)! >= upLayer) {
          layerOf.set(t.parent, upLayer); next.push(t.parent);
        }
      }
    }
    upQueue = [...new Set(next)];
  }
  let downQueue = [taskId], downLayer = 0;
  while (downQueue.length) {
    downLayer++;
    const next: string[] = [];
    for (const id of downQueue) {
      const deps = downstreamOf.get(id) || [];
      for (const d of deps) {
        if (!visited.has(d)) continue;
        if (layerOf.has(d) && layerOf.get(d)! <= downLayer) continue;
        layerOf.set(d, downLayer); next.push(d);
      }
      // child 在下游层 (supertask → child, 或同 parent 的兄弟)
      const t = byId.get(id);
      if (t) {
        for (const ot of allTasks) {
          if (ot.parent === id && visited.has(ot.id)) {
            if (!layerOf.has(ot.id) || layerOf.get(ot.id)! <= downLayer) {
              layerOf.set(ot.id, downLayer); next.push(ot.id);
            }
          }
        }
      }
    }
    downQueue = [...new Set(next)];
  }

  const layers = new Map<number, string[]>();
  for (const [id, layer] of layerOf) {
    if (!layers.has(layer)) layers.set(layer, []);
    layers.get(layer)!.push(id);
  }
  const colW = 180, rowH = 56, padX = 20, padY = 16;
  const minLayer = Math.min(...layers.keys());
  const layerOffset = -minLayer;
  const nodes: DepDagNode[] = [];
  for (const [layer, ids] of layers) {
    const colIdx = layer + layerOffset;
    ids.forEach((id, ri) => {
      const t = byId.get(id);
      if (!t) return;
      nodes.push({
        id, task: t,
        x: padX + colIdx * colW, y: padY + ri * rowH,
        w: colW - 16, h: rowH - 12,
        isCenter: id === taskId, layer,
      });
    });
  }
  const edges: DagEdge[] = [];
  for (const n of nodes) {
    for (const depId of n.task.deps || []) {
      const src = nodes.find(x => x.id === depId);
      if (src) edges.push({ from: src, to: n, bends: [], cross: false, laneY: 0 });
    }
    // 父子关系不再生成边 (看板同规则) —— 改用下面的包裹分组表达
  }

  // 父子包裹分组: 与看板同规则, 父子关系用包裹而非箭头表达。
  // 这里的节点坐标来自 BFS 分层 (与看板的 Sugiyama 分层是两套不同算法), 故不复用 board-layout 的
  // GroupBox 生成逻辑, 而是在已算好的节点坐标上直接求包围盒 —— 对这个小图足够且不引入第二套布局引擎。
  const nodeById = new Map(nodes.map(n => [n.id, n]));
  const childrenByParent = new Map<string, string[]>();
  for (const n of nodes) {
    if (n.task.parent && nodeById.has(n.task.parent)) {
      if (!childrenByParent.has(n.task.parent)) childrenByParent.set(n.task.parent, []);
      childrenByParent.get(n.task.parent)!.push(n.id);
    }
  }
  const groups: DepDagGroup[] = [];
  for (const [pid, kidIds] of childrenByParent) {
    const members = [pid, ...kidIds].map(id => nodeById.get(id)!).filter(Boolean);
    if (members.length < 2) continue; // 无 child 落图内的父不成组, 不画空容器
    const x0 = Math.min(...members.map(m => m.x)) - GROUP_PAD;
    const y0 = Math.min(...members.map(m => m.y)) - GROUP_PAD;
    const x1 = Math.max(...members.map(m => m.x + m.w)) + GROUP_PAD;
    const y1 = Math.max(...members.map(m => m.y + m.h)) + GROUP_PAD;
    groups.push({ id: pid, x: x0, y: y0, w: x1 - x0, h: y1 - y0 });
  }

  const numLayers = layers.size;
  const maxRows = Math.max(1, ...[...layers.values()].map(l => l.length));
  const width = Math.max(padX * 2 + numLayers * colW, ...groups.map(g => g.x + g.w), 0);
  const height = Math.max(padY * 2 + maxRows * rowH, ...groups.map(g => g.y + g.h), 0);
  return { nodes, edges, groups, width, height, centerId: taskId };
}

const GROUP_PAD = 10;

export interface DepDagGroup { id: string; x: number; y: number; w: number; h: number }

export interface DepDagNode {
  id: string; task: NormTask;
  x: number; y: number; w: number; h: number;
  isCenter: boolean; layer: number;
  [key: string]: unknown;
}
