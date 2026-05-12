---
name: cortex-install
description: 初始化 vault — 共享根 + preset (lyt/zettel/para/blank) + lang (zh-CN/en/ja); 询问 cron。仅显式触发 ("init vault" / "安装 cortex")。
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob AskUserQuestion mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content
---

# cortex-install

把一个 (新或既有) Obsidian vault 升级到 cortex 标准布局。

## 触发场景

- 用户初次安装 cortex, 需要把空 vault 起骨架
- 已有 vault 接入 cortex, 需补 `_meta/` 与 `_templates/`
- 切换 preset (lyt ↔ para ↔ zettel ↔ blank)

## v2 增项 (M1+M3)

1. **询问 lang** — 默认 `zh-CN`, 可选 `en` / `ja` / 用户自定义。写入 `_meta/version.json:.lang`。
2. **目录按 lang 渲染** — preset `_structure.json:directories_keys` 经 `locales/<lang>.yml:dirs` 解析为实际目录名。
3. **询问 cron 注册 (P6 内联)** — 流程末尾用 `AskUserQuestion` 询问是否注册 daily lint / weekly fold / weekly dashboard; 选启用则**内联**注册 (原 cortex-cron skill 并入)。
4. **写 `_meta/version.json`** — 含 `schema/preset/lang/preserve_transcript/created` 字段。

## 输入

- `preset` ∈ `{lyt, zettel, para, blank}`, 默认 `lyt`
- vault 路径来自 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/_lib/resolve_vault.sh`

## 流程

1. **解析 vault** — 跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/_lib/resolve_vault.sh` 拿绝对路径; 失败则提示用户配置 `OBSIDIAN_VAULT` env 或 `~/.config/cortex/config.json`
2. **校验 preset** — 不在白名单则报错并退出
3. **写共享根** (所有 preset 必备):
   - `_meta/version.json` — `{"schema": "1.0", "preset": "<preset>", "created": "<UTC ISO>"}`
   - `_meta/lint-baseline.json` — `{"exempt": []}`
   - `_meta/migrations/` — 确保目录存在 (用 `Bash mkdir -p` 或写入一个 `.gitkeep`)
   - `_templates/` — 复制 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/templates/{concept,entity,domain,dashboard,question,source,_index}.md` 到此目录
   - `index.md` — 用 `_templates/_index.md` 内容作为基础, 或写空骨架由用户填充
   - `hot.md` — 空骨架 (frontmatter `type: meta, title: hot`)
   - `log/_index.md` — 空骨架
   - `folds/_index.md` — 空骨架
4. **写 preset 业务目录**:
   - 读 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/<preset>/_structure.json`
   - 按 `directories[]` 在 vault 内创建空目录
   - 按 `seed_files[]` 把 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/<preset>/<src>` 复制到 `<vault>/<dst>`
   - blank preset 的 directories/seed_files 均为空, 跳过即可
5. **询问 git auto-sync (P5)** — 若 `<vault>/.git` 存在 (vault 是 git repo), **必须**用 `AskUserQuestion` 工具(不能用文本式提问) 询问 1 个 single-choice 问题:
   - 问题: "vault 是 git repo, 是否启用 Stop hook 自动 commit?"
   - 选项:
     - `关` (默认) → 写 `_meta/version.json`: `auto_commit=false, auto_push=false`
     - `仅 commit` → `auto_commit=true, auto_push=false` (本地 commit, 不 push)
     - `commit + push` → `auto_commit=true, auto_push=true` (上述 + `git push origin HEAD`)

   提示用户: 启用 `commit + push` 前请自查 vault 不含 secret (P0 masking 只覆盖 ingest/save, 不护手写笔记)。详见 `docs/sync-git.md`。

   vault 不是 git repo → 跳过此步, 不写两个字段 (后续用户可手动 `git init` + 重跑 install)。

6. **回报** — 列已创建/已存在的文件, 提示运行 `/cortex:doctor` 验证
7. **周期任务询问 (P6 — 装机一次性, 原 cortex-cron skill 并入)** — **必须**调 `AskUserQuestion` 工具 (禁文本式提问) 询问 (合并 ≤4 questions 单次调用):
   - Q1 (multiSelect): "勾选要注册的 cron job" — options: `daily 01:00 lint` / `weekly Sun 02:00 fold` / `weekly Sun 02:30 dashboard`
   - Q2 (single): "注册平台" — options: `不启用` (默认) / `launchd (macOS)` / `cron (Linux/macOS)` / `GitHub Actions (远程仓库)`

   - Q2 = `不启用` → 跳过, 安装完成
   - Q2 ∈ {launchd, cron, gha} → 走以下**内联**注册流程 (从原 cortex-cron skill 摘要):

   **解析 PLUGIN_ROOT (cron daemon 不继承 shell env, snippet 必须用绝对路径)**:
   优先级: `$CORTEX_INSTALL_PATH` env > `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` > `$CLAUDE_PLUGIN_ROOT`。**避免**用本地开发源码路径 (cron 上下文不可达)。

   **每 job 的 wrapper**: `${PLUGIN_ROOT}/scripts/cron/{lint,fold,dashboard}.sh`, 内部走 `claude --bare --no-session-persistence --settings ~/.claude/settings.glm-4.7-flash.json -p "..." --allowed-tools "Bash Read Glob"` (只读权限, `--fix` 类操作不进 cron)。

   **后端 1: launchd (macOS)** — 为每 job 写 plist:
   - 路径: `~/Library/LaunchAgents/dev.lazygophers.cortex.<job>.plist`
   - 内容: `<ProgramArguments>` = `["bash", "<PLUGIN_ROOT>/scripts/cron/<job>.sh"]`, `<StartCalendarInterval>` 按 daily 01:00 / weekly Sun 02:00 / weekly Sun 02:30
   - 落盘前**必须**再调 `AskUserQuestion` 打印完整 plist 内容, 选项 `写入` / `取消` / `改时间`
   - 用户选 `写入` → `Write` plist + `Bash launchctl load <plist>`

   **后端 2: cron (Linux/macOS)** — append `~/.cortexrc.cron`:
   - 行格式: `0 1 * * *  bash <PLUGIN_ROOT>/scripts/cron/lint.sh   # cortex.lint`
   - 落盘前 `AskUserQuestion` 打印待 append 的行, 选项 `写入` / `取消` / `改时间`
   - 用户选 `写入` → `Bash echo '...' >> ~/.cortexrc.cron && (crontab -l 2>/dev/null; cat ~/.cortexrc.cron) | crontab -`

   **后端 3: GitHub Actions (远程仓库)** — **不自动写**, 仅打印模板:
   - 提示用户复制到 `<vault repo>/.github/workflows/cortex-cron.yml`
   - 模板要点: `on.schedule.cron`, `jobs.lint/fold/dashboard.runs-on: ubuntu-latest`, `steps` 安装 cortex 插件 + 跑 `bash scripts/cron/<job>.sh`
   - 提示 vault 须为 GitHub repo, secrets 配 `OBSIDIAN_API_KEY` (若 lint 走 REST)

   **关键约束** (与原 cortex-cron 一致):
   - 写 plist / crontab 前**必须** dry-run + `AskUserQuestion` 二次确认
   - cron job 默认 `--allowed-tools "Bash Read Glob"`, 不让 LLM 误改 vault
   - wrapper 提供 `flock -n` + `timeout 600` (复用 `scripts/cron/run.sh`)
   - 不写 `~/.claude/settings.json`, 只写 LaunchAgents / crontab 区域
   - 检测 `$CI` env → 只打印 GHA yaml, 不真写

   **卸载提示**: 用户手动 `launchctl unload <plist> && rm <plist>` (launchd) / 编辑 `~/.cortexrc.cron` 删行 + `crontab ~/.cortexrc.cron` (cron) / 删 `.github/workflows/cortex-cron.yml` (gha)。重跑 `cortex-install` 可再次配置。

