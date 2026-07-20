# 设计 — bin 去 shell 统一 py

## 统一 py wrapper 模板 (三 bin 同构, 只换 X 和注释里的子命令说明)
```python
#!/usr/bin/env python3
"""skein — py wrapper, 复用 scripts/skein.py 入口 (去 shell 依赖)。
原 bash thin wrapper 的 py 等价: CLAUDE_PLUGIN_ROOT 优先, 回退相对 __file__ 推插件根, runpy 复用 scripts/ 入口。"""
import os, sys, runpy
_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_target = os.path.join(_root, "scripts", "skein.py")
sys.argv[0] = _target
runpy.run_path(_target, run_name="__main__")
```
- bin/skein → scripts/skein.py
- bin/skein-hooks → scripts/hooks.py (docstring 注 "子命令: permission/guard/batch/report")
- bin/skein-memory → scripts/memory.py

## 为何 runpy 非 symlink 非 import
- **symlink**: Windows 弱; skein.py L37 `Path(__file__).parent` 在 symlink 下不 resolve 会指 bin/ 而非 scripts/ → sys.path.insert 错位 → hooklib 导入失败。reject。
- **import scripts.skein**: scripts/ 不是 package (无 __init__.py), 且 skein.py `if __name__=="__main__"` guard 下 import 不触发 main()。需额外调 main(), 重复入口逻辑。reject。
- **runpy.run_path(run_name="__main__")**: 以 __main__ 跑目标文件, 触发其 guard, 零重复, 目标脚本 __file__=__main__ 语义正确, sys.argv[0] 显式设为目标路径补全。accept。

## 路径回退正确性
- hook 环境: CLAUDE_PLUGIN_ROOT 由 Claude Code 注入 = 插件根 → _root 正确
- 非 hook (直接 ./bin/skein): __file__ = bin/skein 绝对路径, dirname twice = 插件根 → _root 正确
- worktree / 异常 cwd: 不依赖 cwd, 靠 __file__/env → 稳定

## 验证命令
```bash
# 三文件 py 语法
for f in bin/skein bin/skein-hooks bin/skein-memory; do
  python3 -c "compile(open('plugins/tools/skein/$f').read(),'f','exec')" && echo "$f OK"
done
# 可执行位
ls -l plugins/tools/skein/bin/
# 功能: list 应正常
plugins/tools/skein/bin/skein list --status open 2>&1 | head -3
# 无 CLAUDE_PLUGIN_ROOT 回退
env -u CLAUDE_PLUGIN_ROOT plugins/tools/skein/bin/skein current 2>&1 | head -3
```
