"""
HTML 模板模块

提供 Web 界面的 HTML 模板加载功能。
"""

import os


def get_template_path() -> str:
    """
    获取模板目录路径
    
    Returns:
        str: 模板目录的绝对路径
    """
    return os.path.join(os.path.dirname(__file__), "templates")


def load_index_template() -> str:
    """
    加载首页 HTML 模板
    
    Returns:
        str: HTML 模板内容
    """
    template_path = os.path.join(get_template_path(), "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


HTML_TEMPLATE = load_index_template()
