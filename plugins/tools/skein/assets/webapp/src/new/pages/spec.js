// ============================================================
//  Spec — 规范 (.skein/spec/ 下 core/recall × 类目 × md)
//  设计: 列表 = 卡片网格 + 搜索; 详情 = /spec/detail?id=<rel path> 渲染 md 原文
// ============================================================

import { h, api, md } from '../app.js';

const LAYER_LABEL = { core: '常驻', recall: '召回' };

// 树 {layer: {category: [file]}} → 扁平列表 [{id, layer, category, title}]
function flatten(tree) {
  const out = [];
  for (const [layer, cats] of Object.entries(tree || {})) {
    for (const [category, files] of Object.entries(cats || {})) {
      for (const f of files) {
        out.push({ id: `${layer}/${category}/${f}`, layer, category,
                   title: f.replace(/\.md$/, '') });
      }
    }
  }
  return out;
}

// ---- 规范卡片 ----
function specCard(spec) {
  return h('a.glass-card.hover-float.transition-all.cursor-pointer.block',
    // 参数一律 query (core `[arch] webapp 参数一律 query`), 禁 /spec/<id> path 参数
    { href: `/spec/detail?id=${encodeURIComponent(spec.id)}`, 'data-nav': '' },
    [
      h('div.flex.items-start.gap-3', [
        h('div.w-10.h-10.rounded-lg.bg-accent\\/10.text-accent.flex.items-center.justify-center.flex-shrink-0',
          h('i.fa.fa-file-text-o.text-lg')
        ),
        h('div.flex-1.min-w-0', [
          h('h3.text-base.font-semibold.text-head.truncate', spec.title),
          h('div.text-xs.text-muted.font-mono.truncate', spec.id),
        ]),
      ]),
      h('div.flex.items-center.gap-2.mt-3.text-xs.text-muted', [
        h('span.antd-tag', LAYER_LABEL[spec.layer] || spec.layer),
        h('span.antd-tag', spec.category),
      ]),
    ]
  );
}

// ---- 详情: 单 spec md 原文 ----
async function renderDetail(mount, relPath) {
  const resp = await api.specFile(relPath).catch(() => null);
  const seg = relPath.split('/');
  mount.replaceChildren(
    h('div.mb-6', [
      h('a.text-sm.text-muted.hover\\:text-accent.transition-colors',
        { href: '/spec', 'data-nav': '' }, [h('i.fa.fa-angle-left.mr-1'), '返回规范列表']),
      h('h1.text-3xl.font-bold.text-head.mt-2.mb-1',
        (seg[seg.length - 1] || relPath).replace(/\.md$/, '')),
      h('div.text-xs.text-muted.font-mono', relPath),
    ]),
    h('div.glass-card.p-5',
      resp && resp.content
        ? h('div.md-body', { html: md.renderSafe(resp.content) })
        : h('div.py-16.text-center.text-muted', '规范不存在或读取失败')
    ),
  );
}

export async function render(mount, params) {
  if (params && params.id) return renderDetail(mount, params.id);

  const tree = await api.spec().catch(() => null);
  const specs = flatten(tree);

  mount.replaceChildren(
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-1', '项目规范'),
      h('p.text-muted', `${specs.length} 条规范 · 来自 .skein/spec/`),
    ]),

    h('div.glass-card.mb-6',
      h('label.flex.items-center.gap-2.px-3.py-2.rounded-lg.border.border-brd\\/60.bg-card\\/60', [
        h('i.fa.fa-search.text-muted'),
        h('input', {
          type: 'search',
          placeholder: '搜索规范标题或类目…',
          class: 'bg-transparent outline-none flex-1 text-sm w-full',
          oninput: (e) => filterSpecs(e.target.value),
        }),
      ])
    ),

    h('div#spec-grid.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
      specs.length ? specs.map(specCard)
        : h('div.py-16.text-center.text-muted', '暂无规范 (.skein/spec/ 为空)')
    ),
  );

  function filterSpecs(keyword) {
    const grid = mount.querySelector('#spec-grid');
    if (!grid) return;
    const kw = keyword.toLowerCase().trim();
    const items = specs.filter(s => !kw ||
      s.title.toLowerCase().includes(kw) ||
      s.category.toLowerCase().includes(kw) ||
      s.id.toLowerCase().includes(kw));
    grid.replaceChildren(...items.map(specCard));
  }
}
