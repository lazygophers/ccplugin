---
updated: 2026-06-09
rewrite-version: 1
authored-by: trellisx-spec
mode: optimize
---

# Code Reuse Rules

何时被读: 写新函数 / 新建文件 / 批量修改同语义字段前
谁读: trellis-implement sub-agent; main agent
不遵守的代价: 重复代码扩散, bug fix 不传播, 行为随时间分叉

---

## MUST — 写前必搜

写新函数前 MUST `grep` 项目同名 / 同语义函数; 命中则用旧, 禁新写:

```bash
# 函数名搜索
grep -r "functionName" src/ packages/
# 语义搜索
grep -rE "关键词1|关键词2|关键词3" src/ packages/
```

验证: `grep -rE '<新函数语义>' src/ packages/` 命中 ≥ 1 → MUST NOT 新写, 必须复用或扩展。

## MUST — 三份规则

同语义代码 ≥ 3 处出现 → MUST 抽取共享函数 / 模块, 禁新增第 4 份拷贝。

验证: `grep -rE '<函数语义词>' src/ packages/ | wc -l` ≥ 3 → 当前文件 MUST NOT 新写独立实现。

## MUST — 常量单源

重复常量 MUST 定义在一处, 所有消费方 import, 禁在多文件分别定义。

验证: `grep -r '<常量值>' src/ packages/ | grep -v 'import\|from\|\.h' | wc -l` 必须 = 1 (定义点)。

## MUST — 批量修改后必验

修改影响 ≥ 2 文件时:

1. MUST `grep -rE '<修改内容>' src/ packages/` 确认无遗漏
2. 同语义 ≥ 3 处 → MUST 抽取 (见"三份规则")
3. 验证: grep 结果 = 预期文件列表, 多余 = 遗漏

## MUST — 不对称机制同步

当两种机制产生同一输出集 (e.g. glob 自动复制 vs 手动 `files.set()`):

- 目录结构变更时 MUST 搜索所有引用旧结构的代码路径
- 自动派生路径 + 手动列举路径并存 → 手动端 MUST 同步更新
- MUST 添加回归测试比对两种机制输出

## 禁止

- 禁 copy-paste 验证函数到另一文件 → 抽取到共享 utilities
- 禁创建与已有组件 ≥ 80% 相似的新组件 → 扩展现有组件
- 禁在多文件分别定义同一常量 → 单源定义 + import

## Checklist

- [ ] grep 确认无已有同语义实现
- [ ] 无 copy-paste 逻辑应抽未抽
- [ ] 常量仅定义一处
- [ ] 相似模式遵循同一结构
