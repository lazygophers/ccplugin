// ELK 布局适配层 — 输入 tasks/subs, 输出 RF 节点/边
// ELK 同时负责节点定位和边路由; edgeRouting=SPLINES 让 ELK 直接吐样条控制点,
// 路由本身就绕开 card, 前端只按控制点画贝塞尔 + 轻微抖动做手绘感, 不再自己加波形偏移
// (旧的波形偏移是把直线往法向推, 推过头就压到 card 上、短段还会自绕成圈)

import ELK from "elkjs";
import type { Edge, Node } from "@xyflow/react";
import type { NormTask, NormSubtask } from "./model";

const elk = new ELK();

const BASE_OPTS: Record<string, string> = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  // ORTHOGONAL 而非 SPLINES: 正交路由的折点是明确绕开 card 的走廊, 前端再把折线整体
  // 平滑成一根连续曲线 (见 ElkPathEdge)。SPLINES 直接吐控制点, 但控制点本身在走廊外,
  // 照着画会鼓出去蹭到 card, 且各条边点数不齐 (实测有 2/5/7 点三种), 画法没法统一。
  "elk.edgeRouting": "ORTHOGONAL",
  "elk.layered.spacing.nodeNodeBetweenLayers": "180",
  "elk.layered.spacing.nodeNode": "90",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
  // edgeNode 拉开 = 边不贴 card; edgeEdge 拉开 = 平行边之间留白, 不叠在一起
  "elk.spacing.edgeNode": "60",
  "elk.spacing.edgeEdge": "40",
  "elk.layered.spacing.edgeEdge": "40",
  "elk.layered.spacing.edgeEdgeBetweenLayers": "40",
  // 分组框内的子 task 也参与同一次布局, 边跨层级时才不会被剪到框外
  "elk.hierarchyHandling": "INCLUDE_CHILDREN",
};

interface Pt { x: number; y: number }
interface FlatNode { id: string; rel: Pt; abs: Pt; w: number; h: number; parent: string | null }

/** 递归摊平 ELK 结果: 节点给出相对父节点和绝对两套坐标, 边的 section 坐标换算成画布绝对坐标。
 *
 * 边的坐标基准看 `edge.container` 而不是「边挂在哪个节点的 edges 数组里」—— 开了
 * hierarchyHandling=INCLUDE_CHILDREN 之后, 组内边照样列在 root.edges 上, 但坐标仍相对分组框。
 * 按数组位置推基准就会让组内的边整体偏掉一个分组框的偏移量。 */
function flatten(result: any): { nodes: FlatNode[]; edges: Map<string, Pt[]> } {
  const nodes: FlatNode[] = [];
  const absOf = new Map<string, Pt>([["root", { x: 0, y: 0 }]]);
  const allEdges: any[] = [];

  const walk = (node: any, offX: number, offY: number, parent: string | null): void => {
    allEdges.push(...((node.edges || []) as any[]));
    for (const c of (node.children || []) as any[]) {
      const rel = { x: c.x || 0, y: c.y || 0 };
      const abs = { x: offX + rel.x, y: offY + rel.y };
      nodes.push({ id: c.id, rel, abs, w: c.width || 0, h: c.height || 0, parent });
      absOf.set(c.id, abs);
      walk(c, abs.x, abs.y, c.id);
    }
  };
  walk(result, 0, 0, null);

  const edges = new Map<string, Pt[]>();
  for (const e of allEdges) {
    const o = absOf.get(e.container as string) || { x: 0, y: 0 };
    const pts: Pt[] = [];
    for (const s of (e.sections || []) as any[]) {
      if (s.startPoint) pts.push({ x: s.startPoint.x + o.x, y: s.startPoint.y + o.y });
      for (const b of (s.bendPoints || []) as any[]) pts.push({ x: b.x + o.x, y: b.y + o.y });
      if (s.endPoint) pts.push({ x: s.endPoint.x + o.x, y: s.endPoint.y + o.y });
    }
    if (pts.length) edges.set(e.id, pts);
  }
  return { nodes, edges };
}

export interface DensityOpts { w: number; h: number; gapX: number; gapY: number }

export const DAG_DENSITY: Record<string, DensityOpts> = {
  large:   { w: 260, h: 76, gapX: 54, gapY: 39 },
  compact: { w: 280, h: 80, gapX: 42, gapY: 33 },
  mini:    { w: 120, h: 32, gapX: 42, gapY: 33 },
};

const toElkId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");

