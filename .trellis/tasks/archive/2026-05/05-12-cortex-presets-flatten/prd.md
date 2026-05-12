# PRD — presets/ 扁平化 (lyt 内容上提)

## 背景

用户:
> 我的预期是 presets/ 直接就是目录结构和模板, 不要有 lyt 这样的东西

现 `plugins/tools/cortex/presets/`:
```
presets/
├── lyt/
│   ├── _structure.json
│   └── seed/
├── zettel/
├── para/
└── blank/
```

上一 task 已硬编码 cortex-install preset=lyt,但目录层级仍含 lyt 子目录。用户要**彻底扁平化**,`presets/` 即骨架根。

## 目标

```
presets/
├── _structure.json     # 原 lyt/_structure.json
└── seed/               # 原 lyt/seed/
```

删 `presets/{zettel,para,blank}/` 3 个未用 preset。

## 范围

### 移动

- `presets/lyt/_structure.json` → `presets/_structure.json`
- `presets/lyt/seed/` → `presets/seed/` (整目录)

### 删除

- `presets/lyt/` (移完后空目录删)
- `presets/zettel/`
- `presets/para/`
- `presets/blank/`

### 修改引用点

- `skills/cortex-install/SKILL.md` — `presets/lyt/` 路径改 `presets/`
- 其它 SKILL/docs/test 内引用 (grep 发现 ~15 文件) 同改

### 不在范围

- 不动 `lint/schemas.py` (LYT/PARA/flat schema 保留, 仅 install 路径解耦)
- 不动 hooks 主逻辑 / mcp/ / install.sh / P0-P6 / Phase A
- `_meta/version.json:.preset` 仍写 "lyt" 兜底 (向后兼容老 vault config 读取)

## 详细规范

### 1. mv 操作

```bash
git mv plugins/tools/cortex/presets/lyt/_structure.json plugins/tools/cortex/presets/_structure.json
git mv plugins/tools/cortex/presets/lyt/seed plugins/tools/cortex/presets/seed
rmdir plugins/tools/cortex/presets/lyt
git rm -r plugins/tools/cortex/presets/zettel plugins/tools/cortex/presets/para plugins/tools/cortex/presets/blank
```

### 2. SKILL.md 引用更新

cortex-install/SKILL.md:
- 所有 `presets/lyt/` 改 `presets/`
- 所有 `preset/lyt/_structure.json` 改 `presets/_structure.json`

举例:
```diff
- 读 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/lyt/_structure.json`
+ 读 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/presets/_structure.json`
```

其它 SKILL.md / docs / tests 引用 grep 处理。

### 3. _structure.json 内容微调

```diff
- "preset": "lyt",
- "description": "Linking Your Thinking — 8-bucket + MOC 主导。目录名按 vault.lang 渲染 (locales/<lang>.yml:dirs)。",
+ "description": "cortex vault 骨架 (LYT-inspired 8-bucket + MOC)。目录名按 vault.lang 渲染 (locales/<lang>.yml:dirs)。",
```

仍保 `preset: "lyt"` 字段方便老 lint schemas.py 检测向后兼容(可选,看测试是否依赖)。

实际:删 preset 字段更彻底,_meta/version.json 写 `preset: "lyt"` 由 install 硬编码注入,不依赖 _structure.json。

```diff
- "preset": "lyt",
  "version": "2.0",
- "description": "Linking Your Thinking — 8-bucket + MOC 主导。...",
+ "description": "cortex vault 骨架 — 8-bucket + MOC。目录名按 vault.lang 渲染。",
```

### 4. 删 zettel/para/blank 副作用

这 3 个未用 preset 删除后,若用户 vault `_meta/version.json:.preset` 已是其中之一:
- install 重跑时保留原 preset (上一 task 加的向后兼容)
- 但目录骨架不再有该 preset 模板 → install 仅更新 _meta/_templates,不重写业务目录

lint/schemas.py PARA / flat 保留,既存 vault lint 仍工作。

## 验收

1. `ls plugins/tools/cortex/presets/` 仅 `_structure.json` + `seed/`,无子目录
2. `git rm -r presets/{lyt,zettel,para,blank}` 已删
3. grep `presets/lyt\|presets/zettel\|presets/para\|presets/blank` 仓库 → 仅剩 `_meta/version.json`-related 文档 / lint schemas 引用 (向后兼容场景)
4. cortex-install/SKILL.md 路径全 `presets/<file>` 形式
5. `_structure.json` 字段调整 (删 `preset` 字段或保留)
6. bash plugins/tools/cortex/tests/run.sh 不回归

## 不变量

- 仓库内 presets/ 扁平,无 preset 子目录
- _meta/version.json 仍含 preset 字段 (install 硬写 lyt)
- lint/schemas.py 多 preset 保留 (向后兼容)
- 不破坏 install.sh / hooks / mcp / P0-P6

## 风险

- **测试用例 fixture 含 presets/lyt/ 路径**:test_install / test_session_start 可能引用. **缓解**: grep 替换全引用
- **既存用户 vault `_meta/preset=zettel`**:install 重跑保留原 preset 但插件不再带 zettel 骨架. **缓解**: 文档 + 仅老 vault 已建好的目录不受影响
- **mcp/.venv 等 vendor 缓存路径**:不动 (grep 误匹配)
