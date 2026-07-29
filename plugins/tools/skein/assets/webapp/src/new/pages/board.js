// ============================================================
//  Board — 看板 / DAG
//  设计: 左 DAG/列表 + 右详情面板(点击才显) | 悬浮 popover | 状态多选筛选
//  状态: 规划中 / 待执行 / 执行中 / 验收中 / 已完成
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTasks, normalizeTask, prioLabel, prioTextColor,
         confirmDialog, alertDialog, buildTimeline, subTimelineView } from '../app.js';
import { EDGE_KIND, edgeKinds, edgeLegend, drawEdges, buildDepDAG, depDAGView } from '../lib/depdag.js';

const ST_COLOR = {
  planning: 'st-planning', ready: 'st-ready',
  active:   'st-active',  check: 'st-check',
  done:     'st-done',    failed: 'st-failed',
};
const ST_LABEL = {
  planning: '规划中', ready: '待执行',
  active:   '执行中', check: '验收中',
  done:     '已完成', failed: '失败',
};
const ST_ICON = {
  planning: 'fa-lightbulb-o', ready: 'fa-flag-o',
  active:   'fa-spinner fa-spin', check: 'fa-eye',
  done:     'fa-check-circle', failed: 'fa-times-circle',
};
const ALL_STATUSES = ['planning', 'ready', 'active', 'check', 'done'];
// 默认筛选: 不含已完成 (DAG 中已完成任务做灰色, 默认不占视觉焦点)
const DEFAULT_FILTER = new Set(['planning', 'ready', 'active', 'check']);
// 未完成态: 点击"全部"在全选/未完成之间切换
const INCOMPLETE_STATUSES = ['planning', 'ready', 'active', 'check'];

// ---- Sugiyama 分层布局核心 (零依赖, 思路取自 dagre / elkjs) ----
// 1) rank: 最长路径分层 + 逆序下沉紧缩 —— 无依赖节点贴到消费者前一层, 不再全挤第 0 列拉出横跨全图的长边
// 2) 长边插虚点, 让它在中间层有落脚点: 既参与排序, 又给走线拐点绕开挡路的卡片
// 3) median + transpose 多轮双向扫描降交叉
// 4) 层内折行: 行数上限 R 全图统一, 由可用视口宽高比反解 (不写死行数); 装得下就不折
// 5) 单列层按邻居中位数对齐, 让链路走直
// 复杂度 O(V+E) 级 (transpose 对 >200 的层跳过), 支撑千节点量级
function sugiyama(ids, depsOf, opt) {
  const { colW, rowH, padX, padY, gapY } = opt;
  const maxWidth = opt.maxWidth || 1200;   // 硬约束: 画布宽度永不超过它
  const viewH = opt.viewH || 800;          // 软目标: 一条带尽量高约一屏
  const idSet = new Set(ids);
  const deps = new Map(), succ = new Map();
  for (const id of ids) { deps.set(id, []); succ.set(id, []); }
  for (const id of ids) {
    const seen = new Set();
    for (const d of (depsOf(id) || [])) {
      if (!idSet.has(d) || d === id || seen.has(d)) continue;
      seen.add(d);
      deps.get(id).push(d);
      succ.get(d).push(id);
    }
  }

  // --- 1. 分层 ---
  const rank = new Map();
  const indeg = new Map(ids.map(i => [i, deps.get(i).length]));
  let frontier = ids.filter(i => indeg.get(i) === 0);
  let settled = 0;
  while (frontier.length) {
    const next = [];
    for (const id of frontier) {
      settled++;
      let r = 0;
      for (const d of deps.get(id)) r = Math.max(r, (rank.has(d) ? rank.get(d) : -1) + 1);
      rank.set(id, r);
      for (const s of succ.get(id)) {
        indeg.set(s, indeg.get(s) - 1);
        if (indeg.get(s) === 0) next.push(s);
      }
    }
    frontier = next;
  }
  // 有环兜底: 剩下的按已定 dep 强排 (DAG 数据本不该有环, 但不能因此死循环)
  if (settled < ids.length) {
    for (const id of ids) {
      if (rank.has(id)) continue;
      let r = 0;
      for (const d of deps.get(id)) if (rank.has(d)) r = Math.max(r, rank.get(d) + 1);
      rank.set(id, r);
    }
  }
  // 下沉紧缩: rank 降序遍历, 有后继的贴到 min(后继)-1
  for (const id of ids.slice().sort((a, b) => rank.get(b) - rank.get(a))) {
    const ss = succ.get(id);
    if (!ss.length) continue;
    let m = Infinity;
    for (const s of ss) m = Math.min(m, rank.get(s));
    if (m - 1 > rank.get(id)) rank.set(id, m - 1);
  }
  // 压掉下沉后留下的空层
  const usedRanks = [...new Set(ids.map(i => rank.get(i)))].sort((a, b) => a - b);
  const remap = new Map(usedRanks.map((r, i) => [r, i]));
  for (const id of ids) rank.set(id, remap.get(rank.get(id)));
  const L = usedRanks.length;

  // --- 2. 建边 + 长边插虚点 ---
  const layers = Array.from({ length: L }, () => []);
  const nodeOf = new Map();
  for (const id of ids) {
    const n = { id, rank: rank.get(id), dummy: false };
    nodeOf.set(id, n);
    layers[n.rank].push(n);
  }
  const edges = [];
  let dseq = 0;
  for (const id of ids) {
    for (const d of deps.get(id)) {
      const from = nodeOf.get(d), to = nodeOf.get(id);
      const chain = [];
      for (let r = from.rank + 1; r < to.rank; r++) {
        const dn = { id: `~d${dseq++}`, rank: r, dummy: true };
        layers[r].push(dn);
        chain.push(dn);
      }
      edges.push({ from, to, chain });
    }
  }
  // 相邻层邻接 (虚点串在链上, 与真实节点同等参与排序)
  const adjUp = new Map(), adjDown = new Map();
  const link = (a, b) => {
    if (!adjDown.has(a)) adjDown.set(a, []);
    if (!adjUp.has(b)) adjUp.set(b, []);
    adjDown.get(a).push(b); adjUp.get(b).push(a);
  };
  for (const e of edges) {
    let prev = e.from;
    for (const dn of e.chain) { link(prev, dn); prev = dn; }
    link(prev, e.to);
  }

  // --- 3. 交叉最小化 ---
  const posIn = new Map();
  const reindex = () => { for (const l of layers) l.forEach((n, i) => posIn.set(n, i)); };
  reindex();
  const medianOf = (n, adj) => {
    const ps = (adj.get(n) || []).map(m => posIn.get(m)).sort((a, b) => a - b);
    if (!ps.length) return -1;
    const mid = ps.length >> 1;
    return ps.length % 2 ? ps[mid] : (ps[mid - 1] + ps[mid]) / 2;
  };
  const crossOf = (a, b, adj) => {
    // a 排在 b 上方时, 二者邻边的逆序对数
    const pa = (adj.get(a) || []).map(m => posIn.get(m));
    const pb = (adj.get(b) || []).map(m => posIn.get(m));
    let c = 0;
    for (const x of pa) for (const y of pb) if (y < x) c++;
    return c;
  };
  const idxs = layers.map((_, i) => i);
  for (let it = 0; it < 6; it++) {
    const down = it % 2 === 0;
    const seq = down ? idxs.slice(1) : idxs.slice(0, -1).reverse();
    const adj = down ? adjUp : adjDown;
    for (const li of seq) {
      const layer = layers[li];
      const med = new Map();
      layer.forEach((n, i) => {
        const m = medianOf(n, adj);
        med.set(n, m < 0 ? i : m); // 无邻居的锚在原位, 不被甩到头部
      });
      layer.sort((a, b) => med.get(a) - med.get(b));
      reindex();
      if (layer.length <= 200) {
        for (let round = 0; round < 4; round++) {
          let improved = false;
          for (let i = 0; i + 1 < layer.length; i++) {
            const a = layer[i], b = layer[i + 1];
            if (crossOf(a, b, adj) > crossOf(b, a, adj)) {
              layer[i] = b; layer[i + 1] = a;
              posIn.set(b, i); posIn.set(a, i + 1);
              improved = true;
            }
          }
          if (!improved) break;
        }
      }
    }
    reindex();
  }

  // --- 4. 层序列折行 (蛇形带): 宽度是硬约束, 一带最多放 K 层, 排满换行往下续 ---
  // 这正是 ELK wrapping.strategy 的做法 — 切的是层序列, 让图宽永远塞进可用宽度,
  // 长出来的部分往下走, 由外层的纵向滚动条承担。
  const K = Math.max(1, Math.floor((maxWidth - padX * 2) / colW));
  // 带内目标高度: 一带尽量高约一屏。宽层 (fan-out) 装不下就吃掉本带的相邻列折行,
  // 不折的话 19 个兄弟就堆成一根 4500px 的柱子。
  const bandH = Math.max(4, Math.floor((viewH || 800) / rowH)) * rowH;
  // 虚点只是长边的走线拐点, 不渲染卡片 — 占整行 rowH 就是满屏空白, 缩到通道宽度
  const DUMMY_H = 28;
  const hOf = (n) => (n.dummy ? DUMMY_H : rowH);
  // 贪心装带: 每层按需要的列数入座, 装不下就换带
  const seat = [];   // 每层 { band, col, cols }
  let curBand = 0, curCol = 0;
  for (const l of layers) {
    const need = l.reduce((a, n) => a + hOf(n), 0);
    const cols = Math.min(K, Math.max(1, Math.ceil(need / bandH)));
    if (curCol + cols > K && curCol > 0) { curBand++; curCol = 0; }
    seat.push({ band: curBand, col: curCol, cols });
    curCol += cols;
  }
  const bands = curBand + 1;
  const bandOf = (li) => seat[li].band;

  // --- 5. 坐标: 层内按节点高度累加, 装满一列换下一列 ---
  layers.forEach((l, li) => {
    const st = seat[li];
    let col = 0, acc = 0;
    for (const n of l) {
      const nh = hOf(n);
      if (acc + nh > bandH && acc > 0 && col < st.cols - 1) { col++; acc = 0; }
      n.x = (st.col + col) * colW;
      n.y = acc;
      n.y0 = acc;   // 网格基准位, 对齐只能在其附近微调
      n.band = st.band;
      acc += nh;
    }
  });
  // 层内按邻居中位数对齐 + 保序推挤; 只认同带邻居 (跨带的上下游在图上是回绕线, 不该互相牵引)
  // 位移夹在基准位 ±SLACK 行内: 不夹的话对齐会顺着链路级联推高, 整图越排越长
  const SLACK = 3 * rowH;
  for (let pass = 0; pass < 3; pass++) {
    const seq = pass % 2 === 0 ? idxs : idxs.slice().reverse();
    const adj = pass % 2 === 0 ? adjUp : adjDown;
    for (const li of seq) {
      if (seat[li].cols > 1) continue;   // 折行层是网格, 保持整齐不动
      const layer = layers[li];
      const band = bandOf(li);
      let prev = -Infinity;
      for (const n of layer) {
        const ns = (adj.get(n) || []).filter(m => m.band === band);
        let want = n.y;
        if (ns.length) {
          const ys = ns.map(m => m.y).sort((a, b) => a - b);
          const mid = ys.length >> 1;
          want = ys.length % 2 ? ys[mid] : (ys[mid - 1] + ys[mid]) / 2;
        }
        want = Math.max(n.y0 - SLACK, Math.min(n.y0 + SLACK, want));
        n.y = Math.max(want, prev);
        prev = n.y + hOf(n);
      }
    }
  }
  // 带内归零 → 按带高纵向堆叠
  const span = Array.from({ length: bands }, () => ({ lo: Infinity, hi: -Infinity }));
  let usedCols = 1;
  layers.forEach((l, li) => {
    const s = span[seat[li].band];
    usedCols = Math.max(usedCols, seat[li].col + seat[li].cols);
    for (const n of l) { s.lo = Math.min(s.lo, n.y); s.hi = Math.max(s.hi, n.y + hOf(n)); }
  });
  const bandTop = [];
  const bandsInfo = [];
  let accY = 0;
  for (const s of span) {
    if (s.lo === Infinity) { s.lo = 0; s.hi = 0; }
    bandTop.push({ top: accY, shift: -s.lo });
    // 带的绝对纵向范围 — 跨带的回绕边走带间空隙, 需要它定位水平通道
    bandsInfo.push({ top: accY + padY, bottom: accY + (s.hi - s.lo) + padY });
    accY += (s.hi - s.lo) + rowH;   // 带间留一行间距
  }
  const all = layers.flat();
  for (const n of all) {
    const bt = bandTop[n.band];
    n.x += padX;
    n.y += bt.shift + bt.top + padY;
  }
  const maxY = all.reduce((m, n) => Math.max(m, n.y + (n.dummy ? 0 : rowH - gapY)), 0);
  return {
    layers, edges, bandCols: usedCols, bandsInfo,
    width: usedCols * colW + padX * 2,
    height: maxY + padY,
  };
}

