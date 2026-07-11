#!/usr/bin/env python3
"""SKEIN hook 公共工具 — 注入内容的 token 预算守卫 (纯 stdlib)。

所有 SessionStart / PostTool* hook 注入上下文前, 过 budget_guard():
内容超预算 → stderr 警告 "简化内容", 且截断到硬上限, 免不可控 token 膨胀。
token 估算 = 字符数 // 4 (英混中的粗略常数, 宁可高估)。
"""
import sys

CHARS_PER_TOKEN = 4  # 粗略: 1 token ≈ 4 字符 (中英混排偏保守)


def est_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    """内容超 token 预算则 stderr 警告 + 硬截断到预算。返回可注入文本。

    label 用于警告定位 (哪个 hook)。硬截断防 model 忽视软警告后仍膨胀上下文。
    """
    tok = est_tokens(text)
    if tok <= budget_tokens:
        return text
    limit = budget_tokens * CHARS_PER_TOKEN
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tok} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:limit] + "\n\n… (超预算已截断, 见 stderr)"


if __name__ == "__main__":
    # 自检
    assert est_tokens("a" * 40) == 10
    assert budget_guard("short", 100, "t") == "short"
    long = "x" * 1000
    out = budget_guard(long, 10, "t")  # 预算 10 token = 40 字符
    assert len(out) < len(long) and "截断" in out
    print("hooklib 自检过")
