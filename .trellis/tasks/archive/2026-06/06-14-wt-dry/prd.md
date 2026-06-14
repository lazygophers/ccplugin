# trellisx worktree 路径/分支/命名抽公共函数去重

## Goal

根治 worktree 路径/分支/命名逻辑在 `scripts/trellisx-worktree.py` 与 `scripts/trellisx-finish.py` **各写一份**导致的漂移风险:抽成单一公共模块,两脚本共用。**保持现状约定不变** (`<git根>/.worktrees/{worktree_name}` + 分支 `trellisx-{name}`,多包 `pkg-tid`/`service-tid`/`tid` 命名)。

## 背景 (核实结论, 修正原报告前提)

- 原报告称的 `hooks/trellisx-worktree.py` (`.trellis/worktrees/{tid}` 约定) **不存在** (repo+cache 均无)。worktree 实际创建者 = apply 注入的 `scripts/trellisx-worktree.py` (经 config.yaml after_start hook)。
- finish.py 与 worktree.py 当前**已一致** (都 `.worktrees/{worktree_name}` + `trellisx-{name}`),单仓收尾已验证可用。**不做路径迁移** (用户裁定: 保现状)。
- 真实问题 = 逻辑重复 (DRY),非路径失配。

## Requirements

### R1 新公共模块 `scripts/trellisx_wt.py`
单一真值, 导出:
- `git_top(d)` — 用 `--git-common-dir` 定位**主 worktree** 根 (从 linked worktree 内也正确)
- `worktree_name(tid, pkg, service)` — `pkg-tid` / `service-tid` / `tid`
- `resolve_repo(troot, pkg)` — 3 布局 (groot, service) 解析
- `worktree_paths(groot, tid, pkg, service)` → `(name, wt, br)`:`groot/.worktrees/{name}`,`trellisx-{name}`

### R2 `trellisx-worktree.py` 改用公共模块
- 删本地 `git_top`/`resolve_repo`/inline 的 name/wt/br 计算,改 `import trellisx_wt` (加 `sys.path` 指向脚本自身目录)
- 行为完全不变 (start 建 / archive 销 + merge-base 检查)

### R3 `trellisx-finish.py` 改用公共模块
- 删本地 `git_top`/`worktree_name`/`resolve_repo`/inline name/wt/br,改 `import trellisx_wt`
- 行为不变 (commit→merge→archive→销;冲突 abort;幂等)

### R4 apply 注入更新
- `hook-injection.md` / `workflow-injection.md` 注入点5:复制脚本由 3 → **4** (加 `trellisx_wt.py` 公共模块)
- `apply-verify.md`:断言 `trellisx_wt.py` 已复制 + 两脚本 `import trellisx_wt`

### R5 `.gitignore` 补顶层 `.worktrees/`
- 当前只有 `graphify-out/.worktrees/`,顶层 `.worktrees/` 未排除 → 补 `.worktrees/`

## Acceptance Criteria

- [ ] `scripts/trellisx_wt.py` 存在,语法合法,导出 `worktree_paths`/`worktree_name`/`git_top`/`resolve_repo`
- [ ] `trellisx-worktree.py` + `trellisx-finish.py` 均 `import trellisx_wt`,无本地重复的 wt/br/name 计算
- [ ] 三脚本语法合法
- [ ] `trellisx-finish.py --dry-run --task 06-14-wt-dry` 输出 `worktree = <git根>/.worktrees/06-14-wt-dry (存在=True)`,不再「无 worktree」
- [ ] 行为不变:dry-run 计划与重构前一致 (路径/分支/命名)
- [ ] hook-injection / workflow-injection / apply-verify 反映 4 脚本 + import
- [ ] `.gitignore` 含顶层 `.worktrees/`
- [ ] 仅改插件源 (plugins/tools/trellisx/**) + `.gitignore`

## 范围边界

- ⛔ 不改路径/分支/命名约定 (保 `.worktrees/{name}`)
- ⛔ 不动 .trellis 注入产物
- ⛔ 不加 hooks/ PostToolUse (不存在,不新造)

## Notes

单一交付 (DRY 重构),跨脚本+文档但同一逻辑变更,不拆 child。验收靠 dry-run 行为等价 (重构前后路径/分支/命名输出一致)。
