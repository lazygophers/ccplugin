---
name: cortex-lint
description: 跑 17 条 vault lint (frontmatter/wikilink/orphan/命名/i18n) + autofix; --fix 才落盘。Triggers on "wiki audit", "lint", "vault 体检".
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_patch_content
---

# cortex-lint

对 vault 跑 17 条 lint 规则, 输出 JSON 报告 (errors/warns/summary)。默认 dry-run。

## 触发场景

- 用户问"vault 健康吗 / wiki audit / 找 orphan"
- 显式 "/cortex:lint" 或 "lint the wiki"
- cron daily 任务

## 行为

1. 解析 vault 路径 (跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh`); 不存在则报错
2. 调 `python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/lint/run.py --vault <path> [--fix] [--scope=<glob>]`
3. 解析 JSON 报告:
   - 报错块 (severity=error): rule#1 fm-missing-type, #3 dead-wikilink, #5 duplicate-alias, #10 filename-illegal, #11 block-id-duplicate
   - 警告块 (severity=warn): rule#2 fm-missing-created, #4 orphan-page, #6 hot-too-long, #7 log-too-long, #8 index-missing-section, #9 title-h1-mismatch, #12 callout-unknown-type, #13 path-naming-violation
4. 渲染 markdown 摘要 (按 rule 分组, 列前 20 条命中)
5. 如用户指定 `--fix`:
   - 在 `<vault>/_meta/.cortex-backup/lint/<ts>/` 写 backup
   - 仅对 `autofix:true` 规则改盘 (rule 1/2/6/8/9/11)
   - 其他规则需用户手工处理 (cortex-refactor 可协助 rename/merge)

## 17 条 规则 (rules.json)

| #   | id                    | severity | autofix                                          |
| --- | --------------------- | -------- | ------------------------------------------------ |
| 1   | fm-missing-type       | error    | ✓ (按目录推断)                                   |
| 2   | fm-missing-created    | warn     | ✓ (用 mtime)                                     |
| 3   | dead-wikilink         | error    | ✗ (建议 cortex-new 创建 stub)                    |
| 4   | orphan-page           | warn     | ✗ (人工补 tag/链接)                              |
| 5   | duplicate-alias       | error    | ✗ (人工合并)                                     |
| 6   | hot-too-long          | warn     | ✓ (截断+落 归档/)                                |
| 7   | log-too-long          | warn     | ✗ (digest 自动归档)                              |
| 8   | index-missing-section | warn     | ✓ (自动补条目)                                   |
| 9   | title-h1-mismatch     | warn     | ✓ (以 frontmatter 为准)                          |
| 10  | filename-illegal      | error    | ✗ (cortex-refactor rename)                       |
| 11  | block-id-duplicate    | error    | ✓ (重哈希)                                       |
| 12  | callout-unknown-type  | warn     | ✗ (报告)                                         |
| 13  | path-naming-violation | warn     | ✗ (cortex-refactor rename)                       |
| 14  | fm-duplicate-tags     | warn     | ✓ (保序去重)                                     |
| 15  | fm-banned-tags        | warn     | ✓ (移除 index/meta/template/_index/stub)         |
| 16  | fm-banned-fields      | warn     | ✓ (移除 preset 等)                               |
| 17  | fm-missing-tags       | warn     | ✓ (字段缺失或数量 < 10; autofix 读 fm+正文派生 ≥10, 严禁占位) |

模板/示例文件可在 frontmatter 加 `lint-skip: true` 跳过全部检查 (供 `_templates/**/*.md` 使用)。

## 输出格式

返回给用户的 markdown 报告包含:

```
## cortex-lint 报告

vault: <abs path>
files scanned: N
errors: E   warns: W   fixed: F

### errors

| rule | file | line | msg |
| --- | --- | --- | --- |
...

### warns

(同上)
```

## 安全

- 默认 dry-run, 不动盘
- `--fix` 前在 `_meta/.cortex-backup/lint/<ts>/` 全量 backup 待修改文件
- backup 目录由 cortex 维护, 用户可手动 git ignore (`_meta/.cortex-backup/`)

## 交互修复 (--fix 模式 vault-structure-violation 专用)

**AUTO_MODE 探测**: 若 user prompt 含 `[AUTO_MODE:` 或 `non-interactive` 字样 (来自 shell wrapper, 如 `~/.cortex/scripts/lint.sh --fix`), **跳所有 `AskUserQuestion`, 直执行默认动作**:

- `structure_purge` 违规: 走 **BATCH_MV** 分支 (批量 mv 到 `<backup_root>/`, 跳过 per-item 二次确认)
- `autofix=true` 项: 直接落
- 其它非 autofix 项: 列入报告输出, 不动

**Interactive 模式** (claude session 内直调 `/cortex:cortex-lint --fix`): 走下述 `AskUserQuestion` 4 选项流程, 行为不变。

run.py 的 python 进程不交互, 只输出 JSON 违规列表 + `structure_purge.mv_plan`; **交互全在本 SKILL 流程内**, 实际 mv 操作也在此执行。

cortex-lint --fix 输出 JSON 含 `structure_purge` 字段且 `violation_count > 0` 时:

1. 解析 `structure_purge` (字段: `violation_count` / `backup_root` / `mv_plan[{from,to}]`); 同步从 `errors[]` 拿 `vault-structure-violation` 项 (每项含 `path` / `kind` / `reason` / `backup_target`)
2. **一次性总体确认** — 用 `AskUserQuestion` 工具 (禁文本提问), 4 个选项:
   - **BATCH_MV (推荐)**: 全部移除到 backup — 将 N 个不在 vault schema 内的项批量 mv 到 `<backup_root>/` (非真删, 可恢复)
   - **BATCH_WHITELIST**: 全部加入白名单 — 全部追加 `_meta/version.json:.lint_whitelist[]`
   - **PER_ITEM**: 逐个询问 — 走原逐项 4 选项流程 (向后兼容)
   - **CANCEL**: 取消, 本次不动

   AskUserQuestion 文案示例:
   > "lint 发现 N 个不在 vault schema 内的项. 将批量 mv 到 `<backup_root>/` (非真删, 可恢复). 如何处理?"

3. 按选择落操作:
   - **BATCH_MV (默认推荐)**:
     - `mkdir -p <vault>/<backup_root>`
     - 遍历 `mv_plan[]`, 每项执行:
       - L1: obsidian CLI `obsidian move "<from>" "<to>"` (保 wikilink 更新)
       - L2: `mcp__obsidian` 工具兜底
       - L3: `mkdir -p $(dirname <vault>/<to>) && mv <vault>/<from> <vault>/<to>` (因已总体确认, **跳过 per-item 二次确认**)
     - 报告 `moved N items to <backup_root>`
   - **BATCH_WHITELIST**:
     - 读 `_meta/version.json`, 把所有 `violations[].path` 追加到 `.lint_whitelist[]` (dir 含尾 `/`, file 不含, 去重), 写回
     - 报告 `whitelisted N items`
   - **PER_ITEM** (向后兼容): 对每个违规分别 `AskUserQuestion`, 4 个选项:
     - **移到 backup**: mv 单项到 `<backup_target>` (obsidian CLI → mcp → mv)
     - **移到允许目录**: 列 schema.root_dirs 候选 (`_meta`, `_templates`, `_assets`, `知识库`, `记忆`, `仪表盘`, `归档`, `locales` 等), 用户选目标
     - **加白名单**: 写 `_meta/version.json:.lint_whitelist[]` (dir 含尾 `/`, file 不含)
     - **跳过**: 单次不动, 不写白名单
   - **CANCEL**: 不动, 跳过结构修复段
4. 后续 `errors[]` / `warns[]` 中非 `vault-structure-violation` 项:
   - `rules.json autofix=true` 项: run.py 已自动改盘 (rule 1/2/6/8/9/11)
   - 其它项: 走原 SKILL autofix 流程或单独 `AskUserQuestion`

**数据安全**: 永远 mv 到 backup, **从不**真 rm。backup_root 累积大时用户可手动清 `_meta/.cortex-backup/`。

完整 vault schema 见 `plugins/tools/cortex/scripts/lint/schemas.py` (单一 4 子目录布局)。

白名单匹配规则: vault 根相对路径**精确串相等** (dir 加尾 `/`, file 不加), 不支持 glob。隐藏目录 `.obsidian` / `.trash` 默认 allowed, 无需白名单。

## AUTO_MODE 行为 (wrapper bash 触发, persistent 自决修复)

prompt 含 `[AUTO_MODE]` 时 (来自 `~/.cortex/scripts/lint.sh` wrapper), **严格遵守**:

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并循环执行**直至 lint 稳定; 禁报 "需人工"/"无法处理".

### 强制循环 (loop until stable)

1. Bash 跑 `lint.run --fix`
2. 解析 JSON: 若 `errors_remaining == 0 && structure_purge.violation_count == 0` → 退出循环
3. 否则按"自选执行路径"用工具修每条命中
4. 回 1, 直至稳定 或 同一规则连 5 轮无进展 (穷尽所有工具路径后才允许停)

### 自选执行路径 (AI 自决, 禁问)

| 规则 (非 autofix) | AI 必须执行 |
|-------------------|------------|
| dead-wikilink | lint 解析器已自动剥离 fenced/inline code 内的 `[[...]]`; 残留命中即正文 dead link → `Write` 创 stub 到 `知识库/收件箱/<target>.md`, 最小 frontmatter (type 按目录推断, `created` 用绝对日期 `YYYY-MM-DD`) |
| duplicate-alias | `Edit` 改其中一 frontmatter alias 加目录后缀; 或 Read+Write 合并两文件后删源 |
| orphan-page | Read 正文行数: ≤ 3 行 (空 stub) `git rm` 删除; 否则 `Edit` 加 `tags: [orphan]` 或在最近邻 `_index.md` 插反链 (`bash ~/.cortex/scripts/search.sh` 找邻) |
| filename-illegal / path-naming-violation | `git mv` 改: 长度 ≤ 50 字符, kebab-case, ASCII + 数字 + 连字符; 超长用 `<prefix>-<sha8>.md` (前 30 字符 + content sha 8 位); grep+Edit 改所有引用 |
| callout-unknown-type | `Edit` 替成最近已知 callout (note/tip/warning/info) |
| log-too-long | digest 自动归档 (无需 lint 介入) |
| i18n-path-not-in-locale | 比对 `_meta/version.json:.lang` 与 `locales/<lang>.yml:.dirs` 顶层名; 顶层名不在 locale dirs → `git mv` 改为标准名 |
| vault-misaligned | 单步 `python3 <abs>/scripts/lint/run.py --vault <vault> --sync-templates` 同步 `_templates/`, 再回主循环 |
| frontmatter-schema-violation | run.py --fix 补 type/created; 其余字段 AI 启发式补: `desc` = H1 + 首段 ≤ 100 字; `source_url` = git remote / 原始 URL / "N/A"; `version` = git sha / pkg version / fetch date; `when_to_read` = "当用户问 <topic> 时"; `score` = 1-5 (上游活跃度, 无信号 = 3); `maturity` = 按目录 (项目/收件箱=draft, 领域/=stable, 日记/=review) |
| vault-structure-violation (`structure_purge`) | **BATCH_MV 默认**: `mkdir -p <backup_root>` → 遍历 `mv_plan[]` mv 到 backup_root, **无 AskUserQuestion** |

### 工具优先级 (依次尝试)

1. Bash + Edit/Write 本地直改
2. cortex CLI `bash ~/.cortex/scripts/save.sh` / `search.sh` / `memory.sh write`
3. cortex-refactor 脚本 (复杂 rename)
4. WebSearch / WebFetch (规则模糊时查文档)
5. Read 同 vault 合规样本复制结构

### 严禁 (任一出现 = 契约违反)

| # | 禁止模式 | 反例 |
|---|---------|------|
| 1 | "修复建议" / "建议" / "推荐操作" 章节/表格/列表 | `## 修复建议`, `\| 类型 \| 操作 \|` |
| 2 | 用户确认问句 | `需确认?`, `是否执行?`, `要继续吗?`, 末尾问号 |
| 3 | "需人工"/"待人工处理"/"建议人工" | — |
| 4 | AskUserQuestion 调用 | (allowed-tools 已禁) |
| 5 | "下一步"/"后续"/"如需"导引 | — |
| 6 | 报 errors_remaining > 0 然后停 | **必须继续修, 不许停** |
| 7 | "AI 能力不足"/"无法自动" 推卸辞令 | — |

写盘前不需二次确认 (AUTO_MODE 隐含已授权)。

### 终态输出 (仅这两种)

清空时:
```
fixed_total: <N>
rounds: <N>
final_state: clean
```

stuck (仅当工具客观失败 — 磁盘只读 / git lock / 权限拒绝; 禁用作"我不会"借口):
```
fixed_total: <N>
rounds: <N>
stuck_on: <rule>:<count>
attempted_paths: [...]
```

---

**非 AUTO_MODE** (IDE 内手动调 SKILL / `/cortex:lint --skill` interactive):
主流程及"手动修复建议"段适用, 可输出建议 + 询问。
