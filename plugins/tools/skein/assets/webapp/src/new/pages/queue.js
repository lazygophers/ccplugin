// ============================================================
//  Queue — 队列 (等待执行的任务)
//  设计: 列表视图 + 优先级排序 + 操作按钮
// ============================================================

import { h, api, fmtRelative, normalizeTasks } from '../app.js';

const PRIO_LABEL = { high: '高', mid: '中', low: '低' };
const PRIO_COLOR = { high: 'danger', mid: 'warning', low: 'accent' };
const ST_LABEL = { pending: '待办', active: '执行中', check: '待验收', done: '已完成', failed: '失败' };
const ST_COLOR = {
  pending: 'st-pending', active: 'st-active',
  check: 'st-check', done: 'st-done', failed: 'st-failed',
};

function priorityBadge(p) {
  const prio = p || 'mid';
  return h(`span.px-2.py-0.5.rounded-full.text-xs.font-medium.text-${PRIO_COLOR[prio]}.bg-${PRIO_COLOR[prio]}/10`,
    PRIO_LABEL[prio] + '优先'
  );
}

export async function render(mount, params, ctx) {
  const [dataResp, queueResp] = await Promise.all([
    api.data(), api.queue(),
  ]).catch(() => [null, null]);

  const tasks = normalizeTasks((queueResp && queueResp.tasks) || (dataResp && dataResp.cards) || []);

  // 队列: pending + active + check, 按优先级 + 时间排序
  const queueTasks = tasks
    .filter(t => ['pending', 'active', 'check'].includes(t.status))
    .sort((a, b) => {
      const prioOrder = { high: 0, mid: 1, low: 2 };
      const pa = prioOrder[a.priority] ?? 1;
      const pb = prioOrder[b.priority] ?? 1;
      if (pa !== pb) return pa - pb;
      return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
    });

  const activeCount = queueTasks.filter(t => t.status === 'active').length;
  const pendingCount = queueTasks.filter(t => t.status === 'pending').length;

  mount.replaceChildren(
    // 标题
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-1', '任务队列'),
      h('p.text-muted',
        `${queueTasks.length} 个任务在队列 · ${activeCount} 个执行中 · ${pendingCount} 个待执行`
      ),
    ]),

    // 统计条
    h('div.grid.grid-cols-3.gap-4.mb-6', [
      h('div.glass-card.text-center', [
        h('div.text-2xl.font-bold.text-st-active.mb-1', activeCount),
        h('div.text-xs.text-muted', '执行中'),
      ]),
      h('div.glass-card.text-center', [
        h('div.text-2xl.font-bold.text-st-pending.mb-1', pendingCount),
        h('div.text-xs.text-muted', '待执行'),
      ]),
      h('div.glass-card.text-center', [
        h('div.text-2xl.font-bold.text-st-check.mb-1',
          queueTasks.filter(t => t.status === 'check').length),
        h('div.text-xs.text-muted', '待验收'),
      ]),
    ]),

    // 列表
    h('div.glass-card.p-0.overflow-hidden', [
      h('div.p-4.border-b.border-brd/40.flex.items-center.justify-between', [
        h('div.flex.items-center.gap-2', [
          h('i.fa.fa-list-ul.text-accent'),
          h('span.font-semibold.text-head', '队列列表'),
        ]),
        h('span.text-xs.text-muted', '按优先级排序'),
      ]),
      queueTasks.length
        ? h('div.divide-y divide-line/40',
            queueTasks.map(t => {
              const st = t.status || 'pending';
              return h(`a.flex.items-center.gap-4.p-4.hover\\:bg-card\\/40.transition-colors.cursor-pointer`,
                { href: `/task/${t.id}`, 'data-nav': '' },
                [
                  // 状态指示
                  h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[st]}.flex-shrink-0`),
                  // 主体
                  h('div.flex-1.min-w-0', [
                    h('div.flex.items-center.gap-2.mb-1', [
                      h('span.text-sm.font-medium.text-head.truncate',
                        t.title || t.name || '(未命名)'),
                      priorityBadge(t.priority),
                    ]),
                    h('div.text-xs.text-muted.truncate',
                      t.description || t.id
                    ),
                  ]),
                  // 右侧: 状态 + 时间
                  h('div.text-right.flex-shrink-0', [
                    h(`span.antd-tag.antd-tag-${st}`, ST_LABEL[st] || st),
                    h('div.text-xs.text-muted.mt-1',
                      t.createdAt ? '创建于 ' + fmtRelative(t.createdAt) : ''
                    ),
                  ]),
                ]
              );
            })
          )
        : h('div.py-16.text-center', [
            h('i.fa.fa-inbox.text-4xl.text-muted.opacity-40.mb-3'),
            h('div.text-muted', '队列为空'),
          ]),
    ]),
  );
}
