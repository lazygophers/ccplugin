"""Hook 数据加载工具"""

import json
import os.path
import sys
from typing import Any, Dict


def load_hooks() -> Dict[str, Any]:
    """从 stdin 读取 Hook JSON 数据"""
    try:
        hook_data = json.load(sys.stdin)
        if not isinstance(hook_data, dict):
            raise ValueError("Hook 数据必须是 JSON 对象")
        return hook_data
    except json.JSONDecodeError:
        sys.exit(1)
    except ValueError:
        sys.exit(1)
    except Exception:
        sys.exit(1)
