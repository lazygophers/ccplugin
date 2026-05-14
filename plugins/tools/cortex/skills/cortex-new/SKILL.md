---
name: cortex-new
description: 按模板新建笔记 (concept/entity/domain/dashboard/question/source), 路径按 vault.lang, 填 lang/cli frontmatter。仅显式触发。
argument-hint: "<type> <title> [--lang zh-CN|en|ja]"
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

1. 解析 vault 路径 (跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh`)
2. 读 `<vault>/_templates/<type>.md` (回退到 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/seed/_templates/<type>.md`)
3. 替换 frontmatter 占位:
   - `{{TITLE}}` → 用户输入 `<title>`
   - `{{CREATED}}` / `{{UPDATED}}` → 当前 UTC 日期 `YYYY-MM-DD`
4. 按 §3.2.7 命名规则计算目标路径:
   - `concept` → `知识库/领域/<域>/<kebab>.md` (域 = --domain 指定 或 AI 自决 6 域之一; 缺则 `领域/未分类/`)
   - `entity` → 若属 repo → `知识库/项目/<host>/<org>/<repo>/<entity-kebab>.md`; 否则 `知识库/领域/<域>/<entity-kebab>.md`
   - `project` / `domain` (alias) → `知识库/项目/<host>/<org>/<repo>/_index.md` (github/gitlab 走 origin; 本地项目走相对 $HOME 路径策略, 不足 3 段补 `_local`)
   - `dashboard` → `_assets/dashboards/<topic>-dashboard.md` (后缀强制)
   - `reflection` → `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<kebab>.md` (日记一项)
   - `question` / `fleeting` → `知识库/收件箱/<kebab>.md` (待 digest 分发)
   - `source` → `知识库/收件箱/<host>-<kebab>.md` (非 repo 来源统一落收件箱)
   - `journal` / `log` → `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md` (仅日)
6. 路径冲突检测: 用 `Glob` 或 `mcp__obsidian__obsidian_list_files_in_dir` 检查目标是否存在; 存在时 **必须调 `AskUserQuestion`** 工具询问: "目标路径已存在: `<path>`, 如何处理?" options: `换 slug` / `覆盖` / `取消`; 默认行为 = `取消` (不覆盖)
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

| 情况                                          | 处理                                         |
| --------------------------------------------- | -------------------------------------------- |
| vault 未安装 cortex (无 `_meta/version.json`) | 报错: "请先运行 cortex-install"              |
| `<type>` 不合法                               | 列出 6 个有效值, 退出                        |
| `<title>` 为空                                | 报错                                         |
| 模板缺失                                      | 报错并提示重新跑 cortex-install 复刻模板     |
| 目标文件已存在                                | 报错 + 显示路径, 不动它                      |
| domain title 无法解析为 host/org/repo         | 报错并给出格式示例 `github.com/<org>/<repo>` |

## 不做

- 不创建中间目录 (除非命名规则要求, 如 domain 的 `<host>/<org>/<repo>/`)
- 不打开 Obsidian 应用 (用户可自行点击返回的 `obsidian://` 链接)
- 不更新 `index.md` / `hot.md` (这是 cortex-save / cortex-lint 的职责)
- 不被 LLM 自动触发 (`disable-model-invocation: true`), 必须用户显式说"新建 / cortex new"
