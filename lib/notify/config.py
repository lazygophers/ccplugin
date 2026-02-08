"""
通知模块配置管理

提供音色配置、通知配置的数据类和配置文件加载/保存功能。
配置存储位置: ~/.lazygophers/ccplugin/notify/config.yaml
"""

import os
import os.path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lib.logging import info, warn, error


# 默认数据目录
NOTIFY_DATA_DIR = "~/.lazygophers/ccplugin/notify"


@dataclass
class VoiceSample:
    """语音样本信息

    Attributes:
        path: 音频文件路径
        duration: 音频时长（秒）
        added_at: 添加时间戳
        sample_rate: 采样率
    """

    path: str
    duration: float = 0.0
    sample_rate: int = 22050
    added_at: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class TrainingRecord:
    """训练记录

    Attributes:
        timestamp: 训练时间戳
        epochs: 训练轮数
        samples_count: 使用的样本数量
        loss: 最终损失值（可选）
        method: 训练方法（reference, finetune）
    """

    timestamp: float = field(default_factory=lambda: __import__("time").time())
    epochs: int = 0
    samples_count: int = 0
    loss: Optional[float] = None
    method: str = "reference"


@dataclass
class VoiceConfig:
    """音色配置

    Attributes:
        id: 音色唯一标识
        name: 音色名称（用户友好）
        engine: 引擎类型: "coqui", "system"
        model_name: Coqui 模型名称（如 tts_models/multilingual/multi-dataset/xtts_v2）
        language: 语言代码（zh, en, ja, ko 等）
        speed: 语速倍率（0.5-2.0）
        pitch: 音调倍率（0.5-2.0）
        speaker_wav: 参考音频路径（用于声音克隆）
        is_cloned: 是否为克隆音色
        created_at: 创建时间戳
        samples: 样本列表
        training_history: 训练历史记录
        checkpoint_path: 微调检查点路径（如果进行了深度微调）
    """

    id: str
    name: str
    engine: str = "coqui"
    model_name: Optional[str] = None
    language: str = "zh"
    speed: float = 1.0
    pitch: float = 1.0
    speaker_wav: Optional[str] = None
    is_cloned: bool = False
    created_at: float = field(default_factory=lambda: __import__("time").time())
    samples: List[VoiceSample] = field(default_factory=list)
    training_history: List[TrainingRecord] = field(default_factory=list)
    checkpoint_path: Optional[str] = None

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.id or not isinstance(self.id, str):
            error(f"VoiceConfig.id 必须是非空字符串，得到: {self.id}")
            return False
        if not self.name or not isinstance(self.name, str):
            error(f"VoiceConfig.name 必须是非空字符串，得到: {self.name}")
            return False
        if self.engine not in ["coqui", "system"]:
            error(f"VoiceConfig.engine 必须是 'coqui' 或 'system'，得到: {self.engine}")
            return False
        if self.speed < 0.1 or self.speed > 3.0:
            error(f"VoiceConfig.speed 必须在 0.1-3.0 范围，得到: {self.speed}")
            return False
        if self.pitch < 0.1 or self.pitch > 3.0:
            error(f"VoiceConfig.pitch 必须在 0.1-3.0 范围，得到: {self.pitch}")
            return False
        return True


