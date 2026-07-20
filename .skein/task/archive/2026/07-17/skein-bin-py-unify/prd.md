# bin 去 shell 统一 py — PRD

## 目标
plugins/tools/skein/bin/ 下三个 bash thin wrapper (skein, skein-hooks, skein-memory) 改为 py wrapper, 直接复用 scripts/*.py 入口 (已有 shebang + __main__ + main())。去 shell 依赖, 统一 py 载体。成功: hooks 调用 (skein / skein-hooks / skein-memory) 经 py wrapper 正确转发到 scripts/, 行为与 bash 版完全等价。

## 背景
- 三个 bash wrapper 结构同构: `CLAUDE_PLUGIN_ROOT` (或相对 $0 推) → 找 scripts/ 绝对路径 → `exec python3 scripts/X.py "$@"`
- scripts/skein.py (L2527 __main__), scripts/hooks.py (L178), scripts/memory.py (L345) 都已有 shebang `#!/usr/bin/env python3` + `if __name__=="__main__": main()`
- hooks (plugin.json) 调用形式: `skein session-context` / `skein-hooks guard` / `skein-memory session-start` — 靠 PATH 解析到 bin/

## 方案
bin/X 改 py wrapper (runpy.run_path 复用, 非 symlink):
```python
#!/usr/bin/env python3
"""X — py wrapper, 复用 scripts/X.py 入口 (去 shell 依赖)。"""
import os, sys, runpy
_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv[0] = os.path.join(_root, "scripts", "X.py")
runpy.run_path(sys.argv[0], run_name="__main__")
```
- runpy.run_path 以 `__main__` 跑目标 .py, 触发其 `if __name__=="__main__": main()`, 零重复入口
- CLAUDE_PLUGIN_ROOT 优先 (hook 环境注入), 回退相对 __file__ 推 (bin/ 的父 = 插件根)
- sys.argv[0] 设为目标 .py 路径, 使目标脚本内 `__file__`/`sys.argv[0]` 语义正确 (skein.py L37 sys.path 用 __file__, hooks/memory 若引用 sys.argv[0] 也对)

## 边界
- 范围内: bin/skein, bin/skein-hooks, bin/skein-memory (三文件全文替换 bash → py); 各自指向 scripts/skein.py / hooks.py / memory.py
- 范围外: scripts/*.py 本身 (入口已就绪不改); plugin.json hooks 声明 (调用名 bin/skein 等不变); 其他 bin (无); skein.py 的 CLAUDE_PLUGIN_ROOT 使用 (它不引用, wrapper 注入仅自身定位用)
- 约束: 保留可执行位 (chmod +x); shebang `#!/usr/bin/env python3`; py wrapper 无外部依赖 (仅 stdlib: os/sys/runpy)

## 验收标准
- [ ] bin/skein, bin/skein-hooks, bin/skein-memory 均为 py (shebang #!/usr/bin/env python3, 无 bash)
- [ ] 各 py wrapper runpy.run_path 指向对应 scripts/X.py
- [ ] 三个 bin 保留可执行位 (ls -l 显示 x)
- [ ] `bin/skein list` (或 --help) 正常执行, 行为同 bash 版
- [ ] `bin/skein-hooks guard` / `bin/skein-memory session-start` 不报 ImportError / 路径错 (能转发, hook 子命令本身逻辑可不跑全)
- [ ] 无 CLAUDE_PLUGIN_ROOT 时 (回退 __file__ 推路径) 仍能定位 scripts/
- [ ] node/py 语法合法 (python3 -c "compile(open('bin/skein').read(),'f','exec')" 三文件过)

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json
