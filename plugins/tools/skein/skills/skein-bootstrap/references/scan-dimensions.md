# bootstrap 扫描维度明细 (供 main 校对 researcher 覆盖面)

researcher bootstrap 模式扫以下五维, 每维产 0..N 条候选规则 (无信号则 0 条, 禁硬凑)。每条候选 MUST 附**证据来源** (file:line / 命令输出), 无证据的推断前缀 `推测:`。

| 维度 | 扫什么 | 候选规则示例 | 常见落层 |
|---|---|---|---|
| **命名** | 文件/目录/函数/变量/类型命名惯例, 大小写风格, 前后缀约定 | "测试文件 MUST 用 `test_*.py` 命名" | recall |
| **错误处理** | 异常 vs 返回码, 错误包装/日志模式, 边界校验位置 | "跨层调用 MUST 包装为 domain error, 禁裸抛底层异常" | core/recall |
| **测试** | 测试框架/目录/断言风格, mock 约定, 覆盖率门槛 | "新逻辑 MUST 带 assert 自检, 禁引入测试框架" | recall |
| **架构边界** | 分层/模块依赖方向, 禁止的跨层访问, 目录职责 | "🔴 DB 层禁写裸 SQL, 必走 ORM/repository" | core |
| **构建** | 构建/依赖/发布命令, lint/format 工具, CI 约定 | "提交前 MUST 跑 `make lint`" | recall |

## 提炼原则

- **只提"既有约定"**, 不提"应该改成什么" (bootstrap 是描述现状, 非重构建议)。
- **信号强度**: 反复出现 (grep 多处一致) = 强候选; 单处孤例 = 弱候选或 drop。
- **命令式化**: 描述性观察 ("大多用 X") 改写为可验证契约 ("MUST 用 X"), 交 main/用户在 sediment 定稿。
- **证据密度**: 每条至少 2 处一致证据才算约定; 1 处 = 偶然, 前缀 `推测:` 或 drop。

## 落盘格式 (researcher 写 `.skein/task/bootstrap/research/conventions.md`)

```
维度: <命名/错误处理/测试/架构边界/构建>
候选: <命令式契约文本>
建议层: <core/recall> (仅建议, 终判归 main)
类目: <git/test/arch/build/style/domain/ops>
证据: <file:line 多处>
信号: <强/弱>
```
