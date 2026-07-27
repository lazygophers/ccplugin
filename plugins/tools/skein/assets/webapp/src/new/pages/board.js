// ============================================================
//  Board — 看板 / DAG
//  设计: 左 DAG/列表 + 右详情面板(点击才显) | 悬浮 popover | 状态多选筛选
//  状态: 规划中 / 待执行 / 执行中 / 验收中 / 已完成
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTasks, prioLabel, prioTextColor } from '../app.js';

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
  // 带内目标行数: 一带尽量高约一屏。宽层 (fan-out) 超过 R 行就吃掉本带的相邻列折行,
  // 不折的话 19 个兄弟就堆成一根 4500px 的柱子。
  const R = Math.max(4, Math.floor((viewH || 800) / rowH));
  // 贪心装带: 每层按需要的列数入座, 装不下就换带
  const seat = [];   // 每层 { band, col, cols }
  let curBand = 0, curCol = 0;
  for (const l of layers) {
    const cols = Math.min(K, Math.max(1, Math.ceil(l.length / R)));
    if (curCol + cols > K && curCol > 0) { curBand++; curCol = 0; }
    seat.push({ band: curBand, col: curCol, cols });
    curCol += cols;
  }
  const bands = curBand + 1;
  const bandOf = (li) => seat[li].band;

  // --- 5. 坐标 ---
  layers.forEach((l, li) => {
    const st = seat[li];
    const rows = st.cols > 1 ? Math.ceil(l.length / st.cols) : l.length;
    l.forEach((n, i) => {
      n.x = (st.col + Math.floor(i / rows)) * colW;
      n.y = (i % rows) * rowH;
      n.y0 = n.y;   // 网格基准位, 对齐只能在其附近微调
      n.band = st.band;
    });
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
        n.y = Math.max(want, prev + rowH);
        prev = n.y;
      }
    }
  }
  // 带内归零 → 按带高纵向堆叠
  const span = Array.from({ length: bands }, () => ({ lo: Infinity, hi: -Infinity }));
  let usedCols = 1;
  layers.forEach((l, li) => {
    const s = span[seat[li].band];
    usedCols = Math.max(usedCols, seat[li].col + seat[li].cols);
    for (const n of l) { s.lo = Math.min(s.lo, n.y); s.hi = Math.max(s.hi, n.y); }
  });
  const bandTop = [];
  let accY = 0;
  for (const s of span) {
    if (s.lo === Infinity) { s.lo = 0; s.hi = 0; }
    bandTop.push({ top: accY, shift: -s.lo });
    accY += (s.hi - s.lo) + rowH * 2;   // 带间留一行间距
  }
  const all = layers.flat();
  for (const n of all) {
    const bt = bandTop[n.band];
    n.x += padX;
    n.y += bt.shift + bt.top + padY;
  }
  const maxY = all.reduce((m, n) => Math.max(m, n.y), 0);
  return {
    layers, edges, bandCols: usedCols,
    width: usedCols * colW + padX * 2,
    height: maxY + (rowH - gapY) + padY,
  };
}

// 响应式布局参数
const DAG_SIZES = {
  sm: { colW: 260, rowH: 180, padX: 32, padY: 24, gapX: 24, gapY: 16 },
  md: { colW: 300, rowH: 200, padX: 40, padY: 30, gapX: 30, gapY: 20 },
  lg: { colW: 340, rowH: 220, padX: 50, padY: 40, gapX: 36, gapY: 24 },
  xl: { colW: 380, rowH: 240, padX: 60, padY: 50, gapX: 40, gapY: 28 },
};

// ---- DAG 布局 ----
// view = { w, h } 可用画布尺寸 — 详情面板开合 / 窗口缩放都会改变它, 布局随之重排
// 宽度是硬约束 (画布永不横向溢出), 高度自由, 超出部分由容器纵向滚动条承担
function layoutDAG(tasks, size = 'md', view) {
  if (!tasks || !tasks.length) return { nodes: [], edges: [], width: 0, height: 0 };
  const s = DAG_SIZES[size] || DAG_SIZES.md;
  const byId = new Map(tasks.map(t => [t.id, t]));
  const g = sugiyama(tasks.map(t => t.id), id => byId.get(id).deps || [],
    { ...s, maxWidth: (view && view.w) || 1200, viewH: (view && view.h) || 800 });
  return packLayout(g, s, id => ({ task: byId.get(id) }));
}

