#!/usr/bin/env python3
"""novelist 脚手架 — 初始化一部小说的目录环境。

用法:
    python3 init_novel.py "<小说名>" [--path <父目录>] [--genre <类型>] [--force]

在 <父目录>/<小说名>/ 下创建中文目录骨架 + 模板文件 + 元数据。
父目录默认当前工作目录。已存在且非空时拒绝, 除非 --force。

退出码: 0 成功 / 2 目标已存在(未加 --force) / 3 参数错误。
"""
import argparse
import datetime
import sys
from pathlib import Path

# 目录骨架: 相对路径 -> 该目录下要写的模板文件 {文件名: 内容}
def scaffold(title: str, genre: str) -> dict:
    today = datetime.date.today().isoformat()
    return {
        "总览.md": (
            f"# {title}\n\n"
            f"- 类型: {genre or '未定'}\n"
            f"- 创建: {today}\n"
            f"- 状态: 设定中\n\n"
            "## 一句话简介\n\n（待填：一句话讲清这本书的核心钩子）\n\n"
            "## 题材与基调\n\n（待填）\n\n"
            "## 目录约定\n\n"
            "| 目录 | 归属 skill | 内容 |\n"
            "|---|---|---|\n"
            "| 人物/ | novelist-character | 每人物独立文件夹: 简介/经历/关系 |\n"
            "| 世界观/ | novelist-worldview | 地理/势力/规则/历史 |\n"
            "| 设定/ | novelist-worldview | 物品/组织/术语等其他设定 |\n"
            "| 大纲/ | novelist-outline | 总纲/分卷 |\n"
            "| 情节/ | novelist-outline | 主线/支线/伏笔 |\n"
            "| 章节/ | novelist-write/rewrite | 正文章节 + 索引 |\n"
            "| 元数据/ | novelist-check/proofread | 进度 + 检查/校对报告 |\n"
        ),
        "人物/_索引.md": (
            "# 人物花名册\n\n"
            "| 人物 | 定位 | 首次出场章 | 状态 |\n"
            "|---|---|---|---|\n"
            "| （示例）主角 | 主角 | 第001章 | 设定中 |\n\n"
            "> 每个人物在本目录下有独立文件夹, 含 简介.md / 经历.md / 关系.md 三文件。\n"
        ),
        "世界观/_索引.md": (
            "# 世界观索引\n\n"
            "- [地理](地理.md)\n- [势力](势力.md)\n- [规则](规则.md) — 力量/科技/魔法体系\n- [历史](历史.md)\n"
        ),
        "世界观/地理.md": "# 地理\n\n（待填：区域、地标、气候、地图说明）\n",
        "世界观/势力.md": "# 势力\n\n（待填：国家/组织/派系、关系、势力范围）\n",
        "世界观/规则.md": "# 规则体系\n\n（待填：力量/科技/魔法体系的能力边界与代价——这是一致性检查的核心硬约束）\n",
        "世界观/历史.md": "# 历史\n\n（待填：关键历史事件时间线，影响当下格局的前史）\n",
        "设定/_索引.md": (
            "# 其他设定索引\n\n"
            "（物品 / 组织 / 术语 / 专有名词等。新增一个设定 = 新增一个文件并在此登记。）\n\n"
            "| 设定 | 类型 | 首次出现章 |\n|---|---|---|\n"
        ),
        "大纲/总纲.md": (
            "# 总纲（主线）\n\n"
            "## 核心冲突\n\n（待填：贯穿全书的主要矛盾）\n\n"
            "## 三幕/分卷结构\n\n（待填）\n\n"
            "## 结局走向\n\n（待填）\n"
        ),
        "大纲/分卷.md": "# 分卷大纲\n\n| 卷 | 主题 | 起止章 | 卷末钩子 |\n|---|---|---|---|\n",
        "情节/主线.md": "# 主线情节\n\n| 节点 | 涉及章节 | 推进的核心冲突 |\n|---|---|---|\n",
        "情节/支线.md": "# 支线情节\n\n| 支线 | 涉及人物 | 涉及章节 | 与主线的交汇点 |\n|---|---|---|\n",
        "情节/伏笔.md": (
            "# 伏笔与回收追踪\n\n"
            "| 伏笔 | 埋设章 | 计划回收章 | 状态(未回收/已回收) |\n|---|---|---|---|\n\n"
            "> novelist-check 会核对此表: 已结尾但仍有'未回收'= 一致性缺陷。\n"
        ),
        "章节/_索引.md": (
            "# 章节目录\n\n"
            "| 章 | 标题 | 字数 | 状态(草稿/已检查/已校对/定稿) | 备注 |\n"
            "|---|---|---|---|---|\n"
        ),
        "元数据/进度.md": (
            f"# 进度\n\n- 最后更新: {today}\n- 已写章节: 0\n- 当前阶段: 设定\n\n"
            "## 下一步\n\n（待填）\n"
        ),
        "元数据/检查报告/.gitkeep": "",
        "元数据/校对报告/.gitkeep": "",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="初始化一部小说的目录环境")
    ap.add_argument("title", help="小说名")
    ap.add_argument("--path", default=".", help="父目录(默认当前目录)")
    ap.add_argument("--genre", default="", help="类型, 如 玄幻/科幻/悬疑")
    ap.add_argument("--force", action="store_true", help="目标已存在时仍写入(不覆盖已有文件)")
    args = ap.parse_args()

    if not args.title.strip():
        print("错误: 小说名不能为空", file=sys.stderr)
        return 3

    root = Path(args.path).expanduser().resolve() / args.title.strip()
    if root.exists() and any(root.iterdir()) and not args.force:
        print(f"错误: 目标已存在且非空: {root}\n  如确认追加, 加 --force", file=sys.stderr)
        return 2

    files = scaffold(args.title.strip(), args.genre.strip())
    created, skipped = 0, 0
    for rel, content in files.items():
        fp = root / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        if fp.exists() and args.force:
            skipped += 1
            continue
        fp.write_text(content, encoding="utf-8")
        created += 1

    print(f"✓ 初始化完成: {root}")
    print(f"  新建文件 {created} 个" + (f", 跳过已存在 {skipped} 个" if skipped else ""))
    print("  目录: 人物/ 世界观/ 设定/ 大纲/ 情节/ 章节/ 元数据/")
    print("  下一步: 用 novelist-design 做核心设计(主要剧情+主要人物)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
