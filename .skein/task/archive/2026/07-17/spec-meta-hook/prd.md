# spec metadata 合法性 hook

## 目标

写 `.skein/spec/**/*.md` 后自动检查 frontmatter metadata: 必填字段缺失 + layer 合法值。非阻塞 warning 注入 context。

## 边界

- **检**: title, layer, created, keywords (4 字段必填)
- **不检**: category (用户裁定任意), source, authored-by
- **layer 合法值**: core | recall (非法 → warning)
- **keywords**: 必须存在 (空数组/缺字段 → warning)
- **触发**: PostToolUse Edit|Write|MultiEdit, 文件路径匹配 `.skein/spec/**/*.md`
- **阻断级别**: 非阻塞 (exit 0 + additionalContext warning), 写入照常完成
- **不检**: 非 spec 路径 (task prd.md / design.md 等不动)

## 验收标准

- [x] hooks.py 加 `cmd_spec_meta` 函数: 路径匹配 spec/*.md → 解析 frontmatter → 检 4 字段缺失 + layer 合法 → warning JSON
- [x] DISPATCH 注册 `spec-meta` 命令
- [x] plugin.json PostToolUse 加 matcher `Edit|Write|MultiEdit` → `skein-hooks spec-meta`
- [x] 缺字段示例: 删 title → 写后 hook 输出 "⚠️ spec metadata 缺失: title"
- [x] 非法 layer 示例: layer=foo → 写后 hook 输出 "⚠️ spec metadata 非法: layer=foo (合法: core|recall)"
- [x] 完整 metadata → 无 warning (静默 exit 0)
- [x] 非 spec 文件 → 不触发 (静默)

## 索引

- 详细设计: [design.md](design.md)
- 调度: task.json (脚本真值, `skein.py subtask list spec-meta-hook`)