// 三档节点尺寸 —— 分层排布的高度直接由节点高定 (行 = 依赖深度, 层数不可压)。
// large 卡最宽松; compact(默认中号) 放得下标题 + 状态两行; mini 只剩状态色点 + id, 详情全靠 hover popover。
const DAG_DENSITY = {
  large:   { w: 260, h: 76, gapX: 18, gapY: 26, padX: 40, padY: 30 },
  compact: { w: 190, h: 52, gapX: 14, gapY: 22, padX: 40, padY: 30 },
  mini:    { w: 120, h: 32, gapX: 14, gapY: 22, padX: 40, padY: 30 },
};

// view = { w, h } 可用画布尺寸 — 详情面板开合 / 窗口缩放都会改变它, 布局随之重排。
// 宽度是硬约束 (画布永不横向溢出), 高度自由, 超出部分由容器纵向滚动条承担。
// density 缺省/非法值一律回落中号 compact — 不再走自动降级判定 (autoDensity 已删, 用户明确选档更可靠)。
function layoutDAG(tasks, view, density) {
  if (!tasks || !tasks.length) return { nodes: [], edges: [], width: 0, height: 0, density: density || 'compact' };
  const byId = new Map(tasks.map(t => [t.id, t]));
  const depsOf = id => (byId.get(id).deps || []).filter(d => byId.has(d));
  const ids = tasks.map(t => t.id);
  const maxW = (view && view.w) || 1200;
  const extraOf = id => ({ task: byId.get(id) });
  const d = DAG_DENSITY[density] ? density : 'compact';
  return { ...layoutTiered(ids, depsOf, DAG_DENSITY[d], maxW, extraOf), density: d };
}

// 真分层 (行 = 依赖深度), 靠缩小节点换回来的。
// ADR 0001 当年判分层死刑的 15514px = 66 行 × 220px 行高 —— 行高由卡片尺寸定, 不是算法定的。
// 节点降到 120×32 / 190×52, 同样的层数只占 1/5 高度: 实测 96 节点 2090px / 2850px, 回绕 0。
// 层内一行放不下就折行 (整层仍是同一依赖深度), 折行数按 perRow 均分, 避免末行只剩 1 个。
// 层内顺序按 barycenter (前驱平均 x) 排, 跑两遍让第二遍拿到真实前驱坐标。
function layoutTiered(ids, depsOf, s, maxW, extraOf) {
  const nw = s.w, nh = s.h;
  const inSet = new Set(ids);
  const lay = new Map();
  // 最长路径深度: 按拓扑序推进, 环上节点 (depsOf 拿不到已定层的前驱) 落回 0
  const topo = [];
  {
    const deps = new Map(ids.map(id => [id, depsOf(id).filter(d => inSet.has(d))]));
    const left = new Map(ids.map(id => [id, deps.get(id).length]));
    const succ = new Map(ids.map(id => [id, []]));
    for (const id of ids) for (const d of deps.get(id)) succ.get(d).push(id);
    const q = ids.filter(id => left.get(id) === 0);
    const seen = new Set();
    while (q.length) {
      const cur = q.shift();
      seen.add(cur);
      topo.push(cur);
      for (const nx of succ.get(cur)) { left.set(nx, left.get(nx) - 1); if (left.get(nx) === 0) q.push(nx); }
    }
    for (const id of ids) if (!seen.has(id)) topo.push(id);   // 环兜底: 全量绘制
  }
  for (const id of topo) lay.set(id, Math.max(0, ...depsOf(id).map(d => (lay.get(d) ?? -1) + 1)));

  const tiers = [];
  for (const id of topo) (tiers[lay.get(id)] || (tiers[lay.get(id)] = [])).push(id);
  const perRow = Math.max(1, Math.floor((maxW - s.padX * 2 + s.gapX) / (nw + s.gapX)));
  const rowH = nh + 6;
  const pos = new Map();
  const bary = (id) => {
    const ps = depsOf(id).map(d => pos.get(d)).filter(Boolean);
    return ps.length ? ps.reduce((a, p) => a + p.x, 0) / ps.length : Infinity;
  };
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
  const nodes = topo.map(id => ({ id, ...pos.get(id), w: nw, h: nh, rowH: nh, band: 0, tier: lay.get(id), ...extraOf(id) }));
  const nmap = new Map(nodes.map(n => [n.id, n]));
  const edges = [];
  for (const id of ids) {
    for (const d of depsOf(id)) {
      const from = nmap.get(d), to = nmap.get(id);
      if (from && to) edges.push({ from, to, bends: [], cross: false, laneY: 0 });
    }
  }
  return {
    nodes, edges,
    width: Math.max(...nodes.map(n => n.x + n.w)) + s.padX,
    height: y - s.gapY + s.padY,
  };
}

