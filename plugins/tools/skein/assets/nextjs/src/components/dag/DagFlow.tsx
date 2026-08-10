"use client";

// 通用 React Flow DAG 包装器
// 可缩放 / 可拖拽画布 / 可拖节点, 初始 fitView 居中后自动定位到 active card, 手绘曲线边

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
  const { fitView, setCenter, getZoom, getInternalNode } = useReactFlow();

  useEffect(() => { setNodes(initialNodes); }, [initialNodes]);
  useEffect(() => { setEdges(initialEdges); }, [initialEdges]);

  // ── 居中 + 自动定位 active task ──
  // 依赖 initialNodes 而非 nodes: 拖动会改 nodes, 挂 nodes 上会在拖完 300ms 后把视口拽回去。
  // 先 fitView 保证整图居中且看得全, 再把有 active/running 的那张卡挪到视野中心。
  // 位置一律走 getInternalNode 的 positionAbsolute —— 分组框里的子节点 position 是相对父框的,
  // 直接拿 node.position 算居中会偏掉一个父框的偏移量。
  useEffect(() => {
    if (!initialNodes.length) return;
    const timer = setTimeout(() => {
      fitView({ padding: 0.15, maxZoom: 1, duration: 300 });
      const focus = initialNodes.find(n => {
        const st = ((n.data?.task ?? n.data?.sub) as Record<string, unknown> | undefined)?.status;
        return st === "active";
      });
      if (!focus) return;
      const internal = getInternalNode(focus.id);
      const pos = internal?.internals.positionAbsolute ?? focus.position;
      const w = ((focus.style as CSSProperties)?.width as number) || 280;
      const h = ((focus.style as CSSProperties)?.height as number) || 80;
      setCenter(pos.x + w / 2, pos.y + h / 2, { zoom: getZoom(), duration: 400 });
    }, 300);
    return () => clearTimeout(timer);
  }, [initialNodes, fitView, setCenter, getInternalNode, getZoom]);

  const nodeMap = useMemo(() => new Map(nodes.map(n => [n.id, n])), [nodes]);
  const chain = useMemo(
    () => enableHoverChain ? computeChain(hoverId, edges) : null,
    [hoverId, edges, enableHoverChain],
  );

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
      return {
        ...e,
        className: EDGE_KIND_CLASS[kind],
        style: { strokeOpacity: opacity, strokeWidth: 2.5 },
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, width: 5, height: 5, color: EDGE_KIND_COLOR[kind] },
      };
    });
  }, [edges, nodeMap, chain, dimStatusSet, nodeStatusOf]);

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

  // 拖动开始就把这条边的 ELK 预算路径作废: 路径是按原坐标算的, card 一走边还钉在原地。
  // 清空后 ElkPathEdge 回落到实时 source/target 坐标画曲线, 边跟着 card 走。
  // 重新布局时上面那个 setEdges(initialEdges) 会把路径带回来。
  const handleNodeDragStart = useCallback((_: unknown, node: Node) => {
    setEdges(es => es.map(e => (
      (e.source === node.id || e.target === node.id) && ((e.data?.points as unknown[])?.length)
        ? { ...e, data: { ...e.data, points: [] } } : e
    )));
  }, [setEdges]);

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
        onNodeDragStart={handleNodeDragStart}
        onNodeMouseEnter={(_, node) => setHoverId(node.id)}
        onNodeMouseLeave={() => setHoverId(null)}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={true}
        proOptions={{ hideAttribution: true }}
        minZoom={0.2}
        maxZoom={2}
        panOnDrag={true}
        zoomOnScroll={true}
        zoomOnDoubleClick={true}
        zoomOnPinch={true}
        panOnScroll={false}
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
