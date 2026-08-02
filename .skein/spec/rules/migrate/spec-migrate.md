---
title: spec-migrate
category: migrate
keywords: [spec,migration,inclusion,namespace,archive]
status: active
inclusion: auto
---

## Spec 迁库核心决策

# Spec 迁库核心决策

## 背景
`.skein/spec` 库需要从三层模型（core/recall/external）迁移到新架构（按 inclusion 策略划分，namespace 保留内容类型）。

## 核心决策

### 1. 两阶段迁移
- **阶段一**：机械重排
  - 按新 namespace×inclusion 映射批量移动文件
  - 更新 frontmatter（`inclusion` 字段）
  - 无内容改动，纯结构操作

- **阶段二**：候选启发式打分
  - 扫描全库规则，对归属模糊项打分
  - 评分维度：关键词命中度、文件路径暗示、现有 `inclusion` 值
  - 高分候选自动归类，低分候选人工复核

### 2. core/recall → rules 合并
- 原 `core/` 和 `recall/` 合并为 `rules/` namespace
- 保留 `inclusion` 值区分加载策略（always 常驻 / auto 按需）
- 删除空目录

### 3. inclusion 从层模型改正交模型
- **旧模型**：inclusion 由所在目录隐式决定（core 目录 = always，recall 目录 = auto）
- **新模型**：inclusion 由 frontmatter 字段显式声明
  - `inclusion: always` → SessionStart hook 常驻注入
  - `inclusion: auto` → 按需召回
  - `inclusion: fileMatch` → 按路径 glob 匹配注入
  - `inclusion: manual` → 纯手动检索
- 目录名不再决定加载策略，inclusion 才决定

### 4. 配置键迁移
- 配置键 `spec_core_budget` → `spec_always_budget`
- 语义保持不变：控制 `inclusion: always` 页总字符预算
- 幂等检测：若新键已存在，跳过迁移

### 5. 幂等检测
- 迁移前检测目标状态
- 若新架构已生效，中止迁移（避免重复操作）
- 检测标志：`rules/` 目录存在且 `core/`、`recall/` 为空

### 6. archive 快照可逆
- 迁移前执行 `skein-spec archive` 创建快照
- 归档到 `.skein/spec/.archive/<ts>/`
- 若迁移失败或结果不满意，`skein-spec restore <ts>` 回滚

## 验收标准
- [ ] 旧目录 `core/`、`recall/` 清空或删除
- [ ] 新目录 `rules/` 包含所有迁移规则
- [ ] 所有规则 frontmatter 含有效 `inclusion` 字段
- [ ] `spec_always_budget` 配置键生效
- [ ] `.recall.db` 全文索引自适应新路径

## 关联
- [[recall/arch/spec-memory]] — Spec 三层记忆架构
- [[arch/config]] — 配置真值来源