// 连通分量 (按无向边划分)
function components(ids, depsOf) {
  const adj = new Map(ids.map(id => [id, []]));
  for (const id of ids) {
    for (const d of depsOf(id)) {
      if (!adj.has(d)) continue;
      adj.get(id).push(d);
      adj.get(d).push(id);
    }
  }
  const seen = new Set(), out = [];
  for (const id of ids) {
    if (seen.has(id)) continue;
    seen.add(id);
    const stack = [id], comp = [];
    while (stack.length) {
      const cur = stack.pop();
      comp.push(cur);
      for (const nb of adj.get(cur)) if (!seen.has(nb)) { seen.add(nb); stack.push(nb); }
    }
    out.push(comp);
  }
  return out;
}

// 单个分量: 横排 (LR) 和竖排 (TB) 各算一遍, 取包围盒面积小的。
// 链状分量横排会拉出一条 9000px 的长龙再折带, 竖排只要一列宽 —— 整块画板因此小得多。
function layoutComponent(comp, depsOf, s, inner, viewH) {
  const base = { ...s, padX: 0, padY: 0 };
  const lr = sugiyama(comp, depsOf, { ...base, maxWidth: inner, viewH });
  if (comp.length < 3) return lr;
  // 竖排 = 层沿 y 排、层内沿 x 排: 把两轴间距对调算完再转置回来。
  // maxWidth 给个大数 (竖排不折带), 宽度约束改由 viewH=inner 承担 (它决定层内累加上限)
  const tb = sugiyama(comp, depsOf, { ...base, colW: s.rowH, rowH: s.colW, maxWidth: 1e6, viewH: inner - s.colW });
  transpose(tb, s);
  // 宽度是硬约束: 竖排块自己超宽就不能用 (装箱兜不住单块超宽)
  if (tb.width > inner) return lr;
  return tb.width * tb.height < lr.width * lr.height ? tb : lr;
}

// 转置 sugiyama 结果: 交换两轴坐标, 重算尺寸。竖排不折带, 故清空 bandsInfo
function transpose(g, s) {
  let mx = 0, my = 0;
  for (const l of g.layers) {
    for (const n of l) {
      const t = n.x; n.x = n.y; n.y = t;
      n.band = 0;
      mx = Math.max(mx, n.x);
      my = Math.max(my, n.y);
    }
  }
  g.width = mx + s.colW;
  g.height = my + s.rowH - s.gapY;
  g.bandsInfo = [];
  g.tb = true;
}

// 各连通分量独立 sugiyama, 再把结果矩形货架装箱 (ELK separateConnectedComponents 的做法)。
// 不分的话互不相连的小簇被硬排进同一条层序列: 白占位置, 还扯出满屏跨带长线。
function layoutPacked(ids, depsOf, s, maxW, viewH, extraOf) {
  const inner = Math.max(s.colW, maxW - s.padX * 2);
  const blocks = components(ids, depsOf).map(comp =>
    packLayout(layoutComponent(comp, depsOf, s, inner, viewH), s, extraOf));
  blocks.sort((a, b) => b.height - a.height || b.width - a.width);   // 大块先放, 小块填右侧缝
  const nodes = [], edges = [];
  let x = 0, y = 0, shelfH = 0, W = 0;
  for (const b of blocks) {
    if (x > 0 && x + b.width > inner) { x = 0; y += shelfH; shelfH = 0; }
    const dx = x + s.padX, dy = y + s.padY;
    for (const n of b.nodes) { n.x += dx; n.y += dy; }
    for (const e of b.edges) { e.bends.forEach(p => { p.x += dx; p.y += dy; }); e.laneY += dy; }
    nodes.push(...b.nodes);
    edges.push(...b.edges);
    x += b.width;
    shelfH = Math.max(shelfH, b.height + s.gapY);
    W = Math.max(W, x);
  }
  return { nodes, edges, width: W + s.padX * 2, height: y + shelfH + s.padY * 2 };
}

// sugiyama 结果 → 渲染用 {nodes, edges}: 丢掉虚点, 虚点坐标转成边的拐点
function packLayout(g, s, extraOf) {
  const w = s.colW - s.gapX, hgt = s.rowH - s.gapY;
  const nodes = [];
  for (const l of g.layers) {
    for (const n of l) {
      if (n.dummy) continue;
      nodes.push({ id: n.id, x: n.x, y: n.y, w, h: hgt, band: n.band, ...extraOf(n.id) });
    }
  }
  const nmap = new Map(nodes.map(n => [n.id, n]));
  const info = g.bandsInfo || [];
  const edges = [];
  for (const e of g.edges) {
    const from = nmap.get(e.from.id), to = nmap.get(e.to.id);
    if (!from || !to) continue;
    // 虚点在层内轴上只有 28px (见 sugiyama DUMMY_H), 拐点取它自己的中线; 竖排时两轴对调
    const bends = e.chain.map(d => (g.tb
      ? { x: d.x + 14, y: d.y + hgt / 2 }
      : { x: d.x + w / 2, y: d.y + 14 }));
    const cross = from.band !== to.band;
    // 跨带的回绕边不穿卡片区 — 走目标带上沿的带间空隙
    const laneY = cross && info[to.band] ? Math.max(6, info[to.band].top - s.rowH / 2) : 0;
    edges.push({ from, to, bends, cross, laneY });
  }
  return { nodes, edges, width: g.width, height: g.height };
}

// ---- 子任务 DAG 布局 (迷你) ----
function layoutSubDAG(subs) {
  if (!subs || !subs.length) return { nodes: [], edges: [], width: 0, height: 0 };
  const byId = new Map(subs.map(s => [s.id || s.sid, s]));
  const s = { colW: 160, rowH: 60, padX: 16, padY: 12, gapX: 16, gapY: 12 };
  // 迷你视图嵌在详情面板里, 宽度上限跟面板走 (断点同 design.css 的 .detail-panel)
  const panelW = window.innerWidth >= 1600 ? 720 : window.innerWidth >= 1280 ? 580 : 400;
  const depsOf = id => (byId.get(id).deps || byId.get(id).dependsOn || []).filter(d => byId.has(d));
  return layoutPacked([...byId.keys()], depsOf, s, panelW - 48, 600, id => ({ sub: byId.get(id) }));
}

