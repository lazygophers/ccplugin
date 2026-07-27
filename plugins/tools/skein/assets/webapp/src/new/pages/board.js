// ============================================================
//  Board — 看板 / DAG
//  设计: 左 DAG 画布 + 右详情面板 | 节点悬浮 popover | 状态筛选
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTasks } from '../app.js';

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
  pending: 'fa-clock-o', active: 'fa-spinner fa-spin',
  check: 'fa-eye', done: 'fa-check-circle', failed: 'fa-times-circle',
};
const ALL_STATUSES = ['pending', 'active', 'check', 'done', 'failed'];

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
    if (!cur.length) { cur.push(...remaining); remaining.clear(); }
    for (const id of cur) remaining.delete(id);
    layers.push(cur);
  }

  // 计算坐标 — 增加间距避免折叠
  const colW = 280, rowH = 150, padX = 48, padY = 48;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const t = byId.get(id);
      nodes.push({
        id, task: t,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 32, h: rowH - 30,
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
  const height = padY * 2 + Math.max(1, ...layers.map(l => l.length)) * rowH;
  return { nodes, edges, width, height };
}

// ---- 悬浮 popover ----
function nodePopover(node) {
  const t = node.task;
  const st = t.status || 'pending';
  const progress = t.progress != null ? t.progress : (st === 'done' ? 100 : st === 'active' ? 50 : 0);

  return h('div.dag-popover', [
    h('div.dag-pop-inner', [
      h('div.dag-pop-name', [
        h(`span.dag-pop-badge.${st}`),
        h('span.truncate', t.title || t.name || '(未命名)'),
      ]),
      t.description
        ? h('div.dag-pop-desc', t.description)
        : null,
      h(`div.dag-pop-bar.${st}`, [h('i', { style: { width: progress + '%' } })]),
      (t.deps && t.deps.length)
        ? h('div.dag-pop-deps',
            ['依赖: '].concat(t.deps.slice(0, 3).map(d => h('span', d.slice(0, 10))))
              .concat(t.deps.length > 3 ? [`+${t.deps.length - 3}`] : [])
          )
        : null,
      h('div.dag-pop-meta', [
        h('span', ST_LABEL[st] || st),
        h('span', t.updatedAt ? fmtRelative(t.updatedAt) : '—'),
      ]),
    ]),
  ]);
}

// ---- 节点卡片 ----
function nodeCard(node, onClick) {
  const t = node.task;
  const st = t.status || 'pending';
  return h('div.dag-node-wrap.absolute',
    {
      style: {
        left: node.x + 'px', top: node.y + 'px',
        width: node.w + 'px',
      },
    },
    [
      nodePopover(node),
      h('div.dag-node.glass-card.p-4.cursor-pointer.hover-float.transition-all',
        {
          onclick: (e) => { e.preventDefault(); onClick(t.id); },
          'data-task-id': t.id,
        },
        [
          // 顶部状态条
          h(`div.h-1.rounded-full.-mx-2.-mt-2.mb-3.${ST_COLOR[st]}.opacity-60`),
          // 标题行
          h('div.flex.items-start.gap-2.mb-2', [
            h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.mt-0.5.flex-shrink-0`),
            h('div.flex-1.min-w-0', [
              h('div.text-sm.font-semibold.text-head.truncate', t.title || t.name || '(未命名)'),
              h('div.text-xs.text-muted.font-mono.truncate', '#' + t.id),
            ]),
          ]),
          // 描述
          t.description
            ? h('div.text-xs.text-muted.line-clamp-2.mb-3', t.description)
            : null,
          // 底部: 状态 + 时间
          h('div.flex.items-center.justify-between.text-xs', [
            h(`span.badge.badge-sm.${ST_COLOR[st]}`, ST_LABEL[st] || st),
            h('span.text-muted', t.updatedAt ? fmtRelative(t.updatedAt) : ''),
          ]),
        ]
      ),
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

// ---- 状态筛选栏 ----
function statusFilterBar(statusFilter, countBy, onChange) {
  const total = Object.values(countBy).reduce((a, b) => a + b, 0);
  return h('div.flex.items-center.gap-2.flex-wrap', [
    h(`button.filter-btn${statusFilter === 'all' ? ' active' : ''}`,
      { onclick: () => onChange('all') },
      `全部 (${total})`
    ),
    ...ALL_STATUSES.map(st =>
      h(`button.filter-btn${statusFilter === st ? ' active' : ''}`,
        { onclick: () => onChange(st) },
        `${ST_LABEL[st]} (${countBy[st] || 0})`
      )
    ),
  ]);
}

// ---- 列表视图 ----
function listView(tasks, onClick) {
  const groups = ALL_STATUSES;
  return h('div.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
    groups.map(st => {
      const list = tasks.filter(t => (t.status || 'pending') === st);
      return h('div.glass-card', [
        h('div.flex.items-center.gap-2.mb-4', [
          h(`span.w-3.h-3.rounded-full.${ST_COLOR[st]}`),
          h('span.text-sm.font-semibold.text-head', ST_LABEL[st]),
          h('span.text-xs.text-muted.ml-auto', list.length),
        ]),
        h('div.space-y-2',
          list.length
            ? list.slice(0, 10).map(t =>
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

// ---- 右侧详情面板 ----
function detailPanel(task, onClose) {
  if (!task) {
    return h('aside.detail-panel', [
      h('div.detail-empty', [
        h('i.fa.fa-mouse-pointer'),
        h('p.text-sm', '点击任务节点查看详情'),
      ]),
    ]);
  }

  const st = task.status || 'pending';
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
      h('button.detail-panel-close',
        { onclick: onClose, title: '关闭' },
        h('i.fa.fa-times')
      ),
    ]),

    // 正文
    h('div.detail-panel-body', [
      // 描述
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-2', '任务描述'),
        h('p.text-sm.text-fg.whitespace-pre-wrap', task.description || task.desc || '暂无描述'),
      ]),

      // 基本信息
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', '基本信息'),
        infoRow('状态', h(`span.badge.badge-sm.${ST_COLOR[st]}`, ST_LABEL[st] || st)),
        infoRow('优先级', task.priority ? PRIO_LABEL[task.priority] || task.priority : '中'),
        infoRow('负责人', task.assignee || '未分配'),
        infoRow('预估工时', task.estimate ? task.estimate + ' h' : '—'),
        infoRow('进度', task.progress != null ? task.progress + '%' : (st === 'done' ? '100%' : '—')),
        infoRow('创建于', task.createdAt ? fmtTime(task.createdAt) : '—'),
        infoRow('更新于', task.updatedAt ? fmtTime(task.updatedAt) : '—'),
        task.completedAt ? infoRow('完成于', fmtTime(task.completedAt)) : null,
      ]),

      // 依赖
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', `前置依赖 (${(task.deps || []).length})`),
        (task.deps && task.deps.length)
          ? h('div.flex.flex-col.gap-2',
              task.deps.map(d =>
                h('div.flex.items-center.gap-2.p-2.rounded.bg-surface/50', [
                  h('i.fa.fa-arrow-right.text-xs.text-muted'),
                  h('span.text-sm.font-mono.text-fg.truncate', d),
                ])
              )
            )
          : h('p.text-sm.text-muted', '无前置依赖'),
      ]),

      // 下游
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', '下游任务'),
        '—（待实现）',
      ]),
    ]),
  ]);
}

const PRIO_LABEL = { high: '高优先级', mid: '中优先级', low: '低优先级' };

function infoRow(label, value) {
  return h('div.flex.gap-3.py-2', [
    h('span.text-sm.text-muted.w-20.flex-shrink-0', label),
    h('div.text-sm.text-fg.flex-1', value || '—'),
  ]);
}

// ---- 主渲染 ----
export async function render(mount) {
  const resp = await api.data().catch(() => null);
  const allTasks = normalizeTasks((resp && resp.cards) || []);

  let view = 'dag';
  let statusFilter = 'all';
  let selectedId = null;
  let scale = 1;

  // 状态计数
  const countBy = {};
  for (const t of allTasks) countBy[t.status] = (countBy[t.status] || 0) + 1;

  function getFilteredTasks() {
    if (statusFilter === 'all') return allTasks;
    return allTasks.filter(t => t.status === statusFilter);
  }

  function selectTask(id) {
    selectedId = id;
    draw();
  }

  function closePanel() {
    selectedId = null;
    draw();
  }

  function setFilter(f) {
    statusFilter = f;
    draw();
  }

  function setView(v) {
    view = v;
    draw();
  }

  function draw() {
    const filtered = getFilteredTasks();
    const { nodes, edges, width, height } = layoutDAG(filtered);
    const selectedTask = allTasks.find(t => t.id === selectedId) || null;

    mount.replaceChildren(
      // 标题行
      h('div.flex.items-center.justify-between.mb-4.flex-wrap.gap-3', [
        h('div', [
          h('h1.text-3xl.font-bold.text-head.mb-1', '任务看板'),
          h('p.text-muted', `${allTasks.length} 个任务 · ${filtered.length} 个显示中`),
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
          viewToggle(view, setView),
        ]),
      ]),

      // 状态筛选栏
      h('div.mb-4', statusFilterBar(statusFilter, countBy, setFilter)),

      // 主内容区: 左 DAG + 右详情
      h('div.flex.gap-0.min-h-\\[600px\\].glass-card.overflow-hidden', [
        // 左侧: DAG/列表
        h('div.flex-1.overflow-auto',
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
                    drawEdges(edges),
                    ...nodes.map(n => nodeCard(n, selectTask)),
                  ]
                ),
              ]
            : [listView(filtered, selectTask)]
        ),
        // 右侧: 详情面板
        detailPanel(selectedTask, closePanel),
      ]),
    );
  }

  draw();
}
