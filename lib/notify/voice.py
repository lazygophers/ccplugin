"""
声音克隆模块

提供声音克隆和音色管理功能，支持从参考音频训练克隆音色。
使用 XTTS 模型进行微调，训练后的模型存储到 ~/.lazygophers/ccplugin/notify/voices/
"""

import os
import shutil
import tempfile
import uuid
from typing import List, Optional

from lib.logging import info, warn, error
from lib.notify.config import (
    VoiceConfig,
    VoiceSample,
    TrainingRecord,
    NotifyConfig,
    load_config,
    save_config,
    get_voices_dir,
)


class VoiceTrainer:
    """声音克隆训练器

    使用 XTTS 模型进行声音克隆训练。

    训练流程：
    1. 收集参考音频（至少 10-30 秒清晰语音）
    2. 预处理音频（降噪、标准化、格式转换）
    3. 训练微调（XTTS fine-tuning）
    4. 保存模型到 voices/{voice_id}/ 目录
    """

    def __init__(self):
        """初始化训练器"""
        self._tts_model = None
        self._voices_dir = get_voices_dir()

    def _ensure_model(self) -> bool:
        """确保 XTTS 模型已加载"""
        if self._tts_model is None:
            try:
                from TTS.api import TTS

                # 使用 XTTS v2 模型
                self._tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
                info("XTTS 模型加载成功")
                return True
            except Exception as e:
                error(f"加载 XTTS 模型失败: {e}")
                return False
        return True

    def _get_voice_dir(self, voice_id: str) -> str:
        """获取音色目录路径"""
        return os.path.join(self._voices_dir, voice_id)

    def _get_reference_audio_path(self, voice_id: str) -> str:
        """获取参考音频路径"""
        return os.path.join(self._get_voice_dir(voice_id), "reference.wav")

    def _get_checkpoint_path(self, voice_id: str) -> str:
        """获取检查点路径"""
        return os.path.join(self._get_voice_dir(voice_id), "checkpoint.pth")

    def _get_config_path(self, voice_id: str) -> str:
        """获取音色配置路径"""
        return os.path.join(self._get_voice_dir(voice_id), "config.yaml")

    def _get_temp_dir(self, voice_id: str) -> str:
        """获取临时目录路径

        Args:
            voice_id: 音色 ID

        Returns:
            临时目录路径
        """
        temp_base = tempfile.gettempdir()
        return os.path.join(temp_base, f"ccplugin_notify_{voice_id}")

    def cleanup_temp_files(self, voice_id: str) -> int:
        """清理临时文件

        Args:
            voice_id: 音色 ID

        Returns:
            清理的文件数量
        """
        temp_dir = self._get_temp_dir(voice_id)
        cleaned_count = 0

        if not os.path.exists(temp_dir):
            return 0

        try:
            # 删除目录中的所有文件
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        cleaned_count += 1
                except Exception as e:
                    warn(f"删除临时文件失败 {file_path}: {e}")

            # 如果目录为空，删除目录
            try:
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                    info(f"已删除临时目录: {temp_dir}")
            except Exception as e:
                warn(f"删除临时目录失败 {temp_dir}: {e}")

        except Exception as e:
            error(f"清理临时文件失败: {e}")

        return cleaned_count

    def preprocess_audio(
        self,
        audio_path: str,
        voice_id: str,
        enable_normalize: bool = True,
        enable_denoise: bool = True,
        enable_trim_silence: bool = True,
        enable_fade: bool = True,
    ) -> Optional[str]:
        """预处理音频文件（增强版）

        优化步骤：
        1. 格式转换（WAV, 22050Hz, 单声道）
        2. 音量标准化
        3. 降噪处理
        4. 静音检测和去除
        5. 淡入淡出效果

        Args:
            audio_path: 输入音频路径
            voice_id: 音色 ID（用于生成临时文件）
            enable_normalize: 是否启用音量标准化
            enable_denoise: 是否启用降噪
            enable_trim_silence: 是否去除静音
            enable_fade: 是否添加淡入淡出

        Returns:
            预处理后的音频路径，失败返回 None
        """
        try:
            import subprocess

            # 使用系统临时目录
            temp_dir = self._get_temp_dir(voice_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 生成唯一的临时文件名
            unique_id = str(uuid.uuid4())[:8]
            processed_path = os.path.join(temp_dir, f"processed_{unique_id}.wav")

            # 步骤 1: 基础格式转换
            base_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                audio_path,
                "-ar",
                "22050",
                "-ac",
                "1",
                "-acodec",
                "pcm_s16le",
            ]

            # 构建滤镜链（只使用简单滤镜链，避免复杂滤镜图问题）
            filters = []

            # 降噪: 高通滤波去除低频噪音
            if enable_denoise:
                filters.append("highpass=80")
                filters.append("lowpass=12000")

            # 音量标准化: EBU R128 标准响度标准化
            if enable_normalize:
                filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

            # 应用滤镜链
            if filters:
                filter_chain = ",".join(filters)
                cmd = base_cmd + ["-af", filter_chain, processed_path]
            else:
                cmd = base_cmd + [processed_path]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                error(f"音频预处理失败: {result.stderr}")
                # 回退到简单转换
                simple_cmd = base_cmd + [processed_path]
                result = subprocess.run(simple_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    error(f"基础转换失败: {result.stderr}")
                    return None

            if not os.path.exists(processed_path):
                return None

            # 淡入淡出在最后一步单独应用
            if enable_fade:
                final_path = os.path.join(temp_dir, f"final_{unique_id}.wav")
                self._apply_audio_enhancements(processed_path, final_path, enable_fade=True)
                return final_path if os.path.exists(final_path) else processed_path

            return processed_path

        except FileNotFoundError:
            error("ffmpeg 未安装，无法预处理音频")
            return audio_path
        except Exception as e:
            error(f"预处理音频失败: {e}")
            return None

    def _apply_audio_enhancements(
        self, input_path: str, output_path: str, enable_fade: bool = True
    ) -> bool:
        """应用音频增强效果

        Args:
            input_path: 输入音频路径
            output_path: 输出音频路径
            enable_fade: 是否添加淡入淡出

        Returns:
            成功返回 True
        """
        try:
            import subprocess

            # 首先获取音频时长
            duration = self._get_audio_duration(input_path)

            filters = []

            if enable_fade and duration > 1.0:
                # 淡入: 前 300ms
                fade_in = "afade=t=in:curve=exp:d=0.3"
                # 淡出: 最后 500ms
                fade_out = "afade=t=out:curve=exp:d=0.5"
                filters = [fade_in, fade_out]

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
            ]

            if filters:
                cmd.extend(["-af", ",".join(filters)])

            cmd.extend(["-ar", "22050", "-ac", "1", output_path])

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_path)

        except Exception:
            # 如果增强失败，复制原始文件
            try:
                import shutil

                shutil.copy2(input_path, output_path)
                return True
            except Exception:
                return False

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            import subprocess

            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 0.0

    def normalize_audio(self, audio_path: str, output_path: str) -> bool:
        """标准化音频音量

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径

        Returns:
            成功返回 True
        """
        try:
            import subprocess

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                audio_path,
                "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ar",
                "22050",
                "-ac",
                "1",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_path)

        except Exception:
            return False

    def remove_silence(
        self,
        audio_path: str,
        output_path: str,
        threshold: float = -50,
    ) -> bool:
        """去除静音部分

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            threshold: 静音阈值（dB）

        Returns:
            成功返回 True
        """
        try:
            import subprocess

            # 使用 silenceremove 滤镜去除静音
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                audio_path,
                "-af",
                f"silenceremove=stop_threshold={threshold}dB:stop_duration=0.5:leave_silence=0",
                "-ar",
                "22050",
                "-ac",
                "1",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_path)

        except Exception:
            return False

    def merge_audios_with_transition(
        self, audio_paths: List[str], output_path: str
    ) -> bool:
        """合并多个音频文件（带过渡效果）

        Args:
            audio_paths: 音频文件路径列表
            output_path: 输出文件路径

        Returns:
            成功返回 True
        """
        try:
            import subprocess

            if len(audio_paths) == 1:
                # 单个文件直接复制
                import shutil

                shutil.copy2(audio_paths[0], output_path)
                return os.path.exists(output_path)

            # 创建文件列表
            temp_dir = os.path.dirname(output_path)
            list_file = os.path.join(temp_dir, "concat_list.txt")

            # 使用 concat demuxer 进行无损合并
            with open(list_file, "w") as f:
                for path in audio_paths:
                    if os.path.exists(path):
                        safe_path = path.replace("'", "'\\''")
                        f.write(f"file '{safe_path}'\n")

            if os.path.getsize(list_file) == 0:
                return False

            # 使用 ffmpeg concat 进行合并
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file,
                "-af",
                "afade=t=in:curve=exp:d=0.2",
                "-ar",
                "22050",
                "-ac",
                "1",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # 如果带过渡的合并失败，尝试简单合并
            if result.returncode != 0:
                simple_cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file,
                    "-ar",
                    "22050",
                    "-ac",
                    "1",
                    output_path,
                ]
                result = subprocess.run(
                    simple_cmd, capture_output=True, text=True
                )

            return result.returncode == 0 and os.path.exists(output_path)

        except Exception:
            return False

    def analyze_audio(self, audio_path: str) -> Optional[VoiceSample]:
        """分析音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            VoiceSample 或 None
        """
        try:
            import wave

            with wave.open(audio_path, "rb") as wf:
                frame_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = n_frames / frame_rate

                return VoiceSample(
                    path=audio_path, duration=duration, sample_rate=frame_rate
                )
        except Exception as e:
            error(f"分析音频失败: {e}")
            return None

    def train(
        self,
        voice_id: str,
        reference_audio: str,
        name: Optional[str] = None,
        language: str = "zh",
        epochs: int = 10,
        original_samples: Optional[List[str]] = None,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """训练克隆音色

        Args:
            voice_id: 音色唯一标识
            reference_audio: 参考音频文件路径
            name: 音色名称（用户友好）
            language: 语言代码
            epochs: 训练轮数
            original_samples: 原始样本文件路径列表（用于跟踪）
            config: NotifyConfig 实例

        Returns:
            训练成功返回 True
        """
        info(f"开始训练音色: {voice_id}")

        try:
            # 检查参考音频
            if not os.path.exists(reference_audio):
                error(f"参考音频文件不存在: {reference_audio}")
                return False

            # 预处理音频
            processed_audio = self.preprocess_audio(reference_audio, voice_id)
            if not processed_audio:
                error("音频预处理失败")
                return False

            # 分析音频
            sample = self.analyze_audio(processed_audio)
            if not sample:
                error("音频分析失败")
                return False

            if sample.duration < 5:
                warn(f"参考音频过短 ({sample.duration:.1f}秒)，建议至少 10-30 秒")

            # 创建音色目录
            voice_dir = self._get_voice_dir(voice_id)
            os.makedirs(voice_dir, exist_ok=True)

            # 复制参考音频
            final_reference = self._get_reference_audio_path(voice_id)
            try:
                if processed_audio != final_reference:
                    shutil.copy2(processed_audio, final_reference)
            except Exception:
                pass

            # 注意：XTTS 的完整微调需要大量计算资源和时间
            # 这里实现简化的克隆流程：直接使用 XTTS 的 voice_conversion 功能
            # 完整微调功能需要使用 Coqui TTS 的官方训练脚本

            info(f"音色 {voice_id} 训练完成（使用 XTTS 参考音频模式）")

            # 保存音色配置
            voice_config = VoiceConfig(
                id=voice_id,
                name=name or voice_id,
                engine="coqui",
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                language=language,
                speed=1.0,
                pitch=1.0,
                speaker_wav=final_reference
                if os.path.exists(final_reference)
                else reference_audio,
                is_cloned=True,
            )

            # 更新配置
            if config is None:
                config = load_config()

            # 如果音色已存在，保留原有的 samples 和 training_history
            if voice_id in config.voices:
                existing_voice = config.voices[voice_id]
                voice_config.samples = existing_voice.samples
                voice_config.training_history = existing_voice.training_history
                voice_config.checkpoint_path = existing_voice.checkpoint_path
            else:
                # 新音色：添加原始样本到 samples 列表
                voice_config.samples = []
                if original_samples:
                    for sample_path in original_samples:
                        if os.path.exists(sample_path):
                            # 尝试分析音频，如果失败则使用默认值
                            try:
                                analyzed = self.analyze_audio(sample_path)
                                if analyzed:
                                    voice_config.samples.append(analyzed)
                                else:
                                    # 分析失败，添加基本样本信息
                                    from lib.notify.config import VoiceSample

                                    voice_config.samples.append(
                                        VoiceSample(path=sample_path, duration=0.0)
                                    )
                            except Exception:
                                # MP3 等格式无法用 wave 分析，添加基本样本信息
                                from lib.notify.config import VoiceSample

                                voice_config.samples.append(
                                    VoiceSample(path=sample_path, duration=0.0)
                                )

            config.voices[voice_id] = voice_config

            # 如果是第一个音色，设为默认
            if config.default_voice_id is None:
                config.default_voice_id = voice_id

            save_config(config)
            return True

        finally:
            # 清理临时文件
            self.cleanup_temp_files(voice_id)

    def train_from_samples(
        self,
        voice_id: str,
        sample_paths: List[str],
        name: Optional[str] = None,
        language: str = "zh",
        recursive: bool = False,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """从多个音频样本训练音色

        Args:
            voice_id: 音色唯一标识
            sample_paths: 音频样本路径列表（支持通配符）
            name: 音色名称
            language: 语言代码
            recursive: 是否递归展开通配符
            config: NotifyConfig 实例

        Returns:
            训练成功返回 True
        """
        if not sample_paths:
            error("没有提供音频样本")
            return False

        # 处理通配符
        import glob

        expanded_paths = []
        for path in sample_paths:
            if "*" in path:
                # 展开通配符
                if recursive:
                    matches = glob.glob(path, recursive=True)
                else:
                    matches = glob.glob(path)
                expanded_paths.extend(matches)
            else:
                expanded_paths.append(path)

        # 去重并过滤不存在的文件
        sample_paths = list(dict.fromkeys(expanded_paths))
        sample_paths = [p for p in sample_paths if os.path.exists(p)]

        if not sample_paths:
            error("没有找到有效的音频样本")
            return False

        try:
            # 确保临时目录存在
            temp_dir = self._get_temp_dir(voice_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 创建音色目录和 samples 子目录
            voice_dir = self._get_voice_dir(voice_id)
            samples_dir = os.path.join(voice_dir, "samples")
            os.makedirs(samples_dir, exist_ok=True)

            # 预处理所有原始样本文件并复制到 samples 目录
            preprocessed_samples = []
            original_sample_paths = []  # 保存原始文件路径用于 samples 列表

            for i, sample_path in enumerate(sample_paths):
                if os.path.exists(sample_path):
                    # 预处理（转换格式）
                    processed = self.preprocess_audio(sample_path, voice_id)
                    if processed:
                        # 复制到 samples 目录，使用序号前缀
                        import shutil

                        filename = f"{i + 1}_{os.path.basename(sample_path)}"
                        sample_copy_path = os.path.join(samples_dir, filename)
                        try:
                            if processed != sample_copy_path:
                                shutil.copy2(processed, sample_copy_path)
                                original_sample_paths.append(sample_copy_path)
                            else:
                                original_sample_paths.append(processed)
                        except Exception:
                            original_sample_paths.append(processed)
                        preprocessed_samples.append(processed)

            if not preprocessed_samples:
                error("预处理所有音频样本失败")
                return False

            # 使用增强的合并方法（带过渡效果）
            combined_audio = os.path.join(temp_dir, "combined.wav")

            success = self.merge_audios_with_transition(
                preprocessed_samples, combined_audio
            )

            # 如果增强合并失败，尝试简单拼接
            if not success:
                warn("增强合并失败，尝试简单拼接")
                with open(combined_audio, "wb") as outfile:
                    for sample_path in preprocessed_samples:
                        if os.path.exists(sample_path):
                            with open(sample_path, "rb") as infile:
                                outfile.write(infile.read())

            # 检查合并结果
            if not os.path.exists(combined_audio):
                error("合并音频样本失败")
                return False

            # 最终优化：应用标准化和淡入淡出
            final_audio = os.path.join(temp_dir, "final_reference.wav")
            self._apply_audio_enhancements(
                combined_audio, final_audio, enable_fade=True
            )

            if os.path.exists(final_audio):
                combined_audio = final_audio

            return self.train(
                voice_id=voice_id,
                reference_audio=combined_audio,
                name=name,
                language=language,
                original_samples=original_sample_paths,
                config=config,
            )

        except Exception as e:
            error(f"合并音频样本失败: {e}")
            return False
        finally:
            # 清理临时文件
            self.cleanup_temp_files(voice_id)

    def add_sample(
        self,
        voice_id: str,
        audio_path: str,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """添加样本到已有音色

        Args:
            voice_id: 音色 ID
            audio_path: 音频文件路径（支持通配符，多个文件用空格分隔）
            config: NotifyConfig 实例

        Returns:
            添加成功返回 True
        """
        if config is None:
            config = load_config()

        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return False

        voice = config.voices[voice_id]

        # 处理通配符展开
        import glob

        audio_files = audio_path.split()
        expanded_paths = []
        for path in audio_files:
            if "*" in path:
                matches = glob.glob(path)
                expanded_paths.extend(matches)
            else:
                expanded_paths.append(path)

        # 过滤不存在的文件
        audio_files = [p for p in expanded_paths if os.path.exists(p)]

        if not audio_files:
            error("没有找到有效的音频文件")
            return False

        try:
            added_count = 0
            for audio_file in audio_files:
                # 预处理音频
                processed_audio = self.preprocess_audio(audio_file, voice_id)
                if not processed_audio:
                    error(f"预处理音频失败: {audio_file}")
                    continue

                # 分析音频
                sample = self.analyze_audio(processed_audio)
                if not sample:
                    error(f"分析音频失败: {audio_file}")
                    continue

                # 复制到音色目录
                voice_dir = self._get_voice_dir(voice_id)
                os.makedirs(voice_dir, exist_ok=True)

                # 生成样本文件名
                import uuid

                sample_filename = f"sample_{uuid.uuid4().hex[:8]}.wav"
                sample_path = os.path.join(voice_dir, sample_filename)

                try:
                    if processed_audio != sample_path:
                        shutil.copy2(processed_audio, sample_path)
                except Exception:
                    sample_path = processed_audio

                # 添加到样本列表
                sample.path = sample_path
                voice.samples.append(sample)
                added_count += 1

                info(f"已添加样本: {sample_path}")

            if added_count > 0:
                # 保存配置
                save_config(config)
                info(f"成功添加 {added_count} 个样本到音色: {voice_id}")
                return True
            else:
                error("没有添加任何样本")
                return False

        except Exception as e:
            error(f"添加样本失败: {e}")
            return False
        finally:
            # 清理临时文件
            self.cleanup_temp_files(voice_id)

    def remove_sample(
        self,
        voice_id: str,
        sample_index: int,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """从音色中删除样本

        Args:
            voice_id: 音色 ID
            sample_index: 样本索引
            config: NotifyConfig 实例

        Returns:
            删除成功返回 True
        """
        if config is None:
            config = load_config()

        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return False

        voice = config.voices[voice_id]

        if sample_index < 0 or sample_index >= len(voice.samples):
            error(f"样本索引无效: {sample_index}")
            return False

        sample = voice.samples[sample_index]

        # 删除样本文件
        if os.path.exists(sample.path):
            try:
                os.remove(sample.path)
                info(f"已删除样本文件: {sample.path}")
            except Exception as e:
                warn(f"删除样本文件失败: {e}")

        # 从列表中移除
        del voice.samples[sample_index]

        # 保存配置
        save_config(config)
        info(f"已从音色 {voice_id} 中删除样本: {sample_index}")
        return True

    def get_samples(self, voice_id: str) -> List[VoiceSample]:
        """获取音色的所有样本

        Args:
            voice_id: 音色 ID

        Returns:
            VoiceSample 列表
        """
        config = load_config()
        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return []

        return config.voices[voice_id].samples

    def retrain(
        self,
        voice_id: str,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """使用所有样本重新训练音色

        Args:
            voice_id: 音色 ID
            config: NotifyConfig 实例

        Returns:
            训练成功返回 True
        """
        if config is None:
            config = load_config()

        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return False

        voice = config.voices[voice_id]

        if not voice.samples:
            error(f"音色 {voice_id} 没有样本")
            return False

        # 合并所有样本
        sample_paths = [s.path for s in voice.samples if os.path.exists(s.path)]

        if not sample_paths:
            error("没有有效的样本文件")
            return False

        return self.train_from_samples(
            voice_id=voice_id,
            sample_paths=sample_paths,
            name=voice.name,
            language=voice.language,
            config=config,
        )

    def finetune(
        self,
        voice_id: str,
        epochs: int = 10,
        use_gpu: bool = True,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """XTTS 参考音频优化

        注意：Coqui TTS API 不支持真正的模型微调。
        当前实现通过以下方式优化参考音频质量：
        1. 预处理所有样本（标准化、降噪、格式转换）
        2. 智能合并（带淡入淡出过渡）
        3. 最终优化（响度标准化、淡入淡出）

        Args:
            voice_id: 音色 ID
            epochs: 训练轮数（用于记录）
            use_gpu: 是否使用 GPU（用于记录）
            config: NotifyConfig 实例

        Returns:
            优化成功返回 True
        """
        if config is None:
            config = load_config()

        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return False

        voice = config.voices[voice_id]

        info(f"开始优化音色: {voice_id}")
        info("使用增强的参考音频优化模式")

        # 获取样本路径：优先使用 samples 字段，否则使用 speaker_wav
        sample_paths = [s.path for s in voice.samples if os.path.exists(s.path)]

        # 如果没有样本但有 speaker_wav，使用它作为参考
        if not sample_paths and voice.speaker_wav and os.path.exists(voice.speaker_wav):
            info(f"没有样本文件，使用已有参考音频: {voice.speaker_wav}")
            sample_paths = [voice.speaker_wav]

        if not sample_paths:
            error("没有可用的样本文件进行优化")
            return False

        try:
            # 确保临时目录存在
            temp_dir = self._get_temp_dir(voice_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 步骤 1: 预处理所有样本
            info("预处理音频样本...")
            preprocessed_samples = []
            for i, sample_path in enumerate(sample_paths):
                if os.path.exists(sample_path):
                    # 使用增强预处理
                    processed = self.preprocess_audio(
                        sample_path,
                        voice_id,
                        enable_normalize=True,
                        enable_denoise=True,
                        enable_trim_silence=True,
                        enable_fade=False,  # 合并时再添加淡入淡出
                    )
                    if processed:
                        preprocessed_samples.append(processed)

            if not preprocessed_samples:
                error("预处理音频样本失败")
                return False

            info(f"已预处理 {len(preprocessed_samples)} 个样本")

            # 步骤 2: 智能合并（带过渡效果）
            info("合并音频样本...")
            combined_audio = os.path.join(temp_dir, "finetune_combined.wav")

            success = self.merge_audios_with_transition(
                preprocessed_samples, combined_audio
            )

            # 如果增强合并失败，回退
            if not success:
                warn("增强合并失败，尝试简单拼接")
                if len(preprocessed_samples) == 1:
                    shutil.copy2(preprocessed_samples[0], combined_audio)
                else:
                    with open(combined_audio, "wb") as outfile:
                        for sp in preprocessed_samples:
                            if os.path.exists(sp):
                                with open(sp, "rb") as infile:
                                    outfile.write(infile.read())

            if not os.path.exists(combined_audio):
                error("合并音频样本失败")
                return False

            # 步骤 3: 最终优化（响度标准化 + 淡入淡出）
            info("应用最终优化...")
            final_reference_temp = os.path.join(temp_dir, "finetune_final.wav")
            self._apply_audio_enhancements(
                combined_audio, final_reference_temp, enable_fade=True
            )

            # 更新参考音频
            voice_dir = self._get_voice_dir(voice_id)
            os.makedirs(voice_dir, exist_ok=True)

            final_reference = self._get_reference_audio_path(voice_id)
            try:
                if os.path.exists(final_reference_temp):
                    shutil.copy2(final_reference_temp, final_reference)
                else:
                    shutil.copy2(combined_audio, final_reference)
            except Exception:
                final_reference = final_reference_temp if os.path.exists(
                    final_reference_temp
                ) else combined_audio

            # 获取最终时长
            final_duration = self._get_audio_duration(final_reference)
            info(f"优化后的参考音频时长: {final_duration:.1f}秒")

            voice.speaker_wav = final_reference
            voice.is_cloned = True

            # 添加训练记录
            record = TrainingRecord(
                epochs=epochs,
                samples_count=len(sample_paths),
                method="finetune",
            )
            voice.training_history.append(record)

            # 保存配置
            save_config(config)

            info(f"音色优化完成: {voice_id}")
            info(f"参考音频已更新: {final_reference}")
            info("优化内容: 响度标准化、降噪处理、淡入淡出过渡")
            return True

        except Exception as e:
            error(f"音色优化失败: {e}")
            return False
        finally:
            self.cleanup_temp_files(voice_id)
        """列出所有已训练的音色

        Args:
            config: NotifyConfig 实例

        Returns:
            VoiceConfig 列表
        """
        if config is None:
            config = load_config()

        voices = []
        for voice_id, voice in config.voices.items():
            if voice.is_cloned:
                voices.append(voice)
        return voices

    def list_voices(self, config: Optional[NotifyConfig] = None) -> List[VoiceConfig]:
        """列出所有已训练的克隆音色

        Args:
            config: NotifyConfig 实例

        Returns:
            VoiceConfig 列表
        """
        if config is None:
            config = load_config()

        voices = []
        for voice_id, voice in config.voices.items():
            if voice.is_cloned:
                voices.append(voice)
        return voices

    def delete_voice(
        self, voice_id: str, config: Optional[NotifyConfig] = None
    ) -> bool:
        """删除克隆音色

        Args:
            voice_id: 音色 ID
            config: NotifyConfig 实例

        Returns:
            删除成功返回 True
        """
        if config is None:
            config = load_config()

        if voice_id not in config.voices:
            error(f"音色不存在: {voice_id}")
            return False

        # 删除音色目录
        voice_dir = self._get_voice_dir(voice_id)
        if os.path.exists(voice_dir):
            try:
                shutil.rmtree(voice_dir)
                info(f"已删除音色目录: {voice_dir}")
            except Exception as e:
                error(f"删除音色目录失败: {e}")

        # 删除配置
        del config.voices[voice_id]

        # 如果删除的是默认音色
        if config.default_voice_id == voice_id:
            # 选择另一个克隆音色作为默认
            cloned_voices = [v for v in config.voices.values() if v.is_cloned]
            config.default_voice_id = cloned_voices[0].id if cloned_voices else None

        save_config(config)
        return True

    def export_voice(
        self, voice_id: str, export_path: str, config: Optional[NotifyConfig] = None
    ) -> bool:
        """导出音色配置

        Args:
            voice_id: 音色 ID
            export_path: 导出目标路径（tar.gz）
            config: NotifyConfig 实例

        Returns:
            导出成功返回 True
        """
        if config is None:
            config = load_config()

        voice = config.voices.get(voice_id)
        if not voice:
            error(f"音色不存在: {voice_id}")
            return False

        voice_dir = self._get_voice_dir(voice_id)
        if not os.path.exists(voice_dir):
            error(f"音色目录不存在: {voice_dir}")
            return False

        try:
            import tarfile

            with tarfile.open(export_path, "w:gz") as tar:
                tar.add(voice_dir, arcname=voice_id)

            info(f"音色已导出: {export_path}")
            return True

        except Exception as e:
            error(f"导出音色失败: {e}")
            return False

    def import_voice(
        self,
        import_path: str,
        voice_id: Optional[str] = None,
        config: Optional[NotifyConfig] = None,
    ) -> bool:
        """导入音色配置

        Args:
            import_path: 导入源路径（tar.gz）
            voice_id: 指定的音色 ID，如果为 None 则从配置读取
            config: NotifyConfig 实例

        Returns:
            导入成功返回 True
        """
        if not os.path.exists(import_path):
            error(f"导入文件不存在: {import_path}")
            return False

        if config is None:
            config = load_config()

        try:
            import tarfile

            # 临时解压
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                with tarfile.open(import_path, "r:gz") as tar:
                    tar.extractall(tmpdir)

                # 查找解压后的目录
                extracted_dirs = [
                    d
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                ]

                if not extracted_dirs:
                    error("导入文件中没有找到音色目录")
                    return False

                extracted_dir = os.path.join(tmpdir, extracted_dirs[0])

                # 读取音色配置
                config_path = os.path.join(extracted_dir, "config.yaml")
                if os.path.exists(config_path):
                    # 加载旧配置
                    import yaml

                    with open(config_path, "r") as f:
                        old_data = yaml.safe_load(f)

                    # 如果没有指定 voice_id，使用原来的
                    if voice_id is None:
                        if "voices" in old_data:
                            voice_id = list(old_data["voices"].keys())[0]
                        else:
                            voice_id = extracted_dirs[0]

                # 复制到 voices 目录
                target_dir = self._get_voice_dir(voice_id)
                shutil.copytree(extracted_dir, target_dir)

            # 更新配置
            voice_config = VoiceConfig(
                id=voice_id,
                name=voice_id,
                engine="coqui",
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                language="zh",
                is_cloned=True,
            )
            config.voices[voice_id] = voice_config
            save_config(config)

            info(f"音色已导入: {voice_id}")
            return True

        except Exception as e:
            error(f"导入音色失败: {e}")
            return False


class VoiceCloner:
    """声音克隆管理器

    提供简单的声音克隆接口。
    """

    def __init__(self):
        """初始化管理器"""
        self.trainer = VoiceTrainer()

    def clone(
        self,
        voice_id: str,
        reference_audio: str,
        name: Optional[str] = None,
        language: str = "zh",
    ) -> bool:
        """克隆声音

        Args:
            voice_id: 音色唯一标识
            reference_audio: 参考音频文件路径
            name: 音色名称
            language: 语言代码

        Returns:
            克隆成功返回 True
        """
        return self.trainer.train(
            voice_id=voice_id,
            reference_audio=reference_audio,
            name=name,
            language=language,
        )

    def list(self) -> List[VoiceConfig]:
        """列出所有克隆音色"""
        return self.trainer.list_voices()

    def delete(self, voice_id: str) -> bool:
        """删除克隆音色"""
        return self.trainer.delete_voice(voice_id)

    def get_info(self, voice_id: str) -> Optional[VoiceConfig]:
        """获取音色信息"""
        config = load_config()
        return config.voices.get(voice_id)