// ---- 悬浮 popover ----
function nodePopover(node) {
  const t = node.task;
  const st = t.status || 'planning';
  const subs = t.subtasks || [];
  const subStats = getSubtaskStats(t);
  const hasSubs = subs.length > 0;
  // 进度: 优先用后端已算好的 t.progress (= scripts/skein.py _task_pct, 卡片 spct 字段映射而来);
  // 缺失时按同一公式本地兜底 —— 阶段区间 + 完成度线性插值, 与后端逐值对齐 (skein.py:2468-2495)。
  const TASK_PCT_RANGE = { planning: [0, 5], ready: [5, 10], active: [10, 85], check: [85, 98] };
  // subtask 侧: subtable 只带 acc 清单、不带完成数 (无 "验收done" 字段), 拿不到逐项完成度,
  // 只能退化到状态区间中点 (与后端 _sub_pct 无验收清单时同构: (lo+hi)//2)。
  // 键含中文原值兜底: app.js STATUS_MAP 缺 '运行中'→'active' 映射, 归一化后仍可能是原始中文。
  const SUB_PCT_MID = {
    '待处理': 2, pending: 2, planning: 2,   // SS_PENDING (0,5) 中点
    '运行中': 50, running: 50, active: 50,  // SS_RUNNING (10,90) 中点
    '失败': 50, failed: 50,                  // SS_FAILED (10,90) 中点
  };
  const subPct = s => (s.status === 'done' || s.status === '已完成') ? 100 : (SUB_PCT_MID[s.status] ?? 2);
  const [tLo, tHi] = TASK_PCT_RANGE[st] || [0, 5];
  const progress = t.progress != null ? t.progress
    : st === 'done' ? 100
    : hasSubs ? Math.floor(tLo + (tHi - tLo) * (subs.reduce((a, s) =>
        a + (s.progress != null ? s.progress : subPct(s)), 0) / subs.length) / 100)
    : Math.floor((tLo + tHi) / 2);
  const popIcon = ST_ICON[st] || 'fa-cube';
  const prio = t.priority != null ? Number(t.priority) : 5;
  const prioIcon = prio >= 7 ? 'fa-arrow-up' : prio >= 4 ? 'fa-minus' : 'fa-arrow-down';

  return h('div.dag-popover', [
    h('div.dag-pop-inner', [
      // 头部: 图标 + 标题 + ID + 状态徽章
      h('div.dag-pop-header', [
        h(`div.dag-pop-icon.text-${ST_COLOR[st]}`, [h(`i.fa.${popIcon}`)]),
        h('div.dag-pop-title-group', [
          h('div.flex.items-center.gap-2.mb-1', [
            h('div.dag-pop-name.truncate.flex-1', t.title || t.name || '(未命名)'),
            h(`span.dag-pop-badge.${st}`, ST_LABEL[st] || st),
          ]),
          h('div.dag-pop-id', '#' + t.id),
        ]),
      ]),

      // 描述
      t.description
        ? h('div.dag-pop-desc', t.description)
        : null,

      // 进度条 + 子任务信息
      h('div.dag-pop-progress-section', [
        h('div.dag-pop-bar-wrap', [
          h(`div.dag-pop-bar.${st}`, [h('i', { style: { width: progress + '%' } })]),
          h('span.dag-pop-pct', progress + '%'),
        ]),
        hasSubs
          ? h('div.dag-pop-sub-info', [
              h('i.fa.fa-sitemap.text-xxs'),
              `子任务 ${subStats.done}/${subs.length} · 点击查看详情`,
            ])
          : null,
      ]),

      // 元信息行: 优先级 + 负责人
      h('div.dag-pop-meta-row', [
        h('span.dag-pop-meta-item.flex.items-center.gap-1', [
          h(`i.fa.${prioIcon}.${prioTextColor(prio)}.text-xs`),
          prioLabel(prio) + ` (${prio})`,
        ]),
        t.assignee
          ? h('span.dag-pop-meta-item.flex.items-center.gap-1', [
              h('i.fa.fa-user.text-muted.text-xs'),
              t.assignee,
            ])
          : null,
      ]),

      // 标签
      (t.tags && t.tags.length)
        ? h('div.dag-pop-tags',
            t.tags.slice(0, 4).map(tag => h('span.dag-pop-tag', '#' + tag))
              .concat(t.tags.length > 4 ? [h('span.dag-pop-tag', `+${t.tags.length - 4}`)] : [])
          )
        : null,

      // 依赖
      (t.deps && t.deps.length)
        ? h('div.dag-pop-deps', [
            h('span.dag-pop-deps-label', '依赖: '),
            h('div.dag-pop-deps-tags',
              t.deps.slice(0, 3).map(d => h('span', d.slice(0, 12)))
                .concat(t.deps.length > 3 ? [h('span', `+${t.deps.length - 3}`)] : [])
            ),
          ])
        : null,

      // 底部: 更新时间
      h('div.dag-pop-footer', [
        h('span.flex.items-center.gap-1.text-muted', [
          h('i.fa.fa-clock-o.text-xs'),
          t.updatedAt ? fmtRelative(t.updatedAt) : '—',
        ]),
      ]),
    ]),
  ]);
}

// ---- 子任务进度统计 ----
function getSubtaskStats(task) {
  const subs = task.subtasks || [];
  const total = subs.length;
  if (!total) return { total: 0, done: 0, active: 0, progress: 0 };
  let done = 0, active = 0;
  for (const s of subs) {
    const st = s.status || 'planning';
    if (st === 'done' || st === 'archived') done++;
    else if (st === 'active' || st === 'running') active++;
  }
  return { total, done, active, progress: Math.round((done / total) * 100) };
}

// ---- DAG 节点卡片 ----
// 分层排布下节点尺寸是布局的自变量 (行 = 依赖深度, 高度 = 层数 × 节点高), 所以卡面内容跟着档位走:
// compact 52px 放标题 + id/状态一行, mini 32px 只剩色点 + 标题。两档的详情都在 hover popover 里,
// 卡面少画几行不等于信息丢失。
function nodeCard(node, onClick, dimmed, density = 'compact') {
  const t = node.task;
  const st = t.status || 'planning';
  const subs = t.subtasks || [];
  const subStats = getSubtaskStats(t);
  const hasSubs = subs.length > 0;

  const mini = density === 'mini';
  // 淡化用 .is-dim 而非 tailwind .opacity-40: 后者作用在 wrap 上会把 ::before 的
  // 不透明底垫一起调淡, 连线立刻从卡片里透出来。CSS 里 .is-dim 只淡内层卡面。
  return h(`div.dag-node-wrap.absolute${dimmed ? ' is-dim' : ''}`,
    {
      'data-node-id': t.id,
      style: { left: node.x + 'px', top: node.y + 'px', width: node.w + 'px' },
    },
    [
      nodePopover(node),
      // 卡片本体高度锁定为 node.h — drawEdges 用 node.h 算端点中线, 内容撑高会让连线脱离卡片
      h(`div.dag-node.dag-node-${density}.glass-card.cursor-pointer.transition-all.overflow-hidden.flex.items-center.gap-2.st-${st}`,
        {
          onclick: (e) => { e.preventDefault(); onClick(t.id); },
          'data-task-id': t.id,
          style: { height: node.h + 'px' },
        },
        [
          h(`span.dag-dot.bg-${ST_COLOR[st]}`),
          h('div.flex-1.min-w-0', mini
            ? [h('div.text-xs.text-head.truncate.leading-none', t.title || t.name || t.id)]
            : [
                h('div.text-xs.font-semibold.text-head.truncate.leading-tight', t.title || t.name || '(未命名)'),
                h('div.flex.items-center.text-xxs.text-muted.leading-tight', [
                  h('span.font-mono.truncate', '#' + t.id),
                  hasSubs ? h('span.flex-shrink-0', `${subStats.done}/${subStats.total}`) : null,
                ]),
              ]),
        ]
      ),
    ]
  );
}

// ---- 视图切换 ----
function viewToggle(view, onChange) {
  return h('div.flex.items-center.gap-1.glass.rounded-lg.p-1.border', [
    h(`button.tab-btn.px-3.py-1.5.rounded-md.text-sm.font-medium${view === 'dag' ? ' active' : ''}`,
      { onclick: () => onChange('dag') },
      [h('i.fa.fa-sitemap.mr-1.5'), 'DAG']),
    h(`button.tab-btn.px-3.py-1.5.rounded-md.text-sm.font-medium${view === 'list' ? ' active' : ''}`,
      { onclick: () => onChange('list') },
      [h('i.fa.fa-list.mr-1.5'), '列表']),
  ]);
}

