"""
字符→token 换算系数

基于本库真实 spec 文件标定的字符→token 换算系数。
标定过程见 tests/test_token_conversion_calibration.py
"""

# 推荐换算系数（保守估算，倾向高估 token 数）
# 基于 5 个真实 spec 文件标定：1.7 字符 ≈ 1 token
CHAR_TO_TOKEN_RATIO = 0.58  # 1 字符 ≈ 0.58 tokens
CHARS_PER_TOKEN = 1.7      # 1.7 字符 ≈ 1 token

# 误差范围：0.480 ~ 0.709（基于单个文件的差异）
MIN_RATIO = 0.480
MAX_RATIO = 0.709


def estimate_tokens_from_chars(char_count: int) -> int:
    """
    从字符数估算 token 数（保守估算）

    Args:
        char_count: 字符数

    Returns:
        估算的 token 数（向上取整，倾向高估）
    """
    import math
    # 使用保守系数，向上取整确保不低估
    return math.ceil(char_count * CHAR_TO_TOKEN_RATIO)


def get_conversion_info() -> str:
    """
    获取换算系数说明

    Returns:
        换算系数的详细说明
    """
    return (
        f"字符→token 换算系数: {CHAR_TO_TOKEN_RATIO} ({CHARS_PER_TOKEN} 字符 ≈ 1 token)\n"
        f"误差范围: {MIN_RATIO} ~ {MAX_RATIO}\n"
        f"标定依据: 基于 5 个真实 spec 文件标定，采用保守估算（倾向高估）\n"
        f"标定测试: tests/test_token_conversion_calibration.py"
    )