# check — 质量验证 (委托 skein-check)

执行完成后委托 `skein-check`, 派 `skein-checker` 做质量验证: lint、type-check、tests、契约合规。

未过 → 派合适 agent (无则 `skein-executor`) 按 checker 报告定点修复, 修复后重检, 不跳 finish。check 反复不过 (≥2 轮) 时按 checker 报告聚焦根因; 第 3 轮仍不过 → 停, 跳出调试循环转人工。
