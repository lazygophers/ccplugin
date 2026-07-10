# skein-clean 反例目录

清扫时的禁止操作与正确改法:

| 禁 | 改为 |
|---|---|
| 删未合并分支 / 未 finish 的 worktree | 保留 + 报用户 (可能有未落地改动) |
| 无对应 task 的孤儿 worktree 直接删 | 报用户裁定 |
| 手动 rm .skein/task/<id> 当归档 | 走 `skein.py archive <id>` (进 archive 目录) |
| 清完不刷看板 | 收尾必跑 `skein.py board` |
