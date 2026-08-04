"""shim — 实际实现已搬入 skeinlib/web/serve.py。"""
from skeinlib.web.serve import *  # noqa: F401,F403
# import * 不带下划线开头的名字, 显式补 re-export (boardsource.py + uvicorn factory 字符串依赖)
from skeinlib.web.serve import _serve_app_factory  # noqa: F401
