# 分型扫描 R1 — CLI 工具链 + 文档/插件内容 约定候选

task-id=reconstruct · mode=bootstrap · 只读扫描 · pwd=仓库根
范围: scripts/ lib/ pyproject.toml 系列 + skills/ plugins/ .claude-plugin/ docs/ 顶层 md 配置
说明: 每条 ≥2 处一致才断为约定; 单处标「推测:」或 drop。dispatch 提到的 scripts/spec.py 不存在 (实际 CLI 入口见下)。

---

## A. 构建 / 发布 (build)

### A1. Python 版本统一锁 3.11
- 规则: 所有 Python 子项目 MUST `requires-python >=3.11` 且 `.python-version` 固定 `3.11`。
- 证据: `pyproject.toml:6` (requires-python >=3.11)、`lib/pyproject.toml:5`、`.python-version:1` (3.11)、`plugins/tools/notify/.python-version`、`plugins/tools/version/.python-version` (均 3.11)。
- 建议层: core · 类目: build

### A2. uv 管理依赖与锁 (非 pip/poetry)
- 规则: 依赖解析/同步 MUST 走 uv (`uv lock -U` + `uv sync`); lockfile 为 `uv.lock`; 本地包经 `[tool.uv.sources]` path 引用。
- 证据: `uv.lock` (795KB 存在)、`pyproject.toml:41-42` (`[tool.uv.sources.lib] path=./lib`)、`scripts/update_version.py:65,79` (`uv lock -U failed` / `uv sync failed` 错误串, 脚本核心即跑 uv)、`.clinerules` 无关但 uv 全仓统一。
- 建议层: core · 类目: build

### A3. Monorepo 多 pyproject, 各子项目独立打包
- 规则: 根 + lib + 每个 plugin 各自持 pyproject/.python-version; 版本更新脚本遍历所有子项目跑 uv。
- 证据: `pyproject.toml`、`lib/pyproject.toml`、`plugins/tools/version/pyproject.toml`; `scripts/update_version.py:1-4` docstring "Runs 'uv lock -U' and 'uv sync' in all project directories"。
- 建议层: recall · 类目: build

### A4. CLI 入口经 [project.scripts] 声明 (非直接 python 文件路径)
- 规则: 每个用户命令 MUST 在 `[project.scripts]` 注册 `name = "scripts.<mod>:<entry>"`; argparse 脚本入口 `:main`, typer 应用入口 `:app`。
- 证据: `pyproject.toml:21-27` (clean/update/info/check/install=`:main`, md2html=`scripts.md2html:app`)。
- 建议层: recall · 类目: build

### A5. setuptools 打包只收 scripts*, 排除 plugins/lib
- 规则: 根包 `packages.find` MUST `include=["scripts*"]` 且 `exclude=["plugins*","lib*"]` (lib 作独立 path 依赖, plugins 不进 wheel)。
- 证据: `pyproject.toml:36-39`。
- 建议层: recall · 类目: build

### A6. 版本号四段式独立 .version 文件, 自动 bump
- 规则: 构建版本经 `.version` 文件 (格式 `major.minor.patch.build`) 维护, 由 version 插件 hooks 自动 bump; pyproject `version` 三段与之对应。
- 证据: `.version:1` (0.0.195.45)、`pyproject.toml:3` (0.0.195)、`plugins/tools/version/.version`、marketplace version 插件描述 "通过 Hooks 自动检测任务完成并更新构建版本号"。
- 建议层: recall · 类目: build

---

## B. CLI-library 脚本约定 (script)

### B1. CLI 脚本用 argparse (typer 仅富交互例外)
- 规则: scripts/ 下 CLI 默认 MUST 用标准库 argparse; 仅需子命令树/富终端的工具 (md2html) 用 typer。
- 证据: `scripts/check.py:17`、`clean.py:23`、`info.py:10`、`install.py:17`、`update.py:12`、`update_version.py:7` 均 `import argparse` + `ArgumentParser`; 唯 `scripts/md2html.py:21-27` 用 `typer.Typer`。6:1 → argparse 为约定。
- 建议层: recall · 类目: script

