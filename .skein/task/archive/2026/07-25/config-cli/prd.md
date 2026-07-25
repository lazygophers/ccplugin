# skein config 读写 CLI — PRD (主入口)

## 目标
- [ ] skein.py 加 config 子命令支持读写配置: config get [key] 打印生效值 (无 key 出全部); config set <key> <value> 校验键属 CONFIG_DEFAULTS + 按类型 coerce 后写 config.yaml
## 边界
- 范围内: 抽模块级 _coerce_config(k,v) 复用 web _cfg_save 逻辑; 加 config 方法 (get/set); 注册 parser+dispatch; set 入 MUTATING 集(经锁). 范围外: 不改 config() 读逻辑/CONFIG_DEFAULTS/ENV override; 不加 reset(YAGNI)
## 验收标准
- [ ] config get 出全部键=生效值; config get max_active 出单值; config set max_active 3 写盘且 get 读回 3; config set 未知键报错非静默; config set auto_commit false 正确 coerce 为 bool; 类型不合报错; pytest 全绿
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list config-cli`)
