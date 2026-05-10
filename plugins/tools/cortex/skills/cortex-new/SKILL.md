---
name: cortex-new
description: 按模板新建 cortex 笔记 (concept/entity/domain/dashboard/question/source), 自动填 frontmatter, 重名不覆盖。仅显式触发 (disable-model-invocation: true)。
argument-hint: "<type> <title>"
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-new

按 cortex 模板新建一篇笔记。

## 用法

```
cortex-new concept "Event-driven Architecture"
cortex-new entity  "Obsidian"
cortex-new domain  "github.com/lazygophers/ccplugin"
cortex-new dashboard "Concepts Overview"
cortex-new question "How to handle vault migrations?"
cortex-new source "Building a Second Brain"
```

`<type>` 必须 ∈ `{concept, entity, domain, dashboard, question, source}`。
`<title>` 是页面 H1, 含空格请用引号包裹。

## 行为

1. 解析 vault 路径 (跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh`)
2. 读 `<vault>/_meta/version.json` 拿 `preset` 字段; 不存在则报错并提示先跑 cortex-install
3. 读 `<vault>/_templates/<type>.md` (回退到 `${CLAUDE_PLUGIN_ROOT}/templates/<type>.md`)
4. 替换 frontmatter 占位:
   - `{{TITLE}}` → 用户输入 `<title>`
   - `{{CREATED}}` / `{{UPDATED}}` → 当前 UTC 日期 `YYYY-MM-DD`
   - `{{PRESET}}` → vault 当前 preset
5. 按 §3.2.7 命名规则计算目标路径:
   - `concept` → `10_concepts/<kebab-title>.md` (LYT) / `zettels/<UID>-<slug>.md` (Zettel) / `3_resources/<kebab>.md` (PARA)
   - `entity` → `20_entities/<kebab>.md` (LYT) / 其他 preset 对应位置
   - `domain` → `30_domains/<host>/<org>/<repo>/_domain.md` (从 title 解析 git remote)
   - `dashboard` → `60_dashboards/<topic>-dashboard.md` (后缀强制)
   - `question` → `50_questions/<kebab>.md`
   - `source` → `40_sources/<kebab>.md`
   - blank preset 一律落到 vault 根 + `<type>/`
6. 路径冲突检测: 用 `Glob` 或 `mcp__obsidian__obsidian_list_files_in_dir` 检查目标是否存在; 存在则报错并显示已存在的路径, **不覆盖**
7. 写入: 优先 `mcp__obsidian__obsidian_append_content` (新文件视作追加创建), 失败回退 `Write`
8. 报告写入路径与 `obsidian://open?vault=<name>&file=<path>` 链接

## 路径与命名

slug 生成规则 (kebab):
- 转小写
- 中文/全角 → 保留
- 空格 → `-`
- 移除禁用字符 `: \ / | ? * < > "` (跨平台)
- 长度 ≤ 40 字符 (超出截断, 末尾不留 `-`)

## 错误恢复

| 情况 | 处理 |
|------|------|
| vault 未安装 cortex (无 `_meta/version.json`) | 报错: "请先运行 cortex-install [preset]" |
| `<type>` 不合法 | 列出 6 个有效值, 退出 |
| `<title>` 为空 | 报错 |
| 模板缺失 | 报错并提示重新跑 cortex-install 复刻模板 |
| 目标文件已存在 | 报错 + 显示路径, 不动它 |
| domain title 无法解析为 host/org/repo | 报错并给出格式示例 `github.com/<org>/<repo>` |

## 不做

- 不创建中间目录 (除非命名规则要求, 如 domain 的 `<host>/<org>/<repo>/`)
- 不打开 Obsidian 应用 (用户可自行点击返回的 `obsidian://` 链接)
- 不更新 `index.md` / `hot.md` (这是 cortex-save / cortex-lint 的职责)
- 不被 LLM 自动触发 (`disable-model-invocation: true`), 必须用户显式说"新建 / cortex new"
