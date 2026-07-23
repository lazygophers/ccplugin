# SKEIN 文档

独立任务管理插件 — 零 trellis/trellisx 依赖, 自带 `.skein/` 工作区。
名取「线团」: 任务如纱线, 编织、调度、收束。

## 一句话上手

```
/skein-exec 给用户模块加上手机号登录, 含短信验证码下发与校验
```

复杂请求自动触发 `skein-flow` 闭环, 无需显式命令。

## 前置条件 & 初始化

| 条件 | 说明 |
| --- | --- |
| git ≥ 2.5 | 需要 `git worktree` |
| Python ≥ 3.9 | — |

```
skein init    # 或由 skein-setup skill 自动触发
```

**.skein/ 目录**:

| 路径 | 用途 | 维护者 |
| --- | --- | --- |
| `config.yaml` | 用户配置 | 用户 |
| `task.json` | 状态汇总 | 脚本 (AI 禁读写) |
| `task.md` / `task.html` | 看板 | 脚本渲染 |
| `task/<id>/` | task 记录 | 脚本 + AI |
| `spec/core/` | 常驻规则 | skein-spec |
| `spec/recall/` | 按需规则 | skein-spec |

## 首个 task

```
/skein-exec 加一个用户列表页, 含分页和搜索
```

| 阶段 | 行为 |
| --- | --- |
| plan | brainstorm + grill + PRD + subtask DAG |
| exec | DAG 调度, worktree 隔离, 每步验收 |
| check | lint / type / test / contract |
| finish | 合并 → sediment → archive |

```
skein current    # 活跃 task
skein board      # 文本看板
skein view       # 可视化 HTML 看板
```

## 核心概念

| 概念 | 说明 |
| --- | --- |
| task | 闭环工作记录, 存 `.skein/task/<id>/` |
| 闭环 | plan→exec→check→finish, 不可跳步 |
| worktree 隔离 | 每 task 一个 git worktree, 主工作区零改动 |
| 双层 DAG | task + subtask 同构 DAG, 完成即派 |
| 两层规则记忆 | core (常驻注入) + recall (按需召回) |
| sediment 判定门 | finish 时判 learning → core/recall/drop |
| contract | planning 锁不变量, check 逐条验证 |

## 请求路由

| 信号 | 条件 | 行为 |
| --- | --- | --- |
| flow | 跨文件 / 多步 / 破坏式 | 自动建 task |
| inline | 单文件小改 | 直接改 |
| grey | 模糊 | AskUserQuestion |

`/skein-exec` = 强制 flow 信号。

## 文档

- [skein.md](skein.md) — 架构 / 生命周期 / 调度 / 规则记忆
- [reference.md](reference.md) — CLI / skill / agent / config / 场景 / 术语
- [examples/](examples) — 完整样例 .skein/
