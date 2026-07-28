// ============================================================
//  depdag — 依赖关系图 (以任一 task 为中心的上下游) + 通用 DAG 连线渲染
//  从 board.js 抽出: board 详情面板 / task 详情页共用同一份图与连线绘制。
// ============================================================

import { h } from '../app.js';

const ST_COLOR = {
  planning: 'st-planning', ready: 'st-ready',
  active:   'st-active',  check: 'st-check',
  done:     'st-done',    failed: 'st-failed',
};
// 连线语义 (边 from→to 表示 "to 依赖 from", from 是被依赖方)
const EDGE_KIND = {
  ready:   { color: 'st-done',   label: '依赖已完成' },
  blocked: { color: 'st-active', label: '阻塞 · 上游可执行' },
  stuck:   { color: 'st-failed', label: '阻塞 · 上游被卡' },
};

// 边捆绑: 扇入 ≥3 的跨行长边合流到一条主干竖线 (目标卡左侧的列间通道)。
// m8-version 扇入 31, 各走各的通道就是 31 根贯穿全高的竖线; 合流成 1 根既清爽,
// 也直接读出「这一束都通向同一个节点」。主干 x 不过 chan() —— 错开就散了, 合流全靠共用同一 x。
// 同行/相邻的短边不参与: 它们本来就一格到位, 绕主干反而更长。
function bundleTrunks(edges) {
  const byTo = new Map();
  for (const e of edges) {
    if (e.cross || Math.abs(e.to.y - e.from.y) <= (e.from.rowH || e.from.h)) continue;
    if (!byTo.has(e.to.id)) byTo.set(e.to.id, []);
    byTo.get(e.to.id).push(e);
  }
  const trunks = new Map();
  for (const [id, group] of byTo) {
    if (group.length >= 3) trunks.set(id, { x: group[0].to.x - 16, set: new Set(group) });
  }
  return trunks;
}

// 正交折点 → 圆角直角 path。相邻点必须共享 x 或 y (每段纯横或纯竖), 退化点直接丢。
function orthPath(raw) {
  const pts = [];
  for (const p of raw) {
    const last = pts[pts.length - 1];
    if (last && Math.abs(last.x - p.x) < 0.5 && Math.abs(last.y - p.y) < 0.5) continue;
    pts.push(p);
  }
  if (pts.length < 2) return '';
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const pv = pts[i - 1], p = pts[i], nx = pts[i + 1];
    const inLen = Math.abs(p.x - pv.x) + Math.abs(p.y - pv.y);
    const outLen = Math.abs(nx.x - p.x) + Math.abs(nx.y - p.y);
    const r = Math.min(10, inLen / 2, outLen / 2);
    d += ` L ${p.x - Math.sign(p.x - pv.x) * r} ${p.y - Math.sign(p.y - pv.y) * r}`;
    d += ` Q ${p.x} ${p.y} ${p.x + Math.sign(nx.x - p.x) * r} ${p.y + Math.sign(nx.y - p.y) * r}`;
  }
  const end = pts[pts.length - 1];
  return d + ` L ${end.x} ${end.y}`;
}

// ---- 边语义判定 ----
// from 是被依赖方: done → 依赖已满足 (绿); 未 done 且 from 自己的依赖全 done → from 现在就能跑 (黄);
// from 自己也有未完成依赖 → 这条链短期解不开 (红)。图外的 id 视为已满足 (被筛掉的基本是 done)。
function edgeKinds(edges) {
  const item = new Map();
  for (const e of edges) for (const n of [e.from, e.to]) item.set(n.id, n.task || n.sub || {});
  const stOf = (id) => (item.has(id) ? (item.get(id).status || 'planning') : 'done');
  return (e) => {
    if (stOf(e.from.id) === 'done') return 'ready';
    const f = item.get(e.from.id) || {};
    const deps = f.deps || f.dependsOn || [];
    return deps.every(d => stOf(d) === 'done') ? 'blocked' : 'stuck';
  };
}

// ---- 连线图例 ----
function edgeLegend() {
  const line = (color, dashed) => h('svg', { width: '26', height: '10', 'aria-hidden': 'true' }, [
    h('path', {
      d: 'M 1 5 L 25 5', fill: 'none', stroke: `var(--${color})`,
      'stroke-width': '2', 'stroke-dasharray': dashed ? '4 3' : null,
    }),
  ]);
  return h('div.dag-legend', [
    ...Object.entries(EDGE_KIND).map(([, v]) =>
      h('span.dag-legend-item', [line(v.color, false), v.label])),
    // 虚线只表"跨行回绕", 线色仍是上面三种语义色 — 别让人以为虚线自成一色
    h('span.dag-legend-item', [line('muted', true), '虚线 = 跨行回绕 (颜色含义同上)']),
  ]);
}

