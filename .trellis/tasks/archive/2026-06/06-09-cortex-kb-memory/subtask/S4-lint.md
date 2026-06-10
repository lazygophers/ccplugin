---
id: S4
slug: lint
deliverable: D4
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: sub-agent
isolation: none
depends-on: [S2, S3]
blocks: [S6]
estimated-tokens: 14000
---

# S4 · 写 cortex-lint skill + lint.sh

## 目标

落 link/frontmatter/命名校验脚本 + 触发 skill, 对给定 vault 检出不合规项, `--fix` 自动规范化。

## 产出

- `plugins/tools/cortex/skills/cortex-lint/SKILL.md`
- `plugins/tools/cortex/scripts/lint.sh` (bash 入口 + 调 python3 子模块)
- `plugins/tools/cortex/scripts/_lint/` (python 模块: rules.py, fixers.py, runner.py)
- `plugins/tools/cortex/tests/fixtures/lint/` 含 ≥ 3 类违规:
  - 死 wikilink (`[[不存在的页]]`)
  - frontmatter 缺 required 字段 (type / area / level)
  - 路径不合规 (domains 只 1 级 / scripts 命名非 kebab)

## 验证

```bash
# 检模式列出违规
bash plugins/tools/cortex/scripts/lint.sh --check plugins/tools/cortex/tests/fixtures/lint/
# 期望: 退出码 ≠ 0; stdout 含 "violations: <N>" 且 N ≥ 3

# 修模式
bash plugins/tools/cortex/scripts/lint.sh --fix plugins/tools/cortex/tests/fixtures/lint/

# 复查
bash plugins/tools/cortex/scripts/lint.sh --check plugins/tools/cortex/tests/fixtures/lint/
# 期望: 退出码 0; stdout 含 "no violations"

# Skill frontmatter
python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/skills/cortex-lint/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-lint' and fm['description']
print('OK')
"
```

## 资源

- 独占文件: `plugins/tools/cortex/skills/cortex-lint/**` `plugins/tools/cortex/scripts/lint.sh` `plugins/tools/cortex/scripts/_lint/**` `plugins/tools/cortex/tests/fixtures/lint/**`
- 与 S5 不互斥
- 审批槽位: 否

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S2 | `skills/cortex-schema-knowledge/SKILL.md` (规则源) | 文件检测 |
| S3 | `skills/cortex-schema-memory/SKILL.md` (规则源) | 文件检测 |

## 执行细节

1. **lint 规则** (从 S2/S3 schema 派生):
   - R1 wikilink: 每个 `[[X]]` 必须能解析到 vault 内文件
   - R2 frontmatter required: type 必填, type=domain 要 area, type=rule 要 level, type=project 要 source
   - R3 命名: domains/ 至少 2 级; scripts/ 文件名 kebab-case
   - R4 同构: 用户级与项目级 .wiki/ 内部目录树一致 (memory/L0-core,L1-long,L2-mid,L3-short,L4-inbox + projects + domains + scripts)
   - R5 孤儿: 无反向 wikilink + 创建 > 30d 的 md 标 orphan (warn 级, 不 fix)
   - R6 等级语义一致 (防反直觉反写): memory 子目录名必须严格匹配 `L0-core / L1-long / L2-mid / L3-short / L4-inbox`; 任一文件 frontmatter `level: L1` 但路径在 `L3-short/` → 报错; 路径名出现 `L1-recent / L1-short / L3-long` 等反直觉写法 → 报错
   - R7 脚本目录用途分离: 检测到 `<repo>/.cortex/scripts/` (项目级误建用户入口) → 报错; `~/.cortex/scripts/` 出现 vault 内部脚本 frontmatter (`type: vault-script`) → warn
2. **fixers**:
   - R1: 不自动 fix (太危险), 报告中列出
   - R2: 补默认值 (`type` 按路径推断, `area` 按 domains/<area>/ 推断)
   - R3: 拒绝 fix domains 命名 (人工决策); scripts 自动 kebab 改名 + 留 git mv 提示
   - R4: 缺目录补 mkdir
   - R5: warn only
3. **lint.sh 入口**:
   - `--target <dir>`: 必填
   - `--check` (默认) / `--fix`: 二选一
   - `--rules R1,R2,...`: 可选子集
   - 输出: stdout 计数 + stderr 详情
4. **dry-run 默认**: `--fix` 才落盘, `--check` 仅报告

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-kb-memory

## 目标
写 cortex-lint skill + lint.sh + python 模块 + fixture, 实现 5 类 lint 规则 (R1-R5) + 对应 fixer, dry-run 默认。

## 已知
- 上游: skills/cortex-schema-knowledge/SKILL.md + skills/cortex-schema-memory/SKILL.md (规则源)
- 7 规则: wikilink / frontmatter / 命名 / 同构 / 孤儿 / 等级语义一致 / 脚本目录用途分离
- bash + python3, 无 node 依赖

## 工作目录与范围
- cwd: /Users/luoxin/persons/lyxamour/ccplugin
- 可改: plugins/tools/cortex/skills/cortex-lint/** plugins/tools/cortex/scripts/lint.sh plugins/tools/cortex/scripts/_lint/** plugins/tools/cortex/tests/fixtures/lint/**
- 禁改: 其他 plugins/tools/cortex/; .trellis/**; ~/.cortex/**

## 输出格式
- SKILL.md ≤ 180 行
- lint.sh ≤ 80 行 (主体在 python)
- _lint/*.py 每个模块 ≤ 200 行

## 验收标准
subtask "验证" 节全部命令通过, --check 报 ≥ 3 违规, --fix 后 --check 退出 0。

## 失败处理
- 工具错 → 重试 1 次
- 规则模糊 → "需要: <问题>" 回 main
- python 依赖问题 → 只用 stdlib, 不引外部包

## Sub-agent 自防护
trellis-implement, 不 spawn 其他。
```

## 回滚

- 触发条件: fixture --fix 后产生数据损坏 / lint 无法收敛
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/skills/cortex-lint/ plugins/tools/cortex/scripts/lint.sh plugins/tools/cortex/scripts/_lint/ plugins/tools/cortex/tests/fixtures/lint/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| --fix 误改用户数据 | 不可逆损坏 | 默认 dry-run; --fix 前强制 git status 检查 (在大目录), warn 未提交变更 |
| 7 规则覆盖不全 | 实际违规未检出 | 留 R8-R10 占位接口, 文档列已知 gap |
| 同构检测对开放扩展位误报 | 用户额外目录被标违规 | R4 只检必备目录子集, 不检 ~/.cortex/ 顶层额外目录 |

## 历史

- 2026-06-09: created
