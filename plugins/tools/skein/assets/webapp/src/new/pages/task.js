// ============================================================
//  Task — 任务详情
//  设计: 左侧详情 + 右侧时间线 / 依赖
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTask, normalizeTasks } from '../app.js';

const ST_LABEL = { pending: '待办', active: '执行中', check: '待验收', done: '已完成', failed: '失败' };
const ST_COLOR = {
  pending: 'st-pending', active: 'st-active',
  check: 'st-check', done: 'st-done', failed: 'st-failed',
};
const ST_ICON = {
  pending: 'fa-clock-o', active: 'fa-spinner.fa-spin',
  check: 'fa-eye', done: 'fa-check-circle', failed: 'fa-times-circle',
};

// ---- 信息项 ----
function infoItem(label, value) {
  return h('div.flex.gap-3.py-2', [
    h('span.text-sm.text-muted.w-20.flex-shrink-0', label),
    h('div.text-sm.text-fg.flex-1', value || '—'),
  ]);
}

// ---- 时间线 ----
function timeline(events) {
  if (!events || !events.length) {
    return h('div.py-8.text-center.text-muted.text-sm', '暂无活动记录');
  }
  return h('div.relative',
    events.map((ev, i) =>
      h('div.flex.gap-3.relative.pb-5', [
        // 竖线 + 圆点
        h('div.relative.flex-shrink-0.w-5', [
          h('span.absolute.left-2.top-1.-translate-x-1/2.w-2.5.h-2.5.rounded-full.bg-accent.border-2.border-card'),
          i < events.length - 1
            ? h('span.absolute.left-2.top-3.bottom-0.w-px.bg-line.-translate-x-1/2')
            : null,
        ]),
        // 内容
        h('div.flex-1.pb-1', [
          h('div.text-sm.text-fg.font-medium', ev.type || ev.action || '事件'),
          ev.message ? h('div.text-xs.text-muted.mt-0.5', ev.message) : null,
          h('div.text-xs.text-muted.mt-1',
            ev.timestamp ? fmtTime(ev.timestamp) : ''
          ),
        ]),
      ])
    )
  );
}

// ---- 主渲染 ----
export async function render(mount, params, ctx) {
  const taskId = params.id;

  // 并行: 任务详情 + 所有任务(用于依赖渲染)
  const [taskResp, allResp] = await Promise.all([
    api.task(taskId),
    api.data(),
  ]).catch(() => [null, null]);

  const task = normalizeTask(taskResp && (taskResp.task || taskResp.card || taskResp));
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

  const st = task.status || 'pending';
  const deps = task.deps || [];
  const depTasks = allTasks.filter(t => deps.includes(t.id));
  const dependents = allTasks.filter(t => (t.deps || []).includes(taskId));

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
        h(`span.antd-tag.antd-tag-${st}.text-base.px-4.py-1`, ST_LABEL[st] || st),
      ]),
    ]),

    // 两列布局
    h('div.grid.grid-cols-1.lg\\:grid-cols-3.gap-6', [
      // 左: 详情
      h('div.lg\\:col-span-2.space-y-6', [
        // 描述
        task.description
          ? h('div.glass-card', [
              h('h3.section-title', '任务描述'),
              h('div.text-sm.text-fg.leading-relaxed.whitespace-pre-wrap', task.description),
            ])
          : null,

        // 验收标准
        task.acceptance
          ? h('div.glass-card', [
              h('h3.section-title', [
                h('i.fa.fa-check-square-o.text-st-check'),
                '验收标准',
              ]),
              h('div.text-sm.text-fg.leading-relaxed.whitespace-pre-wrap', task.acceptance),
            ])
          : null,

        // 时间线
        h('div.glass-card', [
          h('h3.section-title', [
            h('i.fa.fa-history.text-accent'),
            '活动记录',
          ]),
          timeline(task.events || task.logs || []),
        ]),
      ]),

      // 右: 信息面板
      h('div.space-y-6', [
        // 基本信息
        h('div.glass-card', [
          h('h3.section-title', '基本信息'),
          infoItem('状态', h(`span.antd-tag.antd-tag-${st}`, ST_LABEL[st] || st)),
          infoItem('优先级',
            task.priority === 'high' ? '高' : task.priority === 'low' ? '低' : '中'
          ),
          infoItem('负责人', task.assignee || '未分配'),
          infoItem('预估工时', task.estimate ? task.estimate + ' 小时' : '—'),
          infoItem('进度', task.progress != null ? task.progress + '%' : '—'),
        ]),

        // 前置依赖
        h('div.glass-card', [
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
                      h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[d.status || 'pending']}`),
                      h('span.text-sm.text-fg.truncate.flex-1', d.title || d.name || d.id),
                    ]
                  )
                )
              )
            : h('div.py-4.text-center.text-xs.text-muted', '无前置依赖'),
        ]),

        // 被依赖
        dependents.length
          ? h('div.glass-card', [
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
                      h(`span.w-2.h-2.rounded-full.bg-${ST_COLOR[d.status || 'pending']}`),
                      h('span.text-sm.text-fg.truncate.flex-1', d.title || d.name || d.id),
                    ]
                  )
                )
              ),
            ])
          : null,

        // 操作
        h('div.glass-card', [
          h('h3.section-title', [
            h('i.fa.fa-cog.text-accent'),
            '操作',
          ]),
          h('div.space-y-2', [
            ['active', '开始执行', 'fa-play'].slice(0, 1), // placeholder
          ]),
          h('div.flex.flex-wrap.gap-2', [
            h('button.antd-btn.antd-btn-primary.flex-1',
              { onclick: () => alert('编辑功能开发中') },
              [h('i.fa.fa-pencil.mr-1.5'), '编辑']
            ),
            st === 'pending'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alert('状态变更开发中') },
                  [h('i.fa.fa-play.mr-1.5'), '开始'])
              : null,
            st === 'active'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alert('状态变更开发中') },
                  [h('i.fa.fa-check.mr-1.5'), '完成'])
              : null,
          ]),
        ]),
      ]),
    ]),
  );
}
