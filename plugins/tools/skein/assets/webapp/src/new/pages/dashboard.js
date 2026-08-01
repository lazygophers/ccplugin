// ============================================================
//  Dashboard — 概览
//  设计: 4 个 KPI 卡片 + 紧凑状态网格 + 最近活跃 / 最近完成列表
//  主题: beach ocean/sand（暗=暮色海岸，亮=晴空碧海），无 glassmorphism，无堆叠进度条
// ============================================================

import { h, api, fmtRelative, normalizeTasks, normalizeStatus } from '../app.js';
import { aggregateEta, fmtHours, overallProgress } from '../eta.js';

// ---- 状态元数据 ----
const ST_META = {
  planning: { key: 'planning', label: '规划中', color: 'st-planning', icon: 'fa-pencil-square-o' },
  ready:    { key: 'ready',    label: '待执行', color: 'st-ready',    icon: 'fa-clock-o' },
  active:   { key: 'active',   label: '执行中', color: 'st-active',   icon: 'fa-spinner' },
  check:    { key: 'check',    label: '待验收', color: 'st-check',    icon: 'fa-eye' },
  done:     { key: 'done',     label: '已完成', color: 'st-done',     icon: 'fa-check' },
};
const ST_ORDER = ['planning', 'ready', 'active', 'check', 'done'];

// ---- KPI 卡片 ----
function kpiCard(label, value, iconClass, colorVar, hint) {
  return h('div.card.hover\:border-hover.transition-all', [
    h('div.flex.items-start.justify-between.mb-2', [
      h('span.text-xs.text-muted.font-medium', label),
      h(`div.w-9.h-9.rounded-lg.flex.items-center.justify-center.text-${colorVar}.bg-${colorVar}/10`,
        h(`i.fa.${iconClass}`)
      ),
    ]),
    h('div.text-2xl.font-bold.text-head.mb-1', String(value)),
    hint ? h('div.text-xs.text-muted.truncate', hint) : null,
  ]);
}

// ---- 紧凑状态网格（替代堆叠进度条） ----
function statusGrid(stats) {
  const total = Object.values(stats).reduce((a, b) => a + b, 0) || 1;
  return h('div.card', [
    h('h3.section-title-sm.mb-3', '状态分布'),
    h('div.grid.grid-cols-2.md\\:grid-cols-5.gap-2',
      ST_ORDER.map((s) => {
        const meta = ST_META[s];
        const count = stats[s] || 0;
        const pct = ((count / total) * 100).toFixed(0);
        return h('div.flex.items-center.gap-2.p-2.rounded-lg.bg-card', [
          h(`div.w-8.h-8.rounded-lg.flex.items-center.justify-center.text-${meta.color}.bg-${meta.color}/10`,
            h(`i.fa.${meta.icon}.text-xs`)
          ),
          h('div.min-w-0', [
            h('div.text-xs.text-muted', meta.label),
            h('div.text-sm.font-semibold.text-head', `${count}`,
              h('span.text-muted.font-normal.ml-1', `(${pct}%)`)
            ),
          ]),
        ]);
      })
    ),
  ]);
}

// ---- 任务列表行 ----
function taskRow(task) {
  const st = task.status || 'planning';
  const meta = ST_META[st] || ST_META.planning;
  return h('a.flex.items-center.gap-3.p-2.rounded-lg.border.border-transparent.hover\\:border-brd\\/60.hover\\:bg-card\\/40.transition-all.cursor-pointer',
    { href: `/task/detail?id=${task.id}`, 'data-nav': '' },
    [
      h(`span.w-2.h-2.rounded-full.bg-${meta.color}.flex-shrink-0`),
      h('div.flex-1.min-w-0', [
        h('div.text-sm.font-medium.text-head.truncate',
          task.title || task.name || '(未命名)'
        ),
        h('div.text-xs.text-muted.truncate',
          task.description || task.id
        ),
      ]),
      h(`span.antd-tag.antd-tag-${st}.flex-shrink-0`, meta.label),
      h('span.text-xs.text-muted.flex-shrink-0',
        task.updatedAt ? fmtRelative(task.updatedAt) : ''
      ),
    ]
  );
}

// ---- 列表卡片 ----
function listCard(title, icon, tasks, emptyText) {
  return h('div.card', [
    h('h3.section-title-sm.mb-3', [
      h(`i.fa.${icon}.text-accent`),
      title,
    ]),
    tasks && tasks.length
      ? h('div.divide-y.divide-line\\/50', tasks.map(taskRow))
      : h('div.py-10.text-center.text-muted.text-sm', emptyText || '暂无数据'),
  ]);
}

// ---- 主渲染 ----
export async function render(mount) {
  const dash = await api.dashboard().catch(() => null) || {};

  // statusDist 键是中文状态 → 归一到 5 状态系统
  const countBy = {};
  for (const [k, v] of Object.entries(dash.statusDist || {})) {
    const s = normalizeStatus(k);
    countBy[s] = (countBy[s] || 0) + v;
  }

  const recentActive = normalizeTasks(dash.recentActive || []);
  const recentDone = normalizeTasks(dash.recentDone || []);
  const taskCount = dash.taskCount || 0;
  const doneRate = dash.doneRate || 0;

  const etaTasks = normalizeTasks(dash.etaCards || []);
  const overallPct = overallProgress(etaTasks);
  const agg = aggregateEta(etaTasks, dash.maxActive || 2);
  const remainText = agg.hours > 0 ? fmtHours(agg.hours) : '—';
  const remainHint = agg.hours > 0
    ? `总工时 ${fmtHours(agg.work)} · 并发 ${dash.maxActive || 2}` +
      (agg.unknown ? ` · ${agg.unknown} 个未估工时` : '')
    : (etaTasks.length ? '全部完成' : '暂无任务');

  mount.replaceChildren(
    // 页标题
    h('div.mb-5', [
      h('h1.text-2xl.font-bold.text-head.mb-1', '项目概览'),
      h('p.text-sm.text-muted', `共 ${taskCount} 个任务 · 整体进度 ${overallPct}% · 预计剩余 ${remainText}`),
    ]),

    // KPI 4 卡
    h('div.grid.grid-cols-2.lg\\:grid-cols-4.gap-3.mb-4', [
      kpiCard('整体进度', `${overallPct}%`, 'fa-tasks', 'accent',
        `${countBy.done || 0}/${taskCount} 完成 · 按工时加权`),
      kpiCard('预计剩余', remainText, 'fa-hourglass-half', 'st-planning', remainHint),
      kpiCard('进行中', countBy.active || 0, 'fa-spinner', 'st-active',
        `${countBy.check || 0} 个待验收`),
      kpiCard('待办', (countBy.planning || 0) + (countBy.ready || 0), 'fa-clock-o', 'st-ready',
        `${countBy.ready || 0} 个已就绪 · ${doneRate}% 完成率`),
    ]),

    // 状态分布
    h('div.mb-4', statusGrid(countBy)),

    // 两列: 最近活跃 + 最近完成
    h('div.grid.grid-cols-1.lg\\:grid-cols-3.gap-4', [
      h('div.lg\\:col-span-2', listCard('最近活跃', 'fa-bolt', recentActive, '暂无进行中的任务')),
      h('div', listCard('最近完成', 'fa-check-square-o', recentDone, '暂无已完成的任务')),
    ]),
  );
}
