# apply 强制化 finish 收尾 (脚本化半硬)

## Goal

让 `trellisx-apply` 注入的 workflow 收尾从「提示用户 finish / 软约束」升级为**脚本化强制收尾**: check 通过后 AI 调用一键脚本完成 commit→merge→archive→销 worktree, finish 与 worktree 删除是强制必须的, 不再停在「提醒用户运行 /finish-work」。

## 背景 / 决策

- 用户授权: **允许 apply 直接修改 workflow.md 的 finish 部分** (局部豁免铁律1「绝不替换原生」, 仅限 finish 段)。
- 机制选型: **脚本化 finish (半硬)** —— 加 `trellisx-finish.py` 一键收尾脚本 + workflow.md finish 改强措辞调用脚本; 不加 Stop hook 硬拦 (那是「两者结合」选项)。
- commit 自动化: 用户作为项目 owner 显式要求其 trellisx 流程强制 commit/finish, 即对该项目注入流程的授权 (全局「禁主动 commit」是 AI 对用户的默认, 用户对自有流程的设计意图覆盖之)。脚本 commit 消息由调用方 `--message` 传入或默认生成。

## Requirements

### R1 新脚本 `trellisx-finish.py` (插件 scripts/ + apply 复制到目标项目 .trellis/scripts/)
一键强制收尾, 幂等可重入:
1. 定位 active task (`task.py current`) + 对应 worktree/分支
2. worktree 有改动 → `git add -A` + `git commit -m <msg>` (msg 来自 `--message`, 缺省 `chore(task): <tid> 收尾提交`)
3. 合并 worktree 分支回主分支 (`git merge --no-ff trellisx-<name>`); 冲突 → 退出码非 0 + 报告冲突文件, 不强解
4. `task.py archive <tid>` (触发 after_archive hook → trellisx-worktree.py 检测已合并 → 销毁 worktree + 删分支)
5. 输出收尾报告 (提交 sha / 合并 / 归档路径)
失败任一步 → 非 0 退出 + 明确错误, 不静默继续。

### R2 apply 注入: workflow.md finish 段强制化 (workflow-injection.md)
- in_progress 块收尾序列改为: check 通过 → **调用 `trellisx-finish.py`** 强制收尾 (替代「提醒用户 /finish-work」)。
- **允许改写原生 3.5 收尾提醒段** (用户授权的 finish 局部豁免): 由「提醒用户可运行 /finish-work」改为「AI 强制调用 trellisx-finish.py, finish/worktree 删除为必须」。其余原生段 (no_task/planning/check/前缀) 仍守铁律1 不动。

### R3 apply hook/script 注入 (hook-injection.md)
- apply 执行时把 `trellisx-finish.py` 复制到目标项目 `.trellis/scripts/`。
- commit 消息确认门: 保留「AI 出提交计划」但不再等用户逐次确认 (强制), 仅在 commit 计划展示后直接执行 (尊重 owner 授权)。

### R4 apply SKILL.md + apply-verify.md 同步
- 铁律1 增「finish 段局部豁免」说明; 注入维度表「闭环」行改为脚本化强制收尾。
- apply-verify.md 断言 `trellisx-finish.py` 已复制 + workflow finish 段含脚本调用。

## Acceptance Criteria

- [ ] `plugins/tools/trellisx/scripts/trellisx-finish.py` 存在, `python3 -c "ast.parse"` 语法通过
- [ ] 脚本含 commit→merge→archive→销 worktree 全序列 + 冲突非 0 退出 + 幂等
- [ ] `workflow-injection.md` finish 注入由「提醒」改「强制调用脚本」, 标注 finish 段豁免铁律1
- [ ] `hook-injection.md` 含 trellisx-finish.py 复制步骤
- [ ] `apply/SKILL.md` 铁律1 finish 豁免 + 注入维度闭环行更新
- [ ] `apply-verify.md` 含 finish 脚本断言
- [ ] 仅改插件源 (plugins/tools/trellisx/**), 不动 .trellis 注入产物

## 范围边界

- ✅ 改 trellisx 插件源 (scripts + apply skill + references)
- ⛔ 不加 Stop hook 硬拦 (用户选半硬)
- ⛔ 不动 .trellis/ 注入产物 (dogfood 注入是另一回事)
- ⛔ 不改其他 skill (orchestrate/spec/workspace/flow)

## Notes

单一交付 (强制化 finish 一条线), 跨多文件但属同一逻辑变更, 不拆 child。
