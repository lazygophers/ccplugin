# hooks.py 多行文案 str 改 triple-quoted — PRD (主入口)

## 目标
- [x] hooks.py 4 处多行文案 str (_UNINIT_TRELLIS/_UNINIT_PLAIN/_INIT_CTX/cmd_report ctx) 从隐式单行拼接改为 triple-quoted 多行 str, 文本语义不变
## 边界
- 范围: hooks.py 4 处文本型 str (284/292/297/138)
- 范围外: tuple 常量 (ENGINE/WRITE_CMDS/OURS/SPEC_*) 非文本拼接不改
- 范围外: skein.py 不动
- 已知约束: triple-quoted 内用真实换行替代
- ; 同行续接 (无
- 的拼接) 保持同行; f-string (cmd_report) 兼容 triple-quoted
## 验收标准
- [ ] 4 处 str 改为 triple-quoted (单引号或双引号均可)
- [x] 注入文案与改前逐字一致 (hook echo 实测比对)
- [ ] ast.parse hooks.py 通过
- [ ] python3 -c 导出 4 常量值与改前一致
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list hooks-str-multiline`)
