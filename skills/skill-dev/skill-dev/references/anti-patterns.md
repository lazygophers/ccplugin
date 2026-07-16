# 反模式黑名单 + 失败处理

> skill-dev 流程 A 的 dim9 反向约束。主入口 SKILL.md「流程 A · 创建」。

## 失败处理（dim3 三段式编码）

编写过程中常见失败的 if-then 三段式：

| 触发条件 | 一线修复 | 仍失败兜底 |
|----------|---------|-----------|
| `claude -p` 质检返回空/错误 | 查 frontmatter YAML（tab/空格混用、引号未闭合），`--debug` 看 parse 错误 | 最小化 frontmatter 只留 name+description 重试 |
| AI 识别错误（skill 被当别的用途） | description key use case 前置 + 删歧义词 | 拆成 2 个更聚焦的 skill |
| skill 不触发（false negative） | description 补用户会说的关键词 | 查是否被 `skillOverrides` 关闭 / 预算裁剪（`/doctor`） |
| skill 误触发（false positive） | description 收窄「何时用」边界 | 加 `disable-model-invocation: true` 改手动 |
| SKILL.md 超 500 行 / 超 token 预算 | 拆 `references/`（CJK 密度 2-3x 英文，表格/代码块密度更高） | 评估拆多个 skill |
| 改了 skill 但 session 没生效 | 新 session 或重新 `/skill-name` invoke | 见 Phase 6，invoke 后 session 不重读文件 |
| 反拷问暴露逻辑漏洞 | 补对应失败分支到本文 | 标记 known limitation，description 限制使用范围 |

## 反模式黑名单（dim9 反向约束）

### P0 致命（skill 失效）

| # | 反模式 | 正例 |
|---|--------|------|
| 1 | vague description（「Helps with marketing」） | `Processes marketing campaign data from CSV/Excel, generates ROI reports. Use when analyzing campaign metrics, conversion rates, or marketing spend.` |
| 2 | frontmatter YAML 缩进/引号错误 | `claude --debug` 查 parse 错误（常见：tab/空格混用、引号未闭合） |
| 3 | description 关键词被截断丢 | key use case 前置；🔴 控制在 **512 字符内**（项目底线）；超长分流 `when_to_use`（< 128）；长列表用 `skillOverrides` `name-only` 释放预算（`/doctor` 查裁剪） |
| 4 | 路径错误 / skill 孤立 | `find . -name SKILL.md` 确认存在 + `claude -p "列出所有可用 skill"` 验证发现 |
| 5 | description 太泛致误触发（false positive） | 收窄「何时用」边界 + should-not-trigger 测试（skill-creator） |

### P1 严重（效果劣化）

| # | 反模式 | 正例 |
|---|--------|------|
| 6 | 解释 Claude 已知的事 | 只加 Claude 不知道的 |
| 7 | SKILL.md 超 500 行 | 拆 `references/` |
| 8 | 给太多选项 | 给 default + escape hatch |
| 9 | 嵌套引用过深 | 只深一层 |
| 10 | 无 eval 就发布 | 先建 ≥3 场景 eval（Phase 5 步骤 1） |
| 11 | Windows 反斜杠路径 | 统一正斜杠 |
| 12 | token 超 compaction 预算（≠ 行数） | CJK/表格/代码块密度高，500 行中文可能 8000+ token，多 skill session 被反复踢出且无错误信息——控制实际 token 不只行数 |

### P2 中等（质量损耗）

| # | 反模式 | 正例 |
|---|--------|------|
| 13 | 术语混用（field/box/element） | 选定一个贯穿 |
| 14 | 时间敏感信息内联 | 放 old patterns `<details>` |
| 15 | 脚本 punt 错误给 Claude | 显式 try/except + 默认值 |
| 16 | voodoo constants（TIMEOUT=47） | 注释为何这个值 |
| 17 | 假设包已安装 | 显式 `pip install` |

### P3 结构性

| # | 反模式 | 正例 |
|---|--------|------|
| 18 | 只写正例不写反例 | 反例黑名单成章（本节即示范） |
| 19 | 「必须」措辞代替视觉标记 | 🔴 / 🛑 视觉标记（LLM 扫标记优先于语义） |
| 20 | 两列 fallback（症状/解法） | 三段式（触发条件/一线修复/兜底，见上方「失败处理」） |
| 21 | 过度优化硬凑轮数 | Δ<2 连续 2 轮即停 |
| 22 | runtime 钉死单一平台 | 中立 badge + 中立措辞 |
