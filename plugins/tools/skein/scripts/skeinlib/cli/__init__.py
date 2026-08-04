"""cli — 三个 CLI 入口的统一包。

main.py (skein CLI) / spec.py (spec CLI) / hooks.py (hooks CLI)。
入口薄壳 skein.py/spec.py/hooks.py 从此包 import main()。
"""
from skeinlib.cli.main import (  # noqa: F401
    app,
    config_app,
    main as skein_main,
    prd_app,
    task_app,
)
from skeinlib.cli.main import main  # noqa: F401
