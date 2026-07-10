# skein-check 反例目录

check 阶段禁止行为与纠正动作。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| main 亲跑 lint/test | 派 `skein-checker` |
| checker 自己改代码 | checker 只读, 修复派 `skein-implementer` |
| check 未过就 finish | 未全绿禁 finish |
| 无限重检不设上限 | 第 3 轮仍 FAIL → STOP 报用户 |
| 凭空断言"应该能过"跳过实跑 | checker 必跑真命令验 |
