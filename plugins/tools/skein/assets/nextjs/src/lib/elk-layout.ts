// ELK 布局适配层 — 输入 tasks/subs + 视口尺寸, 输出 React Flow 节点/边
// elkjs 提供 Layered (Sugiyama) 布局, 替代原自研 sugiyama() + layoutDAG()

import ELK from "elkjs";
import type { Edge, Node } from "@xyflow/react";
import type { NormTask, NormSubtask } from "./model";

const elk = new ELK();

// ELK base layout options — Layered (Sugiyama) 方向 TB
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

// ── 看板 DAG 布局 (含 supertask 分组) ──
export async function layoutBoardDAG(
  tasks: NormTask[],
  density: keyof typeof DAG_DENSITY = "compact",
): Promise<{ nodes: Node[]; edges: Edge[] }> {
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

  // 构造 ELK graph JSON
  const layoutId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");
  const elkNodes: any[] = [];
  const elkEdges: any[] = [];
  const groupIdSet = new Set(groupIds);
  const childIdSet = new Set(groupIds.flatMap(g => childrenOf.get(g)!));

  // 独立 task → 顶层节点
  for (const t of tasks) {
    if (childIdSet.has(t.id)) continue;
    if (groupIdSet.has(t.id)) {
      // supertask → 顶层 compound 节点, children 在内部
      const children = childrenOf.get(t.id)!;
      const childNodes = children.map(cid => ({
        id: layoutId(cid),
        width: d.w,
        height: d.h,
        layoutOptions: { "elk.portConstraints": "FIXED_SIDE" },
      }));
      elkNodes.push({
        id: layoutId(t.id),
        width: d.w + 28,
        height: d.h * Math.max(1, children.length) + 42,
        layoutOptions: {
          ...BASE_OPTS,
          "elk.padding": "[top=28,left=14,bottom=14,right=14]",
        },
        children: childNodes,
      });
    } else {
      elkNodes.push({
        id: layoutId(t.id),
        width: d.w,
        height: d.h,
      });
    }
  }

  // 边: deps 关系 (父子关系不画边)
  const childToGroup = new Map<string, string>();
  for (const g of groupIds) for (const c of childrenOf.get(g)!) childToGroup.set(c, g);

  let edgeSeq = 0;
  for (const t of tasks) {
    for (const dep of t.deps || []) {
      if (!byId.has(dep)) continue;
      const fromId = childToGroup.has(dep) ? layoutId(dep) : layoutId(dep);
      const toId = layoutId(t.id);
      // 确保两端都在图中
      const fromInGroup = childToGroup.has(dep);
      const toInGroup = childToGroup.has(t.id);
      elkEdges.push({
        id: `e${edgeSeq++}`,
        sources: [fromId],
        targets: [toId],
        // 跨容器边: 容器→容器, 需容器做端口
        ...(fromInGroup !== toInGroup && fromInGroup ? {} : {}),
      });
    }
  }

  const root = {
    id: "root",
    layoutOptions: {
      ...BASE_OPTS,
      "elk.padding": "[top=20,left=40,bottom=20,right=40]",
    },
    children: elkNodes,
    edges: elkEdges,
  };

  const result = await elk.layout(root);

  // 提取 React Flow 节点
  const rfNodes: Node[] = [];
  const rfEdges: Edge[] = [];

  function extractNodes(elkNode: any, offset = { x: 0, y: 0 }) {
    const ox = (elkNode.x || 0) + offset.x;
    const oy = (elkNode.y || 0) + offset.y;
    // compound 节点本身 → group node
    if (elkNode.children && elkNode.children.length > 0) {
      const taskId = reverseId(elkNode.id);
      const task = byId.get(taskId);
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          type: "taskGroup",
          position: { x: ox, y: oy },
          data: { task, width: elkNode.width, height: elkNode.height },
          style: { width: elkNode.width, height: elkNode.height },
        });
      }
      for (const child of elkNode.children) {
        extractNodes(child, { x: ox, y: oy });
      }
    } else {
      const taskId = reverseId(elkNode.id);
      const task = byId.get(taskId);
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          position: { x: ox, y: oy },
          type: "taskCard",
          data: { task },
          style: { width: elkNode.width, height: elkNode.height },
          parentId: undefined, // 将在下面处理
        });
      }
    }
  }

  // 映射 ELK compound → React Flow parentNode
  function extractWithParent(elkNode: any, parentId: string | null = null, offset = { x: 0, y: 0 }) {
    const ox = (elkNode.x || 0) + offset.x;
    const oy = (elkNode.y || 0) + offset.y;
    if (elkNode.children && elkNode.children.length > 0) {
      const taskId = reverseId(elkNode.id);
      const task = byId.get(taskId);
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          type: "taskGroup",
          position: { x: ox, y: oy },
          data: { task, width: elkNode.width, height: elkNode.height },
          style: { width: elkNode.width, height: elkNode.height },
        });
      }
      for (const child of elkNode.children) {
        extractWithParent(child, elkNode.id, { x: ox, y: oy });
      }
    } else {
      const taskId = reverseId(elkNode.id);
      const task = byId.get(taskId);
      if (task) {
        rfNodes.push({
          id: elkNode.id,
          position: { x: ox, y: oy },
          type: "taskCard",
          data: { task, groupId: parentId },
          style: { width: elkNode.width, height: elkNode.height },
          ...(parentId ? { parentId: parentId } : {}),
        });
      }
    }
  }

  const idMap = new Map<string, string>();
  // 记录 ELK id → task id 映射
  for (const t of tasks) idMap.set(layoutId(t.id), t.id);

  function reverseId(elkId: string): string {
    return idMap.get(elkId) || elkId;
  }

  rfNodes.length = 0;
  extractWithParent(result);

  // 边
  rfEdges.length = 0;
  for (const t of tasks) {
    for (const dep of t.deps || []) {
      if (!byId.has(dep)) continue;
      rfEdges.push({
        id: `edge-${dep}-${t.id}`,
        source: layoutId(dep),
        target: layoutId(t.id),
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
  const w = opts?.w || 148;
  const h = opts?.h || 48;
  const byId = new Map(subs.map(s => [s.id, s]));
  const layoutId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");

  const elkNodes = subs.map(s => ({
    id: layoutId(s.id),
    width: w,
    height: h,
  }));

  const elkEdges: any[] = [];
  for (const s of subs) {
    for (const dep of s.deps || []) {
      if (!byId.has(dep)) continue;
      elkEdges.push({
        id: `e-${dep}-${s.id}`,
        sources: [layoutId(dep)],
        targets: [layoutId(s.id)],
      });
    }
  }

  const root = {
    id: "root",
    layoutOptions: {
      ...BASE_OPTS,
      "elk.padding": "[top=16,left=16,bottom=16,right=16]",
    },
    children: elkNodes,
    edges: elkEdges,
  };

  const result = await elk.layout(root);
  const idMap = new Map<string, string>();
  for (const s of subs) idMap.set(layoutId(s.id), s.id);

  const rfNodes: Node[] = (result.children || []).map((n: any) => ({
    id: n.id,
    position: { x: n.x, y: n.y },
    type: "subtaskCard",
    data: { sub: byId.get(idMap.get(n.id) || n.id)! },
    style: { width: n.width, height: n.height },
  }));

  const rfEdges: Edge[] = elkEdges.map(e => ({
    id: e.id,
    source: e.sources[0],
    target: e.targets[0],
    type: "smoothstep",
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

  // 父子关系
  const parentId = task.parent;
  if (parentId && byId.has(parentId) && !visited.has(parentId)) {
    visited.add(parentId);
  }
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
  const layoutId = (id: string) => id.replace(/[^a-zA-Z0-9_]/g, "_");

  const elkNodes = inTasks.map(t => ({
    id: layoutId(t.id),
    width: 160,
    height: 40,
  }));

  const elkEdges: any[] = [];
  for (const t of inTasks) {
    for (const dep of t.deps || []) {
      if (!visited.has(dep)) continue;
      elkEdges.push({
        id: `e-${dep}-${t.id}`,
        sources: [layoutId(dep)],
        targets: [layoutId(t.id)],
      });
    }
  }

  const root = {
    id: "root",
    layoutOptions: {
      ...BASE_OPTS,
      "elk.padding": "[top=16,left=20,bottom=16,right=20]",
    },
    children: elkNodes,
    edges: elkEdges,
  };

  const result = await elk.layout(root);
  const idMap = new Map<string, string>();
  for (const t of inTasks) idMap.set(layoutId(t.id), t.id);

  const rfNodes: Node[] = (result.children || []).map((n: any) => ({
    id: n.id,
    position: { x: n.x, y: n.y },
    type: "depTaskCard",
    data: { task: byId.get(idMap.get(n.id) || n.id)!, isCenter: idMap.get(n.id) === taskId },
    style: { width: n.width, height: n.height },
  }));

  const rfEdges: Edge[] = elkEdges.map(e => ({
    id: e.id,
    source: e.sources[0],
    target: e.targets[0],
    type: "smoothstep",
  }));

  return { nodes: rfNodes, edges: rfEdges, centerId: layoutId(taskId) };
}
