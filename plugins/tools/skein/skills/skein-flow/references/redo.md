# redo — 断点续跑

redo 解的是 session 意外结束后的状态卡死，不是回滚：只改 subtask 状态，不删除、不撤销上一轮已产出的文件改动，也不新增引擎命令（复位就用现有 `subtask fail` + `subtask start` 拼法）。

动手前必须说明：redo 期间禁止有 agent 在跑；全部 running subtask 一律当孤儿，不做心跳/存活探测/时长阈值。

| 起点状态    | redo 行为                                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| `pending`   | 无 running 可复位；续 plan 到收敛。带 `--plan` 时停在 confirm 前。                                              |
| `research`  | 复位 running research subtask；续 research 到 done，再 `skein task plan` 回 pending。带 `--plan` 时停在 confirm 前。 |
| `active`    | 复位全部 running subtask，再回 exec 调度。                                                                      |
| `check`     | 无 subtask 可复位；直接重派 `skein-checker`。带 `--plan` 时说明已过规划阶段，参数未生效。                       |
| `finishing` | 无 subtask 可复位；直接重派 `skein-finisher`。带 `--plan` 时说明已过规划阶段，参数未生效。                      |
| `done`      | 报已闭环，无事可做。                                                                                            |

active 起点复位固定拼法：

```bash
skein subtask fail <tid> <sid> --note "redo 孤儿复位: session 意外退出, 全部运行中一律当孤儿"
skein subtask start <tid> <sid>
```

复位后必须回传被复位清单；无 running subtask 时回传「无运行中 subtask 需复位，直接续调度」。
