// ELK 布局适配层 — 输入 tasks/subs + 视口尺寸, 输出 React Flow 节点/边
// elkjs 提供 Layered (Sugiyama) 布局, 替代原自研 sugiyama() + layoutDAG()

import ELK from "elkjs";
import type { Edge, Node } from "@xyflow/react";
import type { NormTask, NormSubtask } from "./model";

const elk = new ELK();

// ELK base layout options — Layered (Sugiyama) 方向 DOWN
const BASE_OPTS: Record<string, string> = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  "elk.layered.spacing.nodeNodeBetweenLayers": "60",
  "elk.layered.spacing.nodeNode": "30",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
  "elk.spacing.edgeNode": "20",
};

export interface DensityOpts { w: number; h: number; gapX: number; gapY: number }

export const DAG_DENSITY: Record<string, DensityOpts> = {
  large:   { w: 260, h: 76, gapX: 54, gapY: 39 },
  compact: { w: 240, h: 72, gapX: 42, gapY: 33 },
  mini:    { w: 120, h: 32, gapX: 42, gapY: 33 },
};

// ELK id 必须合法: 只允许字母数字下划线
const toElkId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");

// ── 看板 DAG 布局 (含 supertask 分组) ──
// 策略: 所有 task (含 supertask 的 child) 作为顶层平级节点参与 ELK 布局, 不用 compound 层级。
// 布局完成后, supertask 的 group 框根据其 children 的实际坐标算包围盒, 作为纯视觉装饰渲染。
// 这样所有边都是顶层节点间的边, 不存在跨 compound 层级的穿框问题。
export async function layoutBoardDAG(
  tasks: NormTask[],
  density: keyof typeof DAG_DENSITY = "compact",
): Promise<{ nodes: Node[]; edges: Edge[] }> {
  if (!tasks.length) return { nodes: [], edges: [] };
  const d = DAG_DENSITY[density] || DAG_DENSITY.compact;
  const byId = new Map(tasks.map(t => [t.id, t]));

  // 父子分组
  const childrenOf = new Map<string, string[]>();
  for (const t of tasks) {
    if (t.parent && t.parent !== t.id && byId.has(t.parent)) {
      if (!childrenOf.has(t.parent)) childrenOf.set(t.parent, []);
      childrenOf.get(t.parent)!.push(t.id);
    }
  }
  const groupIds = [...childrenOf.keys()].filter(pid => childrenOf.get(pid)!.length > 0);
  const groupIdSet = new Set(groupIds);
  const childIdSet = new Set(groupIds.flatMap(g => childrenOf.get(g)!));

  // 所有 task 作为顶层节点 (supertask 本身不参与, 只做 group 框)
  const layoutTaskIds = tasks.filter(t => !groupIdSet.has(t.id)).map(t => t.id);
  const elkNodes = layoutTaskIds.map(id => ({
    id: toElkId(id),
    width: d.w,
    height: d.h,
  }));

  // 边: deps 关系 (父子关系不画边)
  const elkEdges: any[] = [];
  for (const t of tasks) {
    if (groupIdSet.has(t.id)) continue; // supertask 本身不出边
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
    layoutOptions: {
      ...BASE_OPTS,
      "elk.padding": "[top=20,left=40,bottom=20,right=40]",
    },
    children: elkNodes,
    edges: elkEdges,
  });

  // 提取 RF 节点 (全部顶层, 绝对坐标)
  const elkIdToTaskId = new Map<string, string>();
  for (const id of layoutTaskIds) elkIdToTaskId.set(toElkId(id), id);
  const posMap = new Map<string, { x: number; y: number; w: number; h: number }>();
  for (const n of (result.children || []) as any[]) {
    posMap.set(n.id, { x: n.x || 0, y: n.y || 0, w: n.width || 0, h: n.height || 0 });
  }

  const rfNodes: Node[] = [];
  for (const n of (result.children || []) as any[]) {
    const taskId = elkIdToTaskId.get(n.id);
    if (!taskId) continue;
    const task = byId.get(taskId);
    if (!task) continue;
    rfNodes.push({
      id: n.id,
      position: { x: n.x || 0, y: n.y || 0 },
      type: "taskCard",
      data: { task, rawId: taskId },
      style: { width: n.width || d.w, height: n.height || d.h },
    });
  }

  // group 框: 根据 children 实际坐标算包围盒
  const GROUP_PAD = 14;
  const GROUP_HEADER = 28;
  for (const gid of groupIds) {
    const kids = childrenOf.get(gid)!.map(kid => toElkId(kid));
    const kidPos = kids.map(k => posMap.get(k)).filter(Boolean) as { x: number; y: number; w: number; h: number }[];
    if (!kidPos.length) continue;
    const minX = Math.min(...kidPos.map(p => p.x)) - GROUP_PAD;
    const minY = Math.min(...kidPos.map(p => p.y)) - GROUP_PAD - GROUP_HEADER;
    const maxX = Math.max(...kidPos.map(p => p.x + p.w)) + GROUP_PAD;
    const maxY = Math.max(...kidPos.map(p => p.y + p.h)) + GROUP_PAD;
    const parentTask = byId.get(gid);
    if (!parentTask) continue;
    rfNodes.push({
      id: `group_${toElkId(gid)}`,
      position: { x: minX, y: minY },
      type: "taskGroup",
      data: { task: parentTask, rawId: gid },
      style: { width: maxX - minX, height: maxY - minY },
      draggable: false,
      selectable: true,
    });
  }

  // RF 边: 只保留真实 deps 边 (去掉虚拟约束边)
  const rfEdges: Edge[] = [];
  for (const t of tasks) {
    if (groupIdSet.has(t.id)) continue;
    for (const dep of t.deps || []) {
      if (!byId.has(dep) || groupIdSet.has(dep)) continue;
      rfEdges.push({
        id: `edge-${dep}-${t.id}`,
        source: toElkId(dep),
        target: toElkId(t.id),
        type: "smoothstep",
      });
    }
  }

  return { nodes: rfNodes, edges: rfEdges };
}

