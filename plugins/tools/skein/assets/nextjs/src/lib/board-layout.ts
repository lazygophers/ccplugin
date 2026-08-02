// 看板 DAG 布局: 分层 (tiered) 打包 + supertask 容器分组 (两段式)
// 分组方案见 .skein/task/dag-parent-nesting/design.md — 组内布局→组当超节点→外层布局, 复用同一个 layoutTiered

import type { NormTask } from "./model";
import type { DagNode, DagEdge } from "./depdag";

export interface LayoutNode extends DagNode { task: NormTask; rowH: number; groupId?: string; }

export const DAG_DENSITY = {
  large:   { w: 260, h: 76, gapX: 54, gapY: 39, padX: 120, padY: 45 },
  compact: { w: 190, h: 52, gapX: 42, gapY: 33, padX: 120, padY: 45 },
  mini:    { w: 120, h: 32, gapX: 42, gapY: 33, padX: 120, padY: 45 },
} as const;
export type Density = keyof typeof DAG_DENSITY;

type Sizing = { w: number; h: number; gapX: number; gapY: number; padX: number; padY: number };
type SizeFn = (id: string) => { w: number; h: number };

export function layoutTiered(
  ids: string[],
  depsOf: (id: string) => string[],
  s: Sizing,
  maxW: number,
  extraOf: (id: string) => Record<string, unknown>,
  sizeOf?: SizeFn,
) {
  const inSet = new Set(ids);
  const lay = new Map<string, number>();
  const topo: string[] = [];
  {
    const deps = new Map(ids.map(id => [id, depsOf(id).filter(d => inSet.has(d))]));
    const left = new Map(ids.map(id => [id, deps.get(id)!.length]));
    const succ = new Map(ids.map(id => [id, [] as string[]]));
    for (const id of ids) for (const d of deps.get(id)!) succ.get(d)!.push(id);
    const q = ids.filter(id => left.get(id) === 0);
    const seen = new Set<string>();
    while (q.length) { const cur = q.shift()!; seen.add(cur); topo.push(cur); for (const nx of succ.get(cur)!) { left.set(nx, left.get(nx)! - 1); if (left.get(nx) === 0) q.push(nx); } }
    for (const id of ids) if (!seen.has(id)) topo.push(id);
  }
  for (const id of topo) lay.set(id, Math.max(0, ...depsOf(id).map(d => (lay.get(d) ?? -1) + 1)));
  const tiers: string[][] = [];
  for (const id of topo) (tiers[lay.get(id)!] || (tiers[lay.get(id)!] = [])).push(id);

  const pos = new Map<string, { x: number; y: number }>();
  const bary = (id: string) => { const ps = depsOf(id).map(d => pos.get(d)).filter(Boolean) as { x: number }[]; return ps.length ? ps.reduce((a, p) => a + p.x, 0) / ps.length : Infinity; };

  const buildResult = (sizeOfEach: SizeFn, y: number) => {
    const nodes = topo.map(id => { const sz = sizeOfEach(id); return { id, ...pos.get(id)!, w: sz.w, h: sz.h, rowH: sz.h, band: 0, tier: lay.get(id), ...extraOf(id) }; });
    const nmap = new Map(nodes.map(n => [n.id, n]));
    const edges: DagEdge[] = [];
    for (const id of ids) for (const d of depsOf(id)) { const from = nmap.get(d), to = nmap.get(id); if (from && to) edges.push({ from, to, bends: [], cross: false, laneY: 0 }); }
    return { nodes, edges, width: Math.max(0, ...nodes.map(n => n.x + n.w)) + s.padX, height: y - s.gapY + s.padY };
  };

  if (!sizeOf) {
    // ── 均匀网格路径 (无 sizeOf 时逐字节保持原算法, 是零回归的关键) ──
    const nw = s.w, nh = s.h;
    const perRow = Math.max(1, Math.floor((maxW - s.padX * 2 + s.gapX) / (nw + s.gapX)));
    const rowH = nh + 6;
    let y = s.padY;
    for (let pass = 0; pass < 2; pass++) {
      y = s.padY;
      for (const tier of tiers) {
        if (!tier) continue;
        if (pass) tier.sort((a, b) => bary(a) - bary(b));
        const rows = Math.ceil(tier.length / perRow);
        const cnt = Math.ceil(tier.length / rows);
        tier.forEach((id, i) => {
          const r = Math.floor(i / cnt), c = i % cnt;
          const rowN = Math.min(cnt, tier.length - r * cnt);
          const x0 = s.padX + (maxW - s.padX * 2 - (rowN * (nw + s.gapX) - s.gapX)) / 2;
          pos.set(id, { x: Math.max(s.padX, x0) + c * (nw + s.gapX), y: y + r * rowH });
        });
        y += rows * rowH - 6 + s.gapY;
      }
    }
    return buildResult(() => ({ w: nw, h: nh }), y);
  }

  // ── 变尺寸路径 (供组超节点参与外层布局): 逐行 flow 打包, 按行内最大高度换行 ──
  let y = s.padY;
  for (let pass = 0; pass < 2; pass++) {
    y = s.padY;
    for (const tier of tiers) {
      if (!tier) continue;
      if (pass) tier.sort((a, b) => bary(a) - bary(b));
      const rows: string[][] = [[]];
      let rowW = s.padX;
      for (const id of tier) {
        const sz = sizeOf(id);
        if (rows[rows.length - 1].length > 0 && rowW + sz.w > maxW - s.padX) { rows.push([]); rowW = s.padX; }
        rows[rows.length - 1].push(id);
        rowW += sz.w + s.gapX;
      }
      for (const row of rows) {
        const rowWidth = row.reduce((a, id) => a + sizeOf(id).w, 0) + Math.max(0, row.length - 1) * s.gapX;
        let x = Math.max(s.padX, s.padX + (maxW - s.padX * 2 - rowWidth) / 2);
        let maxH = 0;
        for (const id of row) {
          const sz = sizeOf(id);
          pos.set(id, { x, y });
          x += sz.w + s.gapX;
          maxH = Math.max(maxH, sz.h);
        }
        y += maxH + 6 + s.gapY;
      }
    }
  }
  return buildResult(sizeOf, y);
}