### B2. main() 返回 int 退出码, 顶部 sys.exit(main())
- 规则: CLI 入口 MUST `def main() -> int` 返回退出码 (0=成功, 1=失败), 模块尾 `if __name__=="__main__": sys.exit(main())`。
- 证据: `check.py:1088 def main()->int` + `:988 return 0` `:980 return 1`; `install.py:411,578,581-582`; `update.py:1024,1257`; `update_version.py:145,168,187`; `clean.py:336,460,463`。退出码 0/1 二值一致。
- 建议层: core · 类目: script

### B3. 脚本首行 shebang + 模块 docstring
- 规则: 每个可执行脚本 MUST 首行 `#!/usr/bin/env python3` + 紧随模块级 docstring 说明用途。
- 证据: `check.py:1-2`、`clean.py:1-2`、`info.py:1-3`、`install.py:1-3`、`update.py:1-3`、`update_version.py:1-2`、`subagent_statusline.py:1-3`、`statusline.py:1`。8/8 一致。
- 建议层: recall · 类目: script

### B4. 终端输出走 rich Console (非裸 print)
- 规则: 用户可见输出 MUST 经 `rich.console.Console` (表格/面板/规则), 依赖 rich。
- 证据: `check.py:26-35` (`from rich...` + `console=Console()`, 全仓 221 处 console.print); `pyproject.toml:9` rich 依赖。
- 建议层: recall · 类目: script
- 注: 未见 `Console(stderr=True)` 分离 (仅第三方库出现)。stdout/stderr 机器纯净 vs 叙事分工 **未成约定** → 空 (见 G1 gap)。

### B5. 函数签名带类型注解 + 中文 docstring
- 规则: 公共函数 MUST 带类型注解 (参数 + 返回) 并配中文 docstring (Args/Returns)。
- 证据: `scripts/utils.py:8-25` (`format_duration(seconds: Union[int,float]) -> str` + Args/Returns 中文)、`:28-30`; `check.py:1088 ->int`; `install.py:411 ->int`。部分新脚本用 `from __future__ import annotations` (`statusline.py:2`、`subagent_statusline.py:2`、`lib/tests/*`)。
- 建议层: recall · 类目: script

---

## C. 测试 (test)

### C1. pytest + asyncio_mode=auto (lib 层)
- 规则: 库测试 MUST 用 pytest; 异步测试 `asyncio_mode="auto"` 免逐个标记。
- 证据: `lib/pyproject.toml:23-24` (`[tool.pytest.ini_options] asyncio_mode="auto"`)、`lib/tests/` (test_db*.py + conftest.py)。
- 建议层: recall · 类目: test

### C2. 集成测试用 marker 门控, 默认不跑
- 规则: 需容器的集成测试 MUST 打 `@pytest.mark.integration` 并由环境变量 `RUN_DB_INTEGRATION=1` 显式开启 (testcontainers)。
- 证据: `lib/pyproject.toml:25` (`markers=["integration: requires container; gated by RUN_DB_INTEGRATION=1"]`)、`lib/tests/test_db_*_integration.py`。
- 建议层: recall · 类目: test

### C3. Skill/command/agent 内容改动过 claude -p 理解门 + test-prompts.json 回归
- 规则: commands/skills/agents/agent.md 的优化 MUST 经 `claude -p "<内容>" --output-format stream-json | jq ...` 验证 AI 可正确识别; skill 目录 SHOULD 配 `test-prompts.json` (prompt/expected 对) 做触发回归。
- 证据: `CLAUDE.md:5-23` (显式硬规 + 适用范围列 commands/skills/agents/agent.md); `skills/git/git-commit/test-prompts.json` (id/prompt/expected)、`skills/git/git-merge/…`、`git-pr/…`、`git-rebase/…`、`skill-dev/skill-dev/test-prompts.json`。
- 建议层: core · 类目: test (成文硬规, 可直升 core)

---

## D. 架构边界 (arch)

### D1. lib = 共享库层, scripts 单向依赖 lib
- 规则: 通用工具/DB ORM MUST 归 `lib` (独立包), scripts 经 `from lib...` 引用; 依赖单向 scripts→lib, lib 不反依赖 scripts。
- 证据: `lib/pyproject.toml:4` "Shared library for ccplugin - utilities and database ORM"、`lib/db/adapters/base.py:9` (`from lib.db.core import ...`)、`pyproject.toml:11` (lib 作依赖) + `:41-42` path 源。
- 建议层: recall · 类目: arch

