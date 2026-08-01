// ============================================================
//  Spec — 规范 (.skein/spec/ 下 namespace × 类目 × md)
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
  return h('a.card.transition-all.cursor-pointer.block',
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

// 值渲染: 数组 → chip 组; 状态 → 徽标; 其余 → 文本
// frontmatter 只留 5 字段 (时间类已废弃 — 注入上下文无意义且费 token)
const META_LABEL = { title: '标题', layer: '层级', category: '类目', keywords: '关键词', status: '状态' };
const META_ORDER = ['layer', 'category', 'status', 'keywords'];

function metaValue(key, val) {
  if (Array.isArray(val)) {
    return val.length
      ? h('div.flex.flex-wrap.gap-1.5', val.map(v => h('span.antd-tag', String(v))))
      : h('span.text-muted', '—');
  }
  if (key === 'status') return h('span.antd-tag' + (val === 'active' ? '.success' : ''), String(val));
  if (key === 'layer') return h('span.antd-tag', LAYER_LABEL[val] || String(val));
  return h('span', String(val));
}

// 元数据侧栏: 单列 (窄栏), 键值上下堆
function metaCard(meta) {
  const keys = [...META_ORDER.filter(k => meta[k] != null),
                ...Object.keys(meta).filter(k => k !== 'title' && !META_ORDER.includes(k))];
  if (!keys.length) return null;
  return h('div.card.p-4', [
    h('h3.section-title', [h('i.fa.fa-info-circle.text-accent'), '元数据']),
    h('div.space-y-3',
      keys.map(k => h('div', [
        h('div.text-xs.text-muted.mb-1', META_LABEL[k] || k),
        h('div.text-sm.text-fg.break-words', metaValue(k, meta[k])),
      ]))
    ),
  ]);
}

// ---- 详情: 单 spec (meta/body 由后端 /spec/file 解析好, 前端只渲染) ----
async function renderDetail(mount, relPath) {
  const resp = await api.specFile(relPath).catch(() => null);
  const seg = relPath.split('/');
  const meta = (resp && resp.meta) || {};
  const body = (resp && resp.body) || '';
  const title = meta.title || (seg[seg.length - 1] || relPath).replace(/\.md$/, '');
  mount.replaceChildren(
    h('div.mb-6', [
      h('a.text-sm.text-muted.hover\\:text-accent.transition-colors',
        { href: '/spec', 'data-nav': '' }, [h('i.fa.fa-angle-left.mr-1'), '返回规范列表']),
      h('h1.text-3xl.font-bold.text-head.mt-2.mb-1', title),
      h('div.text-xs.text-muted.font-mono', relPath),
    ]),
    // 左信息栏 (元数据) + 右正文
    h('div.grid.grid-cols-1.lg\\:grid-cols-4.gap-6.items-start', [
      h('div.lg\\:col-span-1', metaCard(meta)),
      h('div.lg\\:col-span-3.card.p-5',
        // 规则类 spec 常只有 frontmatter (标题即全部内容), body 空时给占位而非空白卡
        !resp
          ? h('div.py-16.text-center.text-muted', '规范不存在或读取失败')
          : body.trim()
            ? h('div.md-body', { html: md.renderSafe(body) })
            : h('div.py-10.text-center.text-muted.text-sm', '此规范无正文 — 全部内容见标题与左侧元数据')
      ),
    ]),
  );
}

export async function render(mount, params, ctx) {
  if (params && params.id) return renderDetail(mount, params.id);

  const tree = await api.spec().catch(() => null);
  const specs = flatten(tree);

  // 类型 = 层级 (常驻/召回) × 类目 (arch/planning/skill/...); URL query 同步
  const q = (params && params.query) || {};
  const layers = [...new Set(specs.map(s => s.layer))];
  const cats = [...new Set(specs.map(s => s.category))].sort();
  let curLayer = layers.includes(q.layer) ? q.layer : 'all';
  let curCat = cats.includes(q.cat) ? q.cat : 'all';
  let kw = q.q || '';

  function match(s) {
    if (curLayer !== 'all' && s.layer !== curLayer) return false;
    if (curCat !== 'all' && s.category !== curCat) return false;
    const k = kw.toLowerCase().trim();
    return !k || s.title.toLowerCase().includes(k) ||
      s.category.toLowerCase().includes(k) || s.id.toLowerCase().includes(k);
  }

  function apply() {
    const grid = mount.querySelector('#spec-grid');
    const cnt = mount.querySelector('#spec-count');
    if (!grid) return;
    const items = specs.filter(match);
    grid.replaceChildren(...(items.length ? items.map(specCard)
      : [h('div.py-16.text-center.text-muted', '无匹配规范')]));
    if (cnt) cnt.textContent = `${items.length} / ${specs.length} 条规范 · 来自 .skein/spec/`;
    if (ctx && ctx.setQuery) {
      ctx.setQuery({ layer: curLayer === 'all' ? null : curLayer,
                     cat: curCat === 'all' ? null : curCat, q: kw || null }, true);
    }
  }

  // 筛选 chip 组: 值 all = 不筛
  function chips(name, values, labelOf, getCur, setCur) {
    const btn = (v) => h(`button.filter-btn${getCur() === v ? '.active' : ''}`,
      { 'data-chip': name, 'data-val': v,
        onclick: (e) => {
          setCur(v);
          mount.querySelectorAll(`[data-chip="${name}"]`).forEach(b =>
            b.classList.toggle('active', b.getAttribute('data-val') === v));
          apply();
        } },
      labelOf(v));
    return h('div.flex.items-center.gap-2.flex-wrap',
      [h('span.text-xs.text-muted.w-10.flex-shrink-0', name === 'layer' ? '层级' : '类目'),
       btn('all'), ...values.map(btn)]);
  }

  mount.replaceChildren(
    h('div.mb-6', [
      h('h1.text-3xl.font-bold.text-head.mb-1', '项目规范'),
      h('p#spec-count.text-muted', `${specs.length} 条规范 · 来自 .skein/spec/`),
    ]),

    h('div.card.mb-6.space-y-3', [
      h('label.flex.items-center.gap-2.px-3.py-2.rounded-lg.border.border-brd\\/60.bg-card\\/60', [
        h('i.fa.fa-search.text-muted'),
        h('input', {
          type: 'search', value: kw,
          placeholder: '搜索规范标题或类目…',
          class: 'bg-transparent outline-none flex-1 text-sm w-full',
          oninput: (e) => { kw = e.target.value; apply(); },
        }),
      ]),
      chips('layer', layers, v => v === 'all' ? '全部' : (LAYER_LABEL[v] || v),
            () => curLayer, v => { curLayer = v; }),
      chips('cat', cats, v => v === 'all' ? '全部' : v, () => curCat, v => { curCat = v; }),
    ]),

    h('div#spec-grid.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4',
      specs.length ? specs.filter(match).map(specCard)
        : h('div.py-16.text-center.text-muted', '暂无规范 (.skein/spec/ 为空)')
    ),
  );
}
