---
name: cortex-reflect
description: DMN 跨域综合 — 读最近高频 L2/L3 找跨 domain 连接 + 未解决疑问, 输出到 知识库/收件箱/<YYYY-Wnn>-反思-{连接,疑问,洞察}.md (等 digest 分发)。触发: "reflect" / "反思" / "周/月复盘" / weekly cron。
disable-model-invocation: true
allowed-tools: Bash Read Write Glob
---

# cortex-reflect

模拟大脑 default mode network (DMN) — 在空闲/周末扫近期记忆, 找跨 domain 的洞察连接和未解决疑问, 写入 `知识库/收件箱/<YYYY-Wnn>-反思-{连接,疑问,洞察}.md` (作为待 digest 分发条目, digest 阶段决定升 领域/<域> 或 项目/<repo>/笔记/)。

## 触发场景
- weekly cron (与 digest 串行, 不独立调度)
- monthly 用户触发月度复盘
- 用户显式 "reflect this week" / "本周反思" / "找跨域连接"
- cortex-cartographer 生成 canvas/dashboard 前的输入

## 输入
- --window: 默认 `7d`; 可 `30d` / `90d`
- --kinds: 默认 `[connection, question]`; 可加 `insight`
- --dry-run: 仅打印分析

## 流程

1. **读源**:
   - Glob `记忆/L2-中期/semantic/**/*.md` (weight ≥ 0.5)
   - Glob `记忆/L3-短期/episodic/<window>/*.md`
   - Glob `记忆/views/consolidated/<latest>.md` (cortex-digest 输出)
2. **domain 提取**:
   - 从 ref 字段反查 `知识库/领域/<L1>/<L2>/...` 推 domain 标签
   - 无 ref → 从 tags / 标题关键词推断
3. **连接发现** (kind=connection):
   - 不同 domain 实体在同一 episode/week 共现 ≥ 2 次
   - 写 `知识库/收件箱/<YYYY-Wnn>-反思-连接.md`:
     ```markdown
     ## A↔B (技术/编程语言/Go ↔ 元学习/思维框架)
     - 共现 episode: L3://episodic/2026-05-10/T0930
     - 共现 episode: L3://episodic/2026-05-12/T1430
     - 假设连接: <AI 一句话>
     ```
4. **疑问归集** (kind=question):
   - 扫 episode/session body 中的 `?` 结尾句 + 显式 `TODO?` / `疑问:` 标记
   - 去重后归类到 domain
   - 写 `知识库/收件箱/<YYYY-Wnn>-反思-疑问.md`
5. **洞察提议** (kind=insight, 可选):
   - 高 weight L2 条目 + 跨域引用 ≥ 3 → 候选洞察
   - 写 `知识库/收件箱/<YYYY-Wnn>-反思-洞察.md` (草稿, 待用户精修, digest 决定是否升 领域/<域>)
6. **不直接 promote**: 仅写知识库反思区, promote 决策走 cortex-promote

## 输出
```
[reflect] window=2026-W19
  scanned: 18 L2 + 32 L3 + 1 consolidated weekly
  domains touched: 7 (技术/编程语言/Go, 元学习/思维框架, ...)
  connections: 4 (written to 知识库/收件箱/2026-W19-反思-连接.md)
  questions: 11 (written to 知识库/收件箱/2026-W19-反思-疑问.md)
  insights: 2 (draft to 知识库/收件箱/2026-W19-反思-洞察.md)
```

## 错误处理
- 0 个跨域共现 → 仍写空骨架文件 (便于用户手动补充)
- frontmatter 无 ref → 用 tags fallback
- 收件箱目录不存在 → 自动 mkdir
- 同周文件已存在 → append 新发现, 不覆盖 (幂等)

## AUTO_MODE 兼容
[AUTO_MODE: ...] (cron 默认) 全自动写盘。洞察类 (kind=insight) 默认不开 (AI 生成易腐化), 仅显式 --kinds=insight 才生成草稿。
