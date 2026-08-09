"use client";

// 自定义边: ELK 正交路径 → 手绘风格波浪曲线
// ELK 正交路径保证不穿 card, 在此基础上做平滑 + 波形偏移
// 波形让直线段有手绘感, 非横平竖直

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

// 对正交路径做平滑: 折点用圆弧过渡 + 直线段叠加法向正弦波偏移
function smoothOrthoWavy(pts: Pt[], sourceIdx: number, sourceTotal: number, edgeHash: number): string {
  const p = dedup(pts);
  if (p.length < 2) return "";

  const sCenter = (sourceTotal - 1) / 2;
  const sign = sourceTotal > 1 ? Math.sign(sourceIdx - sCenter) || 1 : 1;
  // edgeHash → 0..1, 给每条边不同的波形种子
  const seed = (edgeHash % 1000) / 1000;

  if (p.length === 2) {
    const [a, b] = p;
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const nx = -dy / len, ny = dx / len;
    // 弧度: 基础 0.12 × len, 加 seed 变化, 限制防接近 card
    const mag = Math.min(18, len * (0.1 + seed * 0.06)) * sign;
    const mx = (a.x + b.x) / 2 + nx * mag;
    const my = (a.y + b.y) / 2 + ny * mag;
    return `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
  }

  const R = 0.38; // 折点圆弧占比
  let d = `M ${p[0].x} ${p[0].y}`;

  for (let i = 0; i < p.length - 1; i++) {
    const a = p[i];
    const b = p[i + 1];
    const dx = b.x - a.x, dy = b.y - a.y;
    const segLen = Math.sqrt(dx * dx + dy * dy) || 1;

    let tStart = 0, tEnd = 1;
    if (i > 0) {
      const prevLen = Math.sqrt((a.x - p[i-1].x) ** 2 + (a.y - p[i-1].y) ** 2) || 1;
      tStart = Math.min(0.4, (Math.min(segLen, prevLen) * R) / segLen);
    }
    if (i < p.length - 2) {
      const nextLen = Math.sqrt((p[i+2].x - b.x) ** 2 + (p[i+2].y - b.y) ** 2) || 1;
      tEnd = 1 - Math.min(0.4, (Math.min(segLen, nextLen) * R) / segLen);
    }

    const sx = a.x + dx * tStart;
    const sy = a.y + dy * tStart;
    const ex = a.x + dx * tEnd;
    const ey = a.y + dy * tEnd;

    if (i > 0 && tStart > 0.01) {
      d += ` Q ${a.x} ${a.y} ${sx} ${sy}`;
    }

    const subDx = ex - sx, subDy = ey - sy;
    const subLen = Math.sqrt(subDx * subDx + subDy * subDy) || 1;
    const nx = -subDy / subLen, ny = subDx / subLen;

    // 波幅: 基础 + seed 变化, 每段略有不同
    // 限制波幅防止边偏移到 card 旁边
    const segSeed = (edgeHash + i * 37) % 100 / 100;
    const waveAmp = Math.min(12, subLen * (0.05 + segSeed * 0.04)) * sign;

    // 波浪: 两段 quadratic 拼出 S 弯, 偏移量用 seed 变化
    const amp1 = waveAmp * (0.8 + segSeed * 0.4);
    const amp2 = waveAmp * (0.8 + (1 - segSeed) * 0.4);

    const t1x = sx + subDx * 0.33 + nx * amp1;
    const t1y = sy + subDy * 0.33 + ny * amp1;
    const midX = sx + subDx * 0.5;
    const midY = sy + subDy * 0.5;
    const t2x = sx + subDx * 0.67 - nx * amp2;
    const t2y = sy + subDy * 0.67 - ny * amp2;

    if (subLen > 2) {
      d += ` Q ${t1x} ${t1y} ${midX} ${midY} Q ${t2x} ${t2y} ${ex} ${ey}`;
    } else {
      d += ` L ${ex} ${ey}`;
    }
  }

  const last = p[p.length - 1];
  d += ` L ${last.x} ${last.y}`;
  return d;
}

export const ElkPathEdge = memo(function ElkPathEdge({
  id, sourceX, sourceY, targetX, targetY,
  style, markerEnd, data,
}: EdgeProps) {
  const points = (data?.points as Pt[]) || [];
  const sourceIdx = (data?.sourceIdx as number) || 0;
  const sourceTotal = (data?.sourceTotal as number) || 1;

  let d: string;
  if (points.length >= 2) {
    const edgeHash = (id || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    d = smoothOrthoWavy(points, sourceIdx, sourceTotal, edgeHash);
  } else {
    // 没有 ELK 路径: 用简单 quadratic
    const mx = (sourceX + targetX) / 2;
    const my = (sourceY + targetY) / 2 + 15;
    d = `M ${sourceX} ${sourceY} Q ${mx} ${my} ${targetX} ${targetY}`;
  }

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
