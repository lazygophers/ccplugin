# skills 动态感知 worktree 启用态

## 目标

skein 支持 worktree 隔离(`use_worktree=true`, 默认)与原地执行(`use_worktree=false` 或非 git → task `worktree=null`)两态。但 exec/check/finish 三个 SKILL.md、`skein-exec/references/scheduling-algorithm.md` 的 dispatch prompt 模板、以及 skein-executor/checker/finisher 三个 agent 的描述, 全部硬编码"在 task worktree 内 / 禁碰主工作区", 原地态下无对应指引且与"改主工作区"矛盾。

改造使这些 AI 面向文案**动态感知** worktree 启用态:

- [ ] skein.py `config` 加 `--json` 输出, 使 `skein config --json | jq -r .use_worktree` 可解析布尔真值。
- [ ] exec/check/finish SKILL.md 用 Claude Code 官方 `` !`cmd` `` 注入 (skill 载入时执行, 输出替换占位符) 渲染当前 worktree 启用态: `` !`skein config --json 2>/dev/null | jq -r .use_worktree` ``。
- [ ] 三 SKILL.md + dispatch 模板 + 三 agent 把绝对的"worktree 内"措辞改为**两态条件式**: worktree 启用 → task worktree 路径 + 隔离铁律; 禁用(原地) → 仓库根 + 免隔离说明。工作目录真值以 task 的 `worktree` 字段为准(null=原地)。

## 边界

- [ ] 改文件: `plugins/tools/skein/scripts/skein.py`(config_cmd + config parser 加 --json)、`tests/test_config_cli.py`(补 --json 用例)、`skills/skein-exec/SKILL.md`、`skills/skein-exec/references/scheduling-algorithm.md`、`skills/skein-check/SKILL.md`、`skills/skein-finish/SKILL.md`、`agents/skein-executor.md`、`agents/skein-checker.md`、`agents/skein-finisher.md`。
- [ ] `--json` 只作用于无参 `config`(展示态); `set`/`reset` 输出不变。JSON 为生效配置(含 ENV override + 缺键回填)。
- [ ] 注入命令用裸 `skein`(沿用现有 skills 全用裸 `skein xxx` 约定); `2>/dev/null` + jq 缺失/空输出时优雅降级(文案仍给两态说明, 不依赖注入必成功)。
- [ ] 不改 worktree 创建/合并/生命周期逻辑(Task A 已定)、不改 `use_worktree` 语义、不改调度 DAG。
- [ ] 措辞两态化不得削弱既有铁律: worktree 启用时"禁碰主工作区"仍在; 仅新增原地态分支。

## 验收标准

- [ ] `skein config --json` 输出合法 JSON, `skein config --json | jq -r .use_worktree` 得 `true`/`false`; 无参 `skein config`(不带 --json)仍输出 `key=value` 行(不回归)。
- [ ] `set`/`reset` 输出格式不变。
- [ ] exec/check/finish SKILL.md 各含一处 `` !`skein config --json ... | jq -r .use_worktree` `` 注入占位, 且正文对工作目录给 worktree/原地两态指引。
- [ ] dispatch prompt 模板(scheduling-algorithm.md)工作目录字段两态化: worktree 启用填 worktree 路径 + 隔离铁律; 原地填仓库根。
- [ ] skein-executor/checker/finisher 三 agent 描述与正文的"worktree 内"改为不假定隔离的两态措辞。
- [ ] `test_config_cli.py` 补 --json 用例, `uv run --with pytest python -m pytest .../tests/test_config_cli.py -q` 全绿; `python3 -c "import ast; ast.parse(...)"` 通过。
- [ ] 改动的 skills/agents 经 `claude -p` 理解测试确认 AI 能正确识别两态指引(CLAUDE.md 代码质量检查规范)。

## 索引

- [ ] 实现: `skein.py:231` config_cmd + `:3107` config parser; 6 个 skills/agents 文案
- [ ] 测试: `tests/test_config_cli.py` + `claude -p` 理解测试
- [ ] 关联: Task A `worktree-git-toplevel`(已合入)、审计发现的 7 处硬编码