// ---- SVG 连线 ----
// 起止点贴 card 边缘: from 右边中 → to 左边中 (水平流向)。
// 箭头 marker 标方向 (谁→谁); hover card 时高亮其连线 (edge-highlight class)。
function drawEdges(edges, getEdgeInfo) {
  if (!edges.length) return null;

  const kindOf = edgeKinds(edges);

  // 每种边语义一个箭头 marker (同色), id 去重
  const usedKinds = new Set();
  const markers = [];
  for (const e of edges) {
    const k = kindOf(e);
    if (usedKinds.has(k)) continue;
    usedKinds.add(k);
    markers.push(h('marker',
      { id: `arrow-${k}`, viewBox: '0 0 10 10', refX: '9', refY: '5',
        markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse' },
      [h('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: `var(--${EDGE_KIND[k].color})` })]
    ));
  }

  // 通道分配: 竖直段挤在列间空隙里, 同一空隙的多条边互相让开几像素 (电路板走线)
  const lanes = new Map();
  const chan = (v, axis) => {
    const k = axis + Math.round(v / 10);
    const n = lanes.get(k) || 0;
    lanes.set(k, n + 1);
    return v + (n % 5) * 7 - 14;
  };
  const trunks = bundleTrunks(edges);
  const paths = edges.map(e => {
    const trunk = trunks.get(e.to.id);
    const bundled = !!trunk && trunk.set.has(e);
    // 竖排分量 (layoutComponent 选了 TB) 的边: 走上下边; 横排走左右边
    const vert = !bundled
      && Math.abs(e.to.x - e.from.x) < e.from.w && e.to.y > e.from.y + e.from.h / 2;
    // 出入边按相对位置选, 不能写死「右沿出、左沿进」—— 蛇形行序下近一半的边是右→左,
    // 写死会让首段从右沿往回穿过源卡自己。线只许从边缘朝外起步、朝内收尾。
    const bx = bundled ? trunk.x : e.to.x + e.to.w / 2;
    const rightward = bx >= e.from.x + e.from.w / 2;    // 去向在源的右边?
    const downward = e.to.y >= e.from.y;
    // 起止点贴 card 边缘; marker 自带尺寸故终点贴边即可
    const x1 = vert ? e.from.x + e.from.w / 2 : (rightward ? e.from.x + e.from.w : e.from.x);
    const y1 = vert ? (downward ? e.from.y + e.from.h : e.from.y) : e.from.y + e.from.h / 2;
    const x2 = vert ? e.to.x + e.to.w / 2
      : (bundled || rightward ? e.to.x : e.to.x + e.to.w);
    const y2 = vert ? (downward ? e.to.y : e.to.y + e.to.h) : e.to.y + e.to.h / 2;
    const kind = kindOf(e);
    const dimmed = getEdgeInfo ? !!getEdgeInfo(e).dimmed : false;
    // 折点全部正交 (每段纯横或纯竖), 再由 orthPath 打圆角
    const pts = [{ x: x1, y: y1 }];
    if (bundled) {
      // 出源卡侧沿朝外 → 下探到源所在行的行间通道 (同一行的多条接入线在此重叠, 又是一次合流)
      // → 横向并入主干 → 沿主干竖直下到目标 → 横入目标左沿
      // 通道走行底 (node.rowH) 而非源卡底: 分层排布下两者相等, 但子任务迷你 DAG 的行仍可能不等高
      const sx = x1 + (rightward ? 16 : -16), yc = e.from.y + (e.from.rowH || e.from.h) + 10;
      pts.push({ x: sx, y: y1 }, { x: sx, y: yc }, { x: trunk.x, y: yc }, { x: trunk.x, y: y2 });
    } else if (e.cross) {
      // 跨带回绕边: 出侧沿 stub → 走带间水平通道 → 从目标侧沿 stub 进入, 不穿卡片区
      const sx = chan(x1 + (rightward ? 30 : -30), 'x');
      const ex = chan(x2 + (rightward ? -30 : 30), 'x');
      const yc = chan(e.laneY, 'y');
      pts.push({ x: sx, y: y1 }, { x: sx, y: yc }, { x: ex, y: yc }, { x: ex, y: y2 });
    } else if (vert) {
      // 竖排: 逐段 竖-横-竖, 水平段落在两行之间的通道里
      let px = x1, py = y1;
      for (const m of [...(e.bends || []), { x: x2, y: y2 }]) {
        const cy = chan((py + m.y) / 2, 'y');
        pts.push({ x: px, y: cy }, { x: m.x, y: cy });
        px = m.x; py = m.y;
      }
    } else {
      // 横排: 逐段 横-竖-横, 竖直段落在两列之间的通道里 (长边有虚点拐点, 顺着走)
      let px = x1, py = y1;
      for (const m of [...(e.bends || []), { x: x2, y: y2 }]) {
        const cx = chan((px + m.x) / 2, 'x');
        pts.push({ x: cx, y: py }, { x: cx, y: m.y });
        px = m.x; py = m.y;
      }
    }
    pts.push({ x: x2, y: y2 });
    const d = orthPath(pts);
    const opacity = dimmed ? '0.12' : (e.cross ? '0.4' : '0.55');
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${EDGE_KIND[kind].color})`,
      'stroke-width': '2', 'stroke-opacity': opacity,
      'stroke-dasharray': e.cross ? '7 5' : null,
      'marker-end': `url(#arrow-${kind})`,
      class: 'dag-edge',
      'data-from': e.from.id, 'data-to': e.to.id,
    });
  });
  return h('svg.absolute.inset-0.pointer-events-none.dag-edges',
    { style: { width: '100%', height: '100%' }, 'aria-hidden': 'true' },
    [
      h('defs', markers),
      ...paths,
    ]
  );
}

// ---- 依赖 DAG：以当前任务为中心的上下游 ----
function buildDepDAG(taskId, allTasks) {
  const byId = new Map(allTasks.map(t => [t.id, t]));
  const task = byId.get(taskId);
  if (!task) return { nodes: [], edges: [], width: 0, height: 0, centerId: taskId };

  // BFS 收集所有上游（deps）和下游（dependents）
  const visited = new Set([taskId]);
  const upstream = [];   // 上游任务 id
  const downstream = []; // 下游任务 id

  // 计算下游 map: id -> [依赖它的任务id]
  const downstreamOf = new Map();
  for (const t of allTasks) {
    for (const d of t.deps || []) {
      if (!downstreamOf.has(d)) downstreamOf.set(d, []);
      downstreamOf.get(d).push(t.id);
    }
  }

  // BFS 上游
  let queue = [...(task.deps || [])];
  while (queue.length) {
    const id = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);
    upstream.push(id);
    const t = byId.get(id);
    if (t && t.deps) queue.push(...t.deps.filter(d => !visited.has(d)));
  }

  // BFS 下游
  queue = downstreamOf.get(taskId) || [];
  while (queue.length) {
    const id = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);
    downstream.push(id);
    const next = downstreamOf.get(id) || [];
    queue.push(...next.filter(d => !visited.has(d)));
  }

  // 分层布局: 上游在左 (负数层), 当前任务在中间 (0层), 下游在右 (正数层)
  const layerOf = new Map();
  layerOf.set(taskId, 0);

  // 上游分层: BFS 从当前任务往上游推
  let upQueue = [taskId];
  let upLayer = 0;
  while (upQueue.length) {
    upLayer--;
    const next = [];
    for (const id of upQueue) {
      const t = byId.get(id);
      if (!t) continue;
      for (const d of t.deps || []) {
        if (!visited.has(d)) continue;
        if (layerOf.has(d) && layerOf.get(d) >= upLayer) continue;
        layerOf.set(d, upLayer);
        next.push(d);
      }
    }
    upQueue = [...new Set(next)];
  }

  // 下游分层: BFS 从当前任务往下游推
  let downQueue = [taskId];
  let downLayer = 0;
  while (downQueue.length) {
    downLayer++;
    const next = [];
    for (const id of downQueue) {
      const deps = downstreamOf.get(id) || [];
      for (const d of deps) {
        if (!visited.has(d)) continue;
        if (layerOf.has(d) && layerOf.get(d) <= downLayer) continue;
        layerOf.set(d, downLayer);
        next.push(d);
      }
    }
    downQueue = [...new Set(next)];
  }

  // 按层分组
  const layers = new Map(); // layerIndex -> [ids]
  for (const [id, layer] of layerOf) {
    if (!layers.has(layer)) layers.set(layer, []);
    layers.get(layer).push(id);
  }

  const colW = 180, rowH = 56, padX = 20, padY = 16;
  const minLayer = Math.min(...layers.keys());
  const layerOffset = -minLayer; // 把最左层对齐到 0

  const nodes = [];
  for (const [layer, ids] of layers) {
    const colIdx = layer + layerOffset;
    ids.forEach((id, ri) => {
      const t = byId.get(id);
      if (!t) return;
      nodes.push({
        id, task: t,
        x: padX + colIdx * colW,
        y: padY + ri * rowH,
        w: colW - 16, h: rowH - 12,
        isCenter: id === taskId,
        layer,
      });
    });
  }

  // 边
  const edges = [];
  for (const n of nodes) {
    const deps = n.task.deps || [];
    for (const depId of deps) {
      const src = nodes.find(x => x.id === depId);
      if (src) edges.push({ from: src, to: n });
    }
  }

  const numLayers = layers.size;
  const maxRows = Math.max(1, ...[...layers.values()].map(l => l.length));
  const width = padX * 2 + numLayers * colW;
  const height = padY * 2 + maxRows * rowH;

  return { nodes, edges, width, height, centerId: taskId };
}

