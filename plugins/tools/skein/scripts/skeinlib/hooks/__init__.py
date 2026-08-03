"""Claude Code harness hook 层 —— **每个 prompt 都跑, 是全仓最热的路径**。

## 模块划分 (一 hook 一文件, 不按协议位置合并)
- `cli`        子命令分发。DISPATCH 存 `"模块:函数"` 字符串做**懒加载** —— 见其 docstring,
               这是本层最重要的一条设计。一 hook 一文件不是推翻这个懒加载设计, 而是让它真正
               生效: 原先 4 个 hook 挤一个模块 (`gate.py` / `postwrite.py`) 时, 调其中一个仍要
               付另外 3 个的加载成本; 拆开后每个子命令只付自己那条链的账。
- `util`       `git_root` / `load_stdin` / `ENGINE` / `BLOCKED`, 多子命令共用的零件 (下沉自
               原 `gate.py`)。
- `permission` PreToolUse 权限门。
- `guard`      写前守卫。
- `batch`      批量操作门。
- `report`     结果上报。
- `fmt`        PostToolUse 格式化。
- `spec_meta`  PostToolUse spec 元数据写入。
- `flow_gate`  PostToolUse flow 门禁。
- `stopcheck`  Stop hook。单独一个模块因为它是唯一加载整个 `spec` 门面的子命令。
- `prompt`     UserPromptSubmit。全仓最热的一段。
- `agent`      agent-start / agent-stop。协议不同 (argv 而非 stdin), 故分开放显眼。
- `runner`     钩子执行器 (`_run_hooks`) + 叙事器 `DBG` + token 预算守卫。skein/spec 两侧共用,
               放共享模块免二者相互反向 import。
- `judge`      任务复杂度判定的纯函数 (启发式正则打分)。

`scripts/hooks.py` 只剩 sys.path 接线 + 转发, 与 `skein.py` / `spec.py` 两个入口同形。

## 热路径纪律 (改这层前先读)
1. **重 import 一律局部**: `subprocess` / `time` / `sqlite3` 只在真用到的子命令里 import,
   禁提到模块顶部 —— 每个 prompt 都要付那个钱。
2. **正则模块级预编译**: 禁在函数体里 `re.compile`。
3. **失败静默**: 配置笔误 / 文件缺失 / json 损坏三类一律不得让 hook 退非零 —— 打断的是用户
   每一次对话。硬报错交 `skein doctor`。
4. 拆包/搬家后跑一次 `python3 -X importtime -c "import hooks"`, 不得高于搬家前 (~6.5ms)。
"""
