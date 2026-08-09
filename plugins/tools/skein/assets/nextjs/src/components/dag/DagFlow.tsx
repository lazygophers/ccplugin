"use client";

// 通用 React Flow DAG 包装器 — 处理视口、pan/zoom、hover chain、状态感知着色
// 被 board page (taskDAG) 和 task detail page (depDAG/subtaskDAG) 共用

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeMouseHandler,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// ── 边状态分类 (ready/blocked/stuck) — 从 depdag.ts 移植语义 ──
export type EdgeKind = "ready" | "blocked" | "stuck";

function computeEdgeKind(
  edge: Edge,
  nodeMap: Map<string, Node>,
): EdgeKind {
  const fromNode = nodeMap.get(edge.source);
  const toNode = nodeMap.get(edge.target);
  const fromTask = fromNode?.data?.task as Record<string, unknown> | undefined;
  const toTask = toNode?.data?.task as Record<string, unknown> | undefined;
  const fromStatus = (fromTask?.status as string) || "planning";
  if (fromStatus === "done") return "ready";
  const deps = (toTask?.deps || toTask?.dependsOn || []) as string[];
  const stOf = (id: string): string => {
    const n = nodeMap.get(id);
    return (n?.data?.task as Record<string, unknown>)?.status as string || "planning";
  };
  return deps.every(d => stOf(d) === "done") ? "blocked" : "stuck";
}

const EDGE_KIND_CLASS: Record<EdgeKind, string> = {
  ready: "dag-edge-ready",
  blocked: "dag-edge-blocked",
  stuck: "dag-edge-stuck",
};

// ── hover chain: 双向 BFS ──
function computeChain(hoverId: string | null, edges: Edge[]): Set<string> | null {
  if (!hoverId) return null;
  const succ = new Map<string, string[]>();
  const pred = new Map<string, string[]>();
  for (const e of edges) {
    if (!succ.has(e.source)) succ.set(e.source, []);
    if (!pred.has(e.target)) pred.set(e.target, []);
    succ.get(e.source)!.push(e.target);
    pred.get(e.target)!.push(e.source);
  }
  const seen = new Set([hoverId]);
  for (const adj of [succ, pred]) {
    const queue = [hoverId];
    while (queue.length) {
      const cur = queue.shift()!;
      for (const nx of adj.get(cur) || []) {
        if (seen.has(nx)) continue;
        seen.add(nx);
        queue.push(nx);
      }
    }
  }
  return seen;
}

export interface DagFlowProps {
  nodes: Node[];
  edges: Edge[];
  nodeTypes: NodeTypes;
  // 可选: 状态过滤 dim
  dimStatusSet?: Set<string>;
  // 可选: 选中节点 id
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  // 容器高度
  minHeight?: number;
  // 额外 className
  className?: string;
  // 是否显示背景 grid
  showBackground?: boolean;
  // 是否显示控件 (zoom buttons)
  showControls?: boolean;
  // fitView 初始
  fitView?: boolean;
  // 是否启用 hover chain highlight
  enableHoverChain?: boolean;
  // 节点状态字段提取 (判断 dimmed)
  nodeStatusOf?: (node: Node) => string;
}

export function DagFlow({
  nodes: initialNodes,
  edges: initialEdges,
  nodeTypes,
  dimStatusSet,
  selectedId,
  onSelect,
  minHeight = 400,
  className = "",
  showBackground = true,
  showControls = true,
  fitView = true,
  enableHoverChain = true,
  nodeStatusOf,
}: DagFlowProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [hoverId, setHoverId] = useState<string | null>(null);

  // 同步外部数据变化
  useEffect(() => { setNodes(initialNodes); }, [initialNodes]);
  useEffect(() => { setEdges(initialEdges); }, [initialEdges]);

  const nodeMap = useMemo(() => new Map(nodes.map(n => [n.id, n])), [nodes]);

  // hover chain
  const chain = useMemo(
    () => enableHoverChain ? computeChain(hoverId, edges) : null,
    [hoverId, edges, enableHoverChain],
  );

  // 边着色 + dim/hover 样式
  const styledEdges = useMemo(() => {
    return edges.map(e => {
      const kind = computeEdgeKind(e, nodeMap);
      const inChain = chain?.has(e.source) && chain?.has(e.target);

      // 状态过滤 dim
      let dimmed = false;
      if (dimStatusSet && nodeStatusOf) {
        const fromNode = nodeMap.get(e.source);
        const toNode = nodeMap.get(e.target);
        if (fromNode && toNode) {
          dimmed = !dimStatusSet.has(nodeStatusOf(fromNode)) || !dimStatusSet.has(nodeStatusOf(toNode));
        }
      }

      const opacity = chain
        ? (inChain ? 0.95 : 0.1)
        : dimmed ? 0.12 : 0.55;

      return {
        ...e,
        className: EDGE_KIND_CLASS[kind],
        style: { strokeOpacity: opacity },
        animated: kind === "blocked",
      };
    });
  }, [edges, nodeMap, chain, dimStatusSet, nodeStatusOf]);

  // 节点 dim/hover 样式
  const styledNodes = useMemo(() => {
    return nodes.map(n => {
      let dimmed = false;
      if (dimStatusSet && nodeStatusOf) {
        dimmed = !dimStatusSet.has(nodeStatusOf(n));
      }
      const isDim = chain ? !chain.has(n.id) : false;
      const opacity = dimmed ? 0.4 : isDim ? 0.15 : 1;
      return {
        ...n,
        style: { ...(n.style as CSSProperties), opacity },
      };
    });
  }, [nodes, chain, dimStatusSet, nodeStatusOf]);

  const handleNodeClick: NodeMouseHandler = useCallback((_, node) => {
    // 映射回原始 task id
    const rawId = (node.data as Record<string, unknown>)?.rawId as string || node.id;
    onSelect?.(rawId);
  }, [onSelect]);

  return (
    <div className={`dag-flow-container ${className}`} style={{ width: "100%", height: "100%", minHeight }}>
      <ReactFlow
        nodes={styledNodes}
        edges={styledEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={(_, node) => setHoverId(node.id)}
        onNodeMouseLeave={() => setHoverId(null)}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        proOptions={{ hideAttribution: true }}
        fitView={fitView}
        minZoom={0.1}
        maxZoom={2}
        panOnDrag={true}
        zoomOnScroll={true}
        zoomOnDoubleClick={false}
        selectNodesOnDrag={false}
      >
        {showBackground && <Background color="var(--border)" gap={20} size={1} />}
        {showControls && <Controls showInteractive={false} />}
      </ReactFlow>
    </div>
  );
}

// 导出 provider 包装
export function DagFlowProvider({ children }: { children: React.ReactNode }) {
  return <ReactFlowProvider>{children}</ReactFlowProvider>;
}
