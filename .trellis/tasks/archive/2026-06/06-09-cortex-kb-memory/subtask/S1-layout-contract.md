---
id: S1
slug: layout-contract
deliverable: D1
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: main
isolation: none
depends-on: []
blocks: [S2, S3, S4, S5]
estimated-tokens: 8000
---

# S1 · 落地目录契约文档 + validate-layout.sh

## 目标

落一份机器可校验的目录契约 (用户级 `~/.cortex/` + 项目级 `<repo>/.wiki/`), 含 `validate-layout.sh` 脚本, 给定 target dir 能判断是否合规。

## 产出

- `plugins/tools/cortex/docs/layout.md` — 契约文档 (含目录树 + 字段规则 + 同构原则 + 开放扩展位说明)
- `plugins/tools/cortex/scripts/validate-layout.sh` — 校验脚本 (bash, 退出码语义)
- `plugins/tools/cortex/tests/fixtures/layout-ok/` — 合规 fixture (空文件占位即可)
- `plugins/tools/cortex/tests/fixtures/layout-bad/` — 缺项 fixture (缺 L0-rules 或 domains 等)

## 验证

```bash
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-bad/
```

期望输出:
- 第一条: 退出码 0, stdout 含 "OK"
- 第二条: 退出码 ≠ 0, stderr 列出缺失路径

## 资源

- 独占文件: `plugins/tools/cortex/docs/**` `plugins/tools/cortex/scripts/validate-layout.sh` `plugins/tools/cortex/tests/fixtures/layout-*/`
- 端口 / 服务: 无
- 环境: 无
- 审批槽位: 否

## 依赖

无 (基础步骤)

## 执行细节

1. 写 `docs/layout.md`, 主体内容直接抄 design.md "系统边界" 章节, 补:
   - 同构原则: `~/.cortex/.wiki/` 与 `<repo>/.wiki/` 内部结构完全一致, 仅根路径不同
   - 开放扩展位: `~/.cortex/` 顶层除 `.wiki/ config/ state/ scripts/ logs/` 外, 用户可加 `cache/ credentials/ templates/` 等; 校验脚本只检必备项, 不禁额外项
   - scripts 单一真相: `~/.cortex/scripts/` 而非 `~/.cortex/.wiki/scripts/`
2. 写 `scripts/validate-layout.sh`:
   - shebang `#!/usr/bin/env bash` + `set -euo pipefail`
   - 参数解析: `--target <dir>`, 默认 target=$HOME/.cortex
   - 校验必备路径数组 (含两个 scripts 目录, 用途不同):
     - `.wiki/memory/L0-core` `.wiki/memory/L1-long` `.wiki/memory/L2-mid` `.wiki/memory/L3-short` `.wiki/memory/L4-inbox`
     - `.wiki/projects` `.wiki/domains` `.wiki/scripts` (vault 内部脚本)
     - `config` `state` `scripts` (用户操作入口) `logs`
   - 缺失逐条 echo 到 stderr, 累计 1 个以上 exit 1
   - 全部存在打印 "OK: <count> required paths present" exit 0
   - 末尾加 `--help` 文档, 文档明确区分两个 scripts/ 用途
3. 建 fixture: `layout-ok/` 含全部必备目录 (用 `mkdir -p`), `layout-bad/` 故意缺 `.wiki/memory/L0-core` 与 `.wiki/domains` 与 `.wiki/scripts`

## 回滚

- 触发条件: 验证脚本无法判定合规/不合规
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/docs/ plugins/tools/cortex/scripts/validate-layout.sh plugins/tools/cortex/tests/fixtures/layout-*/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 用户机器已有 ~/.cortex/ 数据被脚本误改 | 数据损坏 | 脚本只读不写, 无任何 mkdir/rm 操作 |
| 开放扩展位被误判为违规 | 用户误以为额外目录不允许 | 校验只检必备项, 不检额外项, 文档显式说明 |

## 历史

- 2026-06-09: created