### D2. DB 多后端走适配器模式 (BaseAdapter + per-db 子类)
- 规则: 数据库支持 MUST 经统一 `DatabaseAdapter`→`BaseAdapter`→{mysql,postgresql,sqlite} 适配器分层, 未实现方法 `raise NotImplementedError`。
- 证据: `lib/db/adapters/base.py:12` (`class BaseAdapter(DatabaseAdapter)`)、`:41,44,47` (NotImplementedError)、`lib/db/adapters/{mysql,postgresql,sqlite}.py`。
- 建议层: recall · 类目: arch

### D3. Sub-agent 只读工具白名单 + 递归护栏 (无 Task/Agent)
- 规则: 后台 worker 型 agent MUST 限工具白名单 (读用 Read/Glob/Grep/Bash, 写盘经脚本, 不给 Write/Edit); MUST 不含 Task/Agent 工具 (防递归派发)。
- 证据: `plugins/tools/cortex/agents/cortex-{evolve,lint,ingest,history,extract}-worker.md:4` (`tools: Read, Glob, Grep, Bash[, WebFetch]` + 描述 "无 Write/Edit, 写盘经脚本"); `deepresearch/agents/*.md:6` (`tools: ["Read","Grep","Glob","Bash"...]`)。skein 铁律亦 "均无 Agent/Task 工具做递归护栏"。
- 建议层: recall · 类目: agent

---

## E. 内容组织 / 文档 (skill / command / agent / plugin)

### E1. Skill 必须多文件: SKILL.md + references/ + templates
- 规则: 每个 skill MUST 为多文件结构, 至少含 `SKILL.md`; 长文拆 `references/*.md`, 模板入 `templates/`; 分类目录配 `README.md` 索引。
- 证据: `scripts/CLAUDE.md:17` 显式 "必须采用多文件的 Skills 规范，确保每一个 Skills 都存在 SKILL.md 以及关联的说明文件"; 结构印证 `skills/*/README.md` + `skills/*/*/SKILL.md` + `skills/skill-dev/skill-dev/references/*.md` + `templates/result-card.html`。58 个 SKILL.md 全仓。
- 建议层: core · 类目: skill (成文硬规)

### E2. Skill frontmatter: name + description (含触发词)
- 规则: SKILL.md frontmatter MUST 含 `name` (kebab-case, 与目录同名) 与 `description`; description MUST 内嵌触发词/场景 (「触发词:」或 "Trigger:"); 手动型加 `disable-model-invocation: true`。
- 证据: `skills/git/git-commit/SKILL.md` (name+description "触发词:「提交」「commit」…")、`code-quality/clean-code/SKILL.md`、`skill-dev/skill-dev/SKILL.md:disable-model-invocation:true`。48/58 SKILL 描述含触发词。
- 建议层: core · 类目: skill

### E3. Command frontmatter: description 必填, name/argument-hint/model/memory 选填
- 规则: command md frontmatter MUST 含 `description` (内嵌 `Trigger:` + 边界); SHOULD 含 `name` `argument-hint`; 可选 `model` (haiku 等) `memory: project` `allowed-tools`。
- 证据: `plugins/tools/trellisx/commands/trellisx-go.md` (name+description "Trigger:…"+argument-hint+memory)、`version/commands/version.md` (model:haiku, memory:project)、`notify/commands/notify-config.md` (description + allowed-tools)。
- 建议层: recall · 类目: command

### E4. Agent frontmatter: name + description + tools + model; worker 加 background:true
- 规则: agent md frontmatter MUST 含 `name` `description` `tools` `model` (inherit/haiku/具名); 后台 worker MUST `background: true`。
- 证据: `plugins/tools/cortex/agents/cortex-evolve-worker.md:1-6` (name/description/tools/model:inherit/background:true)、`cortex-lint-worker.md` (model:haiku)、`deepresearch/agents/*.md`。
- 建议层: recall · 类目: agent

