// ============================================================
//  Board — 看板 / DAG
//  设计: 画布 + 节点玻璃卡 + SVG 连线 + 缩放
// ============================================================

import { h, api, fmtRelative, normalizeTasks } from '../app.js';

const ST_COLOR = {
  pending: 'st-pending', active: 'st-active',
  check:   'st-check',   done: 'st-done',
  failed:  'st-failed',
};
const ST_LABEL = {
  pending: '待办', active: '执行中',
  check:   '待验收', done: '已完成', failed: '失败',
};
const ST_ICON = {
  pending: 'fa-clock-o', active: 'fa-spinner.fa-spin',
  check: 'fa-eye', done: 'fa-check-circle', failed: 'fa-times-circle',
};

// ---- 计算 DAG 布局 (拓扑层级 + 列内顺序) ----
function layoutDAG(tasks) {
  const byId = new Map(tasks.map(t => [t.id, t]));
  const indeg = new Map();
  for (const t of tasks) indeg.set(t.id, (t.deps || []).length);

  // 拓扑分层
  const layers = [];
  const remaining = new Set(tasks.map(t => t.id));
  while (remaining.size) {
    const cur = [];
    for (const id of remaining) {
      const t = byId.get(id);
      const depDone = (t.deps || []).every(d => !remaining.has(d));
      if (depDone) cur.push(id);
    }
    if (!cur.length) { cur.push(...remaining); remaining.clear(); } // 保底
    for (const id of cur) remaining.delete(id);
    layers.push(cur);
  }

  // 计算坐标
  const colW = 260, rowH = 130, padX = 40, padY = 40;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const t = byId.get(id);
      nodes.push({
        id, task: t,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 20, h: rowH - 20,
      });
    });
  });

  // 连线
  const edges = [];
  for (const n of nodes) {
    const deps = n.task.deps || [];
    for (const depId of deps) {
      const src = nodes.find(x => x.id === depId);
      if (src) edges.push({ from: src, to: n });
    }
  }

  const width = padX * 2 + layers.length * colW;
  const height = padY * 2 + Math.max(...layers.map(l => l.length)) * rowH;
  return { nodes, edges, width, height };
}

// ---- 节点卡片 ----
function nodeCard(node) {
  const t = node.task;
  const st = t.status || 'pending';
  return h(`a.dag-node.absolute.glass-card.p-4.cursor-pointer.hover-float.transition-all`,
    {
      href: `/task/${t.id}`, 'data-nav': '',
      style: {
        left: node.x + 'px', top: node.y + 'px',
        width: node.w + 'px',
      },
    },
    [
      // 顶部状态条
      h(`div.h-1.rounded-full.-mx-1.-mt-1.mb-3.bg-${ST_COLOR[st]}.opacity-60`),
      // 标题行
      h('div.flex.items-start.gap-2.mb-2', [
        h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.mt-0.5.flex-shrink-0`),
        h('div.flex-1.min-w-0', [
          h('div.text-sm.font-semibold.text-head.truncate', t.title || t.name || '(未命名)'),
          h('div.text-xs.text-muted.font-mono', '#' + t.id),
        ]),
      ]),
      // 描述
      t.description
        ? h('div.text-xs.text-muted.line-clamp-2.mb-3', t.description)
        : null,
      // 底部: 状态 + 时间
      h('div.flex.items-center.justify-between.text-xs', [
        h(`span.antd-tag.antd-tag-${st}`, ST_LABEL[st] || st),
        h('span.text-muted', t.updatedAt ? fmtRelative(t.updatedAt) : ''),
      ]),
    ]
  );
}

// ---- SVG 连线 ----
function drawEdges(edges) {
  if (!edges.length) return null;
  const paths = edges.map(e => {
    const x1 = e.from.x + e.from.w;
    const y1 = e.from.y + e.from.h / 2;
    const x2 = e.to.x;
    const y2 = e.to.y + e.to.h / 2;
    const mx = (x1 + x2) / 2;
    const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
    const st = e.to.task.status || 'pending';
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${ST_COLOR[st]})`,
      'stroke-width': '2', 'stroke-opacity': '0.4',
    });
  });
  return h('svg.absolute.inset-0.pointer-events-none',
    { style: { width: '100%', height: '100%' } },
    paths
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

// ---- 列表视图 ----
function listView(tasks) {
  const groups = ['active', 'pending', 'check', 'done', 'failed'];
  return h('div.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
    groups.map(st => {
      const list = tasks.filter(t => (t.status || 'pending') === st);
      return h('div.glass-card', [
        h('div.flex.items-center.gap-2.mb-4', [
          h(`span.w-3.h-3.rounded-full.bg-${ST_COLOR[st]}`),
          h('span.text-sm.font-semibold.text-head', ST_LABEL[st]),
          h('span.text-xs.text-muted.ml-auto', list.length),
        ]),
        h('div.space-y-2',
          list.length
            ? list.slice(0, 8).map(t =>
                h(`a.flex.items-center.gap-2.p-2.rounded-lg.hover\\:bg-card\\/40.transition-colors`,
                  { href: `/task/${t.id}`, 'data-nav': '' },
                  [
                    h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.text-xs`),
                    h('div.flex-1.min-w-0', [
                      h('div.text-sm.text-fg.truncate', t.title || t.name || '(未命名)'),
                      h('div.text-xs.text-muted.font-mono', '#' + t.id),
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

// ---- 主渲染 ----
export async function render(mount) {
  const resp = await api.data().catch(() => null);
  const tasks = normalizeTasks((resp && resp.cards) || []);

  let view = 'dag';
  let scale = 1;

  const { nodes, edges, width, height } = layoutDAG(tasks);

  function draw() {
    mount.replaceChildren(
      // 标题行
      h('div.flex.items-center.justify-between.mb-6.flex-wrap.gap-3', [
        h('div', [
          h('h1.text-3xl.font-bold.text-head.mb-1', '任务看板'),
          h('p.text-muted', `${tasks.length} 个任务 · DAG 可视化`),
        ]),
        h('div.flex.items-center.gap-3', [
          view === 'dag' ? h('div.flex.items-center.gap-1.glass.rounded-lg.p-1.border.border-brd/40', [
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = Math.min(scale + 0.1, 2); draw(); }, title: '放大' },
              h('i.fa.fa-search-plus')),
            h('span.text-xs.text-muted.px-1', Math.round(scale * 100) + '%'),
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = Math.max(scale - 0.1, 0.3); draw(); }, title: '缩小' },
              h('i.fa.fa-search-minus')),
            h('button.px-2.py-1.rounded-md.text-sm.text-muted.hover\\:text-accent.transition-colors',
              { onclick: () => { scale = 1; draw(); }, title: '重置' },
              h('i.fa.fa-expand')),
          ]) : null,
          viewToggle(view, v => { view = v; draw(); }),
        ]),
      ]),

      // 视图内容
      view === 'dag'
        ? h('div.glass-card.overflow-auto.p-0', [
            h('div.dag-canvas.relative',
              {
                style: {
                  width: width * scale + 'px',
                  height: height * scale + 'px',
                  minWidth: '100%',
                  transform: `scale(${scale})`,
                  'transform-origin': 'top left',
                },
              },
              [
                drawEdges(edges),
                ...nodes.map(nodeCard),
              ]
            ),
          ])
        : listView(tasks),
    );
  }

  draw();
}
