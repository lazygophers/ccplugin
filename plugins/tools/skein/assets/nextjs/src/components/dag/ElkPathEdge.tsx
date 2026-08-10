"use client";

// 自定义边: 把 ELK 的路由结果画成手绘感曲线
//
// ELK 以 edgeRouting=ORTHOGONAL 出折线, 折点构成绕开 card 的走廊。本文件把整条折线做
// Catmull-Rom 平滑成一根连续曲线 (不是把直角磨圆), 再给控制点加一点确定性抖动做手绘感。
//
// 不再自己往法向推波形 —— 那是旧实现里边压到 card 上、以及短段自绕成圈的根因: 推的幅度
// 与线段长度成正比却与周围留白无关, 短段一推就把起点终点绕回去了。

import { memo } from "react";
import { type EdgeProps } from "@xyflow/react";

interface Pt { x: number; y: number }

function dedup(pts: Pt[]): Pt[] {
  const out: Pt[] = [];
  for (const p of pts) {
    const last = out[out.length - 1];
    if (!last || Math.abs(last.x - p.x) > 0.5 || Math.abs(last.y - p.y) > 0.5) out.push(p);
  }
  return out;
}

// 确定性伪随机: 同一条边每次渲染抖动一致, 不会闪
function jitter(seed: number, i: number, amp: number): Pt {
  const a = Math.sin(seed * 12.9898 + i * 78.233) * 43758.5453;
  const b = Math.sin(seed * 39.3468 + i * 11.135) * 24634.6345;
  return { x: (a - Math.floor(a) - 0.5) * amp, y: (b - Math.floor(b) - 0.5) * amp };
}

const add = (p: Pt, o: Pt): Pt => ({ x: p.x + o.x, y: p.y + o.y });

/** Catmull-Rom 转三次贝塞尔: 曲线穿过每个折点, 折点之间是真正的曲线段。 */
function catmullRom(p: Pt[], seed: number, amp: number): string {
  if (p.length === 2) {
    const [a, b] = p;
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    // 单段: 沿主方向出/入, 弯度取线长的固定比例, 不做法向推移
    const k = Math.min(80, len * 0.4);
    const vert = Math.abs(dy) >= Math.abs(dx);
    const c1 = vert ? { x: a.x, y: a.y + k } : { x: a.x + k, y: a.y };
    const c2 = vert ? { x: b.x, y: b.y - k } : { x: b.x - k, y: b.y };
    return `M ${a.x} ${a.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${b.x} ${b.y}`;
  }
  let d = `M ${p[0].x} ${p[0].y}`;
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[i - 1] || p[i];
    const p1 = p[i];
    const p2 = p[i + 1];
    const p3 = p[i + 2] || p2;
    const j = jitter(seed, i, amp);
    const c1 = { x: p1.x + (p2.x - p0.x) / 6 + j.x, y: p1.y + (p2.y - p0.y) / 6 + j.y };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6 + j.x, y: p2.y - (p3.y - p1.y) / 6 + j.y };
    d += ` C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${p2.x} ${p2.y}`;
  }
  return d;
}

export const ElkPathEdge = memo(function ElkPathEdge({
  id, sourceX, sourceY, targetX, targetY,
  style, markerEnd, data,
}: EdgeProps) {
  const raw = (data?.points as Pt[]) || [];
  const pts = dedup(raw.length >= 2 ? raw : [{ x: sourceX, y: sourceY }, { x: targetX, y: targetY }]);
  const seed = (id || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 997;
  // 抖动幅度压在 4px: 大于这个数就可能把线推出 ELK 留出的走线廊道, 蹭到 card
  const AMP = 4;

  const d = catmullRom(pts, seed, AMP);

  return (
    <path
      id={id}
      className="react-flow__edge-path"
      d={d}
      fill="none"
      style={style}
      markerEnd={markerEnd as string}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  );
});