// ---- 状态多选筛选栏 ----
function statusFilterBar(statusSet, countBy, onChange) {
  const total = Object.values(countBy).reduce((a, b) => a + b, 0);
  const allSelected = ALL_STATUSES.every(s => statusSet.has(s));

  function toggle(st) {
    const next = new Set(statusSet);
    if (next.has(st)) next.delete(st); else next.add(st);
    onChange(next);
  }

  function selectAll() {
    if (allSelected) onChange(new Set(INCOMPLETE_STATUSES));
    else onChange(new Set(ALL_STATUSES));
  }

  return h('div.flex.items-center.gap-2.flex-wrap', [
    h(`button.filter-btn${allSelected ? ' active' : ''}`,
      { onclick: selectAll },
      `全部 (${total})`
    ),
    ...ALL_STATUSES.map(st =>
      h(`button.filter-btn.st-${st}${statusSet.has(st) ? ' active' : ''}`,
        { onclick: () => toggle(st) },
        `${ST_LABEL[st]} (${countBy[st] || 0})`
      )
    ),
  ]);
}

// ---- 列表视图 ----
function listView(tasks, onClick, statusSet) {
  const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
  return h('div.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
    ALL_STATUSES.map(st => {
      const list = tasks.filter(t => (t.status || 'planning') === st);
      const isDimmed = !allSelected && !statusSet.has(st);
      return h(`div.glass-card${isDimmed ? ' opacity-40' : ''}`, [
        h('div.flex.items-center.gap-2.mb-4', [
          h(`span.w-3.h-3.rounded-full.${ST_COLOR[st]}`),
          h('span.text-sm.font-semibold.text-head', ST_LABEL[st]),
          h('span.text-xs.text-muted.ml-auto', list.length),
        ]),
        h('div.space-y-2',
          list.length
            ? list.slice(0, 15).map(t =>
                h('div.subtask-row.flex.items-center.gap-2.p-2.rounded-lg.transition-colors.cursor-pointer',
                  { onclick: () => onClick(t.id) },
                  [
                    h(`i.fa.${ST_ICON[st]}.${ST_COLOR[st]}.text-xs`),
                    h('div.flex-1.min-w-0', [
                      h('div.text-sm.text-fg.truncate', t.title || t.name || '(未命名)'),
                      h('div.text-xs.text-muted.font-mono.truncate', '#' + t.id),
                    ]),
                  ]
                )
              )
            : [h('div.py-6.text-center.text-xs.text-muted', '暂无')]
        ),
      ]);
    })
  );
}

// ---- 时间线 (buildTimeline 见 app.js, 与 task 详情页共用) ----

function timelineView(stages, task) {
  if (!stages || !stages.length) {
    return h('div.py-6.text-center.text-muted.text-sm', '暂无活动记录');
  }
  return h('div.tl-axis',
    stages.map((s, i) => {
      const stateClass = s.done ? 'done' : s.current ? 'cur' : '';
      const stClass = s.done ? 'done' : s.current ? 'cur' : 'pending';
      const stLabel = s.done ? '已完成' : s.current ? '当前' : '待执行';
      const dotStyle = (s.done || s.current) ? `--tl-c:${s.color}` : '';
      const stStyle = s.current ? `--tl-c:${s.color};--tl-c-bg:${s.color}26` : '';
      const timeStr = s.time ? fmtTime(s.time) : '—';

      // 子任务计数
      const subs = task && task.subtasks ? task.subtasks : [];
      let extraInfo = '';
      if (s.key === 'started' && subs.length) {
        const done = subs.filter(x => x.status === 'done').length;
        extraInfo = `${done}/${subs.length} 子任务`;
      }

      return h(`div.tl-node${stateClass ? '.' + stateClass : ''}`, [
        h(`span.tl-dot${stateClass ? '.' + stateClass : ''}`, { style: dotStyle }),
        h('div.flex.items-center.gap-2.mb-1', [
          h('span.tl-name', s.label),
          h(`span.tl-st.${stClass}`, { style: stStyle }, stLabel),
        ]),
        h('div.flex.items-center.gap-3', [
          h('span.tl-time', timeStr),
          extraInfo ? h('span.tl-dur', extraInfo) : null,
        ]),
        h('div.tl-desc', s.desc),
        s.key === 'started' && subs.length ? subTimelineView(subs) : null,
      ]);
    })
  );
}

// ---- 子任务 DAG 迷你视图 ----
function subDAGView(subs, onSubClick) {
  const { nodes, edges, width, height } = layoutSubDAG(subs);
  if (!nodes.length) return h('div.py-4.text-center.text-xs.text-muted', '暂无子任务');

  return h('div.sub-dag-wrap.overflow-auto', [
    h('div.relative',
      { style: { width: width + 'px', height: height + 'px', minWidth: '100%' } },
      [
        drawEdges(edges),
        ...nodes.map((n) => {
          const sst = n.sub.status || 'planning';
          // 已完成的子任务仍要渲染 (整条链路完整可读), 只降视觉权重 (.is-done 灰显), 不隐藏。
          return h(`div.sub-dag-node.absolute.flex.items-center.gap-2.px-2.py-1.rounded.border.bg-card/60.cursor-pointer.hover\\:bg-card.transition-colors.${ST_COLOR[sst]}${sst === 'done' ? '.is-done' : ''}`,
            {
              style: { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h + 'px' },
              onclick: (e) => { e.stopPropagation(); if (onSubClick) onSubClick(n.id); },
              'data-sub-id': n.id,
              title: n.sub.title || n.sub.name || n.id,
            },
            [
              h(`span.w-2.h-2.rounded-full.flex-shrink-0.bg-${ST_COLOR[sst]}`),
              h('span.text-xs.text-fg.truncate.flex-1', n.sub.title || n.sub.name || n.id),
            ]
          );
        }),
      ]
    ),
  ]);
}

// ---- PRD 章节渲染 ----
function prdSectionView(prd) {
  if (!prd || !prd.length) return null;
  return prd.map(sec => renderPrdCard(sec));
}
function prdGoalsView(prd) {
  if (!prd || !prd.length) return null;
  const sec = prd.find(s => s.name === '目标');
  if (!sec) return null;
  return [renderPrdCard(sec)];
}
function prdAcceptanceView(prd) {
  if (!prd || !prd.length) return null;
  const sec = prd.find(s => s.name === '验收标准');
  if (!sec) return null;
  return [renderPrdCard(sec)];
}
function renderPrdCard(sec) {
  const icon = sec.name === '目标' ? 'fa-bullseye' : sec.name === '验收标准' ? 'fa-check-square-o' : 'fa-file-text-o';
  const color = sec.name === '目标' ? 'st-planning' : sec.name === '验收标准' ? 'st-check' : 'st-active';
  return h('div.glass-card.p-4', [
    h('div.flex.items-center.gap-2.mb-3', [
      h(`i.fa.${icon}.text-${color}.text-sm`),
      h('div.section-title.text-accent.m-0',
        sec.name + (sec.badge ? ` (${sec.badge[0]}/${sec.badge[1]})` : '')
      ),
    ]),
    sec.items && sec.items.length
      ? h('div.space-y-1.5',
          sec.items.map(item =>
            h('div.flex.items-start.gap-2.text-sm', [
              item.kind === 'check'
                ? h(`i.fa.${item.done ? 'fa-check-square' : 'fa-square-o'}.${item.done ? 'text-st-done' : 'text-muted'}.mt-0.5.flex-shrink-0`)
                : h('span.w-1.h-1.rounded-full.bg-muted.mt-2.flex-shrink-0'),
              h('span.text-fg' + (item.done ? '.line-through.text-muted' : ''), item.text),
            ])
          )
        )
      : h('p.text-sm.text-muted', '—'),
  ]);
}

// ---- 契约章节 ----
function contractsView(contracts) {
  if (!contracts || !contracts.length) return null;
  return h('div.glass-card.p-4', [
    h('div.flex.items-center.gap-2.mb-3', [
      h('i.fa.fa-handshake-o.text-st-check.text-sm'),
      h('div.section-title.text-accent.m-0', `契约 (${contracts.length})`),
    ]),
    h('div.space-y-2',
      contracts.map((c, i) =>
        h('div.p-2.rounded.border', [
          // 契约落盘为字符串 (skein contract --add); 对象形态仅作兼容
          h('div.text-sm.font-medium.text-head.leading-relaxed',
            typeof c === 'string' ? c : (c.name || c.title || `契约 ${i + 1}`)),
          typeof c !== 'string' && (c.desc || c.description)
            ? h('div.text-xs.text-muted.mt-1', c.desc || c.description) : null,
        ])
      )
    ),
  ]);
}

