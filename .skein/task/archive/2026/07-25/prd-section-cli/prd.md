# prd 章节 CLI (读/更/覆盖写) — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] skein.py 新增 `prd` 子命令 (位置子命令 read/write/add/check/uncheck + task id 必填 + --type + --list), 支持读/追加/覆盖写/勾选/反勾选 prd.md 的 目标/边界/验收标准 三章节
- [ ] AI (planning 阶段 main) 经脚本操作 prd 章节内容, 不再裸 Read/Edit prd.md (skills 同步指示走脚本)
- [ ] 网页端 (task.html 看板) 支持用户手动编辑 prd 三章节 (textarea + 保存, 后端走同一脚本写盘逻辑)
- [ ] 写入自动规范: 目标/验收标准章节每条补 `- [ ]` (对齐 fmt), 边界章节原样 (描述非 todo)
- [ ] --type 中英都支持 (目标/goal · 边界/scope · 验收标准/acceptance)
- [ ] 幂等 + 安全校验: type 合法, task 必须存在, prd.md 必须存在

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: CLI `skein prd {read|write|add|check|uncheck} <id> --type {目标|goal|边界|scope|验收标准|acceptance} [--list TEXT]`
- [ ] 范围内: read 不需 --list; write/add/check/uncheck 必填 --list (文本内容, `\n` 多行)
- [ ] 范围内: skills 同步 (skein-plan/SKILL.md + skein-check/SKILL.md) 指示 AI 用 `skein prd` 而非裸 Edit prd.md
- [ ] 范围内: 网页端 task.html 加 prd 编辑入口 (read/write/add 三动作复用脚本逻辑)
- [ ] 范围内: check 阶段 checker 经 `skein prd read <id> --type=acceptance` 取验收标准, 禁 dispatch prompt 传; 勾选态回写经 `skein prd check/uncheck` 禁裸 Edit
- [ ] 非目标: 不动 design.md / findings.md (findings 另有责任)
- [ ] 非目标: 不替换现有 fmt / _validate_prd (职责不同)
- [ ] 非目标: 不做 --file 文件输入 (仅 --list)
- [ ] 已知约束: prd.md 四章节顺序固定 (目标/边界/验收标准/索引), 章节定位用 `## 章节名` 正则 (复用 fmt 机制)
- [ ] 已知约束: `索引` 章节脚本维护, 新命令禁操作 (PRD_SECTIONS 不含索引)
- [ ] 已知约束: 网页端写盘复用 CLI 同一 Python 函数 (抽公共 prd_section_read/add/write/check), 禁复制逻辑

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] `skein prd read <id> --type=目标` 输出该章节正文 (不含 `## 标题` 行, 含其下到下一 `##` 前所有行)
- [x] `skein prd read <id> --type=goal` 等价上行 (英文 alias 映射)
- [x] `skein prd add <id> --type=边界 --list "新增边界"` 把文本追加到章节末 (已有内容保留)
- [x] `skein prd write <id> --type=acceptance --list "- [ ] A\n- [ ] B"` 整章清重建 (仅保留 ## 标题, 描述提示行 + 旧条目全清, 替换为 A/B 两条)
- [x] `skein prd check <id> --type=acceptance --list "返回 200"` 把章节内匹配该文本的 `- [ ]` 行勾选为 `- [x]`
- [x] `skein prd uncheck <id> --type=acceptance --list "返回 200"` 反勾选 (`- [x]`→`- [ ]`)
- [x] 写入后 目标/验收标准 章节每行自动 `- [ ]` 规范 (裸 `- ` / 有序 `N.` 均补 checkbox; 已 checkbox 保留)
- [x] 写入后 边界 章节原样 (不补 checkbox)
- [x] 缺 id (位置参数) 或缺 --type → argparse 报错非 0
- [x] 非法 --type (非 alias 表内值) → argparse 报错非 0
- [x] 非法动作 (非 read/write/add/check/uncheck) → argparse 报错非 0
- [x] task 不存在 / prd.md 不存在 → exit 非 0 + 报错
- [x] check/uncheck 零命中 → exit 非 0 + 报错 (防 silent fail)
- [x] read 不需 --list; write/add/check/uncheck 缺 --list → argparse 报错非 0
- [x] 幂等: write 同文本连跑两次结果一致; check 已勾选行再 check 无变化; read 不写盘
- [x] CLI `skein prd --help` + `skein prd read --help` 等含说明
- [x] skein-plan/SKILL.md 产出工件段指示: prd 章节内容经 `skein prd write/add` 脚本写, 禁裸 Edit prd.md
- [x] skein-check/SKILL.md: checker 经 `skein prd read <id> --type=acceptance` 取验收标准 (禁 dispatch prompt 传); 勾选态回写经 `skein prd check/uncheck` 脚本 (禁裸 Edit)
- [x] task.html 打开后能看到 prd 三章节可编辑 (textarea), 保存后落盘 + 看板刷
- [x] 网页端保存走后端 API, 后端调同一 prd_section_* 函数 (无逻辑复制)
- [x] 现有 fmt / _validate_prd / create 脚手架未被破坏 (回归)
- [x] 索引章节不被新命令误改 (PRD_SECTIONS 不含索引, --type=索引 → 报错)

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list prd-section-cli`)