### E5. 每个 plugin 带 .claude-plugin/plugin.json 清单 + README.md
- 规则: 每个 plugin MUST 有 `.claude-plugin/plugin.json` (字段 name/description/author/homepage/repository/license/keywords, 可选 userConfig/skills) 且 SHOULD 有 `README.md`; 集中在 `.claude-plugin/marketplace.json` (`pluginRoot: ./plugins`) 注册。
- 证据: `plugins/tools/*/.claude-plugin/plugin.json` (7 个)、`.claude-plugin/marketplace.json:1-11` (name/owner/metadata.pluginRoot + plugins[])。README: 7 plugin 中 6 有 (deepresearch 缺 → 弱例外)。
- 建议层: core · 类目: build (plugin 打包硬结构)

### E6. 全部 plugin 统一 AGPL-3.0-or-later 许可
- 规则: 所有 plugin 与 marketplace 条目 license MUST `AGPL-3.0-or-later`。
- 证据: `.claude-plugin/marketplace.json` (6 条) + `plugins/tools/*/.claude-plugin/plugin.json` (7 条) 全为 `"AGPL-3.0-or-later"`, grep 13/13 一致。
- 建议层: core · 类目: ops

### E7. 变更自动进暂存/自动提交
- 规则: 本仓所有变更 MUST 自动纳入版本控制 (提交到暂存区/自动 commit); 禁 push。
- 证据: `CLAUDE.md:1` "所有的变更都需要自动提交到暂存区"; 全局 MEMORY auto-commit-enabled 印证 (跨会话硬规)。
- 建议层: core · 类目: git

---

## F. 风格 (style)

### F1. .editorconfig: LF + UTF-8 + tab(4); 数据文件 2 空格; 无末尾空行
- 规则: 代码 MUST LF 行尾、UTF-8、tab 缩进 (宽 4)、去行尾空白、无文件末空行; yaml/yml/json/toml/md/example 用 2 空格。
- 证据: `.editorconfig:1-12` (root=true, tab, insert_final_newline=false, 数据文件 indent_size=2)。
- 建议层: recall · 类目: style
- ⚠ 漂移: Python 脚本仅半数守 tab — `check.py/install.py/statusline.py` 纯 tab, 而 `update.py/clean.py/info.py/utils.py` 纯 4-空格 (`grep -cP '^\t'` 对比: check=1001/0, update=0/954)。editorconfig 声明为准 (强证据) 但实际未统一执行 → 断为约定但标显著漂移, 不宜直升 core 强制。

### F2. 内容中文, 标识符/代码英文
- 规则: 文档/描述/docstring 用中文, 代码标识符/frontmatter key/commit 术语用英文。
- 证据: `scripts/utils.py:9` 中文 docstring + 英文标识符; SKILL/plugin description 全中文 + name kebab 英文。契合全局 CLAUDE.md 交互规则。
- 建议层: recall · 类目: style

---

## G. 缺口 / 播空 (禁硬凑)

- G1. **stdout(机器纯净)/stderr(叙事) 分工无约定**: scripts 均走 rich stdout, 未见 `Console(stderr=True)` 或 stdout 保留纯 JSON 的分离惯例 → 空。
- G2. **幂等命令 / reindex 写盘同步无 CLI 层约定**: 未在 scripts/ 找到显式幂等/reindex 契约 (相关逻辑在各 plugin 内) → 空。
- G3. **ruff/mypy 无配置**: `.ruff_cache`/`.mypy_cache` 存在, ruff 列 dev 依赖 (`pyproject.toml:46`), 但 pyproject 无 `[tool.ruff]`/`[tool.mypy]` 段, 无 mypy.ini/ruff.toml → 无 lint/type 强制约定 (仅默认跑), 不算约定 → 空。
- G4. **CI 无**: `.github/workflows` 不存在 → 无 CI 约定 → 空。
- G5. **scripts/ 无单测**: 测试仅 lib/tests/ (DB), scripts/*.py (check/update 等 7k 行) 无对应 test → 测试覆盖是 gap 非约定。
- G6. dispatch 假设的 `scripts/spec.py` **不存在**; CLI 入口实为 clean/update/info/check/install/md2html (`pyproject.toml:21-27`)。
