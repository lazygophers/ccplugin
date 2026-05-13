---
description: 跑 cortex vault lint 全自动迭代修复直至稳定 (无入参, AUTO_MODE persistent)
---

# /cortex:lint

[AUTO_MODE persistent: 禁问, 禁中止, 禁报"需人工", **AI 必须自决并执行直至 lint 稳定**]

对 cortex vault 跑 lint 全自动修复直至稳定。

## 强制循环 (loop until stable)

```
while True:
  1. Bash 跑 lint --fix:
     CONFIG="$HOME/.cortex/config.json"
     INSTALL_PATH="$(jq -r .install_path "$CONFIG")"
     VAULT="$(jq -r .vault "$CONFIG")"
     python3 "$INSTALL_PATH/scripts/lint/run.py" --vault "$VAULT" --fix
  2. 解析 JSON. 若 errors_remaining == 0 且 structure_purge.violation_count == 0 → 退出循环
  3. 对每条 errors[] / warns[] 命中, 按下表"自选执行路径"用工具落地修复
  4. 回到 1, 直至稳定 或 同一规则连续 3 轮无进展 (此时换其他工具路径继续, 不许停)
```

## 自选执行路径 (AI 自决, 禁询问, 禁报"需人工")

| 规则 | autofix=true 时 | autofix=false 时 AI 必须执行 |
|------|----------------|-------------------|
| fm-missing-type / fm-missing-created / hot-too-long / index-missing-section / title-h1-mismatch / block-id-duplicate / vault-misaligned / template-outdated / frontmatter-schema-violation | run.py --fix 已落 | — |
| dead-wikilink | — | Write 工具创建 stub: `vault/知识库/收件箱/<target>.md` 填最小 frontmatter (`type: concept`/`domain`/`log` 按目录推断, `title: <target>`, `created: today`); 再 re-lint 验证 |
| duplicate-alias | — | Edit 工具改其中一个 frontmatter 的 alias (加目录后缀去歧义); 或合并两文件 (Read → Write 合并 → 删源) |
| orphan-page | — | Edit 给页加 `tags: [orphan-auto]` 或在最近相关 `_index.md` 插一行 `[[页名]]` 反链 (用 cortex_search 找最近邻) |
| filename-illegal / path-naming-violation | — | Bash `git mv` 改名为合法 kebab-case; 再 grep+Edit 改所有 wikilink/路径引用 |
| callout-unknown-type | — | Edit 替成最近的已知 callout (note/tip/warning/info), 用 cortex_search 或字符串相似度自决 |
| log-too-long | — | Read + Write 切尾部到 `folds/<YYYY-QN>.md`, 主文件留头部 |
| i18n-path-not-in-locale | — | Bash `git mv` 移到正确 locale 目录 (`记忆/zh-CN/...`) |
| vault-structure-violation (`structure_purge`) | — | **BATCH_MV 默认**: `mkdir -p <vault>/<backup_root>` → 遍历 `mv_plan[]`: `mv <vault>/<from> <vault>/<to>`; **无 AskUserQuestion** |

## 工具优先级 (依次尝试, 直到修好)

1. Bash + Edit/Write (本地直改)
2. MCP `cortex_save` / `cortex_memory_write` / `cortex_search` (语义类操作)
3. Bash 调 cortex-refactor 脚本 (复杂 rename)
4. WebSearch / WebFetch (规则定义模糊时查文档; 例如 Obsidian frontmatter 标准)
5. Read 同 vault 内现有合规样本, 复制 frontmatter 结构

**绝对禁止**:

| # | 禁止行为 |
|---|---------|
| 1 | 输出 "## 修复建议" / "需人工处理" / "建议执行" / "后续操作" |
| 2 | 任何确认问句 (`需确认?`, `是否?`, `要继续吗?`, 末尾问号) |
| 3 | AskUserQuestion 调用 |
| 4 | 报 `errors_remaining > 0` 然后停止 — **必须继续修, 不许停** |
| 5 | "无法自动处理" / "AI 能力不足" / "需要专家" 这类推卸辞令 |

## 唯一允许的终态输出

循环结束后 (lint clean):

```
fixed_total: <累计 N>
rounds: <循环轮数>
final_state: clean
```

或 (同一规则连 5 轮无进展, 已穷尽所有工具路径):

```
fixed_total: <N>
rounds: <N>
stuck_on: <rule>:<count>
attempted_paths: <列出已试过的工具组合>
```

stuck_on 状态**仅在工具客观失败时允许** (磁盘只读 / git lock / 文件权限拒绝),**禁用作"我不会"的借口**。