// ---- 详细设计章节 ----
function designView(design) {
  if (!design) return null;
  // 截取前 500 字符做预览, 点击展开
  const preview = design.length > 500 ? design.slice(0, 500) + '...' : design;
  return h('div.glass-card.p-4', [
    h('div.flex.items-center.gap-2.mb-3', [
      h('i.fa.fa-sitemap.text-st-active.text-sm'),
      h('div.section-title.text-accent.m-0', '详细设计'),
    ]),
    h('pre.text-xs.text-fg.whitespace-pre-wrap.font-mono.p-3.rounded.overflow-x-auto', preview),
  ]);
}

// ---- 右侧详情面板 (仅当有选中任务时显示) ----
function detailPanel(task, allTasks, onClose, onSubClick, onOpenDetail, onTaskClick, onDelete) {
  if (!task) return null;

  const st = task.status || 'planning';
  const timeline = buildTimeline(task);

  return h('aside.detail-panel', [
    // 头部
    h('div.detail-panel-header', [
      h('div.flex-1.min-w-0', [
        h('div.flex.items-center.gap-2.mb-1', [
          h(`span.badge.badge-sm.${ST_COLOR[st]}`, ST_LABEL[st] || st),
          h('span.text-xs.text-muted.font-mono', '#' + task.id),
        ]),
        h('h3.text-lg.font-semibold.text-head.truncate', task.title || task.name || '(未命名)'),
      ]),
      h('div.flex.items-center.gap-1', [
        h('button.detail-panel-close',
          { onclick: () => { if (onOpenDetail) onOpenDetail(task.id); },
            title: '打开详情页' },
          h('i.fa.fa-external-link')
        ),
        h('button.detail-panel-close.is-danger',
          { onclick: () => { if (onDelete) onDelete(task); }, title: '删除任务 (软删进 .skein/trash/)' },
          h('i.fa.fa-times-circle')   // fa 子集无 trash 字形, 复用已有字形免重生成 woff2
        ),
        h('button.detail-panel-close',
          { onclick: onClose, title: '关闭' },
          h('i.fa.fa-times')
        ),
      ]),
    ]),

    // 正文
    h('div.detail-panel-body', [
      // 顶部信息区: 紧凑横向排列
      h('div.detail-info-row', [
        // 1. 基本信息
        h('div.glass-card.p-4', [
          h('div.section-title.text-accent.mb-3', '基本信息'),
          infoRow('优先级', prioLabel(task.priority) + ` (${task.priority != null ? Number(task.priority) : 5})`),
          task.assignee ? infoRow('负责人', task.assignee) : null,
          infoRow('预估工时', task.estimate ? task.estimate + ' h' : '—'),
          infoRow('进度', task.progress != null ? task.progress + '%' : (st === 'done' ? '100%' : '—')),
        ]),
        // 2. 任务描述
        h('div.glass-card.p-4', [
          h('div.section-title.text-accent.mb-2', '任务描述'),
          h('p.text-sm.text-fg.whitespace-pre-wrap', task.description || task.desc || '暂无描述'),
        ]),
        // 3. 目标
        ...(prdGoalsView(task.prd) || []),
        // 4. 验收标准
        ...(prdAcceptanceView(task.prd) || []),
        // 5. 契约
        contractsView(task.contracts),
      ]),

      // 依赖 DAG 图（上下游 + 可拖拽）— 仅当有依赖时显示，跨全宽, 提到子任务 DAG 之前
      (() => {
        const { nodes } = buildDepDAG(task.id, allTasks);
        if (nodes.length <= 1) return null;
        return h('div.glass-card.p-4.panel-span-2', [
          h('div.flex.items-center.gap-2.mb-3', [
            h('i.fa.fa-share-alt.text-st-active.text-sm'),
            h('div.section-title.text-accent.m-0', `依赖关系图 (${nodes.length})`),
          ]),
          depDAGView(task, allTasks, onTaskClick),
        ]);
      })(),

      // 子任务 DAG — 跨全宽
      task.subtasks && task.subtasks.length >= 2
        ? h('div.glass-card.p-4.panel-span-2', [
            h('div.section-title.text-accent.mb-3', `子任务 DAG (${task.subtasks.length})`),
            subDAGView(task.subtasks, onSubClick),
          ])
        : null,

      // 详细设计 — 跨全宽
      task.docs && task.docs.design ? h('div.panel-span-2', designView(task.docs.design)) : null,

      // 时间线 — 跨全宽
      h('div.glass-card.p-4.panel-span-2', [
        h('div.section-title.text-accent.mb-3', '生命周期时间线'),
        timelineView(timeline, task),
      ]),
    ]),
  ]);
}

function infoRow(label, value) {
  return h('div.flex.gap-3.py-2', [
    h('span.text-sm.text-muted.w-20.flex-shrink-0', label),
    h('div.text-sm.text-fg.flex-1', value || '—'),
  ]);
}

// 进页视口对准「正在执行」的 task。优先级取最能代表当前战线的状态; 都没有就退到第一张卡。
function focusActive(wrap, nodes) {
  const FOCUS_ORDER = ['active', 'check', 'ready', 'planning', 'done'];
  if (!nodes.length) return;
  const target = FOCUS_ORDER.reduce((hit, st) =>
    hit || nodes.find(n => n.task && n.task.status === st), null) || nodes[0];
  wrap.scrollTo({
    left: Math.max(0, target.x + target.w / 2 - wrap.clientWidth / 2),
    top: Math.max(0, target.y + target.h / 2 - wrap.clientHeight / 2),
    behavior: 'auto',
  });
}

