# cortex-audio-understand 音频理解 skill

## Goal

为 cortex 加音频理解能力, 镜像 cortex-image-understand。支持 ASR 转录 + 音频问答 (VQA-on-audio)。多 provider: zhipu glm-asr / openai whisper / qwen-audio。

## Requirements

1. CLI `scripts/cli/audio_understand.py`
   - 子命令: `probe / transcribe / describe / ask / list`
   - 复用 `_provider_common.py`
   - provider 配置 `mode: chat | asr`
     - `chat` 模式: OpenAI 兼容 chat completions, content 含 `{"type": "input_audio", "input_audio": {"data": "<b64>", "format": "wav"}}`
     - `asr` 模式: OpenAI Whisper 风格 `/v1/audio/transcriptions` multipart upload, body 含 file + model
   - 输入: 本地路径 (b64 编码 / multipart upload) 或 URL (chat 模式)
   - 输出 JSON: `{ok, text, provider, model, mode, duration_seconds?, usage?}`

2. yaml `<vault>/.cortex/config/audio-understand.yaml`
   - providers 含 zhipu-glm-asr / openai-whisper / openai-gpt4o-audio / qwen-audio
   - 字段同 image-understand + `mode` (chat|asr) + `language` (可选, ISO 639-1) + `response_format` (asr 时)
   - defaults: `default_provider / max_tokens / temperature / mode / language`

3. skill `skills/cortex-audio-understand/SKILL.md` + `references/{providers,prompts,modes}.md`
   - 触发: "转录" / "听音频" / "audio transcription" / "ASR" / "音频问答" / "音频理解"
   - 决策树: 纯转录 → transcribe; 内容理解/问答 → describe/ask
   - 模式说明: chat (含 gpt-4o-audio, 支持问答) vs asr (whisper-style, 仅转录)

4. wrapper + 文档同步 (合并到 task #9)

## Acceptance Criteria

- [ ] `bash ~/.cortex/scripts/audio_understand.sh probe` JSON
- [ ] `transcribe <wav> --config openai-whisper` (asr 模式) 返回 text
- [ ] `ask <wav> "说了什么"` (chat 模式) 返回非空
- [ ] 支持 mp3/wav/m4a/webm 格式 (mime 判定)
- [ ] 15+ pytest 单测
- [ ] ruff clean

## Technical Approach

### asr 模式 (Whisper-style)

multipart/form-data POST:
```
POST <endpoint>/v1/audio/transcriptions
Headers: Authorization: Bearer <key>
Body:
  file=@<audio.wav>
  model=whisper-1
  language=zh         (optional)
  response_format=json (default)
```

stdlib `urllib` 不直接支持 multipart, 用 `email.mime.multipart` 或手工拼 `multipart/form-data` boundary。考虑加 `_provider_common` helper `http_multipart(...)`。

### chat 模式 (gpt-4o-audio / zhipu)

content array:
```python
{"type": "input_audio",
 "input_audio": {"data": "<base64>", "format": "wav"}}
```

zhipu 可能用 `audio_url` 而非 `input_audio` — provider 通过 `extra_body` / `audio_field_name` 配置区分。先按 OpenAI 标准实现, zhipu 走 `extra_body` 自定义。

### provider 模板

```yaml
- name: openai-whisper
  endpoint: https://api.openai.com/v1/audio/transcriptions
  model: whisper-1
  api_key_env: OPENAI_API_KEY
  mode: asr
  trusted: false

- name: openai-gpt4o-audio
  endpoint: https://api.openai.com/v1/chat/completions
  model: gpt-4o-audio-preview
  api_key_env: OPENAI_API_KEY
  mode: chat
  disabled: true

- name: zhipu-glm-asr
  endpoint: https://open.bigmodel.cn/api/paas/v4/audio/transcriptions
  model: glm-asr
  api_key_env: ZHIPU_API_KEY
  mode: asr
  trusted: true
  notes: "智谱 ASR, OpenAI 兼容"

- name: qwen-audio
  endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
  model: qwen-audio-turbo
  api_key_env: DASHSCOPE_API_KEY
  mode: chat
  disabled: true
```

## Out of Scope

- TTS (语音合成 — 单独 skill 后续加)
- 实时流式 ASR (websocket)
- 说话人分离 (diarization)
- 视频音轨提取 (走 cortex-video-understand frames 模式后续扩展)

## Technical Notes

- multipart helper 加到 `_provider_common.py`: `http_multipart(url, headers, fields, files, timeout)`
- audio mime 映射: wav/mp3/m4a/webm/flac/ogg
- transcribe 默认 `response_format: json` 返回 `{text: "..."}`; 也可配 `verbose_json` (含 segments)
