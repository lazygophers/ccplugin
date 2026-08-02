# 回退协议

SKEIN 的「回退」是流程扭转，不是状态倒退。执行过程、分流、用户裁定点、回 exec 方式统一见 [flow-loop.md §9](flow-loop.md#9-失败扭转)。本文件只保留术语边界。

## 原则

- task 状态不回滚；`active` 后不退回 `pending`。
- check 失败通过追加修复 subtask 前进式修补。
- 原失败 subtask 历史保留，不删除毁迹。
- 契约只在 planning 阶段可改；exec/check 发现契约错误，必须经用户裁定后重回 planning 或新建 task。
- 能小修不大修；能定点修不重拆 task。

## 触发类别

| 类别 | 说明 | 执行位置 |
|---|---|---|
| 孤立失败 | 实现 bug、环境问题、测试错误，影响面小 | flow-loop 失败扭转 |
| 一致性冲突 | subtask 间实现冲突或契约理解不一致 | flow-loop 失败扭转 + root-cause |
| 方案性缺陷 | design 路线走不通或结构漏洞 | 用户裁定后回 planning / 新建 task |
| 需求理解偏差 | PRD/验收/契约本身错 | 用户裁定后回 planning / 新建 task |

## 根因方法

5 维定位和报告格式见 [root-cause-protocol.md](root-cause-protocol.md)。是否停顿、补什么修复 subtask、何时回 exec，以 [flow-loop.md §9](flow-loop.md#9-失败扭转) 为准。