// ── 看板 DAG 布局 ──
export async function layoutBoardDAG(
  tasks: NormTask[],
  density: keyof typeof DAG_DENSITY = "compact",
): Promise<{ nodes: Node[]; edges: Edge[] }> {
  if (!tasks.length) return { nodes: [], edges: [] };
  const d = DAG_DENSITY[density] || DAG_DENSITY.compact;
  const byId = new Map(tasks.map(t => [t.id, t]));

  const childrenOf = new Map<string, string[]>();
  for (const t of tasks) {
    if (t.parent && t.parent !== t.id && byId.has(t.parent)) {
      if (!childrenOf.has(t.parent)) childrenOf.set(t.parent, []);
      childrenOf.get(t.parent)!.push(t.id);
    }
  }
  const groupIds = [...childrenOf.keys()].filter(pid => childrenOf.get(pid)!.length > 0);
  const groupIdSet = new Set(groupIds);

  // 分组框交给 ELK 当父节点算, 不再在布局后按子节点包围盒手画 —— 手画的框只是「事后圈一下」,
  // ELK 并不知道它存在, 子 task 会被排到框外、别的 task 也会排进框里。
  const GROUP_HEADER = 32;
  const leafOf = (id: string) => ({ id: toElkId(id), width: d.w, height: d.h });
  const inGroup = new Set(groupIds.flatMap(gid => childrenOf.get(gid)!.filter(k => !groupIdSet.has(k))));

  const elkChildren: any[] = [];
  for (const t of tasks) {
    if (groupIdSet.has(t.id) || inGroup.has(t.id)) continue;
    elkChildren.push(leafOf(t.id));
  }
  for (const gid of groupIds) {
    const kids = childrenOf.get(gid)!.filter(k => !groupIdSet.has(k));
    if (!kids.length) continue;
    elkChildren.push({
      id: `group_${toElkId(gid)}`,
      children: kids.map(leafOf),
      layoutOptions: {
        "elk.algorithm": "layered",
        "elk.direction": "DOWN",
        "elk.padding": `[top=${GROUP_HEADER + 20},left=24,bottom=24,right=24]`,
        "elk.spacing.nodeNode": "40",
        "elk.layered.spacing.nodeNodeBetweenLayers": "80",
      },
    });
  }

  const elkEdges: any[] = [];
  for (const t of tasks) {
    if (groupIdSet.has(t.id)) continue;
    for (const dep of t.deps || []) {
      if (!byId.has(dep) || groupIdSet.has(dep)) continue;
      elkEdges.push({
        id: `e_${toElkId(dep)}_${toElkId(t.id)}`,
        sources: [toElkId(dep)],
        targets: [toElkId(t.id)],
      });
    }
  }

  const result = await elk.layout({
    id: "root",
    layoutOptions: { ...BASE_OPTS, "elk.padding": "[top=20,left=40,bottom=20,right=40]" },
    children: elkChildren,
    edges: elkEdges,
  });

  const { nodes: flat, edges: edgePoints } = flatten(result);
  const flatById = new Map(flat.map(n => [n.id, n]));
  const elkIdToTaskId = new Map<string, string>();
  for (const t of tasks) elkIdToTaskId.set(toElkId(t.id), t.id);

  // 父框必须排在子节点前面: React Flow 要求 parentId 指向的节点先出现在数组里
  const rfNodes: Node[] = [];
  for (const gid of groupIds) {
    const g = flatById.get(`group_${toElkId(gid)}`);
    const parentTask = byId.get(gid);
    if (!g || !parentTask) continue;
    const childTasks = childrenOf.get(gid)!.map(kid => byId.get(kid)).filter(Boolean) as NormTask[];
    rfNodes.push({
      id: g.id,
      position: g.rel,
      type: "taskGroup",
      data: {
        task: parentTask, rawId: gid,
        childDone: childTasks.filter(t => t.status === "done").length,
        childTotal: childTasks.length,
      },
      style: { width: g.w, height: g.h },
      draggable: false,
      selectable: true,
    });
  }
  for (const n of flat) {
    const taskId = elkIdToTaskId.get(n.id);
    const task = taskId ? byId.get(taskId) : undefined;
    if (!taskId || !task) continue;  // 分组框已在上面单独发过
    rfNodes.push({
      id: n.id,
      position: n.rel,
      type: "taskCard",
      data: { task, rawId: taskId },
      style: { width: n.w || d.w, height: n.h || d.h },
      // extent=parent: 拖动时也不许拖出 supertask 框 (光靠布局只保证初始位置不越界)
      ...(n.parent ? { parentId: n.parent, extent: "parent" as const } : {}),
    });
  }

  const rfEdges: Edge[] = [];
  for (const t of tasks) {
    if (groupIdSet.has(t.id)) continue;
    for (const dep of t.deps || []) {
      if (!byId.has(dep) || groupIdSet.has(dep)) continue;
      const elkEdgeId = `e_${toElkId(dep)}_${toElkId(t.id)}`;
      rfEdges.push({
        id: `edge-${dep}-${t.id}`,
        source: toElkId(dep),
        target: toElkId(t.id),
        type: "elkpath",
        data: { points: edgePoints.get(elkEdgeId) || [] },
      });
    }
  }

  return { nodes: rfNodes, edges: rfEdges };
}

