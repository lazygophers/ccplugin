// ============================================================
//  Task — 任务详情
//  设计: 左详情(描述/目标/边界/验收/设计/时间线/子任务) + 右信息面板
//  状态: 规划中 / 待执行 / 执行中 / 验收中 / 已完成
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTask, normalizeTasks } from '../app.js';

const ST_LABEL = {
  planning: '规划中', ready: '待执行',
  active:   '执行中', check: '验收中',
  done:     '已完成', failed: '失败',
};
const ST_COLOR = {
  planning: 'st-planning', ready: 'st-ready',
  active:   'st-active',  check: 'st-check',
  done:     'st-done',    failed: 'st-failed',
};
const ST_ICON = {
  planning: 'fa-lightbulb-o', ready: 'fa-flag-o',
  active:   'fa-spinner fa-spin', check: 'fa-eye',
  done:     'fa-check-circle', failed: 'fa-times-circle',
};

// ---- 信息项 ----
function infoItem(label, value) {
  return h('div.flex.gap-3.py-2', [
    h('span.text-sm.text-muted.w-20.flex-shrink-0', label),
    h('div.text-sm.text-fg.flex-1', value || '—'),
  ]);
}

// ---- 时间线 ----
function buildTimeline(task) {
  const events = [];
  if (task.createdAt) events.push({ type: '创建任务', time: task.createdAt, icon: 'fa-plus-circle', color: 'st-planning' });
  if (task.startedAt) events.push({ type: '开始执行', time: task.startedAt, icon: 'fa-play', color: 'st-active' });
  if (task.checkedAt) events.push({ type: '进入验收', time: task.checkedAt, icon: 'fa-eye', color: 'st-check' });
  if (task.finishedAt) events.push({ type: '已完成', time: task.finishedAt, icon: 'fa-check-circle', color: 'st-done' });
  if (task.subtasks && task.subtasks.length) {
    for (const s of task.subtasks) {
      if (s.createdAt) events.push({ type: `子任务创建: ${s.title || s.name || s.sid}`, time: s.createdAt, icon: 'fa-tasks', color: 'st-planning' });
      if (s.finishedAt) events.push({ type: `子任务完成: ${s.title || s.name || s.sid}`, time: s.finishedAt, icon: 'fa-check', color: 'st-done' });
    }
  }
  events.sort((a, b) => a.time - b.time);
  return events;
}

function timelineView(events) {
  if (!events || !events.length) {
    return h('div.py-8.text-center.text-muted.text-sm', '暂无活动记录');
  }
  return h('div.relative',
    events.map((ev, i) =>
      h('div.flex.gap-3.relative.pb-5', [
        h('div.relative.flex-shrink-0.w-5', [
          h(`span.absolute.left-2.top-1.-translate-x-1/2.w-2.5.h-2.5.rounded-full.bg-${ev.color || 'accent'}.border-2.border-card`),
          i < events.length - 1
            ? h('span.absolute.left-2.top-3.bottom-0.w-px.bg-line.-translate-x-1/2')
            : null,
        ]),
        h('div.flex-1.pb-1', [
          h('div.text-sm.text-fg.font-medium', ev.type),
          ev.message ? h('div.text-xs.text-muted.mt-0.5', ev.message) : null,
          h('div.text-xs.text-muted.mt-1', ev.time ? fmtTime(ev.time) : ''),
        ]),
      ])
    )
  );
}

