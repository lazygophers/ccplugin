"""web — HTTP/API 层 (路由 + 数据源 + 视图)。

serve.py: build_app 路由 + server 生命周期
boardsource.py: BoardSourceMixin 生产 adapter
views.py: Snapshot + DataSource Protocol + 各视图纯函数

子模块按需 import (不在 __init__ 里预加载, 避免 web.views 首先被 import 时的循环引用):
  web.views → from skeinlib.web.views import * → 触发本 __init__
  → 若此处预 import serve → serve 再 from skeinlib.web.views import → 半初始化 → ImportError。
"""
