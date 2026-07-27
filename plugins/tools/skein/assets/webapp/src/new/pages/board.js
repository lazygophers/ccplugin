// ============================================================
//  Board — 看板 / DAG
//  设计: 左 DAG/列表 + 右详情面板(点击才显) | 悬浮 popover | 状态多选筛选
//  状态: 规划中 / 待执行 / 执行中 / 验收中 / 已完成
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTasks } from '../app.js';

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
// 默认筛选: 全部 5 个状态 (DAG 需要展示完整依赖链, 包括已完成)
const DEFAULT_FILTER = new Set(ALL_STATUSES);
// 未完成态: 点击"全部"在全选/未完成之间切换
const INCOMPLETE_STATUSES = ['planning', 'ready', 'active', 'check'];

// ---- DAG 布局 ----
function layoutDAG(tasks) {
  const byId = new Map(tasks.map(t => [t.id, t]));
  const indeg = new Map();
  for (const t of tasks) indeg.set(t.id, (t.deps || []).length);

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

  const colW = 260, rowH = 110, padX = 32, padY = 24;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const t = byId.get(id);
      nodes.push({
        id, task: t,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 24, h: rowH - 16,
      });
    });
  });

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

// ---- 子任务 DAG 布局 (迷你) ----
function layoutSubDAG(subs) {
  if (!subs || !subs.length) return { nodes: [], edges: [], width: 0, height: 0 };
  const byId = new Map(subs.map(s => [s.id || s.sid, s]));
  const ids = subs.map(s => s.id || s.sid);

  const layers = [];
  const remaining = new Set(ids);
  while (remaining.size) {
    const cur = [];
    for (const id of remaining) {
      const s = byId.get(id);
      const deps = s.deps || s.dependsOn || [];
      const depDone = deps.every(d => !remaining.has(d));
      if (depDone) cur.push(id);
    }
    if (!cur.length) { cur.push(...remaining); remaining.clear(); }
    for (const id of cur) remaining.delete(id);
    layers.push(cur);
  }

  const colW = 160, rowH = 60, padX = 16, padY = 12;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const s = byId.get(id);
      nodes.push({
        id, sub: s,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 16, h: rowH - 12,
      });
    });
  });

  const edges = [];
  for (const n of nodes) {
    const deps = n.sub.deps || n.sub.dependsOn || [];
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
  const st = t.status || 'planning';
  const subs = t.subtasks || [];
  const subStats = getSubtaskStats(t);
  const hasSubs = subs.length > 0;
  const progress = hasSubs ? subStats.progress : (t.progress != null ? t.progress : (st === 'done' ? 100 : st === 'active' ? 50 : 0));

  return h('div.dag-popover', [
    h('div.dag-pop-inner', [
      h('div.dag-pop-name', [
        h(`span.dag-pop-badge.${st}`),
        h('span.truncate', t.title || t.name || '(未命名)'),
      ]),
      t.description
        ? h('div.dag-pop-desc', t.description)
        : null,
      h('div.dag-pop-bar-wrap', [
        h(`div.dag-pop-bar.${st}`, [h('i', { style: { width: progress + '%' } })]),
        h('span.dag-pop-pct', progress + '%'),
      ]),
      hasSubs
        ? h('div.dag-pop-deps',
            [`子任务 ${subStats.done}/${subs.length}`]
          )
        : null,
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
      style: {
        left: node.x + 'px', top: node.y + 'px',
        width: node.w + 'px',
      },
    },
    [
      nodePopover(node),
      h('div.dag-node.glass-card.p-3.cursor-pointer.hover-float.transition-all',
        {
          onclick: (e) => { e.preventDefault(); onClick(t.id); },
          'data-task-id': t.id,
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
          h('div.flex.items-center.justify-between.text-xs', [
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
function drawEdges(edges, getEdgeInfo) {
  if (!edges.length) return null;
  const paths = edges.map(e => {
    const x1 = e.from.x + e.from.w;
    const y1 = e.from.y + e.from.h / 2;
    const x2 = e.to.x;
    const y2 = e.to.y + e.to.h / 2;
    const mx = (x1 + x2) / 2;
    const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
    let st, dimmed = false;
    if (getEdgeInfo) {
      const info = getEdgeInfo(e);
      st = info.status;
      dimmed = info.dimmed;
    } else {
      st = (e.to.task ? e.to.task.status : e.to.sub.status) || 'planning';
    }
    const opacity = dimmed ? '0.1' : '0.4';
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${ST_COLOR[st]})`,
      'stroke-width': '2', 'stroke-opacity': opacity,
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

// ---- PRD 章节渲染 (目标/边界/验收标准) ----
function prdSectionView(prd) {
  if (!prd || !prd.length) return null;
  return prd.map(sec => {
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
  });
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

// ---- 右侧详情面板 (仅当有选中任务时显示) ----
function detailPanel(task, onClose, onSubClick, onOpenDetail) {
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
      // 描述
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-2', '任务描述'),
        h('p.text-sm.text-fg.whitespace-pre-wrap', task.description || task.desc || '暂无描述'),
      ]),

      // 基本信息
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', '基本信息'),
        infoRow('状态', h(`span.badge.badge-sm.${ST_COLOR[st]}`, ST_LABEL[st] || st)),
        infoRow('优先级', PRIO_LABEL[task.priority] || task.priority || '中'),
        infoRow('负责人', task.assignee || '未分配'),
        infoRow('预估工时', task.estimate ? task.estimate + ' h' : '—'),
        infoRow('进度', task.progress != null ? task.progress + '%' : (st === 'done' ? '100%' : '—')),
        infoRow('创建于', task.createdAt ? fmtTime(task.createdAt) : '—'),
        task.startedAt ? infoRow('开始于', fmtTime(task.startedAt)) : null,
        infoRow('更新于', task.updatedAt ? fmtTime(task.updatedAt) : '—'),
        task.finishedAt ? infoRow('完成于', fmtTime(task.finishedAt)) : null,
      ]),

      // 子任务 DAG
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', `子任务 DAG (${(task.subtasks || []).length})`),
        task.subtasks && task.subtasks.length >= 2
          ? subDAGView(task.subtasks, onSubClick)
          : task.subtasks && task.subtasks.length === 1
            ? h('div.p-2.rounded.bg-surface/50.text-sm', task.subtasks[0].title || task.subtasks[0].name || task.subtasks[0].sid)
            : h('div.py-4.text-center.text-xs.text-muted', '暂无子任务'),
      ]),

      // 时间线
      h('div.glass-card.p-4', [
        h('div.eyebrow.text-accent.mb-3', '生命周期时间线'),
        timelineView(timeline, task),
      ]),

      // 目标 / 验收标准 (来自 PRD)
      ...(prdSectionView(task.prd) || []),

      // 契约
      contractsView(task.contracts),

      // 详细设计
      task.docs && task.docs.design ? designView(task.docs.design) : null,

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

  function draw() {
    const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
    const { nodes, edges, width, height } = layoutDAG(allTasks);
    const selectedTask = allTasks.find(t => t.id === selectedId) || null;
    const hasPanel = !!selectedTask;
    const highlightedCount = allTasks.filter(t => statusSet.has(t.status)).length;

    mount.replaceChildren(
      // 标题行
      h('div.flex.items-center.justify-between.mb-4.flex-wrap.gap-3', [
        h('div', [
          h('h1.text-3xl.font-bold.text-head.mb-1', '任务看板'),
          h('p.text-muted', `${allTasks.length} 个任务 · ${highlightedCount} 个高亮`),
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
      h('div.mb-4', statusFilterBar(statusSet, countBy, setFilter)),

      // 主内容区: 左 DAG + (可选) 右详情
      h(`div.board-main.glass-card.overflow-hidden${hasPanel ? ' has-panel' : ''}`, [
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
        hasPanel ? detailPanel(selectedTask, closePanel, onSubClick, openDetailPage) : null,
      ]),
    );
  }

  draw();
}
