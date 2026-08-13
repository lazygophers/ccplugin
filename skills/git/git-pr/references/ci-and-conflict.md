# CI 状态 · 冲突判定 —— git-pr 详表

主流程见 [../SKILL.md](../SKILL.md)。提交 PR/MR 后的 CHECKPOINT 依据。

## §ci CI/action 状态

### GitHub
```bash
gh pr checks                              # 各 check 的 pass/fail/pending 一览
gh pr checks --watch                      # 阻塞直到跑完(交互场景)
gh run list --branch <branch> --limit 5   # 关联的 workflow run
gh run view <run-id> --log-failed         # 失败 job 的日志(只取 failed 步骤)
```
- `gh pr checks` 退出码:全绿=0,有失败=非0,可据此判定。
- 取失败摘要:`gh run view <run-id> --log-failed | tail -50`,给用户诊断 + 建议,不代改。

### GitLab
```bash
glab ci status                # 当前分支 pipeline 状态
glab ci view                  # pipeline 各 job
glab ci trace <job-id>        # 某 job 日志
```

## §mergeable 冲突判定

### GitHub 字段
```bash
gh pr view --json mergeable,mergeStateStatus -q '{m:.mergeable,s:.mergeStateStatus}'
```
| `mergeable` | 含义 | 动作 |
| --- | --- | --- |
| `MERGEABLE` | 无冲突可合 | 通过 |
| `CONFLICTING` | 有冲突 | AskUserQuestion:是否 merge/rebase 目标分支解冲突(指路 git-merge/git-rebase) |
| `UNKNOWN` | GitHub 后台仍在计算 | **稍等 2-3s 重查一次**,别当无冲突;多次仍 UNKNOWN → 报「GitHub 尚未算出,请稍后网页查」 |

`mergeStateStatus` 补充:`BLOCKED`(缺 review/check)、`BEHIND`(落后 base 需更新)、`DIRTY`(冲突)、`CLEAN`(可合)。

### GitLab 字段
```bash
glab mr view --json    # 看 detailed_merge_status / has_conflicts
```
- `detailed_merge_status`:`mergeable` / `conflict`(冲突) / `ci_still_running` / `not_approved` 等。
- `conflict` → 同 GitHub 冲突分支处理。

## §checkpoint 汇总动作(与 SKILL.md §4 表一致)

| 结果 | 动作 |
| --- | --- |
| CI 绿 + mergeable | 报成功 + URL,完成 |
| CI 失败 | 取 `--log-failed` 摘要 → AskUserQuestion 是否修 |
| 冲突(CONFLICTING/conflict) | AskUserQuestion 是否解 → 指路 git-merge/git-rebase |
| mergeable=UNKNOWN | 稍等重查,别误判 |
| CI pending | 报 pending + 复查命令 |

**始终**:是否修 CI、是否解冲突,都用 AskUserQuestion 问用户,不自主改代码(硬规 3)。
