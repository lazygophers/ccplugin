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

// ---- DAG 布局 ----
function layoutDAG(tasks, size = 'md') {
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

  // 响应式布局参数
  const SIZES = {
    sm: { colW: 260, rowH: 180, padX: 32, padY: 24, gapX: 24, gapY: 16 },
    md: { colW: 300, rowH: 200, padX: 40, padY: 30, gapX: 30, gapY: 20 },
    lg: { colW: 340, rowH: 220, padX: 50, padY: 40, gapX: 36, gapY: 24 },
    xl: { colW: 380, rowH: 240, padX: 60, padY: 50, gapX: 40, gapY: 28 },
  };
  const s = SIZES[size] || SIZES.md;
  const { colW, rowH, padX, padY, gapX: gx, gapY: gy } = s;

  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const t = byId.get(id);
      nodes.push({
        id, task: t,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - gx, h: rowH - gy,
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
  let offsetX = 0, offsetY = 0;
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
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      const ns = getSize();
      if (ns !== curSize) { curSize = ns; draw(); }
    }, 150);
  });

  // ---- DAG 拖拽平移 ----
  function initDrag() {
    const wrap = document.getElementById('board-dag-wrap');
    const canvas = wrap ? wrap.querySelector('.dag-canvas') : null;
    if (!wrap || !canvas || view !== 'dag') return;

    let isDragging = false;
    let startX = 0, startY = 0;
    let startOffsetX = 0, startOffsetY = 0;

    function onMouseMove(e) {
      if (!isDragging) return;
      offsetX = startOffsetX + (e.clientX - startX);
      offsetY = startOffsetY + (e.clientY - startY);
      canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
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
      startOffsetX = offsetX;
      startOffsetY = offsetY;
      wrap.style.cursor = 'grabbing';
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
      e.preventDefault();
    }

    function onTouchMove(e) {
      if (!isDragging || e.touches.length !== 1) return;
      e.preventDefault();
      offsetX = startOffsetX + (e.touches[0].clientX - startX);
      offsetY = startOffsetY + (e.touches[0].clientY - startY);
      canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
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
      startOffsetX = offsetX;
      startOffsetY = offsetY;
      wrap.addEventListener('touchmove', onTouchMove, { passive: false });
      wrap.addEventListener('touchend', onTouchEnd);
    }

    wrap.style.cursor = 'grab';
    wrap.addEventListener('mousedown', onMouseDown);
    wrap.addEventListener('touchstart', onTouchStart, { passive: true });
  }

  function draw() {
    const allSelected = ALL_STATUSES.every(s => statusSet.has(s));
    const { nodes, edges, width, height } = layoutDAG(allTasks, curSize);
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
              { onclick: () => { scale = 1; offsetX = 0; offsetY = 0; draw(); }, title: '重置' },
              h('i.fa.fa-expand')),
          ]) : null,
          viewToggle(view, setView),
        ]),
      ]),

      // 状态筛选栏
      h('div.mb-4', statusFilterBar(statusSet, countBy, setFilter)),

      // 主内容区: 左 DAG/列表 + (可选) 右详情
      h(`div.board-main.glass-card${hasPanel ? ' has-panel' : ''}`, [
        // 左侧: DAG/列表
        h('div.flex-1.board-dag-wrap', { id: 'board-dag-wrap' },
          view === 'dag'
            ? [
                h('div.dag-canvas.relative',
                  {
                    style: {
                      width: width + 'px',
                      height: height + 'px',
                      minWidth: '100%',
                      transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
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
    setTimeout(initDrag, 0);
  }

  draw();
}