// ---- 子任务 DAG 布局 ----
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

  const colW = 200, rowH = 72, padX = 20, padY = 16;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const s = byId.get(id);
      nodes.push({
        id, sub: s,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 16, h: rowH - 14,
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

function subDAGView(subs, onSubClick) {
  const { nodes, edges, width, height } = layoutSubDAG(subs);
  if (!nodes.length) return h('div.py-6.text-center.text-xs.text-muted', '暂无子任务');

  // SVG 连线
  const paths = edges.map(e => {
    const x1 = e.from.x + e.from.w;
    const y1 = e.from.y + e.from.h / 2;
    const x2 = e.to.x;
    const y2 = e.to.y + e.to.h / 2;
    const mx = (x1 + x2) / 2;
    const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
    const st = e.to.sub.status || 'planning';
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${ST_COLOR[st]})`,
      'stroke-width': '2', 'stroke-opacity': '0.5',
    });
  });

  return h('div.sub-dag-wrap.overflow-auto', [
    h('div.relative',
      { style: { width: width + 'px', height: height + 'px', minWidth: '100%' } },
      [
        h('svg.absolute.inset-0.pointer-events-none',
          { style: { width: '100%', height: '100%' } },
          paths
        ),
        ...nodes.map(n =>
          h(`div.sub-dag-node.absolute.glass-card.p-2.cursor-pointer.transition-all`,
            {
              style: { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h + 'px' },
              onclick: (e) => { if (onSubClick) onSubClick(n.id); },
              title: n.sub.title || n.sub.name || n.id,
            },
            [
              h('div.flex.items-center.gap-2.mb-1', [
                h(`span.w-2.h-2.rounded-full.flex-shrink-0.bg-${ST_COLOR[n.sub.status || 'planning']}`),
                h('span.text-xs.font-medium.text-head.truncate', n.sub.title || n.sub.name || n.id),
              ]),
              h('div.text-xs.text-muted', ST_LABEL[n.sub.status || 'planning'] || n.sub.status),
            ]
          )
        ),
      ]
    ),
  ]);
}

// ---- PRD 章节渲染 ----
function prdSectionView(prd) {
  if (!prd || !prd.length) return [];
  return prd.map(sec => {
    const icon = sec.name === '目标' ? 'fa-bullseye' : sec.name === '验收标准' ? 'fa-check-square-o' : 'fa-file-text-o';
    const color = sec.name === '目标' ? 'st-planning' : sec.name === '验收标准' ? 'st-check' : 'st-active';
    return h('div.glass-card.p-5', [
      h('h3.section-title', [
        h(`i.fa.${icon}.text-${color}`),
        sec.name + (sec.badge ? ` (${sec.badge[0]}/${sec.badge[1]})` : ''),
      ]),
      sec.items && sec.items.length
        ? h('div.space-y-2',
            sec.items.map(item =>
              h('div.flex.items-start.gap-3.text-sm', [
                item.kind === 'check'
                  ? h(`i.fa.${item.done ? 'fa-check-square' : 'fa-square-o'}.${item.done ? 'text-st-done' : 'text-muted'}.mt-0.5.flex-shrink-0`)
                  : h('span.w-1.5.h-1.5.rounded-full.bg-muted.mt-2.flex-shrink-0'),
                h('span.text-fg.leading-relaxed' + (item.done ? '.line-through.text-muted' : ''), item.text),
              ])
            )
          )
        : h('p.text-sm.text-muted', '—'),
    ]);
  });
}

// ---- 契约 ----
function contractsView(contracts) {
  if (!contracts || !contracts.length) return null;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-handshake-o.text-st-check'),
      `契约 (${contracts.length})`,
    ]),
    h('div.space-y-3',
      contracts.map((c, i) =>
        h('div.p-3.rounded-lg.bg-surface/50.border.border-brd/30', [
          h('div.text-sm.font-semibold.text-head', c.name || c.title || `契约 ${i + 1}`),
          c.desc || c.description ? h('div.text-xs.text-muted.mt-1.leading-relaxed', c.desc || c.description) : null,
        ])
      )
    ),
  ]);
}

// ---- 详细设计 ----
function designView(design) {
  if (!design) return null;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-sitemap.text-st-active'),
      '详细设计',
    ]),
    h('pre.text-xs.text-fg.whitespace-pre-wrap.font-mono.bg-surface/30.p-4.rounded-lg.overflow-x-auto', design),
  ]);
}

// ---- 子任务列表 ----
function subtaskListView(subs) {
  if (!subs || !subs.length) return null;
  const done = subs.filter(s => s.status === 'done').length;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-tasks.text-accent'),
      `子任务列表`,
      h('span.ml-2.text-xs.text-muted', `(${done}/${subs.length})`),
    ]),
    h('div.space-y-2',
      subs.map(s => {
        const st = s.status || 'planning';
        return h('div.flex.items-center.gap-3.p-3.rounded-lg.hover\\:bg-card/40.transition-colors', [
          h(`span.w-2.5.h-2.5.rounded-full.flex-shrink-0.bg-${ST_COLOR[st]}`),
          h('div.flex-1.min-w-0', [
            h('div.text-sm.text-fg.truncate', s.title || s.name || s.sid || s.id),
            h('div.text-xs.text-muted', ST_LABEL[st] || st),
          ]),
          s.progress != null
            ? h('span.text-xs.text-muted', s.progress + '%')
            : null,
        ]);
      })
    ),
  ]);
}

// ---- 主渲染 ----
export async function render(mount, params, ctx) {
  const taskId = params.id;

  // 并行: 任务详情 + 所有任务(用于依赖渲染)
  const [taskResp, allResp] = await Promise.all([
    api.task(taskId),
    api.data(),
  ]).catch(() => [null, null]);

  // 用列表数据补充详情数据(prd 等只在列表接口有)
  const taskRaw = taskResp && (taskResp.task || taskResp.card || taskResp);
  const listTask = allResp && allResp.cards ? allResp.cards.find(c => c.id === taskId) : null;
  const mergedTask = listTask && taskRaw ? { ...listTask, ...taskRaw } : (taskRaw || listTask);
  const task = normalizeTask(mergedTask);
  const allTasks = normalizeTasks((allResp && allResp.cards) || []);

  if (!task) {
    mount.replaceChildren(
      h('div.glass-card.py-16.text-center', [
        h('i.fa.fa-exclamation-triangle.text-4xl.text-warning.mb-3'),
        h('h2.text-xl.font-semibold.text-head.mb-2', '任务不存在'),
        h('p.text-muted.mb-4', `ID: ${taskId}`),
        h('a.antd-btn.antd-btn-primary',
          { href: '/dashboard', 'data-nav': '' },
          '返回概览'),
      ])
    );
    return;
  }

  const st = task.status || 'planning';
  const deps = task.deps || [];
  const depTasks = allTasks.filter(t => deps.includes(t.id));
  const dependents = allTasks.filter(t => (t.deps || []).includes(taskId));
  const timeline = buildTimeline(task);

  function onSubClick(sid) {
    console.log('subtask clicked:', sid);
  }

  mount.replaceChildren(
    // 面包屑 + 标题
    h('div.mb-6', [
      h('nav.flex.items-center.gap-2.text-sm.text-muted.mb-3', [
        h('a.hover\\:text-accent.transition-colors', { href: '/dashboard', 'data-nav': '' }, '概览'),
        h('i.fa.fa-angle-right.text-xs'),
        h('a.hover\\:text-accent.transition-colors', { href: '/board', 'data-nav': '' }, '看板'),
        h('i.fa.fa-angle-right.text-xs'),
        h('span.text-head', task.title || task.name || task.id),
      ]),
      h('div.flex.items-start.justify-between.flex-wrap.gap-3', [
        h('div', [
          h('div.flex.items-center.gap-3.mb-2', [
            h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.text-xl`),
            h('h1.text-3xl.font-bold.text-head', task.title || task.name || '(未命名)'),
          ]),
          h('div.flex.items-center.gap-3.text-sm.text-muted', [
            h('span.font-mono', '#' + task.id),
            h('span·opacity-40', '·'),
            h('span', task.createdAt ? '创建于 ' + fmtRelative(task.createdAt) : ''),
            h('span·opacity-40', '·'),
            h('span', task.updatedAt ? '更新于 ' + fmtRelative(task.updatedAt) : ''),
          ]),
        ]),
        h(`span.antd-tag.antd-tag-${ST_COLOR[st].replace('st-', '')}.text-base.px-4.py-1`, ST_LABEL[st] || st),
      ]),
    ]),

    // 两列布局
    h('div.grid.grid-cols-1.lg\\:grid-cols-3.gap-6', [
      // 左: 详情
      h('div.lg\\:col-span-2.space-y-6', [
        // 描述
        task.description
          ? h('div.glass-card.p-5', [
              h('h3.section-title', '任务描述'),
              h('div.text-sm.text-fg.leading-relaxed.whitespace-pre-wrap', task.description),
            ])
          : null,

        // 目标 / 验收标准 (来自 PRD)
        ...prdSectionView(task.prd),

        // 契约
        contractsView(task.contracts),

        // 详细设计
        task.docs && task.docs.design ? designView(task.docs.design) : null,

        // 子任务 DAG
        task.subtasks && task.subtasks.length >= 2
          ? h('div.glass-card.p-5', [
              h('h3.section-title', [
                h('i.fa.fa-sitemap.text-accent'),
                `子任务 DAG (${task.subtasks.length})`,
              ]),
              subDAGView(task.subtasks, onSubClick),
            ])
          : null,

        // 子任务列表
        subtaskListView(task.subtasks),

        // 时间线
        h('div.glass-card.p-5', [
          h('h3.section-title', [
            h('i.fa.fa-history.text-accent'),
            '活动时间线',
          ]),
          timelineView(timeline),
        ]),
      ]),

      // 右: 信息面板
      h('div.space-y-6', [
        // 基本信息
        h('div.glass-card.p-5', [
          h('h3.section-title', '基本信息'),
          infoItem('状态', h(`span.antd-tag.antd-tag-${ST_COLOR[st].replace('st-', '')}`, ST_LABEL[st] || st)),
          infoItem('优先级',
            task.priority === 'high' ? '高' : task.priority === 'low' ? '低' : '中'
          ),
          infoItem('负责人', task.assignee || '未分配'),
          infoItem('预估工时', task.estimate ? task.estimate + ' 小时' : '—'),
          infoItem('进度', task.progress != null ? task.progress + '%' : '—'),
          task.createdAt ? infoItem('创建于', fmtTime(task.createdAt)) : null,
          task.startedAt ? infoItem('开始于', fmtTime(task.startedAt)) : null,
          task.checkedAt ? infoItem('验收于', fmtTime(task.checkedAt)) : null,
          task.finishedAt ? infoItem('完成于', fmtTime(task.finishedAt)) : null,
        ]),

        // 前置依赖
        h('div.glass-card.p-5', [
          h('h3.section-title', [
            h('i.fa.fa-link.text-accent'),
            '前置依赖',
            ` (${depTasks.length})`,
          ]),
          depTasks.length
            ? h('div.space-y-2',
                depTasks.map(d =>
                  h(`a.flex.items-center.gap-2.p-2.rounded-lg.hover\\:bg-card\\/40.transition-colors`,
                    { href: `/task/${d.id}`, 'data-nav': '' },
                    [
                      h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[d.status || 'planning']}`),
                      h('span.text-sm.text-fg.truncate.flex-1', d.title || d.name || d.id),
                    ]
                  )
                )
              )
            : h('div.py-4.text-center.text-xs.text-muted', '无前置依赖'),
        ]),

        // 被依赖
        dependents.length
          ? h('div.glass-card.p-5', [
              h('h3.section-title', [
                h('i.fa.fa-share-alt.text-accent'),
                '被依赖',
                ` (${dependents.length})`,
              ]),
              h('div.space-y-2',
                dependents.map(d =>
                  h(`a.flex.items-center.gap-2.p-2.rounded-lg.hover\\:bg-card\\/40.transition-colors`,
                    { href: `/task/${d.id}`, 'data-nav': '' },
                    [
                      h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[d.status || 'planning']}`),
                      h('span.text-sm.text-fg.truncate.flex-1', d.title || d.name || d.id),
                    ]
                  )
                )
              ),
            ])
          : null,

        // 操作
        h('div.glass-card.p-5', [
          h('h3.section-title', [
            h('i.fa.fa-cog.text-accent'),
            '操作',
          ]),
          h('div.flex.flex-wrap.gap-2', [
            h('button.antd-btn.antd-btn-primary.flex-1',
              { onclick: () => alert('编辑功能开发中') },
              [h('i.fa.fa-pencil.mr-1.5'), '编辑']
            ),
            st === 'planning'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alert('状态变更开发中') },
                  [h('i.fa.fa-flag.mr-1.5'), '就绪'])
              : null,
            st === 'ready'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alert('状态变更开发中') },
                  [h('i.fa.fa-play.mr-1.5'), '开始'])
              : null,
            st === 'active'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alert('状态变更开发中') },
                  [h('i.fa.fa-check.mr-1.5'), '提交验收'])
              : null,
          ]),
        ]),
      ]),
    ]),
  );
}
