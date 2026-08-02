# 状态先行铁律

状态硬门、禁止绕过、违反后回到哪里继续，统一见 [flow-loop.md §2](flow-loop.md#2-状态先行硬门)。本文件只保留一句原则，供其他 references 短引。

## 原则

操作 task / subtask / check / finish 前，必须先让对应 `skein` 状态命令成功落盘。理由、效率、简单程度都不是豁免；能过脚本状态门才算合法。

## 索引

- task 状态落盘值与展示名：[flow-loop.md §1.1](flow-loop.md#11-task-状态)
- subtask 状态落盘值与展示名：[flow-loop.md §1.2](flow-loop.md#12-subtask-状态)
- 状态硬门：[flow-loop.md §2](flow-loop.md#2-状态先行硬门)
- 失败扭转：[flow-loop.md §9](flow-loop.md#9-失败扭转)
