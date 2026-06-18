#!/usr/bin/env python3
"""AI 味客观评分 — novelist-humanize 专用。

只算「机器才好数」的 AI 味客观分: tells 正则计数 + 句长方差(burstiness)。
其余审查评分(一致性/文字密度/定稿加权)是纯算术, 由对应 skill 直接心算, 不需脚本。

分数语义: 人味分越高越像人写(满分 100)。

用法:
  python3 score_aitaste.py <章节文件> [--json]
"""
import argparse
import re
import sys

# AI 味 tells 正则(机器可数的风格指纹)
TELLS = {
    "机械过渡词": r"(然而|此外|值得注意的是|总而言之|不难发现|综上所述|总的来说|换句话说|首先|其次|再次|最后)",
    "否定式平行": r"(不是.{1,20}而是|不仅.{1,20}(更是|而且|还))",
    "拔高空词": r"(标志着|彰显|毋庸置疑|不可磨灭|重要的一步|深刻的|淋漓尽致|百感交集)",
}
SENT_END = r"[。！？!?…]"


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"错误: 无法读取 {path}: {e}", file=sys.stderr)
        sys.exit(2)


def stdev(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def main():
    ap = argparse.ArgumentParser(description="AI 味人味分")
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = read_text(args.file)
    chars = len(re.sub(r"\s", "", text))
    kilo = max(chars / 1000.0, 0.001)

    tell_hits = {name: len(re.findall(pat, text)) for name, pat in TELLS.items()}
    total_tells = sum(tell_hits.values())
    tell_density = total_tells / kilo

    lens = [len(re.sub(r"\s", "", p)) for p in re.split(SENT_END, text) if re.sub(r"\s", "", p)]
    sd = stdev(lens)

    tell_penalty = min(tell_density * 8, 50)              # 每千字 1 tell 扣 8, 上限 50
    burst_penalty = min(max(0, (8 - sd)) * 4, 40) if lens else 0  # 句长标准差 < 8 → 扣分
    score = max(0, round(100 - tell_penalty - burst_penalty, 1))

    if args.json:
        import json
        print(json.dumps({
            "humanness_score": score, "chars": chars, "tells": tell_hits,
            "tell_density_per_kilo": round(tell_density, 2),
            "sentence_count": len(lens), "sentence_len_stdev": round(sd, 2),
        }, ensure_ascii=False))
    else:
        print(f"人味分: {score}/100  (越高越像人写)")
        print(f"  有效字数 {chars}, tells {total_tells} 个 ({tell_hits}), 每千字 {tell_density:.2f}")
        print(f"  句数 {len(lens)}, 句长标准差 {sd:.2f} (越高节奏越有起伏)")
        if score < 70:
            print("  ⚠️ AI 味偏重, 需继续去味")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
