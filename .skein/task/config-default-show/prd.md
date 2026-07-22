# config 命令默认展示 + reset 重置

## 目标

重构 skein.py `config` 命令的子命令结构:

- [ ] 无子命令 (`skein config`) → 默认展示全部生效配置 (等价旧 `config get` 无 key)
- [ ] `skein config set <key> <value>` → 写单键 (行为不变)
- [ ] `skein config reset` → 全部重置为 CONFIG_DEFAULTS 默认值 (新增)
- [ ] 删除 `config get` 子命令 (单键查询能力并入无参全量展示, 用户按行 grep)

## 边界

- [ ] 只改 `plugins/tools/skein/scripts/skein.py` (config_cmd 方法 + config parser 注册 + config 帮助文案) 与 `plugins/tools/skein/scripts/tests/test_config_cli.py` (跟进用例)。
- [ ] 不动 web 端点 `_cfg_save` / `_coerce` (自有写路径, 非 CLI); 若 `_exec_argv` argv 白名单含 `config get`/`config set` 需同步更新, 否则不碰。
- [ ] 不动 `CONFIG_DEFAULTS` 键集与 `_coerce_config` 逻辑。
- [ ] `config` 仍留在 MUTATING 集合 (set/reset 写盘; 无参展示走读路径, 多占一次 flock 可接受, 不为省锁拆分)。
- [ ] reset 直接以 CONFIG_DEFAULTS 覆写 config.yaml (丢弃用户既有值, 符合"重置"语义)。

## 验收标准

- [ ] `skein config` 无参 → 打印全部生效配置 `key=value` (含 ENV override 回填), 退出码 0。
- [ ] `skein config set max_active 3` → 写盘 + 回读 `skein config` 中 `max_active=3`。
- [ ] `skein config reset` → config.yaml 覆写为 CONFIG_DEFAULTS, 打印重置结果; 之前 set 的自定义值被清除 (回读为默认)。
- [ ] `skein config get` → 报错 (invalid choice, 子命令已删)。
- [ ] 未知键 set (`config set nope 1`) 仍报未知配置键; 类型不合 (`config set max_active abc`) 仍报类型不合。
- [ ] ENV override 存在时 set/reset 仍给 override 生效提示。
- [ ] test_config_cli.py 全部用例改为无参展示 + set + reset 语义, `uv run --with pytest python -m pytest .../test_config_cli.py -q` 全绿。
- [ ] `python3 -c "import ast; ast.parse(...)"` 语法通过; `skein config -h` 帮助文案更新 (无 get, 含 reset)。

## 索引

- [ ] 实现: `plugins/tools/skein/scripts/skein.py:231` config_cmd + `:3093` config parser
- [ ] 测试: `plugins/tools/skein/scripts/tests/test_config_cli.py`
- [ ] 真值源: `CONFIG_DEFAULTS` (skein.py:162)