## 写入策略

- **不覆盖已有文件** — 用 `Glob` 或 `mcp__obsidian__obsidian_get_file_contents` 检查目标路径, 存在则跳过并标 `(skipped)`
- 优先用 `mcp__obsidian__obsidian_append_content` (vault 索引一致); MCP 不可用回退 `Write`
- 模板文件中的 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` / `{{PRESET}}` 占位 **不在此 skill 替换** — `_templates/` 下保留原样供 `/cortex:new` 使用
- 任何单文件失败不中断后续步骤, 最后统一报错

## 输出格式

```
解析 vault: /Users/.../knowledge/obsidian (源: env)
preset: lyt

[共享根]
✅ 写入 _meta/version.json
✅ 写入 _meta/lint-baseline.json
✅ 创建 _meta/migrations/
✅ 复制 _templates/concept.md
⏭️  _templates/entity.md (已存在)
✅ 写入 index.md
✅ 写入 hot.md
✅ 写入 log/_index.md
✅ 写入 folds/_index.md

[preset: lyt]
✅ 创建 00_MOC/ ... 80_archive/
✅ 复制 00_MOC/home.md
✅ 复制 00_MOC/topics-moc.md
... (省略)

总结: 22 项写入, 3 项跳过, 0 项失败
下一步: /cortex:doctor 验证
```

## 错误处理

- 单文件 IO/权限错: 标 ❌, 继续下一项, 末尾汇总
- vault 路径解析失败: 立即退出并提示配置方式
- preset 名错: 立即退出并列出 4 个有效值
- 模板/preset 源缺失 (插件文件丢): 立即退出, 提示重装 cortex 插件
