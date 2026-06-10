---
id: S5
slug: extract
deliverable: D5
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: sub-agent
isolation: none
depends-on: [S2, S3]
blocks: [S6]
estimated-tokens: 14000
---

# S5 · 写 cortex-extract skill + extract.sh

## 目标

落 L4 inbox → L1/L2/L3 + projects/domains 的提取/分类脚本 + 触发 skill, 含增量游标, dry-run 默认。

## 产出

- `plugins/tools/cortex/skills/cortex-extract/SKILL.md`
- `plugins/tools/cortex/scripts/extract.sh` (bash 入口)
- `plugins/tools/cortex/scripts/_extract/` (python 模块: classifier.py, router.py, writer.py)
- `plugins/tools/cortex/tests/fixtures/extract/L4-inbox/` 含 5 类样本:
  - 临时笔记 (路由 L3-short, 默认入口)
  - 反复出现的偏好 (路由 L2-mid 或 L1-long, 视复用计数)
  - 项目 README 摘要 (路由 projects/<host>/<owner>/<repo>/)
  - 领域知识片段 (路由 domains/<area>/<sub>/)
  - 低价值噪声 (路由 archive 或 delete)

## 验证

```bash
# Dry-run
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/
# 期望: 退出 0, stdout 是 JSON, 含 plan 数组 len ≥ 5, 每条含 {source, target, level/module, reason}

# Apply
bash plugins/tools/cortex/scripts/extract.sh --apply --target plugins/tools/cortex/tests/fixtures/extract/
# 期望: 退出 0; L4-inbox 清空 (或仅余 archive 标记); 目标位置 (memory/L1-3 或 projects/domains) 出现新文件

# 游标
test -f plugins/tools/cortex/tests/fixtures/extract/.cortex-state/extract-cursor.json
# 期望: 文件存在, 记录最新处理时间

# 路径名反直觉防呆: 跑后不应出现 L1-short / L3-long 等反写路径
! find plugins/tools/cortex/tests/fixtures/extract/ -type d -name 'L1-short' -o -name 'L1-recent' -o -name 'L3-long' | grep .

# Skill frontmatter
python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/skills/cortex-extract/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-extract' and fm['description']
print('OK')
"
```

## 资源

- 独占文件: `plugins/tools/cortex/skills/cortex-extract/**` `plugins/tools/cortex/scripts/extract.sh` `plugins/tools/cortex/scripts/_extract/**` `plugins/tools/cortex/tests/fixtures/extract/**`
- 与 S4 不互斥
- 审批槽位: 否

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S2 | `skills/cortex-schema-knowledge/SKILL.md` (路由目标) | 文件检测 |
| S3 | `skills/cortex-schema-memory/SKILL.md` (路由目标 + 阈值) | 文件检测 |

## 执行细节

1. **classifier 三轴判定** (从 S3 抄):
   - 时效: 文件 mtime / frontmatter `created`
   - 强度: 用户标 (frontmatter `weight`) / 关键词识别 ("永远 / 暂时 / 记住")
   - 复用面: 在 inbox 中重复出现的相似度 (简单 keyword overlap)
2. **router 决策表** (升级方向 = 抵抗遗忘, L3 → L1; 默认入口 L3):
   - 关键词 "永远 / 硬性 / never / 严禁" → **L0-core 候选** (默认 ask, 不自动写)
   - 默认入口 (新条目 / 关键词 "暂时 / 临时") → **L3-short** (短期, 易忘)
   - 复用 ≥ 3 次 → 提议 promote 到 **L2-mid** (中期)
   - 复用 ≥ 5 次 + 标 `weight ≥ 0.8` 或关键词 "永久记住" → 提议 promote 到 **L1-long** (长期, 稳固)
   - URL 含 github.com / gitlab.com → projects/<host>/<owner>/<repo>/
   - area 标签存在 → domains/<area>/<sub>/
   - 兜底: 留 L4-inbox archive 标记
3. **增量游标**:
   - 记 `state/extract-cursor.json` (在 target 内, 不在用户机)
   - 记最新处理 mtime, 下次只扫新增
4. **写盘**:
   - dry-run 默认 (stdout JSON plan)
   - --apply 才落盘 + 更新游标
   - L0 写入永远 ask (即使 --apply 也要确认, fixture 测试时 mock)

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-kb-memory

## 目标
写 cortex-extract skill + extract.sh + python 模块 + fixture, 实现 L4 inbox → L1-L3 + projects/domains 路由, 三轴判定, 增量游标, dry-run 默认。

## 已知
- 上游: skills/cortex-schema-knowledge + cortex-schema-memory
- 5 路由类: L0-core (ask) / L3-short (默认入口) / L2-mid (复用 ≥ 3) / L1-long (复用 ≥ 5 + 高 weight) / projects / domains
- 三轴: 抗遗忘度 / 强度 / 复用面
- 等级语义按遗忘曲线: L3 易忘 → L1 稳固 (与"数字越小越长期"反直觉, 路径名必须含 long/mid/short 后缀防写反)

## 工作目录与范围
- cwd: /Users/luoxin/persons/lyxamour/ccplugin
- 可改: plugins/tools/cortex/skills/cortex-extract/** plugins/tools/cortex/scripts/extract.sh plugins/tools/cortex/scripts/_extract/** plugins/tools/cortex/tests/fixtures/extract/**
- 禁改: ~/.cortex/**; 其他插件

## 输出格式
- SKILL.md ≤ 180 行
- extract.sh ≤ 80 行
- _extract/*.py 每模块 ≤ 250 行

## 验收标准
subtask "验证" 节全部命令通过。

## 失败处理
- 工具错 → 重试 1 次
- 路由模糊 → 兜底 archive, 不自动写 L0
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不 spawn 其他。
```

## 回滚

- 触发条件: --apply 把 fixture 改坏 / 游标损坏导致重复处理
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/skills/cortex-extract/ plugins/tools/cortex/scripts/extract.sh plugins/tools/cortex/scripts/_extract/ plugins/tools/cortex/tests/fixtures/extract/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| classifier 误判把临时笔记写到 L1 (长期) | 长期记忆污染 | L1/L2 promote 需复用计数硬阈值, 不靠语义; 默认入口固定 L3 (短期), 不直接进 L1 |
| 路径名写反 (新条目落到 L1-long 而非 L3-short) | 与遗忘曲线语义冲突 | router 输出 plan 时必须包含 `target.path` + `target.level`; lint R6 二次校验路径与 level 一致 |
| L0 被自动写入 | 行为规范污染 | L0 永远 ask, 即使 --apply 也强制确认 |
| 游标失效导致重复处理 | 数据重复 | 游标用 (mtime, sha256) 双键; 处理后立即更新 |
| 与 L4 自动垃圾邮件式累积 | inbox 永远清不空 | --apply 默认 archive (不 delete), 提供 --purge 单独命令 |

## 历史

- 2026-06-09: created
