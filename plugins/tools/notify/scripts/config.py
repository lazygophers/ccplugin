"""
Claude Code Hooks 配置管理模块

支持的 Hook 事件:
- stop: 主 Agent 完成时
- subagent_stop: Task 子代理完成时
- pre_tool_use: 工具调用前
- post_tool_use: 工具调用后
- permission_request: 权限请求时
- user_prompt_submit: 用户提交提示前
- notification: 通知显示时
- session_start: 会话启动/恢复时
- session_end: 会话结束时
- pre_compact: 会话压缩前

配置文件位置: ~/.lazygophers/ccplugin/notify/config.yaml
"""

import os
import os.path
from dataclasses import asdict, dataclass, field
from typing import Dict, Optional


@dataclass
class HookConfig:
    """单个 Hook 配置项

    示例:
            HookConfig(enabled=False, play_sound=False, message="操作完成")
    """

    enabled: bool = False
    play_sound: bool = False
    message: Optional[str] = None

    def validate(self) -> bool:
        """验证配置有效性"""
        if not isinstance(self.enabled, bool):
            raise ValueError(f"enabled 必须是 bool 类型，得到 {type(self.enabled)}")

        if not isinstance(self.play_sound, bool):
            raise ValueError(
                f"play_sound 必须是 bool 类型，得到 {type(self.play_sound)}"
            )

        if self.message is not None and not isinstance(self.message, str):
            raise ValueError(
                f"message 必须是 str 类型或 None，得到 {type(self.message)}"
            )

        return True


@dataclass
class ToolSpecificHookConfig:
    """工具特定的 Hook 配置"""

    write: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 准备写入文件 {{ file_path }}"
        )
    )
    edit: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 准备编辑文件 {{ file_path }}"
        )
    )
    read: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 准备读取文件 {{ file_path }}"
        )
    )
    bash: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 准备执行命令")
    )
    task: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 准备创建任务")
    )
    webfetch: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 准备获取网页")
    )
    websearch: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 准备搜索网页")
    )
    askuserquestion: HookConfig = field(
        default_factory=lambda: HookConfig(
            enabled=True, play_sound=True, message="{{ project_name }} 有问题需要你解决"
        )
    )

    def validate(self) -> bool:
        """验证所有工具配置"""
        for tool in [
            "write",
            "edit",
            "read",
            "bash",
            "task",
            "webfetch",
            "websearch",
            "askuserquestion",
        ]:
            getattr(self, tool).validate()
        return True


@dataclass
class NotificationTypeHookConfig:
    """通知类型 Hook 配置"""

    permission_prompt: HookConfig = field(
        default_factory=lambda: HookConfig(
            enabled=True, play_sound=True, message="权限请求: {{ message }}"
        )
    )
    idle_prompt: HookConfig = field(
        default_factory=lambda: HookConfig(message="等待输入: {{ message }}")
    )
    auth_success: HookConfig = field(
        default_factory=lambda: HookConfig(message="认证成功: {{ message }}")
    )
    elicitation_dialog: HookConfig = field(
        default_factory=lambda: HookConfig(message="工具引出: {{ message }}")
    )
    elicitation_complete: HookConfig = field(
        default_factory=lambda: HookConfig(message="工具引出完成: {{ message }}")
    )
    elicitation_response: HookConfig = field(
        default_factory=lambda: HookConfig(message="工具引出响应: {{ message }}")
    )

    def validate(self) -> bool:
        """验证所有通知类型配置"""
        for notification_type in [
            "permission_prompt",
            "idle_prompt",
            "auth_success",
            "elicitation_dialog",
        ]:
            getattr(self, notification_type).validate()
        return True


@dataclass
class SessionStartHookConfig:
    """SessionStart Hook 配置"""

    startup: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 新会话")
    )
    resume: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 会话恢复")
    )
    clear: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 会话清空")
    )
    compact: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 会话压缩")
    )

    def validate(self) -> bool:
        """验证所有启动场景配置"""
        for scenario in ["startup", "resume", "clear", "compact"]:
            getattr(self, scenario).validate()
        return True


@dataclass
class SessionEndHookConfig:
    """SessionEnd Hook 配置"""

    clear: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 会话清除")
    )
    logout: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 用户注销")
    )
    prompt_input_exit: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 用户退出")
    )
    bypass_permissions_disabled: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 绕过权限禁用")
    )
    other: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 会话结束")
    )

    def validate(self) -> bool:
        """验证所有退出原因配置"""
        for reason in ["clear", "logout", "prompt_input_exit", "other"]:
            getattr(self, reason).validate()
        return True


