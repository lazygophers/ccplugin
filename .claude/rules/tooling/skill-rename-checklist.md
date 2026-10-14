# skill 改名要动的清单（仓库内外共 6 处，漏一处就改名不彻底）

2026-10-14 ask-ui → ask-me 全量改名（commit c7918242、7a7d3afb）实测的完整触达面。
改名 ≠ 只换目录名，还有内外标识符和三份仓库外拷贝：

仓库内（全仓 `grep -rn "旧名"` 扫，graphify-out/ 是生成物可忽略）：

1. skill 目录本身 + `SKILL.md` 的 `name` + 入口脚本文件名（含 `.mts`/`.mjs` 两份）
2. 内部标识符：环境变量（`ASK_UI_SKILL_DIR` → `ASK_ME_SKILL_DIR`）、stderr 标记
   （`ask-ui-id`）、数据目录（`.ask-ui/` → `.ask-me/`）、日志名、localStorage key
3. 引用处：`.claude-plugin/marketplace.json`、`plugin.json`、`scripts/hooks/pre-commit`、
   项目 `CLAUDE.md`、`docs/ONBOARDING.md`、其他 skill 的脚本（如 tracking_progress.py）、
   `.claude/rules/` 各文件里的路径

仓库外（git 扫不到，逐个手动）：

4. 全局 `~/.claude/CLAUDE.md`（当次 15 处）和 `~/.gitignore_global`（旧数据目录名）
5. 装出去的副本：`npx skills remove 旧名` + `npx skills add lazygophers/ccplugin/skills/tools/新名`
   ——`update` 只更新同名 skill，改名必须删旧装新；lock hash 由 CLI 重算，不手改
6. 迁移提示词：其他用户装的是旧名，给一段删旧装新的整段提示词落进 `docs/`（样例
   `docs/ask-me-migration.md`），再把新旧标识符对照表附上

收尾自检：仓库与副本各跑一次 `scripts/self-test.mjs`；`diff -rq` 两份目录；全仓 grep
旧名为零（生成物除外）。

出处：commit c7918242、7a7d3afb；.scratch/memory/2026-10-14.md。
