"""子进程覆盖率接线 —— 只在设了 COVERAGE_PROCESS_START 时生效, 平时零开销。

本套件大半的用例是 `subprocess.run([sys.executable, skein.py, ...])` 跑真 CLI, 这些代码在
子进程里执行, 父进程的 coverage 一行都记不到 (实测总覆盖率被低估到 36%)。Python 启动时 site
模块会自动 import 同名 `sitecustomize`, 而子进程的 sys.path[0] 正是本目录 (脚本所在目录),
所以放这里就能在任何 skein/spec/hooks CLI 子进程里挂上 coverage。
"""
import os

if os.environ.get("COVERAGE_PROCESS_START"):
    try:
        import coverage

        coverage.process_startup()
    except ImportError:  # 没装 coverage 时照常跑测试, 不该因为统计工具缺席就崩
        pass
