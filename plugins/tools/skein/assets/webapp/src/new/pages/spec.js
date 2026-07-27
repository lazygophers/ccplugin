// ============================================================
//  Spec — 规范 / 任务拆分规范
//  设计: 卡片式规范列表 + 搜索筛选
// ============================================================

import { h, api, fmtRelative } from '../app.js';

// ---- 规范卡片 ----
function specCard(spec) {
  return h('a.glass-card.hover-float.transition-all.cursor-pointer.block',
    { href: spec.id ? `/spec/${spec.id}` : '#', 'data-nav': spec.id ? '' : '' },
    [
      h('div.flex.items-start.gap-3.mb-3', [
        h('div.w-10.h-10.rounded-lg.bg-accent/10.text-accent.flex.items-center.justify-center.flex-shrink-0',
          h('i.fa.fa-file-text-o.text-lg')
        ),
        h('div.flex-1.min-w-0', [
          h('h3.text-base.font-semibold.text-head.truncate',
            spec.title || spec.name || '(未命名规范)'
          ),
          h('div.text-xs.text-muted.font-mono', spec.id || ''),
        ]),
      ]),
      spec.description
        ? h('p.text-sm.text-muted.line-clamp-2.mb-3', spec.description)
        : null,
      h('div.flex.items-center.justify-between.text-xs.text-muted', [
        h('span.flex.items-center.gap-1', [
          h('i.fa.fa-tasks'),
          spec.taskCount || spec.tasks || 0,
          ' 个任务模板',
        ]),
        spec.updatedAt ? fmtRelative(spec.updatedAt) : '',
      ]),
    ]
  );
}

export async function render(mount, params, ctx) {
  // 尝试取规范列表, 没有就展示内置示例
  const resp = await api.spec().catch(() => null);
  const specs = (resp && resp.specs) || [];

  // 内置示例规范 (无数据时展示)
  const demoSpecs = specs.length ? specs : [
    { id: 'feat-spec', title: '功能开发规范', description: '标准功能开发的任务拆分模板，包含需求分析、设计、开发、测试、上线全流程。', taskCount: 8, updatedAt: Date.now() - 86400000 * 2 },
    { id: 'bugfix-spec', title: 'Bug 修复规范', description: 'Bug 修复任务拆分模板，包含复现、定位、修复、验证、回归步骤。', taskCount: 5, updatedAt: Date.now() - 86400000 * 5 },
    { id: 'refactor-spec', title: '重构规范', description: '代码重构任务模板，包含评估、方案、实施、测试、文档阶段。', taskCount: 6, updatedAt: Date.now() - 86400000 * 10 },
    { id: 'release-spec', title: '发版规范', description: '版本发布流程模板，包含构建、测试、部署、验证、公告步骤。', taskCount: 7, updatedAt: Date.now() - 86400000 * 1 },
    { id: 'research-spec', title: '技术调研规范', description: '技术选型与调研任务模板，包含背景、方案对比、POC、结论输出。', taskCount: 4, updatedAt: Date.now() - 86400000 * 7 },
    { id: 'doc-spec', title: '文档编写规范', description: '技术文档编写模板，包含大纲、草稿、评审、发布流程。', taskCount: 4, updatedAt: Date.now() - 86400000 * 3 },
  ];

  mount.replaceChildren(
    // 标题
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-1', '任务规范'),
      h('p.text-muted', `${demoSpecs.length} 个可用规范 · 用于标准化任务拆分`),
    ]),

    // 搜索 + 新建
    h('div.glass-card.mb-6', [
      h('div.flex.items-center.gap-3.flex-wrap', [
        h('label.flex-1.min-w-\\[200px\\].flex.items-center.gap-2.px-3.py-2.rounded-lg.border.border-brd/60.bg-card/60', [
          h('i.fa.fa-search.text-muted'),
          h('input',
          {
            type: 'search',
            placeholder: '搜索规范名称或描述…',
            class: 'bg-transparent outline-none flex-1 text-sm w-full',
            oninput: (e) => filterSpecs(e.target.value),
          }
        ),
        ]),
        h('button.antd-btn.antd-btn-primary',
          { onclick: () => alert('新建规范功能开发中') },
          [h('i.fa.fa-plus.mr-1.5'), '新建规范']
        ),
      ]),
    ]),

    // 规范卡片网格
    h('div#spec-grid.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
      demoSpecs.map(specCard)
    ),
  );

  // 简单过滤
  function filterSpecs(keyword) {
    const grid = mount.querySelector('#spec-grid');
    if (!grid) return;
    const kw = keyword.toLowerCase().trim();
    const items = demoSpecs.filter(s =>
      !kw ||
      (s.title || '').toLowerCase().includes(kw) ||
      (s.description || '').toLowerCase().includes(kw) ||
      (s.id || '').toLowerCase().includes(kw)
    );
    grid.replaceChildren(...items.map(specCard));
  }
}
