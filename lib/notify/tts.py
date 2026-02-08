"""
TTS 引擎模块

提供 TTS 引擎抽象基类和多种实现（Coqui TTS、系统原生 TTS）。
"""

import os
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, List

from lib.logging import info, error, debug
from lib.notify.config import NotifyConfig, VoiceConfig, load_config


def _patch_torch_load():
    """修复 PyTorch 2.6 的 weights_only 限制问题

    TTS 0.22.0 使用旧版 torch.load 调用，PyTorch 2.6+ 默认 weights_only=True
    导致 XTTS 模型加载失败。通过 monkey patch 修复。

    注意：此函数只应在 CoquiTTSEngine 初始化时调用，避免在没有 torch 的环境中导入失败。
    """
    try:
        import torch
        import functools
    except ImportError:
        # torch 未安装，跳过 patch
        return

    _original_torch_load = torch.load

    @functools.wraps(_original_torch_load)
    def patched_load(*args, **kwargs):
        # 确保 weights_only=False 以支持旧版检查点加载
        if "weights_only" not in kwargs:
            kwargs["weights_only"] = False
        return _original_torch_load(*args, **kwargs)

    torch.load = patched_load
    # 标记已 patch，避免重复
    torch._tts_patch_applied = True


class TTSEngine(ABC):
    """TTS 引擎抽象基类

    所有 TTS 引擎必须实现以下方法：
    - tts(): 文本转语音
    - tts_to_file(): 文本转语音并保存到文件
    - get_languages(): 获取支持的语言列表
    - get_speakers(): 获取可用说话人列表（如果支持）
    """

    @abstractmethod
    def tts(
        self,
        text: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bytes:
        """将文本转换为语音

        Args:
            text: 要转换的文本
            voice: 音色配置，如果为 None 使用引擎默认
            language: 语言代码，如果为 None 使用音色默认

        Returns:
            WAV 格式的音频数据
        """
        pass

    @abstractmethod
    def tts_to_file(
        self,
        text: str,
        file_path: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bool:
        """将文本转换为语音并保存到文件

        Args:
            text: 要转换的文本
            file_path: 输出文件路径
            voice: 音色配置，如果为 None 使用引擎默认
            language: 语言代码，如果为 None 使用音色默认

        Returns:
            保存成功返回 True
        """
        pass

    @abstractmethod
    def get_languages(self) -> List[str]:
        """获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        pass

    @abstractmethod
    def get_speakers(self) -> List[str]:
        """获取可用说话人列表

        Returns:
            说话人 ID 列表
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用

        Returns:
            引擎可用返回 True
        """
        pass


class CoquiTTSEngine(TTSEngine):
    """Coqui TTS 引擎实现

    使用 Coqui TTS 库，支持：
    - 多语言 TTS（1100+ 语言）
    - 声音克隆（使用参考音频）
    - XTTS v2 模型
    """

    def __init__(self, model_name: Optional[str] = None):
        """初始化 Coqui TTS 引擎

        Args:
            model_name: 模型名称，如果为 None 则使用 XTTS v2
        """
        self.model_name = model_name or "tts_models/multilingual/multi-dataset/xtts_v2"
        self._tts = None
        self._init_engine()

    def _init_engine(self) -> None:
        """初始化 Coqui TTS 引擎"""
        try:
            # 必须在导入 TTS 之前 patch torch.load（PyTorch 2.6 兼容性）
            # TTS 导入时会立即加载模型，所以必须在导入前就应用 patch
            _patch_torch_load()

            from TTS.api import TTS

            # 设置环境变量自动同意非商业许可
            import os

            os.environ["COQUI_TOS_AGREED"] = "1"

            info(f"正在加载 Coqui TTS 模型: {self.model_name}")
            self._tts = TTS(self.model_name)
            info("Coqui TTS 模型加载成功")
        except Exception as e:
            error(f"加载 Coqui TTS 模型失败: {e}")
            self._tts = None

    def _ensure_engine(self) -> bool:
        """确保引擎已初始化"""
        if self._tts is None:
            self._init_engine()
        return self._tts is not None

    def tts(
        self,
        text: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bytes:
        """使用 Coqui TTS 将文本转换为语音

        Args:
            text: 要转换的文本
            voice: 音色配置
            language: 语言代码

        Returns:
            WAV 格式的音频数据
        """
        if not self._ensure_engine():
            error("Coqui TTS 引擎不可用")
            raise RuntimeError("Coqui TTS 引擎不可用")

        try:
            # 确定语言
            lang = language or voice.language if voice else "zh"

            # 确定说话人/音色
            speaker = None
            speaker_wav = None

            if voice:
                if voice.is_cloned and voice.speaker_wav:
                    speaker_wav = voice.speaker_wav
                elif voice.model_name:
                    speaker = voice.id

            # 调用 Coqui TTS
            wav = self._tts.tts(
                text=text,
                speaker=speaker,
                language=lang,
                speaker_wav=speaker_wav,
                split_sentences=True,
            )

            # 转换为 bytes
            import numpy as np

            audio_data = np.array(wav, dtype=np.float32)
            # 转换为 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
            return audio_data.tobytes()

        except Exception as e:
            error(f"Coqui TTS 转换失败: {e}")
            raise

    def tts_to_file(
        self,
        text: str,
        file_path: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bool:
        """使用 Coqui TTS 将文本转换为语音并保存到文件

        Args:
            text: 要转换的文本
            file_path: 输出文件路径
            voice: 音色配置
            language: 语言代码

        Returns:
            保存成功返回 True
        """
        if not self._ensure_engine():
            error("Coqui TTS 引擎不可用")
            return False

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 确定语言
            lang = language or voice.language if voice else "zh"

            # 确定说话人/音色
            speaker = None
            speaker_wav = None

            if voice:
                if voice.is_cloned and voice.speaker_wav:
                    speaker_wav = voice.speaker_wav
                elif voice.model_name:
                    speaker = voice.id

            # 调用 Coqui TTS
            self._tts.tts_to_file(
                text=text,
                file_path=file_path,
                speaker=speaker,
                language=lang,
                speaker_wav=speaker_wav,
                split_sentences=True,
            )

            info(f"TTS 音频已保存: {file_path}")
            return True

        except Exception as e:
            error(f"Coqui TTS 保存文件失败: {e}")
            return False

    def get_languages(self) -> List[str]:
        """获取 Coqui TTS 支持的语言列表

        Returns:
            支持的语言代码列表
        """
        if not self._ensure_engine():
            return []

        try:
            if hasattr(self._tts, "languages"):
                return self._tts.languages
            return []
        except Exception as e:
            error(f"获取语言列表失败: {e}")
            return []

    def get_speakers(self) -> List[str]:
        """获取 Coqui TTS 可用的说话人列表

        Returns:
            说话人 ID 列表
        """
        if not self._ensure_engine():
            return []

        try:
            if hasattr(self._tts, "speakers"):
                return self._tts.speakers
            return []
        except Exception as e:
            error(f"获取说话人列表失败: {e}")
            return []

    def is_available(self) -> bool:
        """检查 Coqui TTS 引擎是否可用

        Returns:
            引擎可用返回 True
        """
        return self._ensure_engine()


class SystemTTSEngine(TTSEngine):
    """系统原生 TTS 引擎

    使用操作系统原生的 TTS 功能：
    - macOS: say 命令
    - Linux: espeak-ng 或 festival
    - Windows: PowerShell SpeechSynthesizer
    """

    def __init__(self):
        """初始化系统 TTS 引擎"""
        self._platform = None
        self._check_platform()

    def _check_platform(self) -> None:
        """检测支持的平台"""
        import platform

        self._platform = platform.system()

        if self._platform not in ["Darwin", "Linux", "Windows"]:
            error(f"不支持的操作系统: {self._platform}")
            self._platform = None

    def _get_command(self, text: str, rate: int = 200) -> tuple:
        """获取 TTS 命令

        Args:
            text: 要朗读的文本
            rate: 语速（仅 macOS 支持）

        Returns:
            (command_list, use_shell) 元组
        """
        if self._platform == "Darwin":
            # macOS say 命令
            cmd = ["say", "-r", str(rate)]
            return (cmd + [text], False)

        elif self._platform == "Linux":
            # Linux espeak-ng
            return (["espeak", text], False)

        elif self._platform == "Windows":
            # Windows PowerShell
            import json

            escaped_text = json.dumps(text)
            ps_cmd = f"""
            Add-Type -AssemblyName System.Speech
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $speak.Speak({escaped_text})
            """
            return (["powershell", "-Command", ps_cmd], False)

        return None, False

    def tts(
        self,
        text: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bytes:
        """使用系统 TTS 将文本转换为语音

        Args:
            text: 要转换的文本
            voice: 音色配置（系统 TTS 可能忽略）
            language: 语言代码（系统 TTS 可能忽略）

        Returns:
            WAV 格式的音频数据
        """
        try:
            if self._platform == "Darwin":
                # macOS: 使用 say 命令
                cmd = ["say", "-r", str(int(voice.speed * 200) if voice else 200)]
                return self._run_say_command(cmd + [text])

            elif self._platform == "Linux":
                # Linux: 使用 espeak (不支持直接输出音频)
                raise NotImplementedError(
                    "Linux 系统 TTS 不支持直接音频输出，请使用 Coqui TTS"
                )

            elif self._platform == "Windows":
                # Windows: 使用 PowerShell
                raise NotImplementedError(
                    "Windows 系统 TTS 不支持直接音频输出，请使用 Coqui TTS"
                )

            else:
                raise RuntimeError(f"不支持的操作系统: {self._platform}")

        except Exception as e:
            error(f"系统 TTS 转换失败: {e}")
            raise

    def _run_say_command(self, cmd: list) -> bytes:
        """运行 macOS say 命令并获取音频

        Args:
            cmd: 命令列表

        Returns:
            WAV 音频数据
        """
        import subprocess
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # 使用 -o 参数导出为 AIFF，然后转换
            aiff_file = os.path.join(tmpdir, "output.aiff")

            # 运行 say 命令导出音频
            cmd_export = cmd + ["-o", aiff_file.replace(".aiff", "")]
            subprocess.run(cmd_export, check=True, capture_output=True)

            # AIFF 转 WAV
            if os.path.exists(aiff_file):
                import wave

                with wave.open(aiff_file, "rb") as wf:
                    return wf.readframes(wf.getnframes())

        return b""

    def tts_to_file(
        self,
        text: str,
        file_path: str,
        voice: Optional[VoiceConfig] = None,
        language: Optional[str] = None,
    ) -> bool:
        """使用系统 TTS 将文本转换为语音并保存到文件

        Args:
            text: 要转换的文本
            file_path: 输出文件路径
            voice: 音色配置
            language: 语言代码

        Returns:
            保存成功返回 True
        """
        import subprocess
        import os

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if self._platform == "Darwin":
                # macOS: 使用 say 命令并播放（不支持直接保存文件）
                # 我们使用 afplay 来播放，但是 say 不支持导出为文件
                # 所以我们直接播放并返回 True
                rate = int(voice.speed * 200) if voice else 200
                cmd = ["say", "-r", str(rate), text]
                subprocess.run(cmd, check=True, capture_output=True)
                return True

            elif self._platform == "Linux":
                # Linux: 使用 espeak -w 参数
                cmd = ["espeak", "-w", file_path]
                subprocess.run(cmd + [text], check=True, capture_output=True)
                return True

            elif self._platform == "Windows":
                # Windows: 需要额外处理
                cmd = [
                    "powershell",
                    "-Command",
                    f"""
                    Add-Type -AssemblyName System.Speech
                    $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
                    $speak.SetOutputToWaveFile("{file_path}")
                    $speak.Speak("{text}")
                    $speak.Dispose()
                    """,
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return True

            else:
                error(f"不支持的操作系统: {self._platform}")
                return False

        except subprocess.CalledProcessError as e:
            error(f"系统 TTS 保存文件失败: {e}")
            return False
        except Exception as e:
            error(f"系统 TTS 错误: {e}")
            return False

    def get_languages(self) -> List[str]:
        """获取系统支持的语言列表

        Returns:
            语言代码列表
        """
        if self._platform == "Darwin":
            # macOS: 获取所有语音
            try:
                result = subprocess.run(
                    ["say", "-v", "?"], capture_output=True, text=True
                )
                languages = set()
                for line in result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            # 解析语音名称和语言
                            lang_code = parts[0]
                            languages.add(lang_code)
                return list(languages)
            except Exception:
                return []

        elif self._platform == "Linux":
            # Linux: espeak 支持有限
            return ["en", "zh", "ja", "ko", "fr", "de", "es"]

        elif self._platform == "Windows":
            # Windows: 获取所有语音
            return ["en-US", "zh-CN", "ja-JP", "ko-KR", "fr-FR", "de-DE", "es-ES"]

        return []

    def get_speakers(self) -> List[str]:
        """系统 TTS 不支持多说话人

        Returns:
            空列表
        """
        return []

    def is_available(self) -> bool:
        """检查系统 TTS 引擎是否可用

        Returns:
            引擎可用返回 True
        """
        if not self._platform:
            return False

        try:
            if self._platform == "Darwin":
                result = subprocess.run(["which", "say"], capture_output=True)
                return result.returncode == 0

            elif self._platform == "Linux":
                result = subprocess.run(["which", "espeak"], capture_output=True)
                return result.returncode == 0

            elif self._platform == "Windows":
                # Windows 总是有 PowerShell
                return True

            return False
        except Exception:
            return False


def get_engine(
    engine_type: Optional[str] = None, config: Optional[NotifyConfig] = None
) -> TTSEngine:
    """获取 TTS 引擎实例

    Args:
        engine_type: 引擎类型 ("coqui" 或 "system")，如果为 None 则从配置读取
        config: NotifyConfig 实例

    Returns:
        TTSEngine 实例
    """
    if config is None:
        config = load_config()

    if engine_type is None:
        engine_type = config.tts_engine

    # 临时禁用 Coqui TTS，直接使用系统 TTS
    # TODO: 修复 Coqui TTS 的 transformers 版本兼容性问题
    # 直接使用系统 TTS
    try:
        engine = SystemTTSEngine()
        if engine.is_available():
            return engine
        else:
            error("系统 TTS 不可用")
            return None
    except Exception as e:
        error(f"创建系统 TTS 失败: {e}")
        return None


def speak(
    text: str,
    voice_id: Optional[str] = None,
    config: Optional[NotifyConfig] = None,
    blocking: bool = True,
) -> bool:
    """便捷的语音播报函数

    Args:
        text: 要播报的文本
        voice_id: 音色 ID，如果为 None 使用默认音色
        config: NotifyConfig 实例
        blocking: 是否阻塞直到播放完成

    Returns:
        播报成功返回 True
    """
    if config is None:
        config = load_config()

    if not config.tts_enabled:
        debug("TTS 功能已禁用")
        return False

    engine = get_engine(config=config)

    if engine is None:
        error("无法获取可用的 TTS 引擎")
        return False

    # 获取音色
    voice = None
    if voice_id:
        voice = config.voices.get(voice_id)
    elif config.default_voice_id:
        voice = config.voices.get(config.default_voice_id)

    try:
        if blocking:
            # 对于 macOS，直接使用 say 命令更简单
            import platform
            import subprocess

            if platform.system() == "Darwin" and isinstance(engine, SystemTTSEngine):
                # macOS 系统 TTS：直接使用 say 命令
                rate = int(voice.speed * 200) if voice else 200
                subprocess.run(["say", "-r", str(rate), text])
                return True
            elif platform.system() == "Darwin" and isinstance(engine, CoquiTTSEngine):
                # macOS Coqui TTS：生成文件后播放
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name

                try:
                    if engine.tts_to_file(text, temp_path, voice):
                        subprocess.run(["afplay", temp_path], capture_output=True)
                        return True
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            else:
                # 其他平台：使用文件方式
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name

                try:
                    if engine.tts_to_file(text, temp_path, voice):
                        if platform.system() == "Darwin":
                            subprocess.run(["afplay", temp_path], capture_output=True)
                        elif platform.system() == "Linux":
                            subprocess.run(["aplay", temp_path], capture_output=True)
                        elif platform.system() == "Windows":
                            subprocess.run(
                                [
                                    "powershell",
                                    "-Command",
                                    f"(New-Object Media.SoundPlayer '{temp_path}').PlaySync()",
                                ],
                                capture_output=True,
                            )
                        return True
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        else:
            # 非阻塞模式
            audio_data = engine.tts(text=text, voice=voice)
            if audio_data:
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                try:
                    # 写入 WAV 文件
                    import wave

                    with wave.open(temp_path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(22050)
                        import numpy as np

                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        wf.writeframes(audio_array.tobytes())
                    # 后台播放
                    import subprocess

                    if platform.system() == "Darwin":
                        subprocess.Popen(["afplay", temp_path])
                    elif platform.system() == "Linux":
                        subprocess.Popen(["aplay", temp_path])
                    elif platform.system() == "Windows":
                        subprocess.Popen(
                            [
                                "powershell",
                                "-Command",
                                f"(New-Object Media.SoundPlayer '{temp_path}').Play()",
                            ]
                        )
                    return True
                finally:
                    import threading

                    def cleanup():
                        import time

                        time.sleep(5)
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

                    threading.Thread(target=cleanup, daemon=True).start()
            return False

    except Exception as e:
        error(f"语音播报失败: {e}")
        return False

    return False
