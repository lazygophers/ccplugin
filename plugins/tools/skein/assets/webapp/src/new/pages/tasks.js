// ============================================================
//  Tasks — 任务列表
//  设计: 表格/列表视图 + 筛选 + 搜索
// ============================================================

import { h, api, fmtRelative, normalizeTasks } from '../app.js';

const ST_LABEL = { pending: '待办', active: '执行中', check: '待验收', done: '已完成', failed: '失败' };
const ST_COLOR = {
  pending: 'st-pending', active: 'st-active',
  check:   'st-check',   done: 'st-done',
  failed:  'st-failed',
};

const PRIO_LABEL = { high: '高', mid: '中', low: '低' };
const PRIO_COLOR = { high: 'danger', mid: 'warning', low: 'accent' };

function statusBadge(status) {
  return h('span.badge.badge-sm.' + ST_COLOR[status], ST_LABEL[status] || status);
}

function priorityBadge(priority) {
  const p = priority || 'mid';
  return h('span.badge.badge-sm.badge-' + PRIO_COLOR[p], PRIO_LABEL[p] + '优先级');
}

function taskRow(task) {
  return h('a.glass-card.flex.items-center.gap-4.p-4.cursor-pointer.hover\\:shadow-lg.transition-all',
    { href: '/task/' + task.id, 'data-nav-link': true },
    [
      h('div.flex-1.min-w-0', [
        h('div.flex.items-center.gap-2.mb-1.flex-wrap', [
          h('span.font-medium.text-head.truncate', task.title || task.name),
          statusBadge(task.status),
          priorityBadge(task.priority),
        ]),
        h('p.text-sm.text-muted.line-clamp-1', task.description || task.desc || '无描述'),
        task.tags && task.tags.length
          ? h('div.flex.gap-1.5.mt-2.flex-wrap',
              task.tags.slice(0, 4).map(t =>
                h('span.tag.tag-accent', '#' + t)
              )
            )
          : null,
      ]),
      h('div.text-right.text-sm.text-muted.whitespace-nowrap', [
        h('div', task.id ? '#' + task.id.slice(0, 8) : ''),
        h('div', task.createdAt ? fmtRelative(task.createdAt) : ''),
      ]),
    ]
  );
}

// ---- 主渲染 ----
export async function render(mount) {
  const resp = await api.data().catch(() => null);
  const tasks = normalizeTasks((resp && resp.cards) || []);

  let filter = 'all';
  let search = '';

  function applyFilter() {
    let filtered = tasks;
    if (filter !== 'all') {
      filtered = filtered.filter(t => t.status === filter);
    }
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(t =>
        (t.title || '').toLowerCase().includes(q) ||
        (t.description || '').toLowerCase().includes(q) ||
        (t.id || '').toLowerCase().includes(q)
      );
    }
    renderList(filtered);
  }

  function setFilter(f, btn) {
    filter = f;
    document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    applyFilter();
  }

  function renderList(list) {
    const content = document.getElementById('tasks-content');
    if (!content) return;

    if (!list.length) {
      content.replaceChildren(
        h('div.glass-card.py-16.text-center', [
          h('i.fa.fa-inbox.text-4xl.text-muted.mb-3'),
          h('p.text-muted', '没有匹配的任务'),
        ])
      );
      return;
    }

    content.replaceChildren(
      h('div.flex.flex-col.gap-3',
        list.map(taskRow)
      )
    );
  }

  // 状态计数
  const countBy = {};
  for (const t of tasks) countBy[t.status] = (countBy[t.status] || 0) + 1;

  mount.replaceChildren(
    // 页标题
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-2', '任务列表'),
      h('p.text-muted', `共 ${tasks.length} 个任务`),
    ]),

    // 筛选栏
    h('div.glass-card.p-3.mb-6', [
      h('div.flex.items-center.gap-2.flex-wrap', [
        h('button.filter-btn.active',
          { 'data-filter': 'all', onclick: (e) => setFilter('all', e.currentTarget) },
          `全部 (${tasks.length})`
        ),
        h('button.filter-btn',
          { 'data-filter': 'pending', onclick: (e) => setFilter('pending', e.currentTarget) },
          `待办 (${countBy.pending || 0})`
        ),
        h('button.filter-btn',
          { 'data-filter': 'active', onclick: (e) => setFilter('active', e.currentTarget) },
          `执行中 (${countBy.active || 0})`
        ),
        h('button.filter-btn',
          { 'data-filter': 'check', onclick: (e) => setFilter('check', e.currentTarget) },
          `待验收 (${countBy.check || 0})`
        ),
        h('button.filter-btn',
          { 'data-filter': 'done', onclick: (e) => setFilter('done', e.currentTarget) },
          `已完成 (${countBy.done || 0})`
        ),
        h('button.filter-btn',
          { 'data-filter': 'failed', onclick: (e) => setFilter('failed', e.currentTarget) },
          `失败 (${countBy.failed || 0})`
        ),
        h('div.flex-1'),
        h('label.flex.items-center.gap-2.px-3.py-1.5.rounded-lg.border.border-brd/60.bg-card/60.min-w-\\[200px\\]', [
          h('i.fa.fa-search.text-muted.text-sm'),
          h('input',
            {
              type: 'search',
              placeholder: '搜索任务…',
              class: 'bg-transparent outline-none flex-1 text-sm w-full',
              oninput: (e) => { search = e.target.value; applyFilter(); },
            }
          ),
        ]),
      ]),
    ]),

    // 任务列表
    h('div#tasks-content'),
  );

  applyFilter();
}