@dataclass
class NotifyConfig:
    """完整通知配置

    Attributes:
        default_voice_id: 默认音色 ID
        voices: 所有可用音色字典
        system_notification: 是否启用系统通知
        tts_enabled: 是否启用 TTS 语音播报
        tts_engine: TTS 引擎类型
        language: 默认语言
        auto_download: 是否自动下载模型
    """

    default_voice_id: Optional[str] = None
    voices: Dict[str, VoiceConfig] = field(default_factory=dict)
    system_notification: bool = True
    tts_enabled: bool = True
    tts_engine: str = "coqui"
    language: str = "zh"
    auto_download: bool = True

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.default_voice_id and self.default_voice_id not in self.voices:
            warn(f"默认音色 ID '{self.default_voice_id}' 不在 voices 字典中")
        for voice_id, voice in self.voices.items():
            if not voice.validate():
                return False
        return True

    def to_dict(self) -> Dict:
        """转换为字典格式（排除 None 值和内部字段）"""
        result = {
            "default_voice_id": self.default_voice_id,
            "system_notification": self.system_notification,
            "tts_enabled": self.tts_enabled,
            "tts_engine": self.tts_engine,
            "language": self.language,
            "auto_download": self.auto_download,
            "voices": {},
        }
        for voice_id, voice in self.voices.items():
            # 序列化 samples
            samples_data = []
            for sample in voice.samples:
                samples_data.append(
                    {
                        "path": sample.path,
                        "duration": sample.duration,
                        "sample_rate": sample.sample_rate,
                        "added_at": sample.added_at,
                    }
                )

            # 序列化 training_history
            history_data = []
            for record in voice.training_history:
                history_data.append(
                    {
                        "timestamp": record.timestamp,
                        "epochs": record.epochs,
                        "samples_count": record.samples_count,
                        "loss": record.loss,
                        "method": record.method,
                    }
                )

            result["voices"][voice_id] = {
                "id": voice.id,
                "name": voice.name,
                "engine": voice.engine,
                "model_name": voice.model_name,
                "language": voice.language,
                "speed": voice.speed,
                "pitch": voice.pitch,
                "speaker_wav": voice.speaker_wav,
                "is_cloned": voice.is_cloned,
                "created_at": voice.created_at,
                "samples": samples_data,
                "training_history": history_data,
                "checkpoint_path": voice.checkpoint_path,
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "NotifyConfig":
        """从字典加载配置"""
        if not data:
            return cls()

        voices = {}
        voices_data = data.get("voices", {})
        for voice_id, voice_info in voices_data.items():
            # 反序列化 samples
            samples = []
            samples_data = voice_info.get("samples", [])
            for sample_data in samples_data:
                samples.append(
                    VoiceSample(
                        path=sample_data.get("path", ""),
                        duration=sample_data.get("duration", 0.0),
                        sample_rate=sample_data.get("sample_rate", 22050),
                        added_at=sample_data.get("added_at", __import__("time").time()),
                    )
                )

            # 反序列化 training_history
            history = []
            history_data = voice_info.get("training_history", [])
            for record_data in history_data:
                history.append(
                    TrainingRecord(
                        timestamp=record_data.get(
                            "timestamp", __import__("time").time()
                        ),
                        epochs=record_data.get("epochs", 0),
                        samples_count=record_data.get("samples_count", 0),
                        loss=record_data.get("loss"),
                        method=record_data.get("method", "reference"),
                    )
                )

            voices[voice_id] = VoiceConfig(
                id=voice_info.get("id", voice_id),
                name=voice_info.get("name", voice_id),
                engine=voice_info.get("engine", "coqui"),
                model_name=voice_info.get("model_name"),
                language=voice_info.get("language", "zh"),
                speed=voice_info.get("speed", 1.0),
                pitch=voice_info.get("pitch", 1.0),
                speaker_wav=voice_info.get("speaker_wav"),
                is_cloned=voice_info.get("is_cloned", False),
                created_at=voice_info.get("created_at", __import__("time").time()),
                samples=samples,
                training_history=history,
                checkpoint_path=voice_info.get("checkpoint_path"),
            )

        return cls(
            default_voice_id=data.get("default_voice_id"),
            system_notification=data.get("system_notification", True),
            tts_enabled=data.get("tts_enabled", True),
            tts_engine=data.get("tts_engine", "coqui"),
            language=data.get("language", "zh"),
            auto_download=data.get("auto_download", True),
            voices=voices,
        )


def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.expanduser(f"{NOTIFY_DATA_DIR}/config.yaml")


def get_voices_dir() -> str:
    """获取克隆音色存储目录"""
    return os.path.expanduser(f"{NOTIFY_DATA_DIR}/voices")


def get_default_config() -> NotifyConfig:
    """获取默认配置"""
    return NotifyConfig()


def load_config(config_path: Optional[str] = None) -> NotifyConfig:
    """加载配置文件

    Args:
        config_path: 配置文件路径，如果为 None 则使用默认路径

    Returns:
        NotifyConfig 实例
    """
    if config_path is None:
        config_path = get_config_path()

    if not os.path.exists(config_path):
        info(f"配置文件不存在，将使用默认配置: {config_path}")
        return get_default_config()

    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = NotifyConfig.from_dict(data)
        info(f"加载通知配置成功: {config_path}")
        return config
    except yaml.YAMLError as e:
        error(f"YAML 解析错误: {e}")
        return get_default_config()
    except Exception as e:
        error(f"加载配置文件失败: {e}")
        return get_default_config()


def save_config(config: NotifyConfig, config_path: Optional[str] = None) -> bool:
    """保存配置文件

    Args:
        config: NotifyConfig 实例
        config_path: 配置文件路径，如果为 None 则使用默认路径

    Returns:
        保存成功返回 True
    """
    if config_path is None:
        config_path = get_config_path()

    try:
        config_dir = os.path.dirname(config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        import yaml

        data = config.to_dict()

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

        info(f"保存通知配置成功: {config_path}")
        return True
    except Exception as e:
        error(f"保存配置文件失败: {e}")
        return False


def list_voices(config: Optional[NotifyConfig] = None) -> List[VoiceConfig]:
    """列出所有可用音色

    Args:
        config: NotifyConfig 实例，如果为 None 则自动加载

    Returns:
        VoiceConfig 列表
    """
    if config is None:
        config = load_config()
    return list(config.voices.values())


def get_voice(config: NotifyConfig, voice_id: str) -> Optional[VoiceConfig]:
    """获取指定音色配置

    Args:
        config: NotifyConfig 实例
        voice_id: 音色 ID

    Returns:
        VoiceConfig 或 None（如果不存在）
    """
    return config.voices.get(voice_id)


def add_voice(config: NotifyConfig, voice: VoiceConfig) -> bool:
    """添加或更新音色配置

    Args:
        config: NotifyConfig 实例
        voice: VoiceConfig 实例

    Returns:
        添加成功返回 True
    """
    if not voice.validate():
        return False
    config.voices[voice.id] = voice
    return True


def remove_voice(config: NotifyConfig, voice_id: str) -> bool:
    """删除音色配置

    Args:
        config: NotifyConfig 实例
        voice_id: 音色 ID

    Returns:
        删除成功返回 True
    """
    if voice_id in config.voices:
        del config.voices[voice_id]
        # 如果删除的是默认音色，清除默认值
        if config.default_voice_id == voice_id:
            config.default_voice_id = None
        return True
    return False


def set_default_voice(config: NotifyConfig, voice_id: str) -> bool:
    """设置默认音色

    Args:
        config: NotifyConfig 实例
        voice_id: 音色 ID

    Returns:
        设置成功返回 True
    """
    if voice_id in config.voices or voice_id is None:
        config.default_voice_id = voice_id
        return True
    return False
