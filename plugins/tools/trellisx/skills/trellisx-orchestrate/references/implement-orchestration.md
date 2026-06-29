# Implement 编排

`implement.md` = 执行清单 + 验证 + review gate + rollback。每条 checklist 项 = 一个可派发 subtask, 必填五要素。

## 必备结构

```markdown
# Implement — <task-title>

## 前置检查
- [ ] design.md 已审, 无开放 TODO
- [ ] 工作分支 / worktree 准备
- [ ] 必要工具 / 凭证就绪 (列具体)

## 执行清单 (按依赖排序)

### S1: <subtask 标题>
- 目标: <动词+对象+结果>
- 产出: <diff 路径 | 报告 | 输出>
- 验证: `<可执行命令>`
- 资源: <write-files glob / exec-scope / 端口 / 配置>   # subtask 文件 frontmatter 写 write-files + exec-scope, 冲突判定见 scheduling.md
- 依赖: 无 / S0
- 执行层: main | sub-agent | agent-team | workflow
- 回滚点: <commit hash 或描述>

### S2: <...>
...

## 验证命令汇总

```bash
# 所有 subtask 完成后必跑
<命令 1>
<命令 2>
```

## Review Gates

- Gate G1 (S1-S3 完成后): <人工审查项 / 命令>
- Gate G2 (全部完成后): <最终审查>

## Rollback 计划

- 若 S<X> 失败: <具体回滚命令 / 步骤>
- 若整体失败: <分支删除 / 数据库还原 / 配置恢复>
```

## 五要素 (每条 subtask 必填)

| 要素 | 说明 |
| --- | --- |
| 目标 | 一句话, 动词 + 对象 + 结果 |
| 产出 | diff / 报告章节 / 命令输出 / 截图 |
| 验证 | 优先可执行命令, 次选人工对比 |
| 资源 | 独占文件 glob / 端口 / 配置 / 审批槽位 |
| 依赖 | 前置 subtask id / 上游产出 / 无 |

详见 `five-elements.md`。

## 排序原则

- 按依赖严格拓扑排序 (依赖在前)
- 同依赖层内, 优先无副作用 / 可并行的项
- 高风险项前置 (尽早暴露)
- 资源冲突项必须串行 (写明顺序)

## 执行层标注

每条 subtask 标 `执行层`, 决策表见 `layer-selection.md`。错层 = 浪费 token 或漏并行。

## Review Gates

不是每个 subtask 都需要 gate, 但以下情况必须有:
- 跨层契约首次实现 (S1 完成后人工审契约)
- 不可回滚操作前 (DB migration / 文件大批量移动)
- 整体集成前 (G2)

## Rollback

每条 subtask 必须有可执行的 rollback (commit revert / config restore / data backfill)。若不可回滚 → 升级为 review gate + P0 风险。

## 写 implement 的硬规

1. **每条 checklist 项必须可独立执行**, 不要写"全部完成后再 ..."。

2. **验证必须是命令**, 禁"看看是不是 OK"。

3. **依赖必须显式**, 用 S<id> 引用; 禁"前面那个完成后"这种模糊指代。

4. **资源必须可判冲突** (subtask 文件 frontmatter 填 `write-files` + `exec-scope`), main 静态算冲突 DAG 自动串行冲突项 (见 `scheduling.md`); 并行 subtask 必须资源不交。

5. **Rollback 必须可执行**, 给出具体命令 / hash。

