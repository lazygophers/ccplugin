---
name: cortex-save
description: 落档非平凡发现到 vault — 路径按 vault.lang, 塞 cli/lang frontmatter, 注入 block-id, 同步 index/hot。Triggers on "save this", "归档", "落档".
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content mcp__obsidian__obsidian_patch_content mcp__obsidian__obsidian_simple_search
---

# cortex-save

把"值得留下的东西"写进 Obsidian vault, 让未来会话能搜到。

## 触发场景

- 用户显式说 "save this" / "落档" / "归档" / `/cortex:save`
- Stop / SubagentStop hook 启发式触发后回到主线让 skill 完成精修 (此时 hook 已先写一份 log, skill 可补充内容或迁移到更合适目录)
- 当前讨论沉淀出 1-2 个明确概念 / 决策 / 实体 / 资源, 主 agent 主动调用

## 输入信号

- 用户参数 (可选): `--topic "X"` / `--from-session` / `--type concept|entity|domain|log|source|question|dashboard`
- 默认: 推断要点 + 默认 `type=log`
- vault 路径必须先解析: `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh`

## 流程

1. **解析 vault**

   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh
   ```
   失败 → 提示用户配 `OBSIDIAN_VAULT` env 或 `~/.config/cortex/config.json`, 退出。

2. **判定来源 + 类型**
   - 用户给了 `--topic` → `type=concept`, 主题为标题
   - 用户给了 `--from-session` 或没参数 → 走 transcript 摘要 (调 save_session.py 自动) 或主 agent 自己抽要点 (`type=log`)
   - 用户讨论的是某项目内事 → `type=domain`, 路径按 git remote 推断

3. **选目录 (按 prd §3.2.7)**:

   | type | 路径模板 |
   |------|----------|
   | concept | `10_concepts/<kebab-title>.md` (LYT) / `zettels/YYYYMMDDHHMM-<slug>.md` (Zettel) |
   | entity | `20_entities/<kebab>.md` |
   | domain | `30_domains/<host>/<org>/<repo>/<sub>.md` |
   | source | `40_sources/<kebab>.md` |
   | question | `50_questions/<kebab>.md` |
   | dashboard | `60_dashboards/<topic>-dashboard.md` |
   | log (默认) | `log/YYYY-MM/DD-HHMM-<slug>.md` (UTC) |

   preset (`_meta/version.json:.preset`) 不是 `lyt` 时, concept 路径切换为对应 preset 的扁平结构。

4. **套模板 + 填 frontmatter**
   - 读 `<vault>/_templates/<type>.md` (不存在则读 `${CLAUDE_PLUGIN_ROOT}/templates/<type>.md`)
   - 替换 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` (UTC `YYYY-MM-DD`) / `{{PRESET}}`
   - tags: 自动加 `[cortex-auto]` 标记由 skill 写入

5. **block-id 自动注入** (prd §10.5)
   - 每个 H2 / H3 段落末尾追加 ` ^cortex-<sha8>`
   - sha8 = `sha256(<rel-path>::<UTC-iso>::<section-index>::<heading>)[:8]`
   - 命中冲突 → seed 加序号重哈希; 检查 `<vault>/log/` `<vault>/folds/` 已有 `^cortex-` 防重复

6. **写入** (prd §10.8 与 obsidian-git 协调)
   - **P0 masking 前置**:写盘前必经 `masking.py` 脱敏 (AWS/OpenAI/Anthropic/GitHub PAT/JWT/PEM/Slack token → `<REDACTED:*>`),`save_session.py` 已内置;手写 body 时先

     ```bash
     SAFE_BODY="$(python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/masking.py <<< "$BODY")"
     ```

     绕过 (仅测试): `CORTEX_SKIP_SANITIZE=1`,生产禁用。
   - 优先 `mcp__obsidian__obsidian_put_content` / `obsidian_append_content`
   - MCP 不可用 → `Write`
   - 检测 `<vault>/.obsidian/plugins/obsidian-git/data.json` 存在 → **不**自动 git commit, 文件末尾加注释 `<!-- cortex-pending-commit -->`

7. **更新索引**
   - `<vault>/index.md` — 类型对应章节加新条目 (无 → 创建章节)
   - `<vault>/hot.md` — `## 最近落档` 段落顶部插入新 wikilink, 保留前 5 条
   - `<vault>/log/_index.md` — log 类型必同步

8. **反向 wikilink 回填**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/backlink_sync.py \
     --vault "$VAULT" --source "<rel-path>"
   ```
   - JSON stdout: `{updated: [...], skipped: [...], missing: [...]}`
   - `updated` — 已在目标页 `## Backlinks` 段追加 `- [[<new-page>]] (cortex-auto)`
   - `skipped` — 目标页已含同源 backlink, 幂等跳过
   - `missing` — wikilink 指向不存在页 (lint rule #3 会另行报告 dead link)
   - 失败仅日志, 不阻断 (退出码恒 0)
   - save_session.py 也已在写入后自动调用 backlink_sync.py, skill 路径手写时无需重复调

9. **快捷调用 save_session.py (--from-session 路径)**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/save_session.py \
     --vault "$VAULT" \
     --transcript "$CLAUDE_TRANSCRIPT_PATH" \
     --reason manual \
     --force \
     --title "用户给的标题"
   ```
   stdout 即落档绝对路径; 退出码 0=成功, 1=失败, 2=未触发 (force 模式不会出现)。

10. **输出**
    - 落档绝对路径 + vault 相对路径 + `obsidian://open?vault=<name>&file=<rel>` URI (URL-encode)
    - 命中的 backlinks 数
    - 未命中 (待补) 的 wikilink 数
    - 提示用户: 若装了 obsidian-git, vault 内 `<!-- cortex-pending-commit -->` 标记将由 OGit 下次同步带上

## 写入策略

- 默认 **不覆盖** 已存在文件 — 文件名冲突时追加 `-2`, `-3`...
- frontmatter `updated` 字段在每次写入时更新; `created` 仅首次设置
- 一次落档失败不阻断其它步骤 (e.g. backlink 失败 → 仅记录, 主文件已写)

## 错误处理

| 失败 | 行为 |
|------|------|
| vault 未解析 | 立即退出, 给配置示例 |
| 模板缺失 (插件文件丢) | 退出, 提示重装 cortex |
| MCP 不可用 | 回退 `Write` |
| save_session.py 退出码 1 | 输出 stderr 内容, 调 `AskUserQuestion` 询问: "save 失败, 如何处理?" options: `手补内容` / `跳过` / `重试` |
| 反向 wikilink 失败 | 仅警告, 主文件保留 |

## 输出范例

```
✅ 落档成功
路径: /Users/x/knowledge/log/2026-05/10-1432-cortex-stop-hook.md
相对: log/2026-05/10-1432-cortex-stop-hook (vault 内)
URI: obsidian://open?vault=knowledge&file=log%2F2026-05%2F10-1432-cortex-stop-hook
backlinks 回填: 2 处 ([[obsidian-hooks]] / [[claude-code-plugin]])
未命中 wikilink: 1 (留待 cortex-lint)
注: 检测到 obsidian-git, 已加 cortex-pending-commit 标记, 不主动 git commit
```

## 不做

- 不 `git commit` / `git push` (与 OGit 冲突, 见 prd §10.8)
- 不删 / 改用户已有内容 (仅追加章节)
- 不解析 canvas (.canvas) / bases (.base) (M6 / 另起 skill)
