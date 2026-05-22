# cortex-video-understand 视频理解 skill

## Goal

为 cortex 加视频理解能力, 镜像 cortex-image-understand。支持两种模式: (1) `video_url` 直传 (zhipu glm-4v-plus / qwen-vl-max-video 等原生支持视频), (2) `frames` 抽帧 (ffmpeg 抽 N 帧后走 image content array, 兼容 openai gpt-4o 等无原生视频模型)。

## Requirements

1. CLI `scripts/cli/video_understand.py`
   - 子命令: `probe / describe / ask / extract / list`
   - 复用 `_provider_common.py`
   - provider 配置 `mode: video_url | frames` (默认 video_url)
   - frames 模式: ffmpeg 抽帧 (`-vf fps=<rate>` 或固定 N 帧, 默认 8 帧均匀采样), 编码 base64 image, 组 vision messages
   - video_url 模式: content array 含 `{"type": "video_url", "video_url": {"url": "<url|data>"}}`
   - 输入: 本地路径 (检查 ffmpeg 可用否) 或 http(s) URL
   - 输出 JSON: `{ok, text, provider, model, mode, frames_used?, usage}`

2. yaml `<vault>/.cortex/config/video-understand.yaml`
   - providers 含 zhipu-glm4v / openai-gpt4o-frames / qwen-vl-max-video 模板
   - 字段同 image-understand + `mode` (video_url|frames) + `frames_count` (frames 模式时, 默认 8) + `frames_fps` (可选, 与 frames_count 互斥)
   - defaults 含 `default_provider / max_tokens / temperature / mode`

3. skill `skills/cortex-video-understand/SKILL.md` + `references/{providers,prompts,modes}.md`
   - 触发: "看视频" / "视频理解" / "video understanding" / "总结视频" / "视频问答"
   - 决策树含 mode 选择 (video_url 优先, 不支持时 fallback frames)
   - frames 模式坑: ffmpeg 必须存在, 默认 8 帧均匀采样

4. wrapper 注册 (合并到 task #9)

5. 文档同步 (合并到 task #9)

## Acceptance Criteria

- [ ] `bash ~/.cortex/scripts/video_understand.sh probe` JSON
- [ ] `describe <mp4> --config zhipu-glm4v` 成功 (video_url 模式)
- [ ] `describe <mp4> --config openai-gpt4o-frames` 成功 (frames 模式, ffmpeg 可用)
- [ ] ffmpeg 缺失时 frames 模式 fail-soft JSON error
- [ ] 15+ pytest 单测 (frame_extraction / content build / mode 切换)
- [ ] ruff check + format clean

## Technical Approach

### frames 模式 ffmpeg 调用

```python
def extract_frames(video_path: Path, count: int, tmp_dir: Path) -> list[Path]:
    duration = ffprobe_duration(video_path)
    interval = duration / count
    frames = []
    for i in range(count):
        ts = interval * (i + 0.5)
        out = tmp_dir / f"frame_{i:03d}.jpg"
        subprocess.run([
            "ffmpeg", "-ss", str(ts), "-i", str(video_path),
            "-vframes", "1", "-q:v", "3", str(out), "-y",
        ], capture_output=True, check=True)
        frames.append(out)
    return frames
```

ffmpeg 缺失 → `shutil.which("ffmpeg")` 检测 → 报错 fallback 提示用 video_url 模式或别的 provider。

### content array

video_url 模式:
```python
content = [{"type": "text", "text": prompt},
           {"type": "video_url", "video_url": {"url": to_video_url(src)}}]
```

frames 模式:
```python
content = [{"type": "text", "text": prompt}]
for frame in frames:
    content.append({"type": "image_url",
                    "image_url": {"url": to_image_data_url(frame)}})
```

### provider 模板

```yaml
- name: zhipu-glm4v
  endpoint: https://open.bigmodel.cn/api/paas/v4/chat/completions
  model: glm-4v-plus
  api_key_env: ZHIPU_API_KEY
  mode: video_url
  trusted: true

- name: openai-gpt4o-frames
  endpoint: https://api.openai.com/v1/chat/completions
  model: gpt-4o-mini
  api_key_env: OPENAI_API_KEY
  mode: frames
  frames_count: 8
  disabled: true

- name: qwen-vl-max-video
  endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
  model: qwen-vl-max
  api_key_env: DASHSCOPE_API_KEY
  mode: video_url
  disabled: true
```

## Out of Scope

- 视频生成 (本 skill 只读)
- 实时流 (chunk streaming)
- 字幕轨提取 (SRT/VTT — 单独 skill 或后续加)
- 音频部分 (走 cortex-audio-understand)

## Technical Notes

- 参考 `scripts/cli/image_understand.py:_run_chat` 流程
- frames 临时目录 `tempfile.mkdtemp(prefix="cortex-video-")`, 调用后清理
- 不缓存帧 (用户重复调用按需重抽)
