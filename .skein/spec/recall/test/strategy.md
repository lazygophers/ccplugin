---
title: strategy
layer: recall
category: test
keywords: [test,integration,subprocess,e2e,exception,assertion,failure,rejected,framings,三件套,反例,正例,测试,演进,SSR,CSR,HTML断言,结构化数据,pre-existing]
status: active
---

## CLI 测试：subprocess 端到端（非 import 白盒）

### 触发场景
编写 skein CLI 测试。

### 陷阱-正解
**陷阱**：import 白盒测试，mock 过度。
**正解**：subprocess 跑真实 skein.py + tmp 仓/git，端到端集成。

### 案例
test_skein.py:22-27 / test_board.py:150-162。

## 失败路径显式断言 (SystemExit/pytest.raises)

### 触发场景
验证并发/失败契约。

### 陷阱-正解
**陷阱**：无异常处理验证。
**正解**：SystemExit / pytest.raises 显式验失败契约。

## Rejected Framings 三件套

### Rejected Framings 三件套

### 触发场景

编写 rubric 或任何需要反例对照的评估文档—— 需要明确"什么不行 + 为什么 + 怎样才行"三要素。

### 陷阱 / 正解

❌ 单列"反例"或"黑名单"章节，罗列"不要做 X/Y/Z"  
根因：AI 不知道为什么被拒、正确做法是什么，容易误判或遗漏  
✅ 每条反例三要素齐全：被拒模式 + 原因 + 正例

### 反例

❌ "不要做 X"（无原因无正例）  
✅ "组件塞进 `.claude-plugin/` 目录 | 被拒原因：插件加载时只认 `plugin.json`，组件在此目录静默不加载 | 正例：组件在插件根；`.claude-plugin/` 仅放 `plugin.json`"

### 案例

- skill-dev 9 维 rubric dim9 (反例与黑名单): 完成准则明确要求「"Rejected framings」段命名被拒模式 + 原因 + 正例」
- plugin-dev optimize-rubric: 硬护栏表格式每条禁令都配原因和正例

### 适用

- rubric 编写（评分标准）
- 质量检查文档
- 任何需要"反例 + 正解"的场景
- 教学型文档（需解释为什么）

### 关联

[[writing-style#正向表述优先原则]] (core, 正向表述优先原则)
[[verification#独立验证防自评偏差]] (core, 独立验证防自评偏差)

## 测试演进纪律

### 测试演进纪律

### 触发场景
实现把服务端渲染改前端渲染时，旧 test 的 HTML/SVG 断言须退役，否则永远 pre-existing 失败。

### 问题根源
- 服务端渲染测试：断言 HTML 字符串 / SVG 结构
- 改前端渲染后：HTML 结构变、异步加载时序变
- **旧断言永久失败**：pre-existing 测试永远报错，阻塞 CI

### 正确演进路径
| 改动类型 | 测试断言演进 |
|---------|------------|
| **SSR → CSR** | HTML/SVG 断言 → 结构化数据完整性断言 |
| **同步 → 异步** | 同步断言 → wait + 断言 |
| **单体 → 组件化** | 集成断言 → 组件 props/state 断言 |

### 结构化数据完整性断言示例
- **不对**：`assert html == '<div class="foo">bar</div>'`
- **对**：`assert data['key'] == expected_value`（测 API 返回数据完整性）

### 适用场景
- 每次重构渲染方式（SSR→CSR、同步→异步）时，检查旧测试断言
- 测试失败时，判是否是演进问题，非 bug

### 关联
- 参考 `core 层索引` 中的 test 相关规则
