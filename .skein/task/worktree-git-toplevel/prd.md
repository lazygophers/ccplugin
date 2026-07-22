# worktree 创建/合并严格针对 git 顶层

## 目标

`_mkwt` (skein.py:598) 当前用 `git rev-parse --is-inside-work-tree` 校验 `--repos` 声明的目标路径是否为 git。该命令对**根仓的任意普通子目录**也返回 `true`(非独立仓也算"在工作树内"), 导致声明一个普通子目录会误通过, 随后 `git worktree add cwd=<普通子目录>` 实际给**根仓**开 worktree, 隔离错位。

改为 git 顶层等值判定: 目标路径必须是它**自己那个 git 仓的顶层**, 才允许开 worktree。这样恰好覆盖:

- [ ] 根仓 `.` → show-toplevel = root = sub ✓
- [ ] git submodule → show-toplevel = submodule 路径 = sub ✓
- [ ] 任意深度嵌套的独立 git → show-toplevel = 该路径 = sub ✓
- [ ] 根仓的普通子目录(非独立 git) → show-toplevel = root ≠ sub ✗(拒)

确保 worktree 的**创建 (`_mkwt`)** 与**合并 (`finish` 逐子 git `cwd=sub` merge)** 都严格作用于正确的 git(根 / submodule / 深层嵌套 git), 不会错落到根仓。

## 边界

- [ ] 只改 `plugins/tools/skein/scripts/skein.py` 的 `_mkwt` 校验逻辑 + 新增/补 `plugins/tools/skein/scripts/tests/test_worktree_cli.py` 用例。
- [ ] 判定用 `Path.resolve()` 归一两侧路径(消符号链接/相对差异)后比较, 不靠字符串直接比。
- [ ] 不改 worktree 落盘路径规则(仍 `<repo>/<worktree_root>/skein-<id>`)、不改 `_ignore_wt`、不改 `finish`/`archive`/`_destroy_worktrees` 的 merge/清理逻辑(它们已 `cwd=sub` 正确)。
- [ ] 不改 `use_worktree` / 单根分支(712)语义。
- [ ] submodule 合并后父仓 gitlink 不自动更新 — 本任务不涉及(既有行为保持, 属独立范畴)。
- [ ] 错误信息保持中文, 明确指出须为 git 顶层(根/submodule/嵌套 git), 普通子目录不可声明。

## 验收标准

- [ ] `_mkwt` 对普通子目录(非独立 git)声明 → `raise SystemExit`, 提示须为 git 顶层。
- [ ] `_mkwt` 对任意深度嵌套独立 git 声明 → 通过并在**该子 git 内**建 worktree+branch(worktree 落 `<repo>/.worktrees/skein-<id>`, 注册进该子 git 的 .git)。
- [ ] `_mkwt` 对根仓 `.` → 通过(show-toplevel == root)。
- [ ] `finish` 对多子 git task 逐子 git `cwd=sub` merge 行为不变, 合并作用于正确 git。
- [ ] 新增测试覆盖: 普通子目录拒绝 / 嵌套独立 git 通过; `uv run --with pytest python -m pytest .../tests/test_worktree_cli.py -q` 全绿。
- [ ] `python3 -c "import ast; ast.parse(...)"` 语法通过。

## 索引

- [ ] 实现: `plugins/tools/skein/scripts/skein.py:598` `_mkwt` 校验段(603-605)
- [ ] 测试: `plugins/tools/skein/scripts/tests/test_worktree_cli.py`
- [ ] 关联: `start` 多子 git 分支(708-711)、`finish` 逐子 git merge(768-799)
