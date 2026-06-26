# 调研来源 + 论文证据

> 全部 URL 经 2026-06-26 curl 核实（arxiv abs meta + GitHub API，http=200）。

## 论文

| 论文 | URL | 一句话贡献 |
|------|-----|-----------|
| SkillLens | [arXiv 2605.23899](https://arxiv.org/abs/2605.23899) · [PDF](https://arxiv.org/pdf/2605.23899) | utility-grounded 评估框架；meta-skill 三维度（dim3/dim5/dim9）让 LLM-as-judge 46.4%→73.8% |
| SkillOpt | [arXiv 2605.23904](https://arxiv.org/abs/2605.23904) · [PDF](https://arxiv.org/pdf/2605.23904) · [Code](https://aka.ms/skillopt) | 首个 text-space optimizer；bounded edits + validation-gated + textual learning-rate |
| microsoft/SkillOpt | [github.com/microsoft/SkillOpt](https://github.com/microsoft/SkillOpt) | 论文官方仓库（2026-05-08 创建） |

两论文均 Microsoft Research，2026/05/22 arxiv online。

## 本地源：darwin-skill

- **路径**：`~/.claude/skills/darwin-skill/SKILL.md`（v2.0 · 2026-05-28）
- **GitHub**：[alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill)
- **借鉴**：9 维 rubric（结构 59 + 效果 35 + meta 6）/ HL-1~4 / git ratchet / judge 独立性 / 相关簇 / dry_run 失效警告 / runtime 红灯扫描
- **darwin 自身实证**（本机 controlled study，非同行评审）：huashu-research 4 类 degradation × 5 judge 盲测一致 V1>V2，Δ 均值 +46.5

## 诚实标注

- 论文真实，但本 skill 9 维适配是 **darwin 转述 SkillLens 的转述**，非论文原班 rubric
- 具体数字（46.4%→73.8%、+23.5 等）为论文 / darwin 自引，本 skill 未独立复现
- SkillOpt 基准在 GPT-5.5 / Codex / Claude Code 上跑，本 skill 在 Opus 4.8 上效果未基准测
- 重要决策必须人审，rubric 不可作唯一依据