@dataclass
class PreCompactHookConfig:
    """PreCompact Hook 配置"""

    manual: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 手动压缩启动")
    )
    auto: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 自动压缩启动")
    )

    def validate(self) -> bool:
        """验证所有压缩触发方式配置"""
        for trigger in ["manual", "auto"]:
            getattr(self, trigger).validate()
        return True


@dataclass
class PostCompactHookConfig:
    """PostCompact Hook 配置"""

    manual: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 手动压缩完成")
    )
    auto: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 自动压缩完成")
    )

    def validate(self) -> bool:
        """验证所有压缩触发方式配置"""
        for trigger in ["manual", "auto"]:
            getattr(self, trigger).validate()
        return True


@dataclass
class HooksConfig:
    """完整的 Claude Code Hooks 配置"""

    stop: HookConfig = field(
        default_factory=lambda: HookConfig(
            enabled=True, play_sound=True, message="{{ project_name }} 任务已完成"
        )
    )
    pre_tool_use: ToolSpecificHookConfig = field(default_factory=ToolSpecificHookConfig)
    post_tool_use: ToolSpecificHookConfig = field(
        default_factory=ToolSpecificHookConfig
    )
    permission_request: HookConfig = field(
        default_factory=lambda: HookConfig(
            enabled=True,
            play_sound=True,
            message="{{ project_name }} 请求权限 ({{ tool_name }})",
        )
    )
    user_prompt_submit: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 收到用户输入")
    )
    notification: NotificationTypeHookConfig = field(
        default_factory=NotificationTypeHookConfig
    )
    session_start: SessionStartHookConfig = field(
        default_factory=SessionStartHookConfig
    )
    session_end: SessionEndHookConfig = field(default_factory=SessionEndHookConfig)
    pre_compact: PreCompactHookConfig = field(default_factory=PreCompactHookConfig)
    post_compact: PostCompactHookConfig = field(default_factory=PostCompactHookConfig)
    post_tool_use_failure: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 工具 {{ tool_name }} 失败: {{ error }}"
        )
    )
    subagent_start: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 子代理 {{ agent_type }} 启动"
        )
    )
    subagent_stop: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 子代理 {{ agent_type }} 完成"
        )
    )
    stop_failure: HookConfig = field(
        default_factory=lambda: HookConfig(
            enabled=True,
            play_sound=True,
            message="{{ project_name }} API 错误: {{ error }}",
        )
    )
    teammate_idle: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 队友 {{ teammate_name }} 空闲"
        )
    )
    task_completed: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 任务完成: {{ task_subject }}"
        )
    )
    task_created: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 任务创建: {{ task_subject }}"
        )
    )
    instructions_loaded: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 指令加载: {{ file_path }} ({{ load_reason }})"
        )
    )
    config_change: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 配置变更: {{ source }}"
        )
    )
    cwd_changed: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 工作目录变更")
    )
    file_changed: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 文件变更: {{ file_path }} ({{ event }})"
        )
    )
    worktree_create: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} Worktree 创建: {{ name }}"
        )
    )
    worktree_remove: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} Worktree 移除: {{ worktree_path }}"
        )
    )
    message_display: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 消息显示")
    )
    post_tool_batch: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 工具批次完成 ({{ tool_calls|length }} 个工具)"
        )
    )
    permission_denied: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 权限被拒绝: {{ tool_name }} - {{ reason }}"
        )
    )
    user_prompt_expansion: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} 命令展开: /{{ command_name }}"
        )
    )
    elicitation: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} MCP 请求输入: {{ mcp_server_name }} - {{ message }}"
        )
    )
    elicitation_result: HookConfig = field(
        default_factory=lambda: HookConfig(
            message="{{ project_name }} MCP 响应: {{ mcp_server_name }} - {{ action }}"
        )
    )
    setup: HookConfig = field(
        default_factory=lambda: HookConfig(message="{{ project_name }} 初始化")
    )

    def validate(self) -> bool:
        """验证所有配置有效性"""
        self.stop.validate()
        self.pre_tool_use.validate()
        self.post_tool_use.validate()
        self.permission_request.validate()
        self.user_prompt_submit.validate()
        self.notification.validate()
        self.session_start.validate()
        self.session_end.validate()
        self.pre_compact.validate()
        self.post_compact.validate()
        self.post_tool_use_failure.validate()
        self.subagent_start.validate()
        self.subagent_stop.validate()
        self.stop_failure.validate()
        self.teammate_idle.validate()
        self.task_completed.validate()
        self.task_created.validate()
        self.instructions_loaded.validate()
        self.config_change.validate()
        self.cwd_changed.validate()
        self.file_changed.validate()
        self.worktree_create.validate()
        self.worktree_remove.validate()
        self.message_display.validate()
        self.post_tool_batch.validate()
        self.permission_denied.validate()
        self.user_prompt_expansion.validate()
        self.elicitation.validate()
        self.elicitation_result.validate()
        self.setup.validate()
        return True

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "HooksConfig":
        """从字典加载配置

        Args:
                config_dict: 配置字典（通常来自 YAML 解析）

        Returns:
                HooksConfig 实例

        Raises:
                ValueError: 配置数据无效
        """
        hooks_data = config_dict.get("hooks", {})

        def load_hook_config(
            data: Optional[Dict], default: Optional[HookConfig] = None
        ) -> HookConfig:
            """加载单个 Hook 配置，使用默认值填充未指定的字段"""
            if not data:
                return default if default is not None else HookConfig()
            enabled = data.get("enabled")
            play_sound = data.get("play_sound")
            message = data.get("message")
            return HookConfig(
                enabled=default.enabled if enabled is None and default else False,
                play_sound=default.play_sound if play_sound is None and default else False,
                message=default.message if message is None and default else message,
            )

        def load_tool_specific_config(
            data: Optional[Dict], defaults: ToolSpecificHookConfig
        ) -> ToolSpecificHookConfig:
            """加载工具特定配置"""
            if not data:
                return defaults
            return ToolSpecificHookConfig(
                write=load_hook_config(data.get("write"), defaults.write),
                edit=load_hook_config(data.get("edit"), defaults.edit),
                read=load_hook_config(data.get("read"), defaults.read),
                bash=load_hook_config(data.get("bash"), defaults.bash),
                task=load_hook_config(data.get("task"), defaults.task),
                webfetch=load_hook_config(data.get("webfetch"), defaults.webfetch),
                websearch=load_hook_config(data.get("websearch"), defaults.websearch),
                askuserquestion=load_hook_config(
                    data.get("askuserquestion"), defaults.askuserquestion
                ),
            )

        def load_notification_config(
            data: Optional[Dict], defaults: NotificationTypeHookConfig
        ) -> NotificationTypeHookConfig:
            """加载通知类型配置"""
            if not data:
                return defaults
            return NotificationTypeHookConfig(
                permission_prompt=load_hook_config(
                    data.get("permission_prompt"), defaults.permission_prompt
                ),
                idle_prompt=load_hook_config(data.get("idle_prompt"), defaults.idle_prompt),
                auth_success=load_hook_config(
                    data.get("auth_success"), defaults.auth_success
                ),
                elicitation_dialog=load_hook_config(
                    data.get("elicitation_dialog"), defaults.elicitation_dialog
                ),
                elicitation_complete=load_hook_config(
                    data.get("elicitation_complete"), defaults.elicitation_complete
                ),
                elicitation_response=load_hook_config(
                    data.get("elicitation_response"), defaults.elicitation_response
                ),
            )

        def load_session_start_config(
            data: Optional[Dict], defaults: SessionStartHookConfig
        ) -> SessionStartHookConfig:
            """加载 SessionStart 配置"""
            if not data:
                return defaults
            return SessionStartHookConfig(
                startup=load_hook_config(data.get("startup"), defaults.startup),
                resume=load_hook_config(data.get("resume"), defaults.resume),
                clear=load_hook_config(data.get("clear"), defaults.clear),
                compact=load_hook_config(data.get("compact"), defaults.compact),
            )

        def load_session_end_config(
            data: Optional[Dict], defaults: SessionEndHookConfig
        ) -> SessionEndHookConfig:
            """加载 SessionEnd 配置"""
            if not data:
                return defaults
            return SessionEndHookConfig(
                clear=load_hook_config(data.get("clear"), defaults.clear),
                logout=load_hook_config(data.get("logout"), defaults.logout),
                prompt_input_exit=load_hook_config(
                    data.get("prompt_input_exit"), defaults.prompt_input_exit
                ),
                other=load_hook_config(data.get("other"), defaults.other),
            )

        def load_pre_compact_config(
            data: Optional[Dict], defaults: PreCompactHookConfig
        ) -> PreCompactHookConfig:
            """加载 PreCompact 配置"""
            if not data:
                return defaults
            return PreCompactHookConfig(
                manual=load_hook_config(data.get("manual"), defaults.manual),
                auto=load_hook_config(data.get("auto"), defaults.auto),
            )

        def load_post_compact_config(
            data: Optional[Dict], defaults: PostCompactHookConfig
        ) -> PostCompactHookConfig:
            """加载 PostCompact 配置"""
            if not data:
                return defaults
            return PostCompactHookConfig(
                manual=load_hook_config(data.get("manual"), defaults.manual),
                auto=load_hook_config(data.get("auto"), defaults.auto),
            )

        defaults = cls()
        return cls(
            stop=load_hook_config(hooks_data.get("stop"), defaults.stop),
            pre_tool_use=load_tool_specific_config(
                hooks_data.get("pre_tool_use"), defaults.pre_tool_use
            ),
            post_tool_use=load_tool_specific_config(
                hooks_data.get("post_tool_use"), defaults.post_tool_use
            ),
            permission_request=load_hook_config(
                hooks_data.get("permission_request"), defaults.permission_request
            ),
            user_prompt_submit=load_hook_config(
                hooks_data.get("user_prompt_submit"), defaults.user_prompt_submit
            ),
            notification=load_notification_config(
                hooks_data.get("notification"), defaults.notification
            ),
            session_start=load_session_start_config(
                hooks_data.get("session_start"), defaults.session_start
            ),
            session_end=load_session_end_config(
                hooks_data.get("session_end"), defaults.session_end
            ),
            pre_compact=load_pre_compact_config(
                hooks_data.get("pre_compact"), defaults.pre_compact
            ),
            post_compact=load_post_compact_config(
                hooks_data.get("post_compact"), defaults.post_compact
            ),
            post_tool_use_failure=load_hook_config(
                hooks_data.get("post_tool_use_failure"), defaults.post_tool_use_failure
            ),
            subagent_start=load_hook_config(
                hooks_data.get("subagent_start"), defaults.subagent_start
            ),
            subagent_stop=load_hook_config(
                hooks_data.get("subagent_stop"), defaults.subagent_stop
            ),
            stop_failure=load_hook_config(
                hooks_data.get("stop_failure"), defaults.stop_failure
            ),
            teammate_idle=load_hook_config(
                hooks_data.get("teammate_idle"), defaults.teammate_idle
            ),
            task_completed=load_hook_config(
                hooks_data.get("task_completed"), defaults.task_completed
            ),
            task_created=load_hook_config(
                hooks_data.get("task_created"), defaults.task_created
            ),
            instructions_loaded=load_hook_config(
                hooks_data.get("instructions_loaded"), defaults.instructions_loaded
            ),
            config_change=load_hook_config(
                hooks_data.get("config_change"), defaults.config_change
            ),
            cwd_changed=load_hook_config(
                hooks_data.get("cwd_changed"), defaults.cwd_changed
            ),
            file_changed=load_hook_config(
                hooks_data.get("file_changed"), defaults.file_changed
            ),
            worktree_create=load_hook_config(
                hooks_data.get("worktree_create"), defaults.worktree_create
            ),
            worktree_remove=load_hook_config(
                hooks_data.get("worktree_remove"), defaults.worktree_remove
            ),
            message_display=load_hook_config(
                hooks_data.get("message_display"), defaults.message_display
            ),
            post_tool_batch=load_hook_config(
                hooks_data.get("post_tool_batch"), defaults.post_tool_batch
            ),
            permission_denied=load_hook_config(
                hooks_data.get("permission_denied"), defaults.permission_denied
            ),
            user_prompt_expansion=load_hook_config(
                hooks_data.get("user_prompt_expansion"), defaults.user_prompt_expansion
            ),
            elicitation=load_hook_config(
                hooks_data.get("elicitation"), defaults.elicitation
            ),
            elicitation_result=load_hook_config(
                hooks_data.get("elicitation_result"), defaults.elicitation_result
            ),
            setup=load_hook_config(hooks_data.get("setup"), defaults.setup),
        )

    @classmethod
    def load_from_file(cls, config_path: str) -> "HooksConfig":
        """从 YAML 文件加载配置

        Args:
                config_path: YAML 配置文件路径

        Returns:
                HooksConfig 实例

        Raises:
                FileNotFoundError: 配置文件不存在
                yaml.YAMLError: YAML 解析错误
                ValueError: 配置数据无效
        """
        import yaml

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

        config = cls.from_dict(config_dict)
        config.validate()
        return config

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {"hooks": asdict(self)}


# 默认配置实例
DEFAULT_CONFIG = HooksConfig()


def get_default_config() -> HooksConfig:
    """获取默认配置"""
    return HooksConfig()


def load_config() -> HooksConfig:
    """加载配置（仅从用户主目录）

    读取路径: ~/.lazygophers/ccplugin/notify/config.yaml
    不存在则返回默认配置。

    Returns:
            HooksConfig 实例
    """
    home_config_path = os.path.join(
        os.path.expanduser("~"), ".lazygophers", "ccplugin", "notify", "config.yaml"
    )

    if os.path.exists(home_config_path):
        try:
            return HooksConfig.load_from_file(home_config_path)
        except Exception:
            pass

    return get_default_config()
