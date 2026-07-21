# prd 章节 CLI (读/更/覆盖写) — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 核心函数 (抽公共, CLI + 网页端复用)

`skein.py` 新增方法 (带 self 用 self.tasks 定位, 网页端后端复用):

```python
# --type 中英映射 (用户选「中英都支持」)
PRD_TYPE_ALIAS = {
    "目标": "目标", "goal": "目标",
    "边界": "边界", "scope": "边界",
    "验收标准": "验收标准", "acceptance": "验收标准", "accept": "验收标准",
}
PRD_SECTIONS = ("目标", "边界", "验收标准")  # 可操作章节 (索引禁动)
TODO_SECTIONS = {"目标", "验收标准"}          # 写入补 - [ ] 的章节

def _prd_split_sections(text: str) -> list[tuple[str, list[str]]]:
    """把 prd.md 全文按 ## 章节切分, 返回 [(章节名, [行...]), ...]。
    复用 fmt 的正则 r'^##\\s+(.+?)\\s*$'。一级标题 (# ...) 和章节间内容归前导。"""

def _prd_locate(prd_path: Path, section: str) -> tuple[list[str], int, int]:
    """定位章节在 prd.md 的 [start, end) 行区间。不存在 raise SystemExit。"""

def prd_section_read(self, tid: str, section: str) -> str:
    """读章节正文 (不含 ## 标题行, 含其下到下一 ## 前所有行, trim 首尾空行)。"""

def _normalize_todo(lines: list[str], section: str) -> list[str]:
    """目标/验收标准章节: 裸 `- xxx` → `- [ ] xxx`; 已 checkbox 保留; 有序 `N. xxx` → `- [ ] xxx`;
    普通非 list 行 → `- [ ] <行>` (验收条目都该可勾)。
    边界章节: 裸文本行 → `- <行>` (补 list marker 不补 checkbox); 已 `- ` 保留; 不动 checkbox。"""

def prd_section_add(self, tid: str, section: str, text: str) -> None:
    """追加 text 到章节末 (已有保留)。text 按 \\n 切多行。
    追加位置: 章节最后一行后, 下一 ## 前。写入前过 _normalize_todo。"""

def prd_section_write(self, tid: str, section: str, text: str) -> None:
    """整章清重建 (仅保留 ## 标题行, 描述提示行 + 旧条目全清, 替换为 text 条目)。
    text 按 \\n 切多行, 过 _normalize_todo。"""

def prd_section_check(self, tid: str, section: str, match: str, flag: bool) -> None:
    """章节内匹配 match 的行, checkbox 切换: flag=True → - [ ]→- [x]; False → 反。
    match 子串匹配 (行内含 match 即命中); 多行命中全切; 零命中 raise SystemExit。"""
```

## CLI 子命令 (位置子命令 + --type + --list)

`skein prd {read|write|add|check|uncheck} <id> --type {目标|边界|验收标准|goal|scope|acceptance} [--list TEXT]`

- 5 位置子命令: `read` / `write` / `add` / `check` / `uncheck`
- `<id>`: 位置参数, 必填, task id
- `--type`: 必填, 中英都支持 (PRD_TYPE_ALIAS 映射到标准中文章节名)
- `--list`: write/add/check/uncheck 必填 (文本内容, `\n` 多行); read 不需要

argparse 结构:
```python
# 主 prd 解析器, 5 个子子命令
prd = sub.add_parser("prd", ...)
prd_sub = prd.add_subparsers(dest="action", required=True)
for act in ("read", "write", "add", "check", "uncheck"):
    p = prd_sub.add_parser(act)
    p.add_argument("id")                                    # 位置参数必填
    p.add_argument("--type", required=True,                 # 中英都接受
                   choices=list(PRD_TYPE_ALIAS.keys()))
    if act != "read":
        p.add_argument("--list", required=True)             # read 不需要 --list
```

校验顺序: task 存在 → prd.md 存在 → type 合法 (alias 映射) → section 在 prd 中存在 → 动作执行。

## 章节定位 + 写入策略

prd.md 四章节顺序固定 (目标/边界/验收标准/索引)。`_prd_locate` 用 `## 章节名` 正则定位 [start, end):

- start = `## section` 行号 + 1
- end = 下一 `## ` 行号 (末章节则文件尾)

章节正文含"描述提示行" (如 `要解决什么 / 用户价值...:`) — write 整章清重建: 仅保留 `## 标题` 行, 描述提示行 + 旧条目全清, 替换为 --list 条目。add 在条目区末追加 (保留已有内容含提示行)。

## check/uncheck 匹配语义

子串匹配 (行内含 --list 文本即命中):
- `skein prd check <id> --type=acceptance --list "返回 200"` → 章节内含 "返回 200" 的 `- [ ]` 行 → `- [x] ...返回 200...`
- 已 `- [x]` 不重复切 (幂等)
- 零命中 → raise SystemExit (防 silent fail, check 回写时命中零 = match 写错)

## 网页端 (task.html)

看板已有 task 详情视图, 加 prd 编辑面板:
- 三章节各一 textarea (read 时填入 `prd_section_read` 输出)
- 保存按钮 → 后端 API `POST /api/task/<id>/prd` body `{action, type, list}`
- 后端调同一 `prd_section_*` 函数 (复用, 禁复制逻辑)
- 保存后刷看板 (onLive 软刷)

后端路由在现有 `serve`/`view` 的 http 服务 (skein.py StaticFiles mount + API)。

## skills 同步

- `skein-plan/SKILL.md` step5 产出工件段: prd 章节经 `skein prd write/add` 写, 禁裸 Edit
- `skein-check/SKILL.md:25` "传 planning 的验收标准" → 改 "checker 自跑 `skein prd read <id> --type=acceptance` 取"
- `skein-check/SKILL.md:31` "main 用 Edit 回写勾选态" → 改 "main 用 `skein prd check/uncheck` 回写"

## 关键取舍

1. **位置子命令 vs flag 动作**: 位置子命令 (用户指定) — 符合 skein 既有 CLI 风格 (create/start/finish 都是位置动词)。
2. **--type 中英都支持**: alias 映射 — 中文对齐脚手架, 英文给偏好 ASCII 的用户; 内部统一存中文。
3. **--list 名字**: 用户指定 — 语义"列表项", 多条 `\n` 分隔。
4. **抽公共函数 vs 内联**: 抽 `prd_section_*` — CLI 和网页端复用, 禁复制 (PONYTAIL: 写一次)。
5. **check 用文本子串匹配 vs 行号**: 文本 — 行号脆弱 (fmt 补 checkbox 会变行), 文本稳定; 零命中报错防 silent。
6. **write 整章清重建 vs 保留提示行**: 清重建 (用户选) — write 语义明确"整章替换", 提示行不是契约是模板引导, 用户 write 时已明确要写啥; add 仍保留已有内容 (追加语义)。
7. **索引章节禁动**: 索引脚本维护 (脚手架写入), 用户误改会断链。
8. **不做 --file 输入**: 仅 --list, 多行 \\n (YAGNI, 用户选)。

## 可能性分支 (planning 研究期发散, 不进最终方案正文)

- 若未来加 design.md / findings.md 章节操作: 复用 _prd_split_sections 机制, 抽成通用 _md_section_* (触发条件: design 也需结构化读写)
- 若 check 需批量勾选: 加 `--list "条1\\n条2\\n条3"` 一次多 match (触发条件: 单次 check 通过项 >5 勾烦) — 当前已支持 (子串匹配多行全切)
- 若网页端需富文本: textarea → markdown 编辑器 (触发条件: 用户反馈 textarea 写多行验收标准累)

