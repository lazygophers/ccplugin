// ============================================================
//  Dashboard — 概览
//  设计: 4 个 KPI 玻璃卡 + 状态分布 + 最近活跃任务 + 最近完成
// ============================================================

import { h, api, fmtRelative, normalizeTasks } from '../app.js';

// ---- 颜色辅助 ----
const ST_COLOR = {
  pending: 'st-pending', active: 'st-active',
  check:   'st-check',   done: 'st-done',
  failed:  'st-failed',
};
const ST_LABEL = {
  pending: '待办', active: '执行中',
  check:   '待验收', done: '已完成', failed: '失败',
};

// ---- KPI 玻璃卡 ----
function kpiCard(label, value, iconClass, colorVar, trend) {
  return h('div.glass-card.hover-float.transition-all', [
    h('div.flex.items-start.justify-between.mb-3', [
      h('span.text-sm.text-muted.font-medium', label),
      h(`div.w-10.h-10.rounded-lg.flex.items-center.justify-center.text-${colorVar}.bg-${colorVar}/10`,
        h(`i.fa.${iconClass}.text-lg`)
      ),
    ]),
    h('div.text-3xl.font-bold.text-head.mb-1', String(value)),
    trend ? h('div.text-xs.text-muted', trend) : null,
  ]);
}

// ---- 状态分布进度条 ----
function statusDistribution(stats) {
  const total = Object.values(stats).reduce((a, b) => a + b, 0) || 1;
  const order = ['pending', 'active', 'check', 'done', 'failed'];
  const items = order.map(s => ({
    key: s, label: ST_LABEL[s], count: stats[s] || 0,
    pct: ((stats[s] || 0) / total) * 100,
    color: ST_COLOR[s],
  }));

  return h('div.glass-card', [
    h('h3.section-title', '状态分布'),
    // 堆叠进度条
    h('div.h-3.rounded-full.bg-line.overflow-hidden.flex.mb-4',
      items.filter(i => i.count > 0).map(it =>
        h(`div.h-full.bg-${it.color}.transition-all.duration-500`,
          { style: { width: it.pct + '%' } }
        )
      )
    ),
    // 图例 + 数字
    h('div.grid.grid-cols-2.md\\:grid-cols-5.gap-3',
      items.map(it =>
        h('div.flex.items-center.gap-2', [
          h(`span.w-2.5.h-2.5.rounded-full.bg-${it.color}.flex-shrink-0`),
          h('div', [
            h('div.text-xs.text-muted', it.label),
            h('div.text-sm.font-semibold.text-head',
              `${it.count} `, h('span.text-muted.font-normal', `(${it.pct.toFixed(0)}%)`)
            ),
          ]),
        ])
      )
    ),
  ]);
}

// ---- 任务列表行 ----
function taskRow(task) {
  const st = task.status || 'pending';
  return h(`a.task-row.flex.items-center.gap-3.p-3.rounded-lg.border.border-transparent.hover\\:border-brd\\/60.hover\\:bg-card\\/40.transition-all.cursor-pointer`,
    { href: `/task/${task.id}`, 'data-nav': '' },
    [
      h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[st]}.flex-shrink-0`),
      h('div.flex-1.min-w-0', [
        h('div.text-sm.font-medium.text-head.truncate',
          task.title || task.name || '(未命名)'
        ),
        h('div.text-xs.text-muted.truncate',
          task.description || task.id
        ),
      ]),
      h(`span.antd-tag.antd-tag-${st}.flex-shrink-0`, ST_LABEL[st] || st),
      h('span.text-xs.text-muted.flex-shrink-0',
        task.updatedAt ? fmtRelative(task.updatedAt) : ''
      ),
    ]
  );
}

// ---- 列表卡片 ----
function listCard(title, icon, tasks, emptyText) {
  return h('div.glass-card', [
    h('h3.section-title', [
      h(`i.fa.${icon}.text-accent`),
      title,
    ]),
    tasks && tasks.length
      ? h('div.divide-y divide-line/50', tasks.map(taskRow))
      : h('div.py-12.text-center.text-muted text-sm', emptyText || '暂无数据'),
  ]);
}

// ---- 主渲染 ----
export async function render(mount) {
  // 并发取数据
  const [dataResp, dashResp] = await Promise.all([
    api.data(), api.dashboard(),
  ]).catch(() => [null, null]);

  const tasks = normalizeTasks((dataResp && dataResp.cards) || (dashResp && dashResp.tasks) || []);
  const stats = (dashResp && dashResp.stats) || {};

  // 状态计数
  const countBy = {};
  for (const t of tasks) {
    const s = t.status || 'pending';
    countBy[s] = (countBy[s] || 0) + 1;
  }

  // 最近活跃: pending + active + check
  const recentActive = tasks
    .filter(t => ['pending', 'active', 'check'].includes(t.status))
    .sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0))
    .slice(0, 8);

  // 最近完成
  const recentDone = tasks
    .filter(t => t.status === 'done' || t.status === 'failed')
    .sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0))
    .slice(0, 5);

  // 总体进度
  const doneCount = countBy.done || 0;
  const totalCount = tasks.length || 1;
  const progressPct = Math.round((doneCount / totalCount) * 100);

  mount.replaceChildren(
    // 页标题
    h('div.mb-8', [
      h('h1.text-3xl.font-bold.text-head.mb-2', '项目概览'),
      h('p.text-muted', `共 ${tasks.length} 个任务 · 完成度 ${progressPct}%`),
    ]),

    // KPI 4 卡
    h('div.grid.grid-cols-2.lg\\:grid-cols-4.gap-4.mb-6', [
      kpiCard('总任务', tasks.length, 'fa-tasks', 'accent',
        `${progressPct}% 完成率`),
      kpiCard('进行中', countBy.active || 0, 'fa-spinner', 'st-active',
        `${countBy.check || 0} 个待验收`),
      kpiCard('待办', countBy.pending || 0, 'fa-clock-o', 'st-pending',
        '等待开始'),
      kpiCard('已完成', countBy.done || 0, 'fa-check-circle', 'st-done',
        `${countBy.failed || 0} 个失败`),
    ]),

    // 状态分布
    h('div.mb-6', statusDistribution(countBy)),

    // 两列: 最近活跃 + 最近完成
    h('div.grid.grid-cols-1.lg\\:grid-cols-3.gap-6', [
      h('div.lg\\:col-span-2', listCard('最近活跃', 'fa-bolt', recentActive, '暂无进行中的任务')),
      h('div', listCard('最近完成', 'fa-check-square-o', recentDone, '暂无已完成的任务')),
    ]),
  );
}