// ---- 依赖 DAG 视图（可拖拽平移） ----
function depDAGView(task, allTasks, onTaskClick) {
  const { nodes, edges, width, height, centerId } = buildDepDAG(task.id, allTasks);
  if (nodes.length <= 1) {
    return h('div.py-6.text-center.text-xs.text-muted', '暂无上下游依赖');
  }

  // 初始偏移：把中心节点移到视图中间
  const centerNode = nodes.find(n => n.isCenter);
  const viewW = 360;
  const initOffsetX = viewW / 2 - (centerNode ? centerNode.x + centerNode.w / 2 : width / 2);
  const initOffsetY = 20;

  const containerId = 'dep-dag-' + task.id;

  // 渲染后绑定拖拽
  setTimeout(() => {
    const container = document.getElementById(containerId);
    if (!container) return;
    const canvas = container.querySelector('.dep-dag-canvas');
    if (!canvas) return;

    let offsetX = initOffsetX, offsetY = initOffsetY;
    let isDragging = false;
    let startX = 0, startY = 0;
    let startOffsetX = 0, startOffsetY = 0;

    function updateTransform() {
      canvas.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    }
    updateTransform();

    // 鼠标拖拽
    container.addEventListener('mousedown', (e) => {
      if (e.target.closest('.dep-dag-node')) return; // 点击节点不触发拖拽
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startOffsetX = offsetX;
      startOffsetY = offsetY;
      container.style.cursor = 'grabbing';
      e.preventDefault();
    });
    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      offsetX = startOffsetX + (e.clientX - startX);
      offsetY = startOffsetY + (e.clientY - startY);
      updateTransform();
    });
    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        container.style.cursor = 'grab';
      }
    });

    // 触摸拖拽
    container.addEventListener('touchstart', (e) => {
      if (e.target.closest('.dep-dag-node')) return;
      if (e.touches.length !== 1) return;
      isDragging = true;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      startOffsetX = offsetX;
      startOffsetY = offsetY;
    }, { passive: true });
    container.addEventListener('touchmove', (e) => {
      if (!isDragging || e.touches.length !== 1) return;
      offsetX = startOffsetX + (e.touches[0].clientX - startX);
      offsetY = startOffsetY + (e.touches[0].clientY - startY);
      updateTransform();
    }, { passive: true });
    container.addEventListener('touchend', () => { isDragging = false; });
  }, 0);

  return h('div.dep-dag-container', { id: containerId }, [
    h('div.dep-dag-canvas.absolute',
      { style: { width: width + 'px', height: height + 'px' } },
      [
        drawEdges(edges),
        ...nodes.map(n =>
          h(`div.dep-dag-node.absolute.flex.items-center.gap-2.px-2.py-1.rounded-md.cursor-pointer.transition-all${n.isCenter ? '.dep-dag-center' : ''}`,
            {
              style: { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h + 'px' },
              onclick: (e) => { e.stopPropagation(); if (onTaskClick) onTaskClick(n.id); },
              'data-task-id': n.id,
              title: n.task.title || n.task.name || n.id,
            },
            [
              h(`span.w-1.5.h-1.5.rounded-full.flex-shrink-0.bg-${ST_COLOR[n.task.status || 'planning']}`),
              h('span.text-xs.text-fg.truncate.flex-1.font-medium', n.task.title || n.task.name || n.id),
              n.isCenter ? h('i.fa.fa-star.text-xs.text-goldSand-mid') : null,
            ]
          )
        ),
      ]
    ),
    h('div.dep-dag-hint', [
      h('i.fa.fa-hand-pointer-o'),
      ' 拖拽可平移视图',
    ]),
  ]);
}

export { EDGE_KIND, edgeKinds, edgeLegend, drawEdges, buildDepDAG, depDAGView };
