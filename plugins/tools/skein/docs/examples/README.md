# 样例 `.skein/`

真实执行中快照——10 task (7 在看板 + 3 归档) 覆盖全部状态 + 显式依赖 DAG。
所有 json/md 由 `skein` / `skein-spec` 真跑生成 (仅 prd/design/findings 手动)。

## Task 一览

| task | 状态 | 说明 | 位置 |
| --- | --- | --- | --- |
| **order-create-api** | 进行中 | exec 中途, 4 subtask 覆盖四态 | `task/order-create-api/` |
| payment-gateway | 检查中 | exec 完, 质量门验证中 | `task/payment-gateway/` |
| inventory-service | 进行中 | 混合态 + 依赖链 | `task/inventory-service/` |
| order-pay | 待处理 | deps order-create-api, 已 plan | `task/order-pay/` |
| refund-flow | 待处理 | deps order-pay+payment-gateway | `task/refund-flow/` |
| order-report | 待处理 | deps order-create-api | `task/order-report/` |
| notification-service | 待处理 | deps payment-gateway | `task/notification-service/` |
| order-query | 已归档 | 前日完成 | `task/archive/2026/07-11/` |
| user-auth | 已归档 | — | `task/archive/2026/07-10/` |
| api-gateway | 已归档 | — | `task/archive/2026/07-09/` |

## Subtask 演示 (order-create-api)

| sid | 名称 | 状态 | 含义 |
| --- | --- | --- | --- |
| s1 | 请求参数校验 | 已完成 | 释放并发槽 |
| s2 | 库存扣减 | 运行中 | 占一个槽 |
| s3 | 订单落库 | 失败 | 幂等键冲突, 待重试 |
| s4 | 订单创建事件 | 待处理 | deps s3 |

> claim 调度: s1+s2 并发 → s1 完成 → s3 补位失败 → 下一步重试 s3 → s4 就绪

## 文件导览

| 路径 | 内容 | 维护者 | AI 读写? |
| --- | --- | --- | --- |
| `config.yaml` | 插件配置 | 用户 | 可读 |
| `task.json` | 顶层状态汇总 `{tasks:[{id,status,deps}]}` | 脚本 | **禁** |
| `task.md` | 文本看板 (从 task.json 渲染) | 脚本 | **禁** |
| `task.html` | 可视化看板 (4 主题 6 配色) | 脚本 | **禁** |
| `board/` | 主题 CSS (从 assets/board/ 拷贝) | 脚本 | git 忽略 |
| `task/<id>/task.json` | 单 task + subtask DAG + contracts | 脚本 | **禁** |
| `task/<id>/task.md` | 子任务看板 | 脚本 | **禁** |
| `task/<id>/prd.md` | planning 主入口 | AI | 可读写 |
| `task/<id>/design.md` | 详细设计 | AI | 可读写 |
| `task/<id>/findings.md` | 调研结论 | AI | 可读写 |
| `task/<id>/research/` | 调研笔记 | AI | 可读写 |
| `task/archive/<年>/<月-日>/<id>/` | 归档 task | 脚本 | 只读 |
| `spec/core/<cat>/*.md` | 常驻规则 | skein-spec | 经命令 |
| `spec/recall/<cat>/*.md` | 按需规则 | skein-spec | 经命令 |

## 规则演示

| 规则 | 层 | 类目 | 内容 |
| --- | --- | --- | --- |
| `order-query-00.md` | core | git | finish 前全量测试绿 |
| `order-create-api-01.md` | core | domain | 金额整数分, 禁 float |
| `order-create-api-00.md` | recall | arch | 幂等键 + Redis 扣减 |
| `order-pay-01.md` | recall | test | 状态机测试覆盖 |

## 试用

```bash
cp -r <plugin>/docs/examples/sample-skein /path/to/repo/.skein
cd /path/to/repo
skein current
skein subtask list order-create-api
skein-spec recall 幂等
```
