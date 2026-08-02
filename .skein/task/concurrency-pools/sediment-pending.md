# concurrency-pools sediment 待补 (2026-08-02)

> **本文件不是 spec, 只是 main 的临时候选清单。** 落盘须经 `skein-spec` CLI 走查重与
> namespace/inclusion 判定, 由 `skein-specer` 处理。

## 更正记录 (2026-08-02)

本文件初版声称 `sediment-pools` 「零写入」, **该判定是错的**。

错因: main 跑了 `git log --oneline -6 -- .skein/spec/`, 而 `053fe262a` 就是返回列表第一条 ——
带 pathspec 的 `git log` 只列出碰过该路径的 commit, 它出现在结果里本身就是证据。main 看到
commit message 是「plan(skein): 新建 drop-ready-frontend」便想当然认为与 spec 无关, 未查 `--stat`。

根因是 main 自己造的: 用 `git add -A` 提交那个 plan commit, 把 specer 正在写的三个 spec 页
一起打包进了一个名字不相干的 commit。

实测:
```
$ git show --stat 053fe262a | grep -i spec
 .skein/spec/recall/impl/robustness.md                    | 13 ++-
 .skein/spec/recall/ops/merge-conflict-resolution.md      | 19 ++++
 .skein/spec/recall/planning/attribution-verification.md  | 16 +++
```

---

## 已落盘 ✅ (specer 完成, 见上述三页)

- **worktree 分支合并禁用批量 `--theirs`, 改三方合并 + 独有改动归因审计**
  → `.skein/spec/recall/ops/merge-conflict-resolution.md`
  该页比 main 给的素材多出一条: 合并后要 grep 符号名确认关键函数仍存在, **不能只靠测试通过就放行** ——
  正是本次事故的要害(测试只覆盖 `.py`, `.ts/.tsx` 的功能删除完全没被抓到)。

- **归因结论要跑命令, 不能凭印象**
  → `.skein/spec/recall/planning/attribution-verification.md`

- **删/改状态枚举等有磁盘残留的模型改动需配存量迁移 subtask**
  → `.skein/spec/recall/impl/robustness.md` (追加章节)

---

## 待处理 (已派回 specer)

### 候选 1: 构建产物完整性判据是引用可达性, 不是 diff 大小

Next.js 每次 build 生成随机 buildId, 所以 rebuild 后 dist **必然**有大量 diff。
「diff 很大」≠「上次构建不完整」。

正确判法: 扫全部 dist `.html`/`.txt` 里的 `/_next/` 引用, 确认目标文件都存在。
本次实测: 引用总数 1541, 唯一缺失 0。

本会话有 checker 因误用 diff 判据而错判 FAIL, 且为此违规跑了 `npm run build`(check 阶段应只读)。

### 候选 2: worktree 与主仓根的 `.skein/task/` 是两份独立副本, 会各自漂移

`skein` 从 **cwd** 解析仓库根。agent 在 worktree 里跑 `subtask done`, 只写 worktree 那份;
main 在主仓根读到的仍是旧状态。反过来 worktree 那份也可能缺主仓根的更新。

本会话因此对错状态两次(d4 一次、f1 一次), main 自己还因为 cwd 在 worktree 里而读到过一次
相反的结论。

硬规: **agent 回传「我已 done」后, main 必须在主仓根自己核一次并补跑 `subtask done`**,
不能直接采信; 读状态前先确认 cwd 在哪个根。

### 候选 3: 文档里的 CLI 示例会被 AI 照抄执行

d4 发现 `skein-clean.md` / `skein-setup.md` 写着让 agent 跑 `skein-spec migrate` ——
该子命令根本不存在(`spec.py --help` 只有 `sediment`/`archive`/`restore`/`restructure`),
照抄会当场报错。

仓库已有 `tests/test_docs_commands.py` 现跑 `--help` 解析合法命令面再逐条校验文档示例,
比人眼扫可靠。改动 skill/agent 文档后应跑它。

### 候选 4: `skein subtask done` 静默丢弃 `--note`

留痕必须自己写进 `design.md`。疑似已沉淀过, 落盘前查重。
