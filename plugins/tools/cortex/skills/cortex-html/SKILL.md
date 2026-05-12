---
name: cortex-html
description: 生成 HTML 片段 — badge/card/timeline/mermaid/heatmap/disclosure, 模板替换 {{VAR}} 占位。触发: "render html" / "生成 HTML 片段" / 其他 skill (cortex-dashboard) 内部调用。
disable-model-invocation: false
allowed-tools: Read Write
---

# cortex-html

读 `_templates/html/<template>.{html,md}` 片段, 用传入 data dict 替换 `{{VAR}}` 占位, 输出 HTML 字符串 (stdout) 或写入指定文件。

## 触发场景
- cortex-dashboard 内部拼装看板时调用
- cortex-summarizer 生成 HTML callout 时调用
- 用户显式 "render html badge" / "生成 timeline"

## 输入
- template: 片段名, 必填; 候选:
  - `badge` / `card` / `timeline` (.html)
  - `mermaid-flowchart` / `mermaid-sankey` / `mermaid-mindmap` (.md, mermaid fence)
  - `canvas-heatmap` (.html)
  - `progressive-disclosure` (.html)
- data: dict, key 匹配模板 `{{KEY}}` 占位 (必填项由模板顶部注释声明)
- --out: 可选, 写入文件路径 (默认 stdout)
- --inline: 可选, 输出去 HTML 注释 (节省 token)

## 流程

1. **解析模板路径**:
   - vault 内: `<vault>/_templates/html/<template>.{html,md}` (优先)
   - plugin fallback: `<PLUGIN_ROOT>/templates/html/<template>.{html,md}`
   - 不存在 → 输出可用模板列表 + 退出 1
2. **读模板**:
   - 顶部注释 `<!-- vars: TITLE, LABEL, COLOR -->` 声明必填 key
   - 缺 key → 输出 missing keys + 退出 1
3. **替换占位**:
   - 简单字符串替换 `{{KEY}}` → `data[KEY]`
   - HTML 转义 (除非 key 名以 `_RAW` 结尾, 用于嵌套 HTML/mermaid)
   - 列表/dict 类型 data: 调子模板循环 (`{{#each ITEMS}}...{{/each}}`)
4. **输出**:
   - --out 指定 → Write 到文件 (校验路径在 vault 内)
   - 默认 stdout 一行打印
5. **--inline** 模式:
   - 折行去缩进, 紧凑输出

## 输出
```
[html] template=card  vars filled: 4/4
  <div class="cortex-card" style="...">
    <h3>{{TITLE}}</h3>
    ...
  </div>
```
或写入文件:
```
[html] template=mermaid-sankey  written: 仪表盘/固化流.md (replaced %%mermaid-block%%)
```

## 错误处理
- 模板不存在 → 列候选 + 退 1
- 必填 key 缺失 → 列 missing + 退 1
- 路径越界 (--out) → 拒
- HTML escape 失败 (非 str data) → 自动 repr, 加 warning

## AUTO_MODE 兼容
[AUTO_MODE: ...] 行为不变 (纯渲染, 无交互)。无候选模板时不询问, 直接 记空模板 fallback (禁中止)。

## Grok Live Artifacts 风格契约 (输出 HTML 时强制)

参考 [Grok Live Artifacts 提示词](https://linux.do/t/topic/2163779)。所有模板 v2 与 cortex-dashboard 注入的 HTML 必符合下述硬约束。

### 硬约束
1. **首字符**: 响应必以 `<div` 开头, 严禁前导文字 / Emoji / 换行
2. **全 inline style**: 严禁 `<style>` 块, 所有样式写在标签 `style="..."` 内
3. **禁裸文本**: 文本必 wrap `<span>` / `<p>` / `<h2>` / `<h3>` / `<div>`
4. **禁 Markdown 符号**: 严禁 `#` / `**` / `- ` 等符号 (mermaid 围栏除外)
5. **单一流**: 整个响应连续 HTML 字符串, 不留空行
6. **公式保留**: `$...$` 或 `$$...$$` 不转 HTML

### 视觉 token
- 主容器: `background:#ffffff; border:1px solid #eef0f2; border-radius:16px; padding:24px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:#1a202c;`
- 标题: `border-left:4px solid #3182ce; padding-left:12px; font-size:1.5rem; font-weight:700;`
- 卡片: `border:1px solid #edf2f7; border-radius:12px; padding:16px;`
- grid: `display:grid; grid-template-columns:repeat(N,1fr); gap:12px;`
- 主色: 蓝`#3182ce` / 绿`#16a34a` / 红`#dc2626` / 橙`#ea580c` / 黄`#ca8a04` / 灰`#6b7280`
- 字体: sans-serif; 文字色: `#1a202c`; 次要文字: `#4a5568` / `#718096`

### 输出例

```html
<div style="background:#ffffff;border:1px solid #eef0f2;border-radius:16px;padding:24px;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);font-family:-apple-system,sans-serif;color:#1a202c;">
<h2 style="font-size:1.5rem;font-weight:700;border-left:4px solid #3182ce;padding-left:12px;margin:0 0 16px 0;">{{TITLE}}</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
<div style="border:1px solid #edf2f7;border-radius:12px;padding:16px;"><span style="font-weight:600;">{{LABEL}}</span><p style="margin:8px 0 0 0;color:#4a5568;">{{VALUE}}</p></div>
</div>
</div>
```

