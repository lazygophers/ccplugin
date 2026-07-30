"""Claude Code harness hook 层 —— **每个 prompt 都跑, 是全仓最热的路径**。

## 三个模块
- `runner`  钩子执行器 (`_run_hooks`) + 叙事器 `DBG` + token 预算守卫。skein/spec 两侧共用,
            放共享模块免二者相互反向 import。
- `judge`   任务复杂度判定的纯函数 (启发式正则打分)。
- 各 `cmd_*` 仍在入口 `scripts/hooks.py` 里 —— 它们是 harness 的 stdin/stdout 契约层。

## 热路径纪律 (改这层前先读)
1. **重 import 一律局部**: `subprocess` / `time` / `sqlite3` 只在真用到的子命令里 import,
   禁提到模块顶部 —— 每个 prompt 都要付那个钱。
2. **正则模块级预编译**: 禁在函数体里 `re.compile`。
3. **失败静默**: 配置笔误 / 文件缺失 / json 损坏三类一律不得让 hook 退非零 —— 打断的是用户
   每一次对话。硬报错交 `skein doctor`。
4. 拆包/搬家后跑一次 `python3 -X importtime -c "import hooks"`, 不得高于搬家前 (~6.5ms)。
"""
