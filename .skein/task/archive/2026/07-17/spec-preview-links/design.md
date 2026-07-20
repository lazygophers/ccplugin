# spec 预览本地文件链接 — 详细设计

## 架构

两处改: md.js (渲染 wikilink) + spec.js (click 委托跳转)。

```
spec body 含 [[slug]]
  → md.renderSafe → inline() 识别 [[slug]] → <a class="spec-wl" data-name="slug">slug</a>
  → v-html 插入预览 div
  → 用户点 .spec-wl → click 委托 (预览容器 @click)
  → 读 e.target.dataset.name → 遍历 this.index 找 path.endsWith("/"+name+".md")
  → 命中: this.selectFile(path) (async 加载 + 切 view 模式)
  → 未命中: no-op (纯文本已渲染, 无链接行为)
```

## md.js inline() 改动

wikilink 规则插在标准链接 `[text](url)` (L14) **之后** (标准链接优先, wikilink 是独立语法不冲突):

```js
// wikilink: [[slug]] 或 [[slug|别名]] → spec 内部跳转链接
s = s.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, function (_, slug, alias) {
  return '<a class="spec-wl" data-name="' + slug + '">' + (alias || slug) + '</a>';
});
```

注意: 此规则在 esc **之后**跑 (s 已 escape), 故 `[[...]]` 原文已变 `[[...]]` (方括号非 HTML 特殊字符, 不受 esc 影响)。slug 含 `<` 等会被 esc 拦截 → 安全。data-name 不加引号转义风险: slug 若含 `"` 会断属性, 但 wikilink slug 通常是 word/-/_, 实际不会含。保守可加 slug.replace(/"/g,"")。

## spec.js 改动

1. 预览容器加 click 委托:
```html
<div v-else-if="mode==='view'" class="md-body" v-html="rendered" @click="onPreviewClick"></div>
```

2. 加方法 `onPreviewClick(e)`:
```js
onPreviewClick(e) {
  var a = e.target.closest('.spec-wl');
  if (!a) return;
  var name = a.dataset.name;
  if (!name) return;
  var hit = Object.values(this.index).find(function (f) {
    return f.path.endsWith('/' + name + '.md');
  });
  if (hit) this.selectFile(hit.path);
},
```

selectFile 已含 mode='view' + 清 fileErr + 加载 content, 复用即可。

## 取舍

- **wikilink 不用 href**: v-html 内容不经 petite-vue 编译, 无法绑 @click; 用 data-name + 事件委托是 petite-vue 下唯一可行法。
- **匹配用 endsWith**: slug 无路径层级信息, 全 index 扫一遍 O(n), spec 文件数 <100, 性能无忧。
- **未命中不报错**: wikilink 可能引用还没创建的文件 (Obsidian 惯例), 静默降级纯文本优于报错。
- **不支持 `[[slug|anchor]]` 锚点**: Obsidian 的 heading 锚点超出范围, 只支持 `[[slug|显示别名]]`。

## 不含调度图

2 文件微改 (md.js ~3 行 + spec.js ~10 行), worktree 豁免原地做。调度归 task.json。
