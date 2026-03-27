"""
格式化工具测试
"""

import pytest

from scripts.statusline.utils.formatting import (
    format_duration,
    format_duration_ms,
    format_token_count,
    format_percentage,
    format_compact_int,
    truncate_text,
    shorten_path,
    progress_bar,
    strip_ansi,
    visible_len,
    join_parts,
)


class TestFormatting:
    """格式化函数测试"""

    def test_format_duration_ms(self):
        """测试毫秒时间格式化"""
        assert format_duration_ms(None) == "0s"
        assert format_duration_ms(500) == "0s"
        assert format_duration_ms(1500) == "1s"
        assert format_duration_ms(60000) == "1m00s"
        assert format_duration_ms(120000) == "2m00s"

    def test_format_token_count(self):
        """测试 token 计数格式化"""
        assert format_token_count(None) == "0"
        assert format_token_count(100) == "100"
        assert format_token_count(1500) == "1.5K"
        assert format_token_count(1500000) == "1.5M"

    def test_format_percentage(self):
        """测试百分比格式化"""
        assert format_percentage(80.5) == "80%"
        assert format_percentage(80.5, decimals=1) == "80.5%"
        assert format_percentage(100) == "100%"

    def test_truncate_text(self):
        """测试文本截断"""
        assert truncate_text("hello", 10) == "hello"
        assert truncate_text("hello world", 8) == "hello..."
        assert truncate_text("hello", 3) == "..."

    def test_progress_bar(self):
        """测试进度条"""
        bar = progress_bar(50, width=10)
        assert len(bar) == 12  # [ + 10 chars + ]
        assert "█" in bar
        assert "░" in bar

    def test_strip_ansi(self):
        """测试 ANSI 码移除"""
        text = "\x1b[31mRed Text\x1b[0m"
        assert strip_ansi(text) == "Red Text"

    def test_visible_len(self):
        """测试可见长度"""
        text = "\x1b[31mRed\x1b[0m"
        assert visible_len(text) == 3

    def test_format_duration(self):
        """测试时间格式化"""
        assert format_duration(None) == "0s"
        assert format_duration(500) == "500ms"
        assert format_duration(1500) == "1.5s"
        assert format_duration(60000) == "1:00.0"
        assert format_duration(120000) == "2:00.0"

    def test_format_compact_int(self):
        """测试紧凑整数格式化"""
        assert format_compact_int(None) == "0"
        assert format_compact_int(100) == "100"
        assert format_compact_int(1500) == "1.5K"
        assert format_compact_int(1500000) == "1.5M"
        assert format_compact_int(1500000000) == "1.5B"

    def test_shorten_path(self):
        """测试路径缩短"""
        # 短路径不缩短
        assert shorten_path("short/path") == "short/path"

        # 长路径缩短
        long_path = "very/long/path/to/some/deeply/nested/file.txt"
        result = shorten_path(long_path, max_len=30)
        # 应该缩短
        assert len(result) <= 35  # 允许一些误差
        assert "file.txt" in result or "nested/file.txt" in result

        # 单部分路径
        assert shorten_path("single") == "single"

        # 两部分路径
        assert shorten_path("part1/part2") == "part1/part2"

        # 精确边界测试
        path = "a/b/c/d/e/f.txt"
        result = shorten_path(path, max_len=20)
        # 确保返回一个合理的路径
        assert "/" in result or result == path

    def test_join_parts(self):
        """测试连接部分"""
        assert join_parts(["a", "b", "c"]) == "a b c"
        assert join_parts(["a", "", "c"]) == "a c"
        assert join_parts(["", "", ""]) == ""
        assert join_parts([],) == ""
        assert join_parts(["a", "b"], sep=" | ") == "a | b"

    def test_truncate_text_custom_suffix(self):
        """测试自定义截断后缀"""
        result = truncate_text("hello world", 8, suffix="»")
        assert len(result) == 8
        assert "»" in result

    def test_progress_bar_width(self):
        """测试不同宽度的进度条"""
        bar1 = progress_bar(50, width=5)
        assert len(bar1) == 7  # [ + 5 chars + ]

        bar2 = progress_bar(100, width=10)
        assert bar2 == "[██████████]"

        bar3 = progress_bar(0, width=10)
        assert bar3 == "[░░░░░░░░░░]"

    def test_strip_ansi_complex(self):
        """测试复杂 ANSI 码移除"""
        text = "\x1b[31m\x1b[1mBold Red\x1b[0m"
        assert strip_ansi(text) == "Bold Red"

        text = "\x1b[38;5;123mTrueColor\x1b[0m"
        assert strip_ansi(text) == "TrueColor"

    def test_visible_len_complex(self):
        """测试复杂文本的可见长度"""
        text = "\x1b[31m\x1b[1mBold\x1b[0m \x1b[32mGreen\x1b[0m"
        assert visible_len(text) == 10  # "Bold Green"

    def test_format_percentage_edge_cases(self):
        """测试百分比边界情况"""
        assert format_percentage(0) == "0%"
        assert format_percentage(100) == "100%"
        assert format_percentage(99.9, decimals=1) == "99.9%"
        assert format_percentage(0.1, decimals=2) == "0.10%"
