# skein-check 反例目录

check 阶段禁止行为与纠正动作。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| main 亲跑 lint/test | 派 `skein-checker` |
| checker 自己改代码 | checker 只读, 修复派 `skein-implementer` |
| check 未过就 finish | 未全绿禁 finish |
| 无限重检不设上限 | 第 3 轮仍 FAIL → 加载 `skein-break-loop` 做结构化根因复盘 (跨维度定位), 禁盲改 |
| 凭空断言"应该能过"跳过实跑 | checker 必跑真命令验 |
| 只跑 lint/test 不验契约 | 先 `skein.py contract <focus>` 读出契约, 逐条报 pass/fail |
