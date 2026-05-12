# PRD — lint 自动同步最新模板

## 背景

当前模板已建好 schema (frontmatter + data-role + HTML grid + Bases query 占位), 但:
- vault 内 `_templates/` 与 plugin `templates/` 可能漂移 (plugin 升级后 vault 不同步)
- vault 内 `_index.md` / 仪表盘/*.md 等 seed 来文件可能停留在旧 schema
- 没有机制检测 / 同步

## 目标

lint 跑时:
1. 检测模板漂移 — vault `_templates/{html,memory,knowledge}/*` 与 plugin source 文件不一致
2. 检测 seed 文件过时 — vault 内由 seed 复制的文件 (`_index.md` / 仪表盘 stub) 模板版本低于当前
3. 默认报告 (warn / error), `--fix` 时自动同步覆盖

### 不在范围
- 不动用户在 `_index.md` 后追加的内容 (只覆盖模板 owned 区域 — 见下"覆盖策略")
- 不动 templates 设计本身

## 设计

### 1. 模板版本机制

**plugin source 加 manifest**:
- `plugins/tools/cortex/templates/_manifest.json`:
  ```json
  {
    "version": 2,
    "templates": {
      "html/badge.html": {"sha256": "...", "version": 2},
      "html/card.html": {"sha256": "...", "version": 2},
      ...
      "memory/L0-core.md": {"sha256": "...", "version": 2},
      "knowledge/project.md": {"sha256": "...", "version": 2}
    }
  }
  ```
  manifest 由脚本生成 (`scripts/regen_template_manifest.py`), 不手维护。

**seed 文件 frontmatter 加 `template_version: <N>`** (44 seed 文件, 已含部分如 `template_version: 1`, 缺的补)。

**presets manifest**:
- `plugins/tools/cortex/presets/_manifest.json`:
  ```json
  {
    "version": 2,
    "seeds": {
      "seed/root/主页.md": {"sha256": "...", "template_version": 2},
      "seed/仪表盘/总览.md": {"sha256": "...", "template_version": 2},
      ...
    }
  }
  ```

### 2. lint 新规则

`lint/run.py` 加 2 rule:

- **rule N+1 `template-outdated`** (warn, fixable):
  - 扫 vault `_templates/{html,memory,knowledge}/*`, 与 plugin `templates/<rel>` 比对 sha256
  - 不一致 → warn `template _templates/<rel> 与 plugin source 不一致 (vault sha=... plugin sha=...)`
  - `--fix` 覆盖 (备份到 lint backup_dir)

- **rule N+2 `seed-outdated`** (warn, fixable):
  - 扫 vault 内由 seed 来的文件 (按 frontmatter `template_version` 字段判断)
  - vault `template_version` < plugin manifest `template_version` → warn
  - `--fix` 重写文件模板 owned 区 (frontmatter 全部 + `<!-- TEMPLATE_START -->` 到 `<!-- TEMPLATE_END -->` 之间的 HTML), 保留 END 标记后的用户自定义内容

### 3. 覆盖策略 (seed-outdated --fix)

模板文件结构:
```markdown
---
<frontmatter, plugin owned>
---
<!-- TEMPLATE_START -->
<HTML scaffold + Bases query + sections, plugin owned>
<!-- TEMPLATE_END -->

<用户自定义内容, 不动>
```

所有 seed 模板末尾加 `<!-- TEMPLATE_END -->` 标记。
`--fix` 时:
- 读 plugin 当前 seed (绝对最新版本)
- 读 vault 文件 `<!-- TEMPLATE_END -->` 之后内容
- 拼接: plugin (开头到 TEMPLATE_END) + vault (TEMPLATE_END 之后)
- 写回

如果 vault 文件无 TEMPLATE_END (老文件): 整体替换 (用户提示, 备份原文件)。

### 4. cortex-lint wrapper 默认行为

`scripts/cron/lint.sh`:
- 默认 `--check` (不改文件, 仅报告)
- 加 `--sync-templates` flag: 自动 fix `template-outdated` + `seed-outdated` 两规则 (不动其他规则的 fixable 项, 那些用户应手动确认)
- cron 调度可选 `--sync-templates`

`~/.cortex/scripts/lint.sh` 用户调用版: 同样 flag。

### 5. cortex-install SKILL 流程更新

install 跑完后, 写 `_meta/template-manifest.json` (vault 侧记录), 内容同 plugin manifest 当前版本。lint 比对 vault manifest vs plugin manifest 加速检测 (不必每文件 sha256)。

## 实施步骤

### 步骤 1: 生成 manifest 脚本

新建 `plugins/tools/cortex/scripts/regen_template_manifest.py`:
- 扫 `plugins/tools/cortex/templates/**/*` + `plugins/tools/cortex/presets/seed/**/*`
- 计算每文件 sha256
- 读文件 frontmatter `template_version` (no→默认 1)
- 写 `templates/_manifest.json` + `presets/_manifest.json`
- 写顶层 `_manifest.json` 含 global version (max of all)

### 步骤 2: 给所有 seed/template 文件加 template_version

- `templates/` 已有 (template_version: 1 或 HTML comment), 标准化
- `presets/seed/` 43 .md 加 frontmatter `template_version: 1`
- 全部加 `<!-- TEMPLATE_END -->` 标记 (在最后)

跑一次 regen_template_manifest.py 生成基线 manifest。

### 步骤 3: lint 新规则

`lint/run.py`:
- import manifest 读取 helper
- 新 `_check_template_outdated(vault, plugin_root) -> list[finding]`
- 新 `_check_seed_outdated(vault, plugin_root) -> list[finding]`
- 在主流程加调用
- `--fix` 时实现覆盖逻辑

### 步骤 4: lint wrapper 加 flag

`scripts/cron/lint.sh` + `install_wrappers.sh` 生成的 `~/.cortex/scripts/lint.sh`:
- 加 `--sync-templates` flag
- 默认 cron 调度 `--sync-templates` (避免漂移堆积)

### 步骤 5: install SKILL 更新

cortex-install SKILL §流程:
- 写 `_meta/template-manifest.json` (复制 plugin manifest current version)

## 验收

- [ ] `plugins/tools/cortex/templates/_manifest.json` 生成成功 (含 sha256 + version)
- [ ] `plugins/tools/cortex/presets/_manifest.json` 生成成功
- [ ] 所有 seed/template 文件含 `template_version` + `<!-- TEMPLATE_END -->`
- [ ] lint 新规则 `template-outdated` + `seed-outdated` 跑得通 (--check 报告 / --fix 修复)
- [ ] lint wrapper 加 `--sync-templates` flag
- [ ] 217 python tests + 新 lint 规则单元测试 PASS
- [ ] 跑 lint 干净 vault 应 0 warning (manifest 一致)
- [ ] 跑 lint 改过 _templates/badge.html 后应 1 warning, `--fix` 后 0

## 风险

| 风险 | 缓解 |
|------|------|
| 用户手改 vault _templates 被覆盖 | TEMPLATE_END 标记 + 备份到 backup_dir; 用户改应改 plugin source 然后 sync |
| TEMPLATE_END 标记冲突 | 用 HTML comment `<!-- TEMPLATE_END -->`, markdown 不渲染 |
| manifest sha 漂移频繁 (CRLF/LF) | normalize line endings 后再 sha |
| install --fix 误覆盖用户 _index 后追加内容 | 严格只动 TEMPLATE_END 之前部分 |

## 子任务拆分 (单 wave 串行)

任务相互依赖, 不并行:
1. 加 template_version + TEMPLATE_END 到所有 seed/template (45 文件)
2. 写 regen_template_manifest.py + 生成初始 manifest (3 文件)
3. lint/run.py 加 2 新规则 + helper (1 文件)
4. wrapper + install SKILL 更新 (3 文件)

合计 4 个串行步骤, 单 trellis-implement agent。
