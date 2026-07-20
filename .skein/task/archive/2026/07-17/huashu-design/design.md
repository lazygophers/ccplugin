# /spec 三栏重设计 — 设计

## 布局 (三栏, h-[calc(100vh-120px)])

```
┌─────────┬───────────────┬───────────────────────────┐
│ 导航树  │ 文件列表      │ 详情区                    │
│ w-56    │ w-72          │ flex-1                    │
│         │               │                           │
│ 🔍搜索  │ [搜索框]      │ 面包屑 core/recall>cat>f  │
│ CORE    │ · esm-00  ops │ [chip:recall][chip:ops]   │
│ RECALL  │ · checker ops │ ─── toggle: 预览 | 编辑 ──│
│  arch   │ · soft-d ops  │                           │
│  frontend│              │ 预览: md renderSafe       │
│  ops ●  │               │ 编辑: metadata表单+textarea│
│  style  │               │                           │
└─────────┴───────────────┴───────────────────────────┘
```

## 第一栏: 导航树 (w-56, card)
- 顶部: 标题 "Spec 记忆" + 概览计数 (core N / recall M)
- 两层折叠: CORE · 常驻 / RECALL · 按需召回; 各层下类目 (arch/frontend/ops/style) 折叠
- 点击类目 → 中栏切换到该 category 文件列表
- 选中态: accent 左边框 + 背景

## 第二栏: 文件列表 (w-72, card)
- 顶部搜索框: 按 title/keywords/文件名 模糊过滤 (客户端 filter)
- 列出当前选中 layer+category 下的文件; 无选中则列全部 (按 layer 分组)
- 每项: 文件名 + 小标签 (category) + title 摘要 (首行)
- 点击 → 右栏加载; 选中态 accent

## 第三栏: 详情区 (flex-1, card)
### 顶部信息条
- 面包屑: `recall / ops / esm-check-...`
- 标签 chip: [layer] [category]
- toggle 按钮组: **预览** | **编辑** (segmented pill, 复用 skein nav pill 风格)

### 预览模式
- `md.renderSafe(content)` 渲染 (含 frontmatter 时, frontmatter 段不渲染为正文 — parse 出来显示到 metadata 表单只读区; 正文只渲染 `---` 之后的 body)

### 编辑模式 (双区)
- **metadata 表单** (顶部, card 内嵌):
  - title: text input (宽)
  - layer: select (core/recall)
  - category: select (arch/frontend/ops/style)
  - keywords: 标签输入 (逗号/回车分隔, 渲染为 chip, 可删)
  - source: text input
  - authored-by: text input
  - created: number (unix ts) input
  - 无 frontmatter 的文件: 表单空 + 提示 "无 metadata, 可新建"
- **正文 textarea** (下方):
  - 等宽字体 (font-mono)
  - 行号槽 (左侧绝对定位行号列, 跟随滚动) — ponytail: 简单实现, textarea 旁 gutter div 同步 scrollTop
  - Tab 键插入 2 空格 (keydown 拦截)
  - `class="spec-editor"` (input.css 定义样式)

### 保存流程
1. 编辑态: draft = serializeFrontmatter(metaForm) + "\n---\n" + bodyDraft
2. Cmd+S 或 点"保存…" → showDiff = true (全屏 diff)
3. diff 全屏覆盖层 (z-modal 2000):
   - 左右双列? 否 — 单列行级 (保留现有 LCS diffLines), 但全屏 + 更大行号槽 + 更强增删色
   - 顶部: +N / -N 统计 + 路径
   - 底部: 取消 / 确认落盘
4. confirmSave → api.specSave(path, draft)

## 快捷键 (编辑态)
- Cmd+S / Ctrl+S → reviewSave (preventDefault)
- Esc → cancelEdit (或关 diff)

## frontmatter parse/serialize (spec.js 内新增轻量函数)
```js
// ponytail: spec frontmatter 都是 flat YAML (key: val / key: [a,b,c]), 不引 yaml 库
function parseFM(md) {
  const m = md.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: md };
  const meta = {};
  m[1].split("\n").forEach((line) => {
    const i = line.indexOf(":");
    if (i < 0) return;
    const k = line.slice(0, i).trim(), v = line.slice(i + 1).trim();
    if (v.startsWith("[") && v.endsWith("]")) meta[k] = v.slice(1, -1).split(",").map(s => s.trim()).filter(Boolean);
    else meta[k] = v;
  });
  return { meta, body: m[2] };
}
function serializeFM(meta, body) {
  const lines = Object.entries(meta).map(([k, v]) => {
    if (Array.isArray(v)) return `${k}: [${v.join(", ")}]`;
    return `${k}: ${v}`;
  });
  return `---\n${lines.join("\n")}\n---\n${body}`;
}
```

## input.css 新增
```css
.spec-3col { display:grid; grid-template-columns: 224px 288px 1fr; gap:1rem; height:calc(100vh - 120px); }
.spec-nav, .spec-list, .spec-detail { overflow:auto; }
.spec-meta-form { display:grid; grid-template-columns: 1fr 1fr; gap:.5rem .75rem; padding:.75rem; border:1px solid var(--line); border-radius:.5rem; margin-bottom:.75rem; }
.spec-meta-form .full { grid-column: 1 / -1; }
.spec-editor-wrap { position:relative; }
.spec-gutter { position:absolute; left:0; top:0; width:2.5rem; height:100%; overflow:hidden; font-family:var(--font-mono,monospace); font-size:13px; line-height:1.5rem; color:var(--muted); text-align:right; padding-right:.5rem; pointer-events:none; }
.spec-editor { padding-left:2.75rem; font-family:var(--font-mono,monospace); font-size:13px; line-height:1.5rem; tab-size:2; }
.spec-kw-chip { display:inline-flex; align-items:center; gap:.25rem; padding:.1rem .4rem; border-radius:.25rem; background:var(--line); font-size:.75rem; }
```

## dist 重建
input.css 改 → 跑 build-css.sh 重建 dist/app.css

## 不改
- diffLines LCS 函数 (复用)
- api 契约 (spec/specFile/specSave)
- 后端 spec endpoint
- 其他 pages

## 验证
- 三栏渲染, 搜索过滤, metadata 表单编辑保存往返 (parse→edit→serialize→save→reload 一致)
- Cmd+S / Esc 快捷键
- diff 全屏
- ESM node --input-type=module spec.js 过
- dist 重建含 .spec-* 类
