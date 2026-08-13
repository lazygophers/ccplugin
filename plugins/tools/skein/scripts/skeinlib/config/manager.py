"""Config — config.yaml 读写 class。全部配置操作经此 class, 无散函数。

字段定义用 pydantic (类型 + 范围 + 默认值 + 说明一体化)。
YAML 解析用 PyYAML (yaml.safe_load / yaml.safe_dump)。
hooks 校验由 pydantic 模型完成。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

# ---- 配置结构定义 (pydantic BaseModel: 类型+范围+默认值+说明) ----

class PoolsConfig(BaseModel):
    """并发池上限。"""
    work: int = Field(default=2, ge=1, description="exec subtask 最大并发数")
    gate: int = Field(default=3, ge=1, description="check+finishing 阶段最大并发数")


class WorktreeConfig(BaseModel):
    """Git worktree 隔离配置。"""
    enabled: bool = Field(default=False, description="是否启用 per-task worktree 隔离")
    root: str = Field(default=".worktrees", description="worktree 存放目录 (相对仓库根)")


class WebConfig(BaseModel):
    """可视化看板 Web 服务配置。"""
    serve: bool = Field(default=True, description="是否启动 http 看板服务")
    board_open: bool = Field(default=True, description="启动时是否自动打开浏览器 (仅 tty 生效)")


class ConfirmConfig(BaseModel):
    """confirm 人审门配置。"""
    unattended: bool = Field(default=False, description=(
        "允许无人值守放行 confirm (cron/CI 场景)。开启后 `confirm --unattended` 免真人批准, "
        "confirmed_by 记 'unattended' 留痕; 默认 false —— 有人在的会话必须走真实用户批准"))


class SpecConfig(BaseModel):
    """Spec 注入预算配置 (字符数, 非 token)。"""
    core_budget: int = Field(default=400, ge=0, description="SessionStart 常驻注入预算")
    always_budget: int = Field(default=517, ge=0, description="每轮 prompt 常驻注入预算 (≈300 token)")


class HookEntry(BaseModel):
    """单个 hook 条目 — 一条 shell 命令 + 执行参数。"""
    model_config = {"extra": "forbid"}
    type: str = Field(default="command", description="条目类型 (目前仅 command)")
    command: str = Field(description="要执行的 shell 命令 (必填)")
    timeout: int = Field(default=60, gt=0, description="超时秒数, 缺省 60")
    continue_on_error: bool = Field(default=False, description="失败是否继续 (False=阻断, True=只告警)")
    cwd: str | None = Field(default=None, description="工作目录 (缺省=task 工作目录)")


class StageHooks(BaseModel):
    """阶段钩子 — before 失败阻断该阶段, after 失败只告警。"""
    before: list[HookEntry] = Field(default_factory=list, description="阶段开始前执行 (失败阻断)")
    after: list[HookEntry] = Field(default_factory=list, description="阶段结束后执行 (失败只告警)")


class AgentHooks(BaseModel):
    """agent 钩子 — start/stop 失败一律只告警不阻断 subtask。"""
    start: list[HookEntry] = Field(default_factory=list, description="agent 启动时执行")
    stop: list[HookEntry] = Field(default_factory=list, description="agent 停止时执行")


class HooksConfig(BaseModel):
    """hooks 完整结构 — 阶段钩子 + subtask 事件钩子 + agent 钩子。

    合法 scope = STAGE_NAMES (8 个阶段 + 3 个 subtask 事件)。
    agent 钩子键名是动态 agent 名 (如 skein-executor), 值为 AgentHooks。
    """
    # 阶段钩子
    create: StageHooks = Field(default_factory=StageHooks)
    confirm: StageHooks = Field(default_factory=StageHooks)
    research: StageHooks = Field(default_factory=StageHooks)
    plan: StageHooks = Field(default_factory=StageHooks)
    exec: StageHooks = Field(default_factory=StageHooks)
    check: StageHooks = Field(default_factory=StageHooks)
    finishing: StageHooks = Field(default_factory=StageHooks)
    finish: StageHooks = Field(default_factory=StageHooks)
    # subtask 事件钩子
    subtask_start: StageHooks = Field(default_factory=StageHooks, alias="subtask.start", description="subtask 启动时")
    subtask_done: StageHooks = Field(default_factory=StageHooks, alias="subtask.done", description="subtask 完成时")
    subtask_fail: StageHooks = Field(default_factory=StageHooks, alias="subtask.fail", description="subtask 失败时")
    # agent 钩子 — 键名是动态 agent 名 (如 skein-executor)
    agent: dict[str, AgentHooks] = Field(default_factory=dict, description="agent 钩子 (键=agent 名)")

    model_config = {"populate_by_name": True, "extra": "forbid"}


# 合法阶段键 (校验用): python 名 + 点号 alias 都收; 排除 agent —— 它是 agent 钩子命名空间不是阶段
LEGAL_HOOK_STAGES: set[str] = {n for n in HooksConfig.model_fields if n != "agent"} | {
    i.alias for i in HooksConfig.model_fields.values() if i.alias}
# 展示用: 每个阶段只出一次, 有 alias 取点号形式 (报错列表里 subtask_done/subtask.done 不重复列)
HOOK_STAGE_DISPLAY: list[str] = sorted(
    (i.alias or n) for n, i in HooksConfig.model_fields.items() if n != "agent")


class ConfigData(BaseModel):
    """config.yaml 完整结构 — config.yaml 的单一类型契约。

    每个字段对应 config.yaml 的一个顶层键。
    缺键时由 pydantic Field default 回填。
    """
    auto_commit: bool = Field(default=True, description="是否自动 commit 改动 (worktree 模式下强制 True)")
    retain_days: int = Field(default=7, ge=-1, description="完成 task 保留天数, 超期自动归档; -1=永不归档")
    pools: PoolsConfig = Field(default_factory=PoolsConfig)
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    spec: SpecConfig = Field(default_factory=SpecConfig)
    confirm: ConfirmConfig = Field(default_factory=ConfirmConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig, description="hooks 配置 (阶段+agent 钩子)")


class Config:
    """config.yaml 读写 class。

    全部配置操作: 读盘/写盘/点号取值/点号设值。
    YAML 解析用 PyYAML; 配置结构由 pydantic 校验。
    """

    # ---- 类级字段 ----
    _path: Path
    _cfg: ConfigData              # 生效配置 (pydantic 校验后的完整结构)
    _validation_error: str | None = None  # 校验错误 (hooks 非法键等, 供 doctor 检测)

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._validation_error = None
        self.reload()

    # ---- 读 ----

    def reload(self) -> ConfigData:
        """读盘 → pydantic 校验+补默认值 → 缓存。文件不存在或缺失键时回写。"""
        if self._path.exists():
            result = yaml.safe_load(self._path.read_text(encoding="utf-8"))
            raw = result if isinstance(result, dict) else {}
            try:
                self._cfg = ConfigData.model_validate(raw)
                self._validation_error = None
            except Exception as e:
                # hooks 非法键/未知字段 → 只降级 hooks 段, 其余顶层键 (pools/worktree/...) 保原值。
                # 整份回默认会让一个笔误的 hook 键静默清空全部配置。
                self._validation_error = str(e)
                try:
                    self._cfg = ConfigData.model_validate({**raw, "hooks": {}})
                except Exception:
                    self._cfg = ConfigData()  # hooks 之外也有错 → 才整份降级
            # 缺失顶层键 → pydantic 补了默认值 → 回写盘保持文件完整。
            # 校验失败时禁回写: 生效配置是降级值, 写回去等于拿默认值覆盖用户原文件。
            if raw and not self._validation_error and not raw.keys() >= {f for f in ConfigData.model_fields}:
                self._write()
        else:
            self._cfg = ConfigData()
            self._write()
        return self._cfg

    @property
    def cfg(self) -> ConfigData:
        """生效配置 (pydantic model, 只读访问)。"""
        return self._cfg

    # ---- 写 ----

    def set(self, path: str, val: Any) -> None:
        """点号路径设值 → pydantic 校验 → 写盘。"""
        parts = path.split(".")
        node: Any = self._cfg
        for p in parts[:-1]:
            node = getattr(node, p)
        # str → 类型转换 (CLI 传入均为 str, pydantic 不在 setattr 时自动转换)
        field_info = type(node).model_fields[parts[-1]]
        ann = field_info.annotation
        if ann is bool:
            val = str(val).strip().lower() in ("true", "1", "yes", "on")
        elif ann is int:
            val = int(val)
        setattr(node, parts[-1], val)
        # pydantic 重新校验
        self._cfg = ConfigData.model_validate(self._cfg.model_dump(by_alias=True))
        self._write()

    def reset(self) -> None:
        """重置为默认值 (ConfigData defaults) → 写盘。"""
        self._cfg = ConfigData()
        self._write()

    # ---- 查询 ----

    def get(self, path: str) -> Any:
        """点号路径取生效值。"""
        node: Any = self._cfg
        for p in path.split("."):
            node = getattr(node, p)
        return node

    # ---- 内部 ----

    @staticmethod
    def yaml_load(text: str) -> dict[str, Any]:
        """YAML 文本 → dict (无校验, 纯解析)。"""
        result = yaml.safe_load(text)
        return result if isinstance(result, dict) else {}

    @staticmethod
    def yaml_dump(data: dict[str, Any]) -> str:
        """dict → YAML 文本 (无校验, 纯序列化)。"""
        return str(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False))

    def _write(self) -> None:
        """序列化 _cfg → 写盘。"""
        self._path.write_text(
            yaml.safe_dump(self._cfg.model_dump(by_alias=True), sort_keys=False, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