export function layoutDAG(tasks: NormTask[], view: { w: number; h: number }, density: Density) {
  if (!tasks.length) return { nodes: [] as LayoutNode[], edges: [] as DagEdge[], groups: [] as GroupBox[], width: 0, height: 0, density };
  const byId = new Map(tasks.map(t => [t.id, t]));
  const depsOf = (id: string) => (byId.get(id)?.deps || []).filter(d => byId.has(d));
  const ids = tasks.map(t => t.id);
  const maxW = view.w || 1200;
  const s = DAG_DENSITY[density] || DAG_DENSITY.compact;

  const childrenOf = new Map<string, string[]>();
  for (const t of tasks) {
    if (t.parent && t.parent !== t.id && byId.has(t.parent)) {
      if (!childrenOf.has(t.parent)) childrenOf.set(t.parent, []);
      childrenOf.get(t.parent)!.push(t.id);
    }
  }
  const groupIds = [...childrenOf.keys()].filter(pid => childrenOf.get(pid)!.length > 0);

  if (!groupIds.length) {
    // 全库无父子数据 (或过滤后无 child) → 与改动前逐字节一致的单次布局调用, 零回归
    const extraOf = (id: string) => ({ task: byId.get(id)! });
    const result = layoutTiered(ids, depsOf, s, maxW, extraOf);
    return { ...result, groups: [] as GroupBox[], density } as unknown as
      { nodes: LayoutNode[]; edges: DagEdge[]; groups: GroupBox[]; width: number; height: number; density: Density };
  }

  const groupIdSet = new Set(groupIds);
  const childIdSet = new Set(groupIds.flatMap(g => childrenOf.get(g)!));
  const childToGroup = new Map<string, string>();
  for (const g of groupIds) for (const c of childrenOf.get(g)!) childToGroup.set(c, g);
  const standaloneIds = ids.filter(id => !childIdSet.has(id) && !groupIdSet.has(id));

  // 1. 组内布局: 每组的 child 单独跑一次现有布局函数, 得组内相对坐标 + 包围盒
  const groupInner = new Map<string, ReturnType<typeof layoutTiered>>();
  for (const gid of groupIds) {
    const children = childrenOf.get(gid)!;
    const childSet = new Set(children);
    const innerDepsOf = (id: string) => depsOf(id).filter(d => childSet.has(d));
    const extraOf = (id: string) => ({ task: byId.get(id)! });
    groupInner.set(gid, layoutTiered(children, innerDepsOf, s, maxW, extraOf));
  }

  // 2. 外层布局: 组当成尺寸 = 包围盒 + padding 的超节点, 与独立 task 一起再跑一次现有布局函数
  const outerIds = [...standaloneIds, ...groupIds];
  const sizeOf: SizeFn = (id) => {
    if (groupIdSet.has(id)) {
      const inner = groupInner.get(id)!;
      return { w: inner.width + GROUP_PAD * 2, h: inner.height + GROUP_PAD * 2 + GROUP_HEADER };
    }
    return { w: s.w, h: s.h };
  };
  // 跨组依赖走排序提升: child 依赖组外 task 时, 外层图上体现为「组 → 该 task」的顺序约束; 绘制仍连回具体 child (见下)
  const outerDepsOf = (outerId: string): string[] => {
    const members = groupIdSet.has(outerId) ? childrenOf.get(outerId)! : [outerId];
    const seen = new Set<string>(); const out: string[] = [];
    for (const m of members) {
      for (const d of depsOf(m)) {
        const dOuter = childToGroup.get(d) || d;
        if (dOuter === outerId || seen.has(dOuter)) continue;
        seen.add(dOuter); out.push(dOuter);
      }
    }
    return out;
  };
  const outerExtraOf = (id: string) => (groupIdSet.has(id) ? {} : { task: byId.get(id)! });
  const outerResult = layoutTiered(outerIds, outerDepsOf, s, maxW, outerExtraOf, sizeOf);

  // 3. 落位: 组内相对坐标 + 超节点绝对坐标 = child 最终坐标; 容器框 = 超节点矩形
  const groups: GroupBox[] = [];
  const nmap = new Map<string, LayoutNode>();
  for (const on of outerResult.nodes) {
    if (groupIdSet.has(on.id)) {
      const inner = groupInner.get(on.id)!;
      const children = childrenOf.get(on.id)!.map(id => byId.get(id)!);
      groups.push({
        id: on.id, parent: byId.get(on.id)!, children,
        x: on.x, y: on.y, w: on.w, h: on.h,
        innerW: inner.width, innerH: inner.height,
        headerH: GROUP_HEADER, pad: GROUP_PAD,
      });
      for (const cn of inner.nodes) {
        nmap.set(cn.id, {
          ...cn,
          x: on.x + GROUP_PAD + cn.x,
          y: on.y + GROUP_HEADER + GROUP_PAD + cn.y,
          rowH: cn.h,
          groupId: on.id,
        } as unknown as LayoutNode);
      }
    } else {
      nmap.set(on.id, { ...on, rowH: on.h } as unknown as LayoutNode);
    }
  }

  // 4. 边: 父子关系不生成边; deps 边全部保留, 端点始终是具体 task 卡片 (组内/跨组同一套渲染, 不区分)
  const edges: DagEdge[] = [];
  for (const id of ids) {
    const to = nmap.get(id);
    if (!to) continue;
    for (const d of depsOf(id)) {
      const from = nmap.get(d);
      if (from) edges.push({ from, to, bends: [], cross: false, laneY: 0 });
    }
  }

  const nodes = [...nmap.values()];
  const width = Math.max(outerResult.width, 0, ...nodes.map(n => n.x + n.w));
  const height = Math.max(outerResult.height, 0, ...nodes.map(n => n.y + n.h));
  return { nodes, edges, groups, width, height, density };
}

export const GROUP_PAD = 14;
export const GROUP_HEADER = 28;

export interface GroupBox {
  id: string;
  parent: NormTask;
  children: NormTask[];
  x: number; y: number; w: number; h: number;
  innerW: number; innerH: number;
  headerH: number; pad: number;
}
