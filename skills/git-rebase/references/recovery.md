# 恢复 · 备份 · 强推 —— git-rebase 详表

主流程见 [../SKILL.md](../SKILL.md)。rebase 不可逆,恢复手段是安全网。

## §backup 备份分支

```bash
git branch "backup/${CUR}-$(date +%Y%m%d-%H%M%S)"
```
- 硬规 1,任何情况不跳。备份是轻量引用(不占空间),指向 rebase 前的 commit。
- 重名(同秒):加 `-2` 或换更细时间戳重试;建不成 → STOP,绝不无备份 rebase。
- **验证无误前不删**。确认 rebase 结果正确后才 `git branch -D backup/<...>`。

## §recover 出错回退(按严重度递增)

| 情形 | 恢复命令 |
| --- | --- |
| rebase 进行中想放弃 | `git rebase --abort`(回到 rebase 前状态) |
| rebase 已完成才发现错 | `git reset --hard backup/<...>`(用备份分支回退) |
| 备份也删了 / 无备份 | `git reflog` 找 rebase 前的 HEAD(形如 `HEAD@{n}: rebase (start)` 前一条),`git reset --hard HEAD@{n}` |
| 某个中间提交丢了 | `git reflog` / `git fsck --lost-found` 找 dangling commit,`git cherry-pick <hash>` 捡回 |

`git reflog` 默认保留 90 天,rebase 前的 HEAD 一定在里面,是最后的安全网。

## §push 已推远端分支的强推

rebase 改写了历史,本地与远端分叉,普通 push 被拒。**禁裸 `--force`**:
```bash
git push --force-with-lease           # ✅ 仅当远端仍是你上次见到的状态才覆盖
git push --force                       # 🔴 禁:无条件覆盖,会抹掉他人期间推的提交
```
- `--force-with-lease`:若他人在你 rebase 期间推了新提交,远端已变 → 推被拒,保护他人工作。
- 更稳:`git push --force-with-lease=<branch>:<你 fetch 到的远端 sha>`。
- 共享分支强推前**必先告知用户**会影响协作者(他们需 `git reset --hard origin/<branch>` 或重新 rebase 各自工作)。用户不接受 → 改用 git-merge。
