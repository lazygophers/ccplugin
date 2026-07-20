# spec 预览本地文件引用超链接

## 目标

spec 预览支持两种本地文件引用链接, 提升跨文件导航体验:
1. `[[wikilink-name]]` (Obsidian 式) → 页内跳转预览该 spec 文件
2. `[text](path)` 标准 md 链接 → 已渲染, 补点击行为 (新窗口打开)

## 边界

- **[[wikilink]]**: `\[\[([^\]|]+)(\|([^\]]+))?\]\]` → `<a class="spec-wl" data-name="slug">displayText</a>` (支持 `[[slug|别名]]` 语法, 无别名显示 slug)
- **匹配**: 在 app.index 中查 path 以 `/<slug>.md` 结尾的项; 找到 → selectFile 跳转; 找不到 → 纯文本 (无链接, 不报错)
- **跳转**: 页内预览 (不新页), selectFile(path) 复用现有加载逻辑
- **[text](path)**: md.js 已渲染为 `<a href>`, sanitize 已加 target=_blank; 本地相对路径点击浏览器会相对当前 URL 解析 → 够用, 不额外处理
- **范围外**: wikilink 跨项目引用 / 图片 wikilink / 嵌套 wikilink 不支持

## 验收标准

- [x] md.js inline() 加 wikilink 规则: `[[slug]]` / `[[slug|别名]]` → `<a class="spec-wl" data-name="slug">文本</a>`
- [x] wikilink 规则在 esc 后跑 (防 XSS, data-name 只允许 word/-/_ 字符)
- [x] spec.js 预览容器加 click 委托: 点 `.spec-wl` → 读 data-name → 查 index 匹配 → selectFile
- [x] 找不到匹配文件 → 纯文本降级 (不报错, 不 toast)
- [x] wikilink 在 `[text](url)` 标准链接规则之后匹配 (优先级: wikilink 语法独立, 不与标准链接冲突)
- [x] chrome 实测: spec 文件含 `[[async-fire-and-forget-sediment-00]]` → 预览显可点击 → 点击跳转到该文件预览

## 索引

- 详细设计: [design.md](design.md)
- 调度: task.json (脚本真值, `skein.py subtask list spec-preview-links`)