// sugiyama 结果 → 渲染用 {nodes, edges}: 丢掉虚点, 虚点坐标转成边的拐点
function packLayout(g, s, extraOf) {
  const w = s.colW - s.gapX, hgt = s.rowH - s.gapY;
  const nodes = [];
  for (const l of g.layers) {
    for (const n of l) {
      if (n.dummy) continue;
      nodes.push({ id: n.id, x: n.x, y: n.y, w, h: hgt, ...extraOf(n.id) });
    }
  }
  const nmap = new Map(nodes.map(n => [n.id, n]));
  const edges = [];
  for (const e of g.edges) {
    const from = nmap.get(e.from.id), to = nmap.get(e.to.id);
    if (!from || !to) continue;
    edges.push({ from, to, bends: e.chain.map(d => ({ x: d.x + w / 2, y: d.y + hgt / 2 })) });
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
  const g = sugiyama([...byId.keys()], id => {
    const sub = byId.get(id);
    return sub.deps || sub.dependsOn || [];
  }, { ...s, maxWidth: panelW - 48, viewH: 600 });
  return packLayout(g, s, id => ({ sub: byId.get(id) }));
}

// ---- 悬浮 popover ----
function nodePopover(node) {
  const t = node.task;
  const st = t.status || 'planning';
  const subs = t.subtasks || [];
  const subStats = getSubtaskStats(t);
  const hasSubs = subs.length > 0;
  const progress = hasSubs ? subStats.progress : (t.progress != null ? t.progress : (st === 'done' ? 100 : st === 'active' ? 50 : 0));
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
function nodeCard(node, onClick, onToggleExpand, isExpanded, dimmed) {
  const t = node.task;
  const st = t.status || 'planning';
  const subs = t.subtasks || [];
  const subStats = getSubtaskStats(t);
  const hasSubs = subs.length > 0;

  return h(`div.dag-node-wrap.absolute${dimmed ? ' opacity-40 grayscale' : ''}`,
    {
      'data-node-id': t.id,
      style: {
        left: node.x + 'px', top: node.y + 'px',
        width: node.w + 'px',
      },
    },
    [
      nodePopover(node),
      // 卡片本体高度锁定为 node.h — drawEdges 用 node.h 算端点中线, 内容撑高会让连线脱离卡片
      h('div.dag-node.glass-card.p-3.cursor-pointer.hover-float.transition-all.overflow-hidden.flex.flex-col',
        {
          onclick: (e) => { e.preventDefault(); onClick(t.id); },
          'data-task-id': t.id,
          style: { height: node.h + 'px' },
        },
        [
          h(`div.h-1.rounded-full.-mx-3.-mt-3.mb-2.${ST_COLOR[st]}.opacity-60`),
          h('div.flex.items-start.gap-2.mb-1.5', [
            h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.mt-0.5.flex-shrink-0.text-sm`),
            h('div.flex-1.min-w-0', [
              h('div.text-sm.font-semibold.text-head.truncate', t.title || t.name || '(未命名)'),
              h('div.text-xs.text-muted.font-mono.truncate', '#' + t.id),
            ]),
          ]),
          t.description
            ? h('div.text-xs.text-muted.line-clamp-2.mb-2', t.description)
            : null,
          hasSubs ? h('div.mb-2', [
            h('div.flex.items-center.justify-between.text-xs.text-muted.mb-1', [
              h('span.flex.items-center.gap-1', [
                h('i.fa.fa-sitemap.text-xxs'),
                `子任务 ${subStats.done}/${subStats.total}`,
              ]),
              h('span', `${subStats.progress}%`),
            ]),
            h('div.h-1.rounded-full.bg-line.overflow-hidden',
              [
                h('div.h-full.rounded-full',
                  {
                    style: {
                      width: subStats.progress + '%',
                      background: 'var(--st-done)',
                    },
                  }
                ),
              ]
            ),
          ]) : null,
          h('div.flex.items-center.justify-between.text-xs.mt-auto', [
            h(`span.badge.badge-sm.${ST_COLOR[st]}`, ST_LABEL[st] || st),
            h('div.flex.items-center.gap-2', [
              hasSubs
                ? h('button',
                    {
                      onclick: (e) => { e.stopPropagation(); if (onToggleExpand) onToggleExpand(t.id); },
                      title: isExpanded ? '收起子任务' : '展开子任务',
                      class: 'text-muted hover:text-accent transition-colors',
                    },
                    [h(`i.fa.fa-chevron-${isExpanded ? 'up' : 'down'}`)]
                  )
                : null,
              h('span.text-muted', t.updatedAt ? fmtRelative(t.updatedAt) : ''),
            ]),
          ]),
        ]
      ),
      isExpanded && hasSubs ? h('div.mt-2.glass-card.p-3',
        { onclick: (e) => e.stopPropagation() },
        [
          h('div.eyebrow.text-accent.mb-2.text-xs', `子任务 DAG (${subs.length})`),
          subs.length >= 2
            ? subDAGView(subs, (sid) => { onClick(t.id); })
            : subs.length === 1
              ? h('div.p-2.rounded.bg-surface/50.text-sm', subs[0].title || subs[0].name || subs[0].sid)
              : null,
        ]
      ) : null,
    ]
  );
}

// ---- SVG 连线 ----
// 起止点贴 card 边缘: from 右边中 → to 左边中 (水平流向)。
// 箭头 marker 标方向 (谁→谁); hover card 时高亮其连线 (edge-highlight class)。
function drawEdges(edges, getEdgeInfo) {
  if (!edges.length) return null;

  // 每个状态一个箭头 marker (用 stroke 色), id 去重
  const usedSts = new Set();
  const markers = [];
  for (const e of edges) {
    let st;
    if (getEdgeInfo) {
      st = getEdgeInfo(e).status;
    } else {
      st = (e.to.task ? e.to.task.status : e.to.sub.status) || 'planning';
    }
    if (usedSts.has(st)) continue;
    usedSts.add(st);
    markers.push(h('marker',
      { id: `arrow-${st}`, viewBox: '0 0 10 10', refX: '9', refY: '5',
        markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse' },
      [h('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: `var(--${ST_COLOR[st]})` })]
    ));
  }

  const paths = edges.map(e => {
    // 起止点退回 card 边缘内一点, 避箭头戳进 card; marker 自带尺寸故终点贴边即可
    const x1 = e.from.x + e.from.w;
    const y1 = e.from.y + e.from.h / 2;
    const x2 = e.to.x;
    const y2 = e.to.y + e.to.h / 2;
    let st, dimmed = false;
    if (getEdgeInfo) {
      const info = getEdgeInfo(e);
      st = info.status;
      dimmed = info.dimmed;
    } else {
      st = (e.to.task ? e.to.task.status : e.to.sub.status) || 'planning';
    }
    let d;
    if (e.bends && e.bends.length) {
      // 跨多层的长边: 串起虚点拐点分段走, 绕开中间层挡路的卡片
      const pts = [{ x: x1, y: y1 }, ...e.bends, { x: x2, y: y2 }];
      d = `M ${x1} ${y1}`;
      for (let i = 1; i < pts.length; i++) {
        const p0 = pts[i - 1], p1 = pts[i], mx = (p0.x + p1.x) / 2;
        d += ` C ${mx} ${p0.y}, ${mx} ${p1.y}, ${p1.x} ${p1.y}`;
      }
    } else {
      // 贝塞尔 control: 跨 layer 用水平中点; 同 x (同 layer / 环 fallback) 用横向偏移避免退化重叠
      const dx = x2 - x1;
      let cx1, cx2;
      if (Math.abs(dx) < 8) {
        // 同列: control 向右弯出再回, 避线段退化为竖线与邻线重叠
        const bow = 60;
        cx1 = x1 + bow; cx2 = x2 + bow;
      } else {
        const mx = (x1 + x2) / 2;
        cx1 = mx; cx2 = mx;
      }
      d = `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;
    }
    const opacity = dimmed ? '0.12' : '0.55';
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${ST_COLOR[st]})`,
      'stroke-width': '2', 'stroke-opacity': opacity,
      'marker-end': `url(#arrow-${st})`,
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

// ---- 视图切换 ----
function viewToggle(view, onChange) {
  return h('div.flex.items-center.gap-1.glass.rounded-lg.p-1.border.border-brd/40', [
    h(`button.px-3.py-1.5.rounded-md.text-sm.font-medium.transition-all${view === 'dag' ? ' bg-accent/20 text-accent' : ' text-muted hover:text-fg'}`,
      { onclick: () => onChange('dag') },
      [h('i.fa.fa-sitemap.mr-1.5'), 'DAG']),
    h(`button.px-3.py-1.5.rounded-md.text-sm.font-medium.transition-all${view === 'list' ? ' bg-accent/20 text-accent' : ' text-muted hover:text-fg'}`,
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
                h('div.flex.items-center.gap-2.p-2.rounded-lg.hover\\:bg-card\\/40.transition-colors.cursor-pointer',
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

// ---- 时间线 ----
const STAGE_COLORS = {
  created:  '#74b9e8',
  ready:    '#429cd1',
  started:  '#237bb8',
  checked:  '#c9a227',
  finished: '#48bb78',
};

function buildTimeline(task) {
  const st = task.status || 'planning';
  const stages = [
    {
      key: 'created', label: '创建', name: '创建任务',
      desc: '任务创建与初始化',
      time: task.createdAt,
      done: !!task.createdAt,
      current: false,
      color: STAGE_COLORS.created,
    },
    {
      key: 'ready', label: '就绪', name: '进入待执行',
      desc: '规划完成，等待开始执行',
      time: task.readyAt,
      done: !!task.readyAt || st === 'ready' || st === 'active' || st === 'check' || st === 'done' || st === 'failed',
      current: st === 'ready',
      color: STAGE_COLORS.ready,
    },
    {
      key: 'started', label: '执行', name: '开始执行',
      desc: '任务执行中，子任务调度',
      time: task.startedAt,
      done: !!task.startedAt || st === 'active' || st === 'check' || st === 'done' || st === 'failed',
      current: st === 'active',
      color: STAGE_COLORS.started,
    },
    {
      key: 'checked', label: '验收', name: '进入验收',
      desc: 'checkpoint 核对 + 场景自适应校验',
      time: task.checkedAt,
      done: !!task.checkedAt || st === 'check' || st === 'done' || st === 'failed',
      current: st === 'check',
      color: STAGE_COLORS.checked,
    },
    {
      key: 'finished', label: '完成', name: '已完成',
      desc: '任务完成，归档沉淀',
      time: task.finishedAt,
      done: !!task.finishedAt || st === 'done',
      current: false,
      color: STAGE_COLORS.finished,
    },
  ];
  // 标记当前进行中的阶段（取第一个 current=true 或最后一个 done 之后的 pending）
  let foundCurrent = false;
  for (const s of stages) {
    if (s.current) { foundCurrent = true; break; }
  }
  if (!foundCurrent) {
    // 找第一个未完成的作为当前
    const firstPending = stages.find(s => !s.done);
    if (firstPending) firstPending.current = false; // pending 态，不算 cur
  }
  return stages;
}

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
        drawEdges(edges, (e) => e.to.sub.status || 'planning'),
        ...nodes.map(n =>
          h(`div.sub-dag-node.absolute.flex.items-center.gap-2.px-2.py-1.rounded.border.border-brd/40.bg-card/60.cursor-pointer.hover\\:bg-card.transition-colors`,
            {
              style: { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h + 'px' },
              onclick: (e) => { e.stopPropagation(); if (onSubClick) onSubClick(n.id); },
              'data-sub-id': n.id,
              title: n.sub.title || n.sub.name || n.id,
            },
            [
              h(`span.w-2.h-2.rounded-full.flex-shrink-0.bg-${ST_COLOR[n.sub.status || 'planning']}`),
              h('span.text-xs.text-fg.truncate.flex-1', n.sub.title || n.sub.name || n.id),
            ]
          )
        ),
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
      h('div.eyebrow.text-accent.m-0',
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
      h('div.eyebrow.text-accent.m-0', `契约 (${contracts.length})`),
    ]),
    h('div.space-y-2',
      contracts.map((c, i) =>
        h('div.p-2.rounded.bg-surface/50.border.border-brd/30', [
          h('div.text-sm.font-medium.text-head', c.name || c.title || `契约 ${i + 1}`),
          c.desc || c.description ? h('div.text-xs.text-muted.mt-1', c.desc || c.description) : null,
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
      h('div.eyebrow.text-accent.m-0', '详细设计'),
    ]),
    h('pre.text-xs.text-fg.whitespace-pre-wrap.font-mono.bg-surface/30.p-3.rounded.overflow-x-auto', preview),
  ]);
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
        drawEdges(edges, (e) => {
          const st = e.to.task.status || 'planning';
          return { status: st, dimmed: false };
        }),
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

// ---- 右侧详情面板 (仅当有选中任务时显示) ----
function detailPanel(task, allTasks, onClose, onSubClick, onOpenDetail, onTaskClick) {
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
          h('div.eyebrow.text-accent.mb-3', '基本信息'),
          infoRow('优先级', prioLabel(task.priority) + ` (${task.priority != null ? Number(task.priority) : 5})`),
          task.assignee ? infoRow('负责人', task.assignee) : null,
          infoRow('预估工时', task.estimate ? task.estimate + ' h' : '—'),
          infoRow('进度', task.progress != null ? task.progress + '%' : (st === 'done' ? '100%' : '—')),
        ]),
        // 2. 任务描述
        h('div.glass-card.p-4', [
          h('div.eyebrow.text-accent.mb-2', '任务描述'),
          h('p.text-sm.text-fg.whitespace-pre-wrap', task.description || task.desc || '暂无描述'),
        ]),
        // 3. 目标
        ...(prdGoalsView(task.prd) || []),
        // 4. 验收标准
        ...(prdAcceptanceView(task.prd) || []),
        // 5. 契约
        contractsView(task.contracts),
      ]),

      // 子任务 DAG — 跨全宽
      task.subtasks && task.subtasks.length >= 2
        ? h('div.glass-card.p-4.panel-span-2', [
            h('div.eyebrow.text-accent.mb-3', `子任务 DAG (${task.subtasks.length})`),
            subDAGView(task.subtasks, onSubClick),
          ])
        : null,

      // 子任务列表 — 跨全宽
      task.subtasks && task.subtasks.length
        ? h('div.glass-card.p-4.panel-span-2', [
            h('div.eyebrow.text-accent.mb-3', `子任务列表 (${task.subtasks.length})`),
            h('div.flex.flex-col.gap-2',
              task.subtasks.map(s => {
                const sst = s.status || 'planning';
                const sIcon = ST_ICON[sst] || 'fa-circle-o';
                const sColor = ST_COLOR[sst] || 'st-planning';
                return h('div.subtask-row.flex.items-center.gap-3.p-2.rounded-lg.cursor-pointer.hover\\:bg-surface/60.transition-all',
                  {
                    onclick: () => { if (onSubClick) onSubClick(s.sid || s.id); },
                    'data-sub-id': s.sid || s.id,
                    title: s.description || s.desc || s.title || s.name,
                  },
                  [
                    h(`span.w-5.h-5.rounded-full.flex.items-center.justify-center.flex-shrink-0.bg-${sColor}/10`,
                      h(`i.fa.${sIcon}.text-xs.text-${sColor}`)
                    ),
                    h('div.flex-1.min-w-0', [
                      h('div.text-sm.text-fg.truncate', s.title || s.name || s.sid || s.id),
                      s.description
                        ? h('div.text-xs.text-muted.line-clamp-1.mt-0.5', s.description)
                        : null,
                    ]),
                    s.progress != null
                      ? h('span.text-xs.text-muted.font-mono', s.progress + '%')
                      : null,
                    s.assignee
                      ? h('span.text-xs.text-muted.flex.items-center.gap-1',
                          [h('i.fa.fa-user.text-xxs'), s.assignee.slice(0, 6)]
                        )
                      : null,
                  ]
                );
              })
            ),
          ])
        : null,

      // 详细设计 — 跨全宽
      task.docs && task.docs.design ? h('div.panel-span-2', designView(task.docs.design)) : null,

      // 依赖 DAG 图（上下游 + 可拖拽）— 仅当有依赖时显示，跨全宽
      (() => {
        const { nodes } = buildDepDAG(task.id, allTasks);
        if (nodes.length <= 1) return null;
        return h('div.glass-card.p-4.panel-span-2', [
          h('div.flex.items-center.gap-2.mb-3', [
            h('i.fa.fa-share-alt.text-st-active.text-sm'),
            h('div.eyebrow.text-accent.m-0', `依赖关系图 (${nodes.length})`),
          ]),
          depDAGView(task, allTasks, onTaskClick),
        ]);
      })(),

      // 时间线 — 跨全宽, 最底部
      h('div.glass-card.p-4.panel-span-2', [
        h('div.eyebrow.text-accent.mb-3', '生命周期时间线'),
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
  const expandedNodes = new Set();

  // 状态计数
  const countBy = {};
  for (const t of allTasks) countBy[t.status] = (countBy[t.status] || 0) + 1;

  function selectTask(id) {
    selectedId = id;
    draw();
  }

  function closePanel() {
    selectedId = null;
    draw();
  }

  function toggleExpand(id) {
    if (expandedNodes.has(id)) expandedNodes.delete(id);
    else expandedNodes.add(id);
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

  function onSubClick(sid) {
    // 子任务点击: 可以高亮/展开, 暂仅打 log
    console.log('subtask clicked:', sid);
  }

  function openDetailPage(id) {
    if (ctx && ctx.navigate) {
      ctx.navigate('/task/' + id);
    }
  }

  // ---- 响应式 size 检测 ----
  function getSize() {
    const w = window.innerWidth;
    if (w >= 1700) return 'xl';
    if (w >= 1440) return 'lg';
    if (w >= 1024) return 'md';
    return 'sm';
  }
  let curSize = getSize();
  // 布局用的可用画布尺寸 — 每次 draw 后按真实 DOM 校正, 详情面板开合 / 窗口缩放都会改到它
  let viewBox = { w: Math.max(400, window.innerWidth - 80), h: Math.max(600, window.innerHeight - 260) };
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      curSize = getSize();
      draw();
    }, 150);
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
    const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
    const { nodes, edges, width, height } = layoutDAG(allTasks, curSize, viewBox);
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
          view === 'dag' ? h('div.flex.items-center.gap-1.glass.rounded-lg.p-1.border.border-brd/40', [
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
                      const fromActive = statusSet.has(fromSt);
                      const toActive = statusSet.has(toSt);
                      return { status: toSt, dimmed: !(fromActive && toActive) };
                    }),
                    ...nodes.map(n => nodeCard(n, selectTask, toggleExpand, expandedNodes.has(n.id), !statusSet.has(n.task.status))),
                  ]
                ),
              ]
            : [listView(allTasks, selectTask, statusSet)]
        ),
        // 右侧: 详情面板 (仅选中时显示)
        hasPanel ? detailPanel(selectedTask, allTasks, closePanel, onSubClick, openDetailPage, selectTask) : null,
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
      }
    });
  }

  draw();
}
