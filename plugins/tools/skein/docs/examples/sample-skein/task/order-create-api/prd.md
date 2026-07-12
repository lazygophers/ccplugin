# PRD (主入口) — order-create-api 订单创建 API

> planning 主入口 (skein-plan 写)。**AI 可读写**, 不受 guard 拦截。需求在此, 详设/调研/调度经索引区跳转。

## 背景 / 目标

下单链路缺一个统一的订单创建入口。新增 `POST /orders`: 校验请求 → 扣库存 → 落订单 → 发创建事件, 一次事务闭环。

## 范围

- ✅ 请求参数校验 (商品 / 数量 / 收货地址)
- ✅ 库存扣减 (原子, 不足即拒)
- ✅ 订单落库 (幂等)
- ✅ 落单成功发 MQ 创建事件 (下游发货/通知消费)
- ❌ 不含: 支付 (归 order-pay) / 优惠券 / 拆单

## 契约 (不可回退不变量, check 逐条验)

1. 同一幂等键重复提交只落一单 (唯一约束)。
2. 库存不足直接 409, 不落订单。

> 契约同时锁进 `task.json` 的 `contracts[]` (`skein.py contract order-create-api --add`), check 阶段 `skein-checker` 逐条验证。

## 验收标准

- 合法请求 + 库存充足 → 201 + 订单号。
- 库存不足 → 409, 订单表无新增。
- 同幂等键并发重复提交 → 只 1 单, 第二次返回同一订单号。

## 索引

- 详细设计: [design.md](design.md) (架构/数据流/取舍/选型)
- 调研收敛: [findings.md](findings.md) (幂等/库存/MQ 选型依据)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list order-create-api`)
