"""Shared constants for CCPlugin scripts."""

LOADING_MESSAGES = [
    "🔍 正在搜索插件市场...",
    "📦 正在加载插件列表...",
    "🚀 正在获取最新数据...",
    "✨ 正在整理插件信息...",
    "🎯 正在匹配已安装插件...",
    "🌐 正在连接市场源...",
    "⚡ 正在加速数据传输...",
    "🔮 正在预测你的需求...",
    "🦄 正在召唤插件精灵...",
    "🌟 正在收集星光数据...",
    "🎭 正在准备精彩展示...",
    "🎪 正在搭建插件舞台...",
    "🔄 正在同步插件版本...",
    "💫 正在施展更新魔法...",
    "🎨 正在绘制更新蓝图...",
]

# Message status types
class MessageStatus:
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"

# Plugin scopes
class PluginScope:
    USER = "user"
    PROJECT = "project"
    UNKNOWN = "unknown"

# Progress animation constants
MESSAGE_CHANGE_PROBABILITY = 0.1
PROGRESS_THRESHOLD = 95
MIN_ADVANCE = 0.5
MAX_ADVANCE = 2.0
