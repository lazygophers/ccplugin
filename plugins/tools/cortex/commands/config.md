---
description: 查看/编辑 cortex 配置 (~/.cortex/config.json) (无入参 → 列当前)
---

# /cortex:config

[AUTO_MODE strict: 禁询问, fail-fast, 仅列不改]

读取并展示 cortex 配置。

**必须**用 Bash 工具执行:

```bash
INSTALL_PATH="$(jq -r .install_path ~/.cortex/config.json)"
python3 "$INSTALL_PATH/scripts/cortex_config.py"
```

输出: 当前 `~/.cortex/config.json` 解析结果 (vault / lang / settings / install_path / timeout_default 等)。

若 config 不存在, 提示用户跑 `install.sh` 初始化。
