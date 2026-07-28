---
title: ui-tests
layer: recall
category: test
keywords: [test,assertion,前缀匹配,UI重写,ponytail,属性锁,子串失配,语义存在]
status: active
---

## test 断言跟进 UI 重写模式 (前缀匹配避属性锁)

### 触发场景

UI 大重写后 index.html 的 `<main>` 元素加了新属性 (如 class), 旧 test 用精确子串 `'<main id="view">'` 断言失配, 但功能未坏。

### 陷阱-正解

**陷阱**: 测试断言锁定完整 HTML 子串, UI 重写加属性就炸, 但实际只是属性多了; 若强制迁回精确子串要么砍掉新加属性 (功能倒退), 要么每次加属性都改测试 (噪声)。

**正解**: 前缀匹配 `'<main id="view"'` (无闭合 `>`), 验语义存在 (SPA 挂载点) 不锁完整属性集; ponytail 注释说明为何放宽。

### 规则

- MUST：UI 重写后断言跟进重写, 不让重写迁就旧断言 (重写先动, 测试随后对齐)。
- MUST：完整 HTML 子串失配但语义存在 → 改前缀匹配 (无闭合 `>`), 保留语义校验放宽属性集。
- MUST：改测试时留 `# ponytail: <原因>` 注释, 说明为何放宽 (避免后续误收紧)。
- MUST：仅锁定的属性消失 (语义真坏) 才报失败; 加属性 (class/style/data-*) 不应阻塞 CI。

### 反例表

| 禁 | 改为 |
|---|---|
| `assert '<main id="view">' in b` (UI 加 class 后失配) | `assert '<main id="view"' in b` (前缀, 验挂载点存在) |
| 砍掉 UI 新加的 class 让旧断言过 | 改断言为前缀匹配, 留 ponytail 注释 |
| 每次加属性都改测试加完整子串 | 一次改前缀匹配, 后续加属性免维护 |

### 案例

webapp-rewrite T7fix2 (commit ec0005d8b, 2026-07):
- test_board.py:172-173 旧断言 `'<main id="view">'` 子串, T7 切默认入口后 index.html main 加 class 致失配。
- 改 `'<main id="view"'` (前缀, 无闭合 `>`) + ponytail 注释: 「前缀匹配 — index.html main 加了 class, 精确子串会失配; 仍验 SPA 挂载点存在」。

### 关联

- recall/skill/cold-start-large-req-2026-07-20-69 (测试演进纪律 — SSR→CSR 整体退役, 本规则是同源更小粒度的属性级跟进)
- recall/test/reconstruct-37 (claude -p 理解门 + test-prompts 回归)