// ── Subtask DAG 布局 (简单分层, 无分组) ──
export async function layoutSubtaskDAG(
  subs: NormSubtask[],
  opts?: { w?: number; h?: number },
): Promise<{ nodes: Node[]; edges: Edge[] }> {
  const w = opts?.w || 220;
  const h = opts?.h || 64;
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

  const rfNodes: Node[] = (result.children || []).map((n: any) => {
    const subId = elkIdToSubId.get(n.id) || n.id;
    return {
      id: n.id,
      position: { x: n.x, y: n.y },
      type: "subtaskCard",
      data: { sub: byId.get(subId)!, rawId: subId },
      style: { width: n.width, height: n.height },
    };
  });

  const rfEdges: Edge[] = elkEdges.map(e => ({
    id: e.id, source: e.sources[0], target: e.targets[0], type: "smoothstep",
  }));

  return { nodes: rfNodes, edges: rfEdges };
}

// ── 依赖关系图布局 (以某 task 为中心的上下游) ──
export async function layoutDepDAG(
  taskId: string,
  allTasks: NormTask[],
): Promise<{ nodes: Node[]; edges: Edge[]; centerId: string }> {
  const byId = new Map(allTasks.map(t => [t.id, t]));
  const task = byId.get(taskId);
  if (!task) return { nodes: [], edges: [], centerId: taskId };

  // BFS 收集上下游
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

  // 父子关系纳入
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
  const elkNodes = inTasks.map(t => ({ id: toElkId(t.id), width: 160, height: 40 }));
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

  const rfNodes: Node[] = (result.children || []).map((n: any) => {
    const tid = elkIdToTaskId.get(n.id) || n.id;
    return {
      id: n.id,
      position: { x: n.x, y: n.y },
      type: "depTaskCard",
      data: { task: byId.get(tid)!, rawId: tid, isCenter: tid === taskId },
      style: { width: n.width, height: n.height },
    };
  });

  const rfEdges: Edge[] = elkEdges.map(e => ({
    id: e.id, source: e.sources[0], target: e.targets[0], type: "smoothstep",
  }));

  return { nodes: rfNodes, edges: rfEdges, centerId: toElkId(taskId) };
}
