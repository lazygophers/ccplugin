---
name: novelist-init
description: 初始化一部新小说的目录环境(scale)。当用户说"新建小说/开一本书/初始化小说项目/搭小说目录"时调用, 创建中文目录骨架(人物/世界观/设定/大纲/情节/章节/元数据)+模板文件。这是 novelist 插件所有其他 skill 的前置——没有目录环境, design/write/check 无处落盘。
when_to_use: 用户要开一本新小说、搭建写作目录、初始化小说工程时。触发词: 新建小说, 开新书, 初始化小说, 搭小说目录, novel init, 建立小说项目。
user-invocable: true
argument-hint: [小说名] [类型]
arguments: [小说名, 可选类型]
---

# novelist-init — 初始化小说目录环境

为一部小说搭建细粒度的中文目录骨架, 让后续设定、编写、检查各有归属、互不冲突。

## 工作流(按序执行)

1. **取参数** — 从用户输入取「小说名」(必需) 与「类型」(可选, 如 玄幻/科幻/悬疑)。缺小说名 → 🔴 STOP, 用 `AskUserQuestion` 问, 禁自行编名。
2. **定父目录** — 默认当前工作目录。若用户指定路径则用之。
3. **🔴 CHECKPOINT — 确认创建参数** — 执行脚本前向用户汇报: 小说名 / 父目录绝对路径 / 类型(若有)。用 `AskUserQuestion` 确认「确认创建 / 取消」。用户取消 → 退出, 不建目录。
4. **跑脚手架** — 执行:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/novelist-init/scripts/init_novel.py "<小说名>" --path <父目录> --genre "<类型>"
   ```
   脚本创建: `人物/ 世界观/ 设定/ 大纲/ 情节/ 章节/ 元数据/` + 各层模板与索引文件。🔴 STOP: 脚本退出码 2(目标已存在且非空) → **禁直接加 `--force` 覆盖**, 先用 `AskUserQuestion` 问用户「换名 / 追加 / 取消」, 用户选追加才补 `--force`。
5. **回报结构** — 向用户列出生成的目录树, 说明每个目录归属哪个 skill(见 `总览.md` 的目录约定表)。
6. **导向下一步** — 提示: 用 `novelist-design` 做核心设计(主要剧情 + 主要人物)。

## 目录归属(防冲突的根基)

完整目录树与归属总表见 `references/directory-schema.md`(整套插件的唯一结构事实源)。速览:

| 目录 | 归属 skill | 内容 |
|---|---|---|
| 人物/<人物名>/ | novelist-character | 简介.md / 经历.md / 关系.md |
| 世界观/ + 设定/ | novelist-worldview | 地理/势力/规则/历史 + 其他设定 |
| 大纲/ + 情节/ | novelist-outline | 总纲/分卷 + 主线/支线/伏笔 |
| 章节/ | novelist-write / novelist-rewrite | 正文 + 章节索引 |
| 元数据/ | novelist-check / novelist-proofread | 进度 + 检查/校对报告 |

## 失败模式(触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 缺小说名 | `AskUserQuestion` 问用户 | 用户不给 → 退出, 不建目录 |
| 目标目录已存在且非空(脚本退出码 2) | 报告用户, 问是「换名 / 追加(--force) / 取消」 | 用户选追加 → 加 `--force` 重跑(不覆盖已有文件) |
| `python3` 不可用 | 提示用户安装 python3 | 仍无 → 退出并说明手动建目录方式 |

## ⛔ 反例黑名单(命中=错, 重来)

| # | 禁做 | 改为 |
|---|---|---|
| 1 | 自行编一个小说名就建目录 | 缺名先 `AskUserQuestion` |
| 2 | 不跑脚本, 手动一个个 mkdir | 一律走 `init_novel.py`, 保证结构一致 |
| 3 | 无 --force 时强行覆盖已存在目录 | 先问用户, 尊重退出码 2 |
| 4 | 初始化时顺手写正文/设定内容 | 本 skill 只搭骨架, 内容交 design/character/worldview |

> 本 skill 是 novelist 插件的入口。完成后所有写作动作都在此目录环境内进行。
