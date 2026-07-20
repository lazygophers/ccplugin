# cli-alias-merge — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [x] del/delete/rm/remove 4 别名 help 不再各显一行, 合并为 argparse aliases 单行展示

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [x] 范围内: skein.py:2869-2872 del 别名循环改 add_parser(aliases=)
- [x] 范围外: 其他命令无别名不动; subtask 子命令不碰
- [x] 约束: argparse 原生 aliases 已验证 help 显 `del (delete, rm, remove)` 单行

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] skein --help 只显一行 del (delete, rm, remove)
- [x] skein del/delete/rm/remove 任一可调用 (handler 不变)
- [x] pytest 全绿

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list cli-alias-merge`)
