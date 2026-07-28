// ============================================================
//  Archive — 归档 (已完成 / 已取消的任务)
//  设计: 时间线式归档列表 + 筛选
// ============================================================

import { h, api, fmtRelative, fmtTime, normalizeTasks } from '../app.js';

const ST_LABEL = { done: '已完成', failed: '失败', cancelled: '已取消', archived: '已归档' };
const ST_COLOR = { done: 'st-done', failed: 'st-failed', cancelled: 'muted', archived: 'muted' };

// ---- 归档项 ----
function archiveItem(task) {
  const st = task.status || 'done';
  return h(`a.flex.items-start.gap-4.p-4.rounded-xl.border.border-brd/40.bg-card/30.hover\\:bg-card\\/60.hover\\:border-brd\\/60.transition-all.cursor-pointer`,
    { href: `/task/detail?id=${task.id}`, 'data-nav': '' },
    [
      // 左侧状态图标
      h(`div.w-10.h-10.rounded-lg.flex.items-center.justify-center.flex-shrink-0.bg-${ST_COLOR[st]}/10.text-${ST_COLOR[st]}`,
        st === 'done'
          ? h('i.fa.fa-check-circle.text-lg')
          : st === 'failed'
          ? h('i.fa.fa-times-circle.text-lg')
          : h('i.fa.fa-archive.text-lg')
      ),
      // 中间内容
      h('div.flex-1.min-w-0', [
        h('div.flex.items-center.gap-2.mb-1', [
          h('span.text-sm.font-medium.text-head.truncate',
            task.title || task.name || '(未命名)'
          ),
          h(`span.antd-tag.antd-tag-${st === 'cancelled' || st === 'archived' ? 'done' : st}.text-xs`,
            ST_LABEL[st] || st
          ),
        ]),
        task.description
          ? h('div.text-xs.text-muted.line-clamp-2.mb-2', task.description)
          : null,
        h('div.flex.items-center.gap-3.text-xs.text-muted', [
          h('span.font-mono', '#' + task.id),
          task.completedAt || task.updatedAt
            ? h('span', fmtTime(task.completedAt || task.updatedAt))
            : null,
        ]),
      ]),
      // 右侧箭头
      h('i.fa.fa-chevron-right.text-muted.flex-shrink-0.mt-3'),
    ]
  );
}

// ---- 分组 ----
function archiveGroup(title, icon, items) {
  if (!items.length) return null;
  return h('div.mb-8', [
    h('div.flex.items-center.gap-2.mb-3', [
      h(`i.fa.${icon}.text-accent`),
      h('span.text-sm.font-semibold.text-head', title),
      h('span.text-xs.text-muted.ml-1', `(${items.length})`),
    ]),
    h('div.space-y-3', items.map(archiveItem)),
  ]);
}

