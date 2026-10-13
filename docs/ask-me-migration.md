# ask-ui → ask-me 迁移指南

ask-ui skill 已改名为 ask-me（仓库 lazygophers/ccplugin）。`npx skills update` 只更新同名 skill，改名的必须「删旧装新」。

## 给你的 agent 的提示词（整段复制）

```text
ask-ui skill 已改名为 ask-me（来自 lazygophers/ccplugin）。请帮我迁移：

1. 删除旧 skill：npx skills remove ask-ui
2. 安装新 skill：npx skills add lazygophers/ccplugin/skills/tools/ask-me
3. 全局 git 忽略文件（git config --global core.excludesfile 指向的那个）里如有 .ask-ui/ 和 .ask-ui-runs/，改成 .ask-me/ 和 .ask-me-runs/
4. 我的 CLAUDE.md / 规则文件里所有 ask-ui 字样换成 ask-me：Skill(ask-ui) → Skill(ask-me)，数据目录 .ask-ui → .ask-me，环境变量 ASK_UI_SKILL_DIR → ASK_ME_SKILL_DIR
5. 项目里的 .ask-ui 数据目录是旧提问记录，不用迁移；确认不需要后直接删
6. 装完验证：node ~/.agents/skills/ask-me/scripts/self-test.mjs，最后一行 ask-me self-test passed 即成功
```

## 变更对照

| 旧 | 新 |
|---|---|
| skill 名 `ask-ui` | `ask-me` |
| 数据目录 `.ask-ui/` | `.ask-me/` |
| stderr 标记 `ask-ui-id` / `ask-ui-submitted` | `ask-me-id` / `ask-me-submitted` |
| 入口脚本 `scripts/ask-ui.mjs` | `scripts/ask-me.mjs` |
| 环境变量 `ASK_UI_SKILL_DIR` | `ASK_ME_SKILL_DIR` |
| 运行日志 `$TEMP/ask-ui.log` | `$TEMP/ask-me.log` |
| 主题存储 key `ask-ui-theme` | `ask-me-theme` |
