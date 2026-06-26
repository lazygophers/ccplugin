# 调研来源 + 论文证据

> 全部 URL 经 2026-06-26 curl 直取 arxiv abs 页 meta 标签（citation_title / citation_author / citation_date）+ GitHub API（`{full_name, message, stargazers_count}`）核实，http=200。

## 论文 1：SkillLens（arXiv 2605.23899）

- **标题**：From Raw Experience to Skill Consumption: A Systematic Study of Model-Generated Agent Skills
- **作者**：Huang Zisu, Xu Jingwen, Yang Yifan, Gong Ziyang, Yang Qihao, Tian Muzhao, Wang Xiaohua, Lv Changze, Gao Xuemei, Dai Qi, Liu Bei, Qiu Kai, Yang Xue, Chen Dongdong, Zheng Xiaoqing, Luo Chong
- **日期**：2026/05/22（arxiv online 2026/05/22）
- **PDF**：https://arxiv.org/pdf/2605.23899
- **机构**：Microsoft Research（同组连发 SkillOpt）
- **核心贡献**：
  - utility-grounded 评估框架，跨 5 个 agentic 任务域
  - 覆盖 skill 全生命周期：experience generation → skill extraction → skill consumption
  - 发现：model-generated skills 平均有益但存在 **negative transfer**；extractor 与 consumer 强弱不相关；skill utility 独立于 model scale / baseline task strength
  - 产出 **meta-skill** 指导 extraction 聚焦实际 utility 相关特征，持续提升质量、显著降低 negative transfer
- **darwin 转述的关键数字**（非本 skill 独立复现）：
  - LLM-as-judge 评估 skill 质量准确率 **46.4%**（接近随机）
  - 加入 meta-skill 三维度后升到 **73.8%**
  - 三维度 = 失败模式编码（dim3）/ 可执行具体性（dim5）/ 反例黑名单（dim9）

## 论文 2：SkillOpt（arXiv 2605.23904）

- **标题**：SkillOpt: Executive Strategy for Self-Evolving Agent Skills
- **作者**：Yang Yifan, Gong Ziyang, Huang Weiquan, Yang Qihao, Zhou Ziwei, Huang Zisu, Li Yan, Gao Xuemei, Dai Qi, Liu Bei, Qiu Kai, Yang Yuqing, Chen Dongdong, Yang Xue, Luo Chong
- **日期**：2026/05/22（arxiv online 2026/05/25）
- **PDF**：https://arxiv.org/pdf/2605.23904
- **Code**：https://aka.ms/skillopt
- **机构**：Microsoft Research
- **核心贡献**（首个系统可控 text-space optimizer for agent skills）：
  - skill 当作 frozen agent 的外部可训练状态，用 weight-space 优化纪律做 text-space 优化
  - 独立 optimizer model 把 scored rollouts 转 **bounded add/delete/replace edits**
  - **validation-gated**：编辑仅当 held-out validation score 严格提升才 accept
  - textual learning-rate + rejected-edit buffer + epoch-wise slow/meta update
  - 部署时 **zero inference-time model calls**
- **基准**：6 benchmark × 7 target model × 3 execution harness（direct chat / Codex / Claude Code）= 52 cell，全 best-or-tied
- ** lifts**（GPT-5.5，no-skill baseline → +skill）：
  - direct chat: **+23.5**
  - Codex agentic loop: **+24.8**
  - Claude Code: **+19.1**
- **transfer**：优化后的 skill artifact 跨 model scale / Codex↔Claude Code / 附近 math benchmark 仍保值（无需再优化）

## 仓库：microsoft/SkillOpt

- **URL**：https://github.com/microsoft/SkillOpt
- **created**：2026-05-08
- **stars**：9352（2026-06-26 取）
- **description**：text-space optimizer that trains reusable natural-language skills for frozen LLM agents through trajectory-driven edits, validation-gated updates, and deployable `best_skill.md` artifacts

## 本地源：darwin-skill

- **路径**：`~/.claude/skills/darwin-skill/SKILL.md`（492 行）
- **GitHub**：https://github.com/alchaincyf/darwin-skill （4338 stars，2026-06-26 取）
- **版本**：v2.0 · 2026-05-28
- **借鉴**：
  - 9 维 rubric（结构 59 + 效果 35 + meta 6 = 100）
  - HL-1~4 high-leverage 杠杆
  - git ratchet（分支隔离 + 只保留改进 commit）
  - judge 独立性（spawn 子 agent 盲评）
  - HL-3 相关簇（dim2/3/4 联动）
  - dry_run > 30% 失效警告
  - runtime 红灯扫描（gate 项）
- **darwin 自身实证**（本机 controlled study，非同行评审）：
  - huashu-research 4 类 degradation × 5 独立 judge 盲测，一致 V1>V2，Δ 均值 +46.5（5/5 high confidence）
  - HL 实战：huashu-gpt-image +10.85（darwin results.tsv 一手记录）

## 诚实标注

- 论文真实，但本 skill 的 9 维适配是**darwin 转述 SkillLens 的转述**，非论文原班 rubric
- 具体数字（46.4%→73.8%、+23.5 等）为论文 / darwin 自引，本 skill 未独立复现
- SkillOpt 基准在 GPT-5.5 / Codex / Claude Code 上跑，本 skill 在 Opus 4.8 上的效果未基准测
- 重要决策（破坏性变更、大范围重写）必须人审，rubric 不可作为唯一依据
