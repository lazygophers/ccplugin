"""shim — 实际实现已搬入 skeinlib/web/views.py。"""
from skeinlib.web.views import *  # noqa: F401,F403
# import * 不带下划线开头的名字, 显式补 re-export (serve.py/boardsource.py 依赖它们)
from skeinlib.web.views import (_cards_signature, _prd_data, _prd_parse, _spec_frontmatter,  # noqa: F401
                                _view_archive, _view_archive_list, _view_board_data,
                                _view_dashboard, _view_queue, _view_search, _view_task_detail)