// ── Subtask DAG 布局 ──
export async function layoutSubtaskDAG(
  subs: NormSubtask[],
  opts?: { w?: number; h?: number },
): Promise<{ nodes: Node[]; edges: Edge[] }> {
  const w = opts?.w || 260;
  const h = opts?.h || 72;
  const byId = new Map(subs.map(s => [s.id, s]));

  const elkNodes = subs.map(s => ({ id: toElkId(s.id), width: w, height: h }));
  const elkEdges: any[] = [];
  for (const s of subs) {
    for (const dep of s.deps || []) {
      if (!byId.has(dep)) continue;
      elkEdges.push({ id: `e_${toElkId(dep)}_${toElkId(s.id)}`, sources: [toElkId(dep)], targets: [toElkId(s.id)] });
    }
  }

  const result = await elk.layout({
    id: "root",
    layoutOptions: { ...BASE_OPTS, "elk.padding": "[top=16,left=16,bottom=16,right=16]" },
    children: elkNodes,
    edges: elkEdges,
  });

  const elkIdToSubId = new Map<string, string>();
  for (const s of subs) elkIdToSubId.set(toElkId(s.id), s.id);
  const { nodes: flat, edges: edgePoints } = flatten(result);

  const rfNodes: Node[] = flat.map(n => {
    const subId = elkIdToSubId.get(n.id) || n.id;
    return {
      id: n.id,
      position: n.rel,
      type: "subtaskCard",
      data: { sub: byId.get(subId)!, rawId: subId },
      style: { width: n.w, height: n.h },
    };
  });

  const rfEdges: Edge[] = elkEdges.map((e: any) => ({
    id: e.id, source: e.sources[0], target: e.targets[0], type: "elkpath",
    data: { points: edgePoints.get(e.id) || [] },
  }));

  return { nodes: rfNodes, edges: rfEdges };
}

// ── 依赖关系图布局 ──
export async function layoutDepDAG(
  taskId: string,
  allTasks: NormTask[],
): Promise<{ nodes: Node[]; edges: Edge[]; centerId: string }> {
  const byId = new Map(allTasks.map(t => [t.id, t]));
  const task = byId.get(taskId);
  if (!task) return { nodes: [], edges: [], centerId: taskId };

  const visited = new Set<string>([taskId]);
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
    visited.add(id);
    const t = byId.get(id);
    if (t && t.deps) queue.push(...t.deps.filter(d => !visited.has(d)));
  }
  queue = downstreamOf.get(taskId) || [];
  while (queue.length) {
    const id = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id);
    queue.push(...(downstreamOf.get(id) || []).filter(d => !visited.has(d)));
  }

  const parentId = task.parent;
  if (parentId && byId.has(parentId) && !visited.has(parentId)) visited.add(parentId);
  if (task.kind === "supertask") {
    for (const t of allTasks) {
      if (t.parent === taskId && !visited.has(t.id)) visited.add(t.id);
    }
  }
  if (parentId) {
    for (const t of allTasks) {
      if (t.parent === parentId && t.id !== taskId && !visited.has(t.id)) visited.add(t.id);
    }
  }

  const inTasks = [...visited].map(id => byId.get(id)!).filter(Boolean);
  const elkNodes = inTasks.map(t => ({ id: toElkId(t.id), width: 200, height: 48 }));
  const elkEdges: any[] = [];
  for (const t of inTasks) {
    for (const dep of t.deps || []) {
      if (!visited.has(dep)) continue;
      elkEdges.push({ id: `e_${toElkId(dep)}_${toElkId(t.id)}`, sources: [toElkId(dep)], targets: [toElkId(t.id)] });
    }
  }

  const result = await elk.layout({
    id: "root",
    layoutOptions: { ...BASE_OPTS, "elk.padding": "[top=16,left=20,bottom=16,right=20]" },
    children: elkNodes,
    edges: elkEdges,
  });

  const elkIdToTaskId = new Map<string, string>();
  for (const t of inTasks) elkIdToTaskId.set(toElkId(t.id), t.id);
  const { nodes: flat, edges: edgePoints } = flatten(result);

  const rfNodes: Node[] = flat.map(n => {
    const tid = elkIdToTaskId.get(n.id) || n.id;
    return {
      id: n.id,
      position: n.rel,
      type: "depTaskCard",
      data: { task: byId.get(tid)!, rawId: tid, isCenter: tid === taskId },
      style: { width: n.w, height: n.h },
    };
  });

  const rfEdges: Edge[] = elkEdges.map((e: any) => ({
    id: e.id, source: e.sources[0], target: e.targets[0], type: "elkpath",
    data: { points: edgePoints.get(e.id) || [] },
  }));

  return { nodes: rfNodes, edges: rfEdges, centerId: toElkId(taskId) };
}
