# concurrency-pools sediment 待补 (2026-08-02)

`sediment-pools` agent 两次转 idle 均无回传, 实测 `.skein/spec/` 零新增零修改
(`git log -- .skein/spec/` 最新仍是 s7 的三个 commit; `find -newermt '-40 minutes'` 空)。
本会话 API 持续断连(已死 16 个 agent), 判定为环境问题, **非「无可沉淀」**。

sediment 属异步 fire-and-forget, 不阻塞 task 闭环, 故 `concurrency-pools` 已正常 finish。
下面是 main 整理的候选点, 待环境恢复后重派 `skein-specer` 处理。**这份文件本身不是 spec,
只是候选清单** —— 落盘仍须经 `skein-spec` CLI 走查重与 namespace/inclusion 判定。

---

## 候选 1: worktree 分支合并禁用「一律取一侧」

本次首轮合并用 `git checkout --theirs` 批量解 36 处冲突, 把**分支切出后才合入 master** 的
`board-live-refresh`(b1~b4) 整个 live-refresh 功能撤销了 —— `applyTaskChanged` /
`applyTaskChangedBatch` 在合并结果里直接消失。

pytest 只抓到 `views.py` 一处(唯一有 Python 测试覆盖的那处), 三个 `.ts/.tsx` 的功能删除
**测试完全抓不到**。

正确做法:
1. 先跑归因审计 —— 列出「排除已知坏 commit 后, `merge-base..master` 真正独有改动的文件」
2. 对落在该清单里的冲突文件, 用 `git merge-file <master版> <共同祖先> <分支版>` 三方合并
3. 不在该清单里的, 才可以整侧取

本次审计结果: 12 个文件有 master 独有改动, 与冲突面交集 4 个, 逐个三方合并/手工补齐后
425 passed。

## 候选 2: 构建产物的完整性判据是引用可达性, 不是 diff 大小

Next.js 每次 build 生成随机 buildId, 所以 rebuild 后 dist **必然**有大量 diff。
「diff 很大」≠「上次构建不完整」。

正确判法: 扫全部 dist `.html`/`.txt` 里的 `/_next/` 引用, 确认目标文件都存在。
本次实测: 引用总数 1541, 唯一缺失 0。

本会话有 checker 因误用 diff 判据而错判 FAIL, 且为此违规跑了 `npm run build`(check 应只读)。

## 候选 3: 删枚举值必须配存量迁移

s1 删 `S_READY` 时没人想到磁盘上还躺着 `status="就绪"` 的存量 task.json, 合入 master 后
doctor 立刻报「非法 status」。缺口是 main 在 exec 期间才发现并补建 s9 才补上的。

凡是删/改**状态枚举、配置键名**这类有磁盘残留的模型改动, 规划期就该配一个迁移 subtask。

迁移器内部保留旧字面量是**刻意的**(要能读到旧值才能迁), 不算残留 —— 零残留扫描要给它开豁免。

## 候选 4: 归因要跑命令, 不能凭印象

checker 报「本 task 零新增 ruff 违反」, main 实跑得 14 errors 并逐条 `git blame`, 确认
2 条系本 task 引入。checker 随后自称其推理是「先有结论再填证据的反面工程」。

## 候选 5: worktree 与主仓根的 `.skein/task/` 是两份独立副本, 会各自漂移

`skein` 从 **cwd** 解析仓库根。agent 在 worktree 里跑 `subtask done`, 只写 worktree 那份;
main 在主仓根读到的仍是旧状态。反过来 worktree 那份也可能缺主仓根的更新。

本会话因此对错状态两次(d4 一次、f1 一次)。

硬规: **agent 回传「我已 done」后, main 必须在主仓根自己核一次并补跑 `subtask done`**,
不能直接采信; 读状态前先确认 cwd 在哪个根。

## 候选 6: `skein subtask done` 静默丢弃 `--note`

留痕必须自己写进 `design.md`。(可能已沉淀过, 落盘前查重)

## 候选 7: 文档里的 CLI 示例会被 AI 照抄执行

d4 发现 `skein-clean.md` / `skein-setup.md` 写着让 agent 跑 `skein-spec migrate` ——
该子命令根本不存在(`spec.py --help` 只有 `sediment`/`archive`/`restore`/`restructure`),
照抄会当场报错。

仓库已有 `tests/test_docs_commands.py` 现跑 `--help` 解析合法命令面再逐条校验文档示例,
比人眼扫可靠。改动 skill/agent 文档后应跑它。
