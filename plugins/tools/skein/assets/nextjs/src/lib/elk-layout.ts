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
  compact: { w: 190, h: 52, gapX: 42, gapY: 33 },
  mini:    { w: 120, h: 32, gapX: 42, gapY: 33 },
};

// ELK id 必须合法: 只允许字母数字下划线
const toElkId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");

// ── 看板 DAG 布局 (含 supertask 分组) ──
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
  const childToGroup = new Map<string, string>();
  for (const g of groupIds) for (const c of childrenOf.get(g)!) childToGroup.set(c, g);

  // 构造 ELK 顶层节点
  const elkTopNodes: any[] = [];
  for (const t of tasks) {
    if (childIdSet.has(t.id)) continue; // child 跳过, 放到 compound 内
    if (groupIdSet.has(t.id)) {
      // supertask → compound 节点
      const children = childrenOf.get(t.id)!;
      elkTopNodes.push({
        id: toElkId(t.id),
        width: d.w + 28,
        height: d.h * Math.max(1, children.length) + 42,
        layoutOptions: {
          "elk.padding": "[top=28,left=14,bottom=14,right=14]",
        },
        children: children.map(cid => ({
          id: toElkId(cid),
          width: d.w,
          height: d.h,
        })),
      });
    } else {
      // 独立 task
      elkTopNodes.push({
        id: toElkId(t.id),
        width: d.w,
        height: d.h,
      });
    }
  }

  // 边: deps 关系 (父子关系不画边)
  // 关键: 跨层级边 (外部→compound 内部 child) 需 hierarchyHandling: INCLUDE_CHILDREN
  const elkEdges: any[] = [];
  for (const t of tasks) {
    for (const dep of t.deps || []) {
      if (!byId.has(dep)) continue;
      elkEdges.push({
        id: `e_${toElkId(dep)}_${toElkId(t.id)}`,
        sources: [toElkId(dep)],
        targets: [toElkId(t.id)],
      });
    }
  }

  const root = {
    id: "root",
    layoutOptions: {
      ...BASE_OPTS,
      "elk.hierarchyHandling": "INCLUDE_CHILDREN",
      "elk.padding": "[top=20,left=40,bottom=20,right=40]",
    },
    children: elkTopNodes,
    edges: elkEdges,
  };

  const result = await elk.layout(root);

  // 提取 React Flow 节点 — compound 节点的坐标是绝对的, child 坐标是相对于 compound 的
  const rfNodes: Node[] = [];
  const elkIdToTaskId = new Map<string, string>();
  for (const t of tasks) elkIdToTaskId.set(toElkId(t.id), t.id);

  function walk(elkNode: any, parentElkId: string | null, absX: number, absY: number) {
    const x = (elkNode.x || 0) + absX;
    const y = (elkNode.y || 0) + absY;
    if (elkNode.children && elkNode.children.length > 0) {
      // compound 节点 → group node (绝对坐标)
      const taskId = elkIdToTaskId.get(elkNode.id);
      const task = taskId ? byId.get(taskId) : null;
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          type: "taskGroup",
          position: { x, y },
          data: { task, rawId: taskId, width: elkNode.width, height: elkNode.height },
          style: { width: elkNode.width, height: elkNode.height },
        });
      }
      for (const child of elkNode.children) walk(child, elkNode.id, x, y);
    } else {
      // 叶子节点
      const taskId = elkIdToTaskId.get(elkNode.id);
      const task = taskId ? byId.get(taskId) : null;
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          position: { x, y },
          type: "taskCard",
          data: { task, rawId: taskId, groupId: parentElkId },
          style: { width: elkNode.width, height: elkNode.height },
        });
      }
    }
  }
  for (const n of (result.children || [])) walk(n, null, 0, 0);

  // React Flow 边
  const rfEdges: Edge[] = tasks.flatMap(t =>
    (t.deps || [])
      .filter(dep => byId.has(dep))
      .map(dep => ({
        id: `edge-${dep}-${t.id}`,
        source: toElkId(dep),
        target: toElkId(t.id),
        type: "smoothstep",
      }))
  );

  return { nodes: rfNodes, edges: rfEdges };
}

// ── Subtask DAG 布局 (简单分层, 无分组) ──
export async function layoutSubtaskDAG(
  subs: NormSubtask[],
  opts?: { w?: number; h?: number },
): Promise<{ nodes: Node[]; edges: Edge[] }> {
  const w = opts?.w || 200;
  const h = opts?.h || 56;
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
