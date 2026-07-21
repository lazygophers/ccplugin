# scripts 极致低内存/io/cpu 优化 — PRD (主入口)

## 目标
skein scripts (skein.py/spec.py/hooklib.py/hooks.py) 降启动开销 — 内存/io/cpu。hook 每 prompt 跑 (热路径), skein.py CLI 每命令跑一次。python 解释器基线 ~20MB 不可避, 优化目标砍 import 冗余 + hook 路径零冗余 IO。

基线 (darwin, python3.13):
- [ ] hooks.py user-prompt: 20MB / 40ms
- [ ] skein.py list: 33MB / 160ms
- [ ] skein import 总 77ms (argparse 9 / subprocess 8 / shutil 4 / typing 3 / pathlib 5)

## 边界
- [ ] 范围内: 4 文件 import 瘦身 (lazy 按命令载) + hook 路径 IO 审计 + 启动开销
- [ ] 范围外: python 解释器固有开销 / 算法复杂度 (业务逻辑不动) / tests 文件
- [ ] 约束: 行为零行为变更 (self-check + 现有 test 全绿)

## 验收标准
- [ ] skein.py 重 import (subprocess/shutil/fcntl/datetime/time) 改 lazy (仅用到的命令载)
- [ ] spec.py sqlite3/subprocess lazy
- [ ] hooks.py 热路径 (user-prompt/guard) IO 审计: cmd_guard `_has_active_task` 扫多 task.json — 评估短路/缓存
- [ ] hooklib.py 审计 (110 行轻量, 预期无需大改)
- [ ] 优化后 profile 对比: skein import < 50ms, hook 路径内存不增
- [ ] self-check + test_skein.py/test_board.py 全绿
- [ ] 零行为变更

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-scripts-perf`)