export async function render(mount, params, ctx) {
  const [dataResp, archResp] = await Promise.all([
    api.data(), api.archive(),
  ]).catch(() => [null, null]);

  const tasks = normalizeTasks((archResp && archResp.tasks) || (dataResp && dataResp.cards) || []);

  // 归档: done + failed + cancelled + archived
  const archived = tasks.filter(t =>
    ['done', 'failed', 'cancelled', 'archived'].includes(t.status)
  );

  const doneTasks = archived.filter(t => t.status === 'done');
  const failedTasks = archived.filter(t => t.status === 'failed');
  const otherTasks = archived.filter(t =>
    !['done', 'failed'].includes(t.status)
  );

  // 按完成时间倒序
  const byTime = (a, b) =>
    new Date(b.completedAt || b.updatedAt || 0) - new Date(a.completedAt || a.updatedAt || 0);
  doneTasks.sort(byTime);
  failedTasks.sort(byTime);
  otherTasks.sort(byTime);

  const q = (params && params.query) || {};
  const VALID_FILTERS = ['all', 'done', 'failed'];
  let currentFilter = VALID_FILTERS.includes(q.status) ? q.status : 'all';
  let searchKw = q.q || '';
  let searchTimer = 0;

  function syncSearchQuery(val) {
    if (ctx && ctx.setQuery) {
      ctx.setQuery({ q: val || null });
    }
  }

  function setFilter(f, btn) {
    currentFilter = f;
    // 更新 tab 样式
    mount.querySelectorAll('.archive-tab').forEach(b => {
      b.className = 'archive-tab px-3 py-1.5 rounded-md text-sm font-medium text-muted hover:text-fg transition-colors';
    });
    if (btn) btn.className = 'archive-tab px-3 py-1.5 rounded-md text-sm font-medium bg-accent/20 text-accent';
    if (ctx && ctx.setQuery) {
      ctx.setQuery({ status: f === 'all' ? null : f });
    }
    applyFilter(searchKw);
  }

  function applyFilter(kw) {
    searchKw = kw != null ? kw : searchKw;
    const content = mount.querySelector('#archive-content');
    if (!content) return;

    const kwL = searchKw.toLowerCase().trim();
    let d = doneTasks, f = failedTasks, o = otherTasks;
    if (currentFilter === 'done') { f = []; o = []; }
    if (currentFilter === 'failed') { d = []; o = []; }

    const filt = list => list.filter(t =>
      !kwL ||
      (t.title || t.name || '').toLowerCase().includes(kwL) ||
      (t.description || '').toLowerCase().includes(kwL) ||
      (t.id || '').toLowerCase().includes(kwL)
    );

    d = filt(d); f = filt(f); o = filt(o);

    const hasAny = d.length || f.length || o.length;
    content.replaceChildren(
      ...(hasAny
        ? [
            archiveGroup('已完成', 'fa-check-circle', d),
            archiveGroup('失败', 'fa-times-circle', f),
            o.length ? archiveGroup('其他', 'fa-archive', o) : null,
          ].filter(Boolean)
        : [h('div.glass-card.py-16.text-center', [
            h('i.fa.fa-search.text-4xl.text-muted.opacity-40.mb-3'),
            h('div.text-muted', '没有匹配的归档任务'),
          ])]
      )
    );
  }

  mount.replaceChildren(
    // 标题
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-1', '任务归档'),
      h('p.text-muted',
        `${archived.length} 个已归档任务 · ${doneTasks.length} 个完成 · ${failedTasks.length} 个失败`
      ),
    ]),

    // 筛选 tab
    h('div.flex.items-center.gap-2.mb-6.glass.rounded-lg.p-1.w-fit.border.border-brd/40', [
      h(`button.archive-tab.px-3.py-1.5.rounded-md.text-sm.font-medium${currentFilter === 'all' ? '.bg-accent/20.text-accent' : '.text-muted.hover\\:text-fg.transition-colors'}`,
        { 'data-filter': 'all', onclick: (e) => setFilter('all', e.currentTarget) },
        '全部'),
      h(`button.archive-tab.px-3.py-1.5.rounded-md.text-sm.font-medium${currentFilter === 'done' ? '.bg-accent/20.text-accent' : '.text-muted.hover\\:text-fg.transition-colors'}`,
        { 'data-filter': 'done', onclick: (e) => setFilter('done', e.currentTarget) },
        '已完成'),
      h(`button.archive-tab.px-3.py-1.5.rounded-md.text-sm.font-medium${currentFilter === 'failed' ? '.bg-accent/20.text-accent' : '.text-muted.hover\\:text-fg.transition-colors'}`,
        { 'data-filter': 'failed', onclick: (e) => setFilter('failed', e.currentTarget) },
        '失败'),
    ]),

    // 搜索
  h('div.glass-card.mb-6', [
    h('label.flex.items-center.gap-2', [
      h('i.fa.fa-search.text-muted'),
      h('input',
        {
          type: 'search',
          placeholder: '搜索已归档的任务…',
          class: 'bg-transparent outline-none flex-1 text-sm w-full',
          value: searchKw,
          oninput: (e) => {
            const val = e.target.value;
            applyFilter(val);
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => syncSearchQuery(val), 400);
          },
        }
      ),
    ]),
  ]),

    // 归档内容
    h('div#archive-content',
      archived.length
        ? [
            archiveGroup('已完成', 'fa-check-circle', doneTasks),
            archiveGroup('失败', 'fa-times-circle', failedTasks),
            otherTasks.length ? archiveGroup('其他', 'fa-archive', otherTasks) : null,
          ]
        : [h('div.glass-card.py-16.text-center', [
            h('i.fa.fa-archive.text-4xl.text-muted.opacity-40.mb-3'),
            h('div.text-muted.mb-1', '暂无归档任务'),
            h('div.text-xs.text-muted', '已完成或失败的任务会显示在这里'),
          ])]
    ),
  );

  // 应用初始筛选/搜索
  if (currentFilter !== 'all' || searchKw) {
    applyFilter(searchKw);
  }
}
