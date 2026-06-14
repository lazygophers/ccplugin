# 移除 plugins/template 插件

## Goal

从仓库与插件市场清单中**完全移除** `plugins/template` 示例插件。

## Requirements

- 删除 `plugins/template/` 目录全部内容
- 移除 `.claude-plugin/marketplace.json` 中 `name=template` 的 plugin 对象
- 不动其他任何插件 (git/deepresearch/version/notify/llms/trellisx/cortex)
- 不手改生成缓存 `.understand-anything/fingerprints.json` (自动重建)
- 不改 `.trellis/`

## Acceptance Criteria

- [ ] `ls plugins/template` 报 No such file
- [ ] `jq '[.plugins[]|select(.source|test("template"))]|length'` = 0
- [ ] `jq empty .claude-plugin/marketplace.json` 通过 (JSON 合法)
- [ ] `jq '.plugins|length'` = 7 (8→7)
- [ ] 全仓 grep 确认无代码硬依赖 template (仅 marketplace + 生成缓存)

## 验证命令

```bash
ls plugins/template 2>&1
jq '[.plugins[]|select(.source|test("template"))]|length' .claude-plugin/marketplace.json
jq empty .claude-plugin/marketplace.json && echo OK
jq '.plugins|length' .claude-plugin/marketplace.json
```

## Notes

- 单一交付轻量任务, PRD-only, 无需 design/implement。
- 失败处理: jq 误删非 template 条目 → 校验剩余 7 名单不符则回滚 marketplace.json。
