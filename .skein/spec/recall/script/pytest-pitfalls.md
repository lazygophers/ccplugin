---
title: pytest-pitfalls
category: script
keywords: [pytest,tmp_path,测试,临时目录,豁免规则,假绿]
status: active
inclusion: auto
---

## pytest tmp_path 命名陷阱

### 触发场景
测试中使用 pytest 的 `tmp_path` fixture 时。

### 陷阱-正解
**陷阱**：`tmp_path` 生成的目录名固定形如 `test_<函数名>0`，含 `/test_` 子串，会命中其他规则（如 `flow_gate.cmd_flow_gate` 对测试路径的豁免规则）而静默放行，导致相关用例假绿/假空。
**正解**：用 `copytree` 或 `shutil` 把临时内容复制到不含 `test_` 的独立临时路径后再使用。

### 铁律
- MUST：若测试在真实路径上操作（如生成 `.gitignore`），不能直接用 `tmp_path`
- MUST：需要独立临时路径时，`copytree` 到不含 `test_` 的位置
- MUST：验收用例须覆盖路径依赖的检查

### 反例表
| 禁 | 改为 |
|---|---|
| 直接在 `tmp_path` 上生成衍生物进行校验 | 用 `copytree` 或 `tempfile.mkdtemp()` 到无 `test_` 前缀的路径 |
| 测试假绿（豁免规则静默放行） | 选择独立命名的临时目录，或在 setUp 剔除豁免规则的干扰 |

### 实现示例
```python
import tempfile
import shutil
import os

def test_something():
    # ❌ 不用 tmp_path 直接做
    # ❌ path = tmp_path / "config"
    
    # ✅ 用独立命名临时目录
    with tempfile.TemporaryDirectory(prefix='validate_') as tmpdir:
        # 做操作...
        pass
```
