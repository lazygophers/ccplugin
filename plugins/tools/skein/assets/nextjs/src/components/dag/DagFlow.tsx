"use client";

// 通用 React Flow DAG 包装器
// 禁止缩放/超宽, 允许上下滚动, 自动定位 active task, 手绘贝塞尔曲线边

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useEdgesState,
  useNodesState,
  useReactFlow,
  MarkerType,
  type Edge,
  type Node,
  type NodeMouseHandler,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ElkPathEdge } from "./ElkPathEdge";

export type EdgeKind = "ready" | "blocked" | "stuck";

function computeEdgeKind(edge: Edge, nodeMap: Map<string, Node>): EdgeKind {
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

const EDGE_KIND_COLOR: Record<EdgeKind, string> = {
  ready: "var(--st-done)",
  blocked: "var(--st-active)",
  stuck: "var(--st-failed)",
};

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
  dimStatusSet?: Set<string>;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  minHeight?: number;
  className?: string;
  showBackground?: boolean;
  showControls?: boolean;
  enableHoverChain?: boolean;
  nodeStatusOf?: (node: Node) => string;
}

const EDGE_TYPES: EdgeTypes = { elkpath: ElkPathEdge };

function DagFlowInner({
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
  enableHoverChain = true,
  nodeStatusOf,
}: DagFlowProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const { setViewport } = useReactFlow();

  useEffect(() => { setNodes(initialNodes); }, [initialNodes]);
  useEffect(() => { setEdges(initialEdges); }, [initialEdges]);

  // ── 居中 + 自动定位 active task ──
  useEffect(() => {
    if (!nodes.length) return;
    const timer = setTimeout(() => {
      const container = document.querySelector(".dag-flow-container") as HTMLElement;
      if (!container) return;
      const cw = container.clientWidth;
      const ch = container.clientHeight;

      const realNodes = nodes.filter(n => n.type !== "taskGroup");
      if (!realNodes.length) return;

      const W = 280;
      const nodeWidth = (n: Node) => ((n.style as CSSProperties)?.width as number) || W;
      const nodeHeight = (n: Node) => ((n.style as CSSProperties)?.height as number) || 80;

      const minX = Math.min(...realNodes.map(n => n.position.x));
      const maxX = Math.max(...realNodes.map(n => n.position.x + nodeWidth(n)));
      const minY = Math.min(...realNodes.map(n => n.position.y));
      const dagCenterX = (minX + maxX) / 2;

      // 水平居中到容器
      const vpX = cw / 2 - dagCenterX;

      // 垂直: 定位到 active task
      const activeNode = realNodes.find(n => {
        const task = n.data?.task as Record<string, unknown> | undefined;
        return task?.status === "active";
      });

      let vpY: number;
      if (activeNode) {
        vpY = ch / 3 - activeNode.position.y - nodeHeight(activeNode) / 2;
      } else {
        vpY = 20 - minY;
      }

      setViewport({ x: vpX, y: vpY, zoom: 1 });
    }, 300);
    return () => clearTimeout(timer);
  }, [nodes, setViewport]);

  const nodeMap = useMemo(() => new Map(nodes.map(n => [n.id, n])), [nodes]);
  const chain = useMemo(
    () => enableHoverChain ? computeChain(hoverId, edges) : null,
    [hoverId, edges, enableHoverChain],
  );

  // ── 边分散: 同源多边给不同 arcIndex, 同目标多边给不同 arcIndex ──
  const edgeArcInfo = useMemo(() => {
    // 按 source 分组
    const bySource = new Map<string, Edge[]>();
    const byTarget = new Map<string, Edge[]>();
    for (const e of edges) {
      if (!bySource.has(e.source)) bySource.set(e.source, []);
      bySource.get(e.source)!.push(e);
      if (!byTarget.has(e.target)) byTarget.set(e.target, []);
      byTarget.get(e.target)!.push(e);
    }
    const info = new Map<string, { sourceIdx: number; sourceTotal: number; targetIdx: number; targetTotal: number }>();
    for (const [src, list] of bySource) {
      list.forEach((e, i) => {
        const existing = info.get(e.id) || { sourceIdx: 0, sourceTotal: 1, targetIdx: 0, targetTotal: 1 };
        existing.sourceIdx = i;
        existing.sourceTotal = list.length;
        info.set(e.id, existing);
      });
    }
    for (const [tgt, list] of byTarget) {
      list.forEach((e, i) => {
        const existing = info.get(e.id) || { sourceIdx: 0, sourceTotal: 1, targetIdx: 0, targetTotal: 1 };
        existing.targetIdx = i;
        existing.targetTotal = list.length;
        info.set(e.id, existing);
      });
    }
    return info;
  }, [edges]);

  // ── 注册 card 位置给 edge 做避障 (保留给可能的未来需要) ──
  const cardPositions = useMemo(() => {
    const positions = new Map<string, { x: number; y: number; w: number; h: number }>();
    for (const n of nodes) {
      if (n.type === "taskGroup") continue;
      const w = ((n.style as CSSProperties)?.width as number) || 280;
      const h = ((n.style as CSSProperties)?.height as number) || 80;
      positions.set(n.id, { x: n.position.x, y: n.position.y, w, h });
    }
    return positions;
  }, [nodes]);

  const styledEdges = useMemo(() => {
    return edges.map(e => {
      const kind = computeEdgeKind(e, nodeMap);
      const inChain = chain?.has(e.source) && chain?.has(e.target);
      let dimmed = false;
      if (dimStatusSet && nodeStatusOf) {
        const fn = nodeMap.get(e.source), tn = nodeMap.get(e.target);
        if (fn && tn) dimmed = !dimStatusSet.has(nodeStatusOf(fn)) || !dimStatusSet.has(nodeStatusOf(tn));
      }
      const opacity = chain ? (inChain ? 0.95 : 0.1) : dimmed ? 0.12 : 0.7;
      const arc = edgeArcInfo.get(e.id);
      return {
        ...e,
        className: EDGE_KIND_CLASS[kind],
        style: { strokeOpacity: opacity, strokeWidth: 2.5 },
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, width: 5, height: 5, color: EDGE_KIND_COLOR[kind] },
        data: { ...e.data, sourceIdx: arc?.sourceIdx || 0, sourceTotal: arc?.sourceTotal || 1, targetIdx: arc?.targetIdx || 0, targetTotal: arc?.targetTotal || 1 },
      };
    });
  }, [edges, nodeMap, chain, dimStatusSet, nodeStatusOf, edgeArcInfo]);

  const styledNodes = useMemo(() => {
    return nodes.map(n => {
      let dimmed = false;
      if (dimStatusSet && nodeStatusOf) dimmed = !dimStatusSet.has(nodeStatusOf(n));
      const isDim = chain ? !chain.has(n.id) : false;
      const opacity = dimmed ? 0.4 : isDim ? 0.15 : 1;
      const isGroup = n.type === "taskGroup";
      const zIndex = isGroup ? -1 : (hoverId === n.id ? 1000 : 0);
      return {
        ...n,
        style: {
          ...(n.style as CSSProperties),
          opacity,
          zIndex,
          ...(isGroup ? { pointerEvents: "none" as const } : {}),
        },
      };
    });
  }, [nodes, chain, dimStatusSet, nodeStatusOf, hoverId]);

  const handleNodeClick: NodeMouseHandler = useCallback((_, node) => {
    const rawId = (node.data as Record<string, unknown>)?.rawId as string || node.id;
    onSelect?.(rawId);
  }, [onSelect]);

  return (
    <div className={`dag-flow-container ${className}`} style={{ width: "100%", height: "100%", minHeight, overflowX: "hidden", overflowY: "hidden" }}>
      <ReactFlow
        nodes={styledNodes}
        edges={styledEdges}
        nodeTypes={nodeTypes}
        edgeTypes={EDGE_TYPES}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={(_, node) => setHoverId(node.id)}
        onNodeMouseLeave={() => setHoverId(null)}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        proOptions={{ hideAttribution: true }}
        minZoom={1}
        maxZoom={1}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnDoubleClick={false}
        zoomOnPinch={false}
        panOnScroll={true}
        panOnScrollMode={"vertical" as any}
        selectNodesOnDrag={false}
        preventScrolling={true}
      >
        {showBackground && <Background color="var(--border)" gap={20} size={1} />}
        {showControls && <Controls showInteractive={false} />}
      </ReactFlow>
    </div>
  );
}

export function DagFlow(props: DagFlowProps) {
  return (
    <ReactFlowProvider>
      <DagFlowInner {...props} />
    </ReactFlowProvider>
  );
}

export function DagFlowProvider({ children }: { children: React.ReactNode }) {
  return <ReactFlowProvider>{children}</ReactFlowProvider>;
}
