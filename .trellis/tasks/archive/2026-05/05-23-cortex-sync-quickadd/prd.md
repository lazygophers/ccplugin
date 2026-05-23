# cortex 模版全量 sync + quickadd 集成

## Goal

vault `_templates/` 多年演进, 已积累 35+ 模版 (knowledge/ memory/ html/ 子目录); plugin `presets/seed/_templates/` 仅 10 个, 严重滞后。同时 Obsidian quickadd 插件 (`.obsidian/plugins/quickadd/data.json`) 引用了 plugin 没有的模版, 用户每次 install 后必须手抄。

本任务:
1. 全量回灌 vault `_templates/` → plugin `presets/seed/_templates/` (canonical 源)
2. 重生成 `_meta/template-manifest.json` 的 sha256 hash (基于新模版)
3. install.sh 加自动写 `.obsidian/plugins/quickadd/data.json` (备份旧文件)
4. 加 quickadd 文档章节 (docs/模板与美化.md + 知识库结构.md)

## What I already know

- vault 路径: `/Users/luoxin/persons/knowledge/obsidian/_templates/`
- vault 顶层 11 个 + html/ 7 个 + knowledge/ 13 个 + memory/ 6 个 = 37 模版
- plugin 现有 (`plugins/tools/cortex/presets/seed/_templates/`): _index.md / _manifest.json / dashboard.md / domain-topic.md / frontmatter-schema.yaml / inbox.md / journal-day.md / project.md / triggers.yaml + html/ knowledge/ memory/ 子目录骨架
- quickadd 配置 `data.json` 含 6 choice (闪念笔记 / 网页剪藏 / 写日记 / 概念笔记 / 项目笔记 / 问题笔记)
- 引用模版: `_templates/knowledge/{journal-day,domain-concept,project}.md` + `_templates/question.md`
- install.sh 当前未写 `.obsidian/plugins/` (cortex 不动 Obsidian 配置)
- `_meta/template-manifest.json` 有 sha256 字段, lint 规则 20 `vault-misaligned` 用此校验

## Requirements

### R1 模版全量 sync

- 列 vault `_templates/` 全部 .md/.html (含子目录)
- 与 plugin `presets/seed/_templates/` 差集对比
- 缺失文件: 从 vault 拷贝到 plugin (保留子目录结构)
- 已存在但内容不同: vault 优先 (vault 是活跃使用版本; plugin 落后)
- plugin 独有 (`_manifest.json` / `frontmatter-schema.yaml` / `triggers.yaml`): 保留不动

### R2 template-manifest.json 重生成

- 新写脚本 `scripts/regen_template_manifest.py` 或扩 `cortex-install` 加 manifest 同步
- 输出: `_meta/template-manifest.json` 含每个模版 `{sha256, template_version: 1}`
- 排除 `_manifest.json` 自身 + yaml schema 文件
- 输出到 plugin `presets/seed/_meta/template-manifest.json` (供 install.sh 拷贝)

### R3 install.sh quickadd 集成

新 step `step_quickadd` (位于 step_vault_skeleton 之后, step_python_deps 之前):
- 检查 `<vault>/.obsidian/plugins/quickadd/` 存在
- 不存在 → 提示 "quickadd 未装, 跳过" 不报错
- 存在 → 备份现有 `data.json` 到 `data.json.bak.<UTC>`, 写新 `data.json` (从 `presets/quickadd/data.json` 模版)
- 模版位置: `plugins/tools/cortex/presets/quickadd/data.json` (从 vault 当前 data.json 拷贝作为初始)
- 提示用户重启 Obsidian

### R4 文档同步

- `docs/模板与美化.md` 加 quickadd 章节 (6 choice 速查 + 自定义指引 + manifest 同步原理)
- `docs/知识库结构.md` 加 `_templates/` 子目录展开 (顶层 / html / knowledge / memory)
- `README.md` 列模版数 10 → 实际数 (扫到的全集)
- `cortex-install` skill references 加 quickadd 段
- memory cortex-plugin-2026-05-13.md 加 quickadd 集成事实

## Acceptance Criteria

- [ ] `ls plugins/tools/cortex/presets/seed/_templates/` 覆盖 vault `_templates/` 全集
- [ ] `_meta/template-manifest.json` sha256 与 plugin 模版字节一致
- [ ] `bash install.sh --target test-vault` 在测试目录跑通, 含 quickadd 步骤
- [ ] 测试: 加 `test_quickadd_install.py` (mock vault, 验证备份 + 写入)
- [ ] ruff + pytest 全过
- [ ] .version bump

## Technical Approach

### 拷贝脚本 (一次性)

```bash
rsync -av --include="*/" --include="*.md" --include="*.html" --exclude="*" \
  /Users/luoxin/persons/knowledge/obsidian/_templates/ \
  plugins/tools/cortex/presets/seed/_templates/
```

`_manifest.json` 不覆盖 (plugin 内有自己版本)。yaml schema 不在 vault `_templates/` 中, 不冲突。

### manifest 重生成

```python
def regen_manifest(templates_dir: Path, manifest_path: Path) -> None:
    entries = {}
    for f in sorted(templates_dir.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(templates_dir).as_posix()
        if rel in ("_manifest.json", "frontmatter-schema.yaml", "triggers.yaml"):
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        entries[rel] = {"sha256": h, "template_version": 1}
    manifest_path.write_text(json.dumps({
        "version": 1,
        "generated": now_iso(),
        "entries": entries,
    }, indent=2, ensure_ascii=False))
```

### install.sh step_quickadd

```bash
step_quickadd() {
  local qa_dir="$VAULT/.obsidian/plugins/quickadd"
  if [[ ! -d "$qa_dir" ]]; then
    log_info "quickadd 未装, 跳过 (装后重跑 install.sh 即生效)"
    return 0
  fi
  if [[ -f "$qa_dir/data.json" ]]; then
    local ts; ts=$(date -u +%Y%m%dT%H%M%SZ)
    cp "$qa_dir/data.json" "$qa_dir/data.json.bak.$ts"
    log_info "quickadd: 备份现有 data.json → data.json.bak.$ts"
  fi
  cp "$PLUGIN_ROOT/presets/quickadd/data.json" "$qa_dir/data.json"
  log_ok  "quickadd: 写入 6 choice 配置, 请重启 Obsidian"
}
```

## Out of Scope

- 自动安装 quickadd 插件本身 (用户须先装)
- 模版渲染引擎重写
- templater-obsidian 插件集成 (后续单独)
- 模版去重/合并 (vault 现状作为权威)

## Technical Notes

- 参考: `plugins/tools/cortex/install.sh` 现有 step_* 模式 (`step_user_config / step_vault_skeleton / step_python_deps`)
- 参考: `plugins/tools/cortex/skills/cortex-install/references/install-flow.md` 安装流程文档
- 参考: lint 规则 20 `vault-misaligned` 处理 plugin-managed 文件 (改 plugin 端会触发 vault lint)
- quickadd 模版按 frozen snapshot 提交; 用户自定义 choice 必失。备份 + 提示是最低保险