// ---- 主渲染 ----
export async function render(mount, params, ctx) {
  const resp = await api.data().catch(() => null);
  const allTasks = normalizeTasks((resp && resp.cards) || []);

  const q = params.query || {};

  // 从 URL 解析初始状态
  let view = q.view === 'list' ? 'list' : 'dag';
  let statusSet;
  if (q.status) {
    const arr = q.status.split(',').filter(s => ALL_STATUSES.includes(s.trim()));
    statusSet = new Set(arr.length ? arr : DEFAULT_FILTER);
  } else {
    statusSet = new Set(DEFAULT_FILTER);
  }
  let selectedId = null;
  let scale = 1;
  let focusedOnce = false;

  // 状态计数 — draw() 内每次重算 (原地 patch 后 allTasks 状态可能变, 计数不能只算一次)
  let countBy = {};
  // 当前一轮 DAG 布局结果缓存, 增量 patch (patchDagNode/patchEdgesFor) 靠它定位节点/边, 不用重新 layout
  let curNodes = [], curEdges = [], curDensity = 'compact';

  function selectTask(id) {
    selectedId = id;
    draw();
  }

  function closePanel() {
    selectedId = null;
    draw();
  }

  function setFilter(set) {
    statusSet = set;
    const arr = ALL_STATUSES.filter(s => set.has(s));
    const isDefault = arr.length === DEFAULT_FILTER.size && [...DEFAULT_FILTER].every(s => set.has(s));
    if (ctx && ctx.setQuery) {
      ctx.setQuery({ status: isDefault ? null : arr.join(',') });
    }
    draw();
  }

  function setView(v) {
    view = v;
    if (ctx && ctx.setQuery) {
      ctx.setQuery({ view: v === 'dag' ? null : v });
    }
    draw();
  }

  // 清理已完成: 归档是可逆的 (进 archive/, 归档页可查), 但仍二次确认再执行
  async function cleanDone() {
    const yes = await confirmDialog({
      title: '清理已完成任务',
      message: `将归档全部 ${countBy.done} 个已完成任务 (等价 skein clean --days=0)。\n归档可逆 — 归档页仍可查回。`,
      ok: '归档',
    });
    if (!yes) return;
    try {
      const r = await api.exec('clean', { days: 0 });
      if (!r || !r.ok) throw new Error((r && (r.stderr || r.error)) || '清理失败');
    } catch (e) {
      await alertDialog('清理失败: ' + (e && e.message ? e.message : e), '清理失败');
      return;
    }
    await render(mount, params, ctx);  // 重拉 /data 重绘 (计数/DAG 全变)
  }

  // 删除任务: 软删进 .skein/trash/ (skein del), 可从 trash 恢复
  async function deleteTask(t) {
    const yes = await confirmDialog({
      title: '删除任务',
      message: `删除任务 #${t.id} ${t.title || t.name || ''}?\n软删进 .skein/trash/, 可从磁盘恢复; 在途 task 的 worktree/分支会一并销毁。`,
      ok: '删除',
      danger: true,
    });
    if (!yes) return;
    try {
      const r = await api.exec('del', { id: t.id });
      if (!r || !r.ok) throw new Error((r && (r.stderr || r.error)) || '删除失败');
    } catch (e) {
      await alertDialog('删除失败: ' + (e && e.message ? e.message : e), '删除失败');
      return;
    }
    selectedId = null;  // 面板里删的就是当前选中项, 关掉再重绘
    await render(mount, params, ctx);
  }

  function onSubClick(sid) {
    // 子任务点击: 可以高亮/展开, 暂仅打 log
    console.log('subtask clicked:', sid);
  }

  function openDetailPage(id) {
    if (ctx && ctx.navigate) {
      ctx.navigate('/task/detail?id=' + encodeURIComponent(id));
    }
  }

  // 节点档位: 小/中/大三档, 默认中号(compact); 用户切过一次就记住 (localStorage), 换页/刷新不用重切
  let densityPref = 'compact';
  try {
    const v = localStorage.getItem('skein.dag.density');
    if (v === 'mini' || v === 'compact' || v === 'large') densityPref = v;
  } catch (_) { /* 隐私模式禁 localStorage */ }
  function setDensity(d) {
    densityPref = d;
    try { localStorage.setItem('skein.dag.density', d); } catch (_) { /* 同上 */ }
    draw();
  }
  // 布局用的可用画布尺寸 — 每次 draw 后按真实 DOM 校正, 详情面板开合 / 窗口缩放都会改到它
  let viewBox = { w: Math.max(400, window.innerWidth - 80), h: Math.max(600, window.innerHeight - 260) };
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(draw, 150);
  });

  // ---- DAG 抓手拖拽 ----
  // 拖的是容器滚动位置, 不是 transform — 画布宽度已被布局钳进容器, 纵向靠滚动条,
  // 再叠 translate 会和滚动条打架 (拖出去的部分滚动条够不着)
  function initDrag(dagEdges = []) {
    const wrap = document.getElementById('board-dag-wrap');
    const canvas = wrap ? wrap.querySelector('.dag-canvas') : null;
    if (!wrap || !canvas || view !== 'dag') return;

    let isDragging = false;
    let startX = 0, startY = 0;
    let startSL = 0, startST = 0;

    function onMouseMove(e) {
      if (!isDragging) return;
      wrap.scrollLeft = startSL - (e.clientX - startX);
      wrap.scrollTop = startST - (e.clientY - startY);
    }
    function onMouseUp() {
      isDragging = false;
      wrap.style.cursor = 'grab';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    }
    function onMouseDown(e) {
      if (e.target.closest('.dag-node-wrap, .sub-dag-node, button, a, input, textarea, select')) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startSL = wrap.scrollLeft;
      startST = wrap.scrollTop;
      wrap.style.cursor = 'grabbing';
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
      e.preventDefault();
    }

    function onTouchMove(e) {
      if (!isDragging || e.touches.length !== 1) return;
      wrap.scrollLeft = startSL - (e.touches[0].clientX - startX);
      wrap.scrollTop = startST - (e.touches[0].clientY - startY);
    }
    function onTouchEnd() {
      isDragging = false;
      wrap.removeEventListener('touchmove', onTouchMove);
      wrap.removeEventListener('touchend', onTouchEnd);
    }
    function onTouchStart(e) {
      if (e.target.closest('.dag-node-wrap, .sub-dag-node, button, a, input, textarea, select')) return;
      if (e.touches.length !== 1) return;
      isDragging = true;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      startSL = wrap.scrollLeft;
      startST = wrap.scrollTop;
      wrap.addEventListener('touchmove', onTouchMove, { passive: true });
      wrap.addEventListener('touchend', onTouchEnd);
    }

    wrap.style.cursor = 'grab';
    wrap.addEventListener('mousedown', onMouseDown);
    wrap.addEventListener('touchstart', onTouchStart, { passive: true });

    // hover card 高亮整条链路 (该节点 + 全部上游 + 全部下游, 传递闭包) 的节点与连线, 其余降透明
    const edgesSvg = canvas.querySelector('.dag-edges');
    if (edgesSvg) {
      // 双向邻接表 (一次建好, 每次 hover 只跑 BFS)
      const succ = new Map(), pred = new Map();
      for (const e of dagEdges) {
        if (!succ.has(e.from.id)) succ.set(e.from.id, []);
        if (!pred.has(e.to.id)) pred.set(e.to.id, []);
        succ.get(e.from.id).push(e.to.id);
        pred.get(e.to.id).push(e.from.id);
      }
      function chainOf(id) {
        const seen = new Set([id]);
        for (const adj of [succ, pred]) {
          const queue = [id];
          while (queue.length) {
            for (const nx of adj.get(queue.shift()) || []) {
              if (seen.has(nx)) continue;
              seen.add(nx);
              queue.push(nx);
            }
          }
        }
        return seen;
      }
      const cards = () => canvas.querySelectorAll('.dag-node-wrap');
      function applyChain(chain) {
        cards().forEach(c => {
          const inChain = chain && chain.has(c.getAttribute('data-node-id'));
          c.classList.toggle('chain-active', !!inChain);
          c.classList.toggle('chain-dim', !!chain && !inChain);
        });
        edgesSvg.querySelectorAll('.dag-edge').forEach(p => {
          // 边在链路内 = 两端都在链路内
          const hit = chain && chain.has(p.getAttribute('data-from')) && chain.has(p.getAttribute('data-to'));
          p.classList.toggle('edge-active', !!hit);
          p.style.strokeOpacity = chain ? (hit ? '0.95' : '0.1') : '';
        });
      }
      canvas.addEventListener('mouseover', (e) => {
        // 只认外层 task 卡片 — 子 DAG 节点 id 不在 task 邻接表内, 命中它会把整图误暗
        const card = e.target.closest('.dag-node-wrap');
        const tid = card ? card.getAttribute('data-node-id') : null;
        applyChain(tid ? chainOf(tid) : null);
      });
      canvas.addEventListener('mouseout', (e) => {
        if (!e.relatedTarget || !canvas.contains(e.relatedTarget)) applyChain(null);
      });
    }
  }

  function draw() {
    countBy = {};
    for (const t of allTasks) countBy[t.status] = (countBy[t.status] || 0) + 1;
    const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
    const lay = layoutDAG(allTasks, viewBox, densityPref);
    const { nodes, edges, width, height } = lay;
    curNodes = nodes; curEdges = edges; curDensity = lay.density;
    const selectedTask = allTasks.find(t => t.id === selectedId) || null;
    const hasPanel = !!selectedTask;
    const highlightedCount = allTasks.filter(t => statusSet.has(t.status)).length;

    mount.replaceChildren(
      // 标题行 (标题 / 状态筛选 / 缩放 / 视图切换 同一行)
      h('div.board-head.flex.items-center.mb-4.flex-wrap.gap-3', [
        h('div.flex-shrink-0', [
          h('h1.text-2xl.font-bold.text-head.mb-0\\.5', '任务看板'),
          h('p.text-muted.text-xs', `${allTasks.length} 个任务 · ${highlightedCount} 个高亮`),
        ]),
        h('div.flex-1.min-w-0', statusFilterBar(statusSet, countBy, setFilter)),
        h('div.flex.items-center.gap-3.flex-shrink-0', [
          view === 'dag' ? h('div.flex.items-center.gap-1.glass.rounded-lg.p-1.border', [
            h(`button.px-2.py-1.rounded-md.text-sm.transition-colors.${curDensity === 'mini' ? 'text-accent' : 'text-muted'}.hover\\:text-accent`,
              { onclick: () => setDensity('mini'), title: '切到迷你节点' },
              h('i.fa.fa-th')),
            h(`button.px-2.py-1.rounded-md.text-sm.transition-colors.${curDensity === 'compact' ? 'text-accent' : 'text-muted'}.hover\\:text-accent`,
              { onclick: () => setDensity('compact'), title: '切到中号节点' },
              h('i.fa.fa-th-large')),
            h(`button.px-2.py-1.rounded-md.text-sm.transition-colors.${curDensity === 'large' ? 'text-accent' : 'text-muted'}.hover\\:text-accent`,
              { onclick: () => setDensity('large'), title: '切到大号节点' },
              h('i.fa.fa-square-o')),
            h('span.w-px.h-4.bg-brd/60.mx-1'),
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = Math.min(scale + 0.1, 2); draw(); }, title: '放大' },
              h('i.fa.fa-search-plus')),
            h('span.text-xs.text-muted.px-1', Math.round(scale * 100) + '%'),
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = Math.max(scale - 0.1, 0.3); draw(); }, title: '缩小' },
              h('i.fa.fa-search-minus')),
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = 1; const wp = document.getElementById('board-dag-wrap'); if (wp) wp.scrollTo(0, 0); draw(); }, title: '重置' },
              h('i.fa.fa-expand')),
          ]) : null,
          // 清理已完成 = skein clean --days=0 (归档到 archive/, 可在归档页查回); 无完成 task 时不显示
          countBy.done ? h('button.filter-btn.st-done',
            { onclick: cleanDone, title: '归档全部已完成任务 (等价 skein clean --days=0)' },
            [h('i.fa.fa-archive.mr-1.5'), `清理已完成 (${countBy.done})`]) : null,
          viewToggle(view, setView),
        ]),
      ]),

      // 主内容区: 左 DAG/列表 + (可选) 右详情
      h(`div.board-main.glass-card${hasPanel ? ' has-panel' : ''}`, {
        id: 'board-main',
        style: view === 'dag' ? { height: 'calc(100vh - 200px)' } : null,
      }, [
        // 左侧: DAG/列表 (高度由下面 rAF 锁在 .board-main 上, 内部自己滚)
        h('div.flex-1.board-dag-wrap', { id: 'board-dag-wrap' },
          view === 'dag'
            ? [
                h('div.dag-canvas.relative',
                  {
                    style: {
                      width: width + 'px',
                      height: height + 'px',
                      minWidth: '100%',
                      transform: `scale(${scale})`,
                      'transform-origin': 'top left',
                    },
                  },
                  [
                    drawEdges(edges, (e) => {
                      const fromSt = e.from.task ? e.from.task.status : 'planning';
                      const toSt = e.to.task ? e.to.task.status : 'planning';
                      return { dimmed: !(statusSet.has(fromSt) && statusSet.has(toSt)) };
                    }),
                    ...nodes.map(n => nodeCard(n, selectTask, !statusSet.has(n.task.status), curDensity)),
                  ]
                ),
              ]
            : [listView(allTasks, selectTask, statusSet)]
        ),
        // 右侧: 详情面板 (仅选中时显示)
        hasPanel ? detailPanel(selectedTask, allTasks, closePanel, onSubClick, openDetailPage, selectTask, deleteTask) : null,
        // 连线图例 (浮在画布区左下角, 不随画布滚动)
        view === 'dag' ? edgeLegend() : null,
      ]),
    );
    setTimeout(() => initDrag(edges), 0);
    requestAnimationFrame(() => {
      const wrap = document.getElementById('board-dag-wrap');
      const main = document.getElementById('board-main');
      if (!wrap || !main || view !== 'dag') return;
      // 高度锁在 .board-main 上, 画布区和详情面板都 100% 跟它 —— 谁都别把页面撑出滚动条。
      // 按它在视口里的真实起点精算, 正好吃满剩余空间。
      const top = main.getBoundingClientRect().top;
      main.style.height = Math.max(320, window.innerHeight - top - 20) + 'px';
      // 还剩滚动余量 (外层 padding/margin) 就再扣掉 — 滚动条只该长在画布区和面板里
      const de = document.documentElement;
      const spill = de.scrollHeight - de.clientHeight;
      if (spill > 0) main.style.height = Math.max(320, main.clientHeight - spill) + 'px';
      // 宽度校正后重排 — 宽度是布局硬约束, 面板开合会改它; 差值收敛到 40px 内即停
      const w = wrap.clientWidth;
      if (w > 100 && Math.abs(w - viewBox.w) > 40) {
        viewBox = { w, h: wrap.clientHeight };
        draw();
        return;
      }
      // 布局稳定后, 首次进页把视口对准正在执行的 task (画布高达数千 px, 从左上角开始等于什么都没看到)
      if (!focusedOnce) {
        focusedOnce = true;
        focusActive(wrap, nodes);
      }
    });
  }

  // ---- WS 增量: 单卡片/DAG 节点原地 patch, 不整树重绘 (选中态/滚动/档位/面板开合都保) ----
  const escId = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/[^a-zA-Z0-9_-]/g, '\\$&'));

  function patchEdgesFor(id) {
    const svg = document.querySelector('#board-dag-wrap .dag-edges');
    if (!svg || !curEdges.length) return;
    const kindOf = edgeKinds(curEdges);
    for (const e of curEdges) {
      if (e.from.id !== id && e.to.id !== id) continue;
      const path = svg.querySelector(`path[data-from="${escId(e.from.id)}"][data-to="${escId(e.to.id)}"]`);
      if (!path) continue;
      const k = kindOf(e);
      path.setAttribute('stroke', `var(--${EDGE_KIND[k].color})`);
      path.setAttribute('marker-end', `url(#arrow-${k})`);
      // ponytail: 新 kind 对应的 <marker> defs 里可能没有 (罕见: 该图历来只出现过 1-2 种边语义),
      // 缺失时箭头会不显示但不报错, 比为这种小概率整树重绘划算。
    }
  }

  function patchDagNode(id) {
    const node = curNodes.find(n => n.id === id);
    const wrap = document.querySelector(`.dag-node-wrap[data-node-id="${escId(id)}"]`);
    if (!node || !wrap) { draw(); return; }  // 布局里找不到 (罕见结构漂移) → 兜底整绘
    const dimmed = !statusSet.has(node.task.status || 'planning');
    wrap.replaceWith(nodeCard(node, selectTask, dimmed, curDensity));
    patchEdgesFor(id);
  }

  function patchPanel(id) {
    const aside = document.querySelector('.detail-panel');
    if (!aside) return;
    const body = aside.querySelector('.detail-panel-body');
    const scrollTop = body ? body.scrollTop : 0;
    const t = allTasks.find(x => x.id === id);
    const fresh = detailPanel(t, allTasks, closePanel, onSubClick, openDetailPage, selectTask, deleteTask);
    aside.replaceWith(fresh);
    const freshBody = fresh.querySelector('.detail-panel-body');
    if (freshBody) freshBody.scrollTop = scrollTop;
  }

  function applyCardDelta(id, cardData) {
    const idx = allTasks.findIndex(t => t.id === id);
    if (cardData == null) {                          // 后端摘除的 task (删除/归档)
      if (idx === -1) return;
      allTasks.splice(idx, 1);
      if (selectedId === id) selectedId = null;       // 面板正显示它才关, 显示别的 task 不受影响
      draw();
      return;
    }
    const norm = normalizeTask(cardData);
    if (idx === -1) {                                 // 新 task 出现 — 结构性, 走整绘
      allTasks.push(norm);
      draw();
      return;
    }
    Object.assign(allTasks[idx], norm);                // 原地更新, 保对象引用 (selectedTask 闭包不失效)
    if (view === 'dag') {
      patchDagNode(id);
      if (selectedId === id) patchPanel(id);
    } else {
      draw();  // list 视图按状态分列, 状态变=换列, 当结构性处理 (selectedId/statusSet 仍经闭包原样保留)
    }
  }

  if (ctx && ctx.onLive) {
    ctx.onLive((msg) => {
      if (!msg || msg.type !== 'task-changed' || !msg.id) return;
      applyCardDelta(msg.id, msg.card);
    });
  }

  draw();
}
