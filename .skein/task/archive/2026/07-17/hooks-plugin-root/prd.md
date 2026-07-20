# hooks 用 CLAUDE_PLUGIN_ROOT — PRD

## 目标
plugin.json hooks command 从裸命令名改为 `${CLAUDE_PLUGIN_ROOT}/bin/<script>`, 不依赖 PATH/alias。

## 背景
当前 9 处 hooks 用裸命令名 (skein/skein-memory/skein-hooks), 靠 PATH (cache bin) 或 alias 解析。不可靠 — PATH 缺失或 alias 未定义则 hook 失败。bin/ wrapper 已支持 CLAUDE_PLUGIN_ROOT。

## 改动
plugin.json 9 处 hook command:
- `skein-memory <args>` → `${CLAUDE_PLUGIN_ROOT}/bin/skein-memory <args>`
- `skein <args>` → `${CLAUDE_PLUGIN_ROOT}/bin/skein <args>`
- `skein-hooks <args>` → `${CLAUDE_PLUGIN_ROOT}/bin/skein-hooks <args>`

已用 `${CLAUDE_PLUGIN_ROOT}` 的 3 处不改 (serve monitor / pip3 install)。

## 边界
- 范围内: plugin.json hooks 段 9 处 command
- 范围外: bin/ wrapper (已支持 CLAUDE_PLUGIN_ROOT); monitors serve (已用); skills/agents/commands
- 约束: 用户选 ${CLAUDE_PLUGIN_ROOT}

## 验收
- [ ] 9 处裸命令改 ${CLAUDE_PLUGIN_ROOT}/bin/<script>
- [ ] JSON 合法 (jq . 解析过)
- [ ] 3 处已用 ${CLAUDE_PLUGIN_ROOT} 不变
