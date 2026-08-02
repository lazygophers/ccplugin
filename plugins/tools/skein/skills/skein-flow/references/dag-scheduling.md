# DAG 调度算法

SKEIN DAG 调度的算法说明：依赖模型、ready 判定、排序、池模型。执行循环、plan-ahead 过程、自愈、阶段跳转统一见 [flow-loop.md](flow-loop.md)。

## 1. DAG 依赖模型

SKEIN 只认显式依赖边，不推测隐式顺序。

| 层级 | 字段 | 登记位置 | 登记命令 |
|---|---|---|---|
| subtask | `depends_on` / `deps` | per-task `task.json` 的 `subtasks[].depends_on` | `skein subtask add --deps <sid1>,<sid2>` |
| task | `deps` | 顶层 task 索引 | `skein create --deps <tid1>,<tid2>` |

`A --deps B` 表示 A 依赖 B，B done 后 A 才 ready。

## 2. 唯一边源原则

- 并行与否只看显式 DAG。
- 有序关系必须在 planning 阶段写入 `depends_on`。
- 无真实顺序依赖就不加边；共享契约用单个前置 subtask 承载。
- subtask 参数表见 [subtask-operations.md](subtask-operations.md)。

## 3. ready 判定

```text
subtask.ready = 所有 depends_on 均 done
                且 subtask.status == pending
                且 pools.work 有空槽
```

| 操作 | 是否被 deps 阻塞 | 说明 |
|---|---|---|
| `skein create` / `subtask add` | 否 | planning 可提前做。 |
| `skein confirm` | 是 | task 前置未 done 时拒。 |
| `skein claim exec` | 是 | subtask 前置未 done 不 ready。 |

## 4. 排序

ready 数超过空闲槽时，`claim exec` 按稳定排序截取：

1. 拓扑深度降序：阻塞下游最多者优先。
2. task 登记序：同深度时先创建 task 优先。
3. subtask 登记序：同 task 同深度时先 add subtask 优先。

拓扑深度：

```text
crit_weight(node) = 1 + max(crit_weight(child) for child in children(node))
叶子 = 1
```

## 5. BFS 分层

用于看板渲染 / 调试输出：

```text
layer(source) = 0
layer(node) = max(layer(dep)) + 1
```

## 6. 双池模型

| 池 | 计数对象 | 配置 | 校验位置 |
|---|---|---|---|
| `work` | `status=running` 的 exec/research subtask | `pools.work` | `skein claim exec` / `subtask start` |
| `gate` | `status=check` / `status=finishing` 的 task | `pools.gate` | `skein finishing` |

`skein confirm` 不占池；真正资源约束在 running subtask 与 gate task。

## 7. claim 命令族

| 命令 | 范围 | 语义 |
|---|---|---|
| `skein claim` | 全局跨 task | 同时处理 exec + check 两路；回传自带 agent 路由（subtask 行 `agent:` 列 = `skein-executor`/`skein-researcher`，task 行 `agents` = `skein-checker` 或 `skein-finisher`+`skein-specer`），main 照单派。 |
| `skein claim --dry-run` | 全局跨 task | 同时预览 exec ready subtask 与 check/finishing task，不改态。 |
| `skein claim exec` | 全局跨 task | 批量认领 ready subtask 并标 `running`。 |
| `skein claim exec --dry-run` | 全局跨 task | 只读预览 exec ready subtask，不改态。 |
| `skein claim check` | 全局跨 task | 认领可进 check / finishing 的 task。 |
| `skein subtask claim <tid>` | 单 task | 单 task 内批量认领。 |
| `skein subtask start <tid> <sid>` | 单 subtask | 启动 pending/failed subtask。 |

完成即派、失败自愈、redo 后续调度见 [flow-loop.md §5](flow-loop.md#5-exec-过程)、[flow-loop.md §8](flow-loop.md#8-redo-断点续跑)、[flow-loop.md §9](flow-loop.md#9-失败扭转)。

## 8. dispatch 参数

exec 统一派 `skein:skein-executor`。dispatch 只给 tid、sid、工作目录；executor 自读 `skein subtask show <tid> <sid>`。完整载体规则见 [carrier-rules.md](carrier-rules.md)。
