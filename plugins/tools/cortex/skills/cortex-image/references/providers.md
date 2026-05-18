# cortex-image — Providers

`<vault>/.cortex/config/image-gen.yaml` 驱动多 provider。下表给出常见家族的 endpoint 模板 + 默认 model 名。

## OpenAI-compat 家族 (绝大多数, 推荐)

OpenAI 协议 `POST /v1/images/generations`, body 含 `model / prompt / n / size / [quality, style, response_format]`。`/v1/models` GET 用于 probe。

| Provider | endpoint | 推荐 model | 备注 |
|---|---|---|---|
| OpenAI | `https://api.openai.com/v1/images/generations` | `dall-e-3` (`dall-e-2`) | size: 1024x1024 / 1792x1024 / 1024x1792 (dall-e-3); quality: `standard\|hd`; style: `vivid\|natural` |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<deploy>/images/generations?api-version=2024-02-01` | `dall-e-3` | header 需 `api-key`, 走 `extra_headers` |
| SiliconFlow | `https://api.siliconflow.cn/v1/images/generations` | `black-forest-labs/FLUX.1-schnell` | OpenAI 协议兼容 |
| Together.AI | `https://api.together.xyz/v1/images/generations` | `black-forest-labs/FLUX.1-schnell` | OpenAI 协议 |
| DeepInfra | `https://api.deepinfra.com/v1/openai/images/generations` | `stabilityai/sd3.5` | OpenAI 协议 |
| 智谱 BigModel | `https://open.bigmodel.cn/api/paas/v4/images/generations` | `glm-image` / `cogview-4` / `cogview-3-flash` | 同 OpenAI 响应形态 (`data[].url`); 默认 size `1280x1280`; 不接受 `n` 字段 |

## 非 OpenAI 协议家族 (需自写 extra_body 适配, 当前 CLI 走 OpenAI 协议 — 这些 provider 可配但 generate 路径需 wrapper 改造)

| Provider | endpoint | 协议特点 |
|---|---|---|
| Stability AI (REST) | `https://api.stability.ai/v2beta/stable-image/generate/sd3` | multipart/form-data, response 是图片 bytes |
| Replicate | `https://api.replicate.com/v1/predictions` | 异步 polling, 需 `Prefer: wait` header |
| 自部署 SD WebUI (A1111) | `http://<host>:7860/sdapi/v1/txt2img` | 局域网常用, key 通常无, 走 LAN |
| ComfyUI | `http://<host>:8188/prompt` | workflow json, 重度自定义 |
| Google Imagen 4 | `https://generativelanguage.googleapis.com/v1beta/models/imagen-4:generateImages` | API key in query string |

**当前 image_gen.py 仅原生支持 OpenAI-compat 路径** (POST body JSON, response `data[0].url|b64_json`)。其他协议需走 `extra_body` 微调或自写适配层。

## probe 策略

`image_gen probe` 默认 `GET <base>/models`:

1. **base 推导**: 从 endpoint 去尾, 例如 `https://api.openai.com/v1/images/generations` → `https://api.openai.com/v1/models`
2. **认证 header**: `Authorization: Bearer <key>` (key 从 `api_key_env` 或 `api_key` 取, env 优先)
3. **判定**:
   | HTTP | 含义 | 行为 |
   |---|---|---|
   | 200-299 | 健康 | `last_status` 写; `disabled=false` 自动恢复 |
   | 401/403 | 鉴权失败 | `trusted=true` → 保留; `trusted=false` → 自动 `disabled=true` |
   | 404 | 路径错 / 不支持 /models | 同 401 处理 (路径 + 协议错) |
   | 5xx | 服务器临时错 | 仅记 last_status, 不 disable |
   | timeout / 网络错 | 网络问题 | 仅记 last_status=0, 不 disable |

**不发实付 POST**: probe 只读 `/models`, 0 成本; 真要确认能出图, 跑一次 `generate` 1024x1024 standard 即可。

## 安全建议

1. **优先 api_key_env**: yaml commit 进 git 时不暴露密钥; AI / 同事拉仓库不会拿到 key
2. **inline api_key**: validate_config.py 会 warn; 若 vault git 仓库, 改用 env
3. **GitHub secret scanning**: OpenAI / Anthropic / Stability key 都在 GitHub 推送扫描列表, 一旦 commit 会自动 revoke + email; 不要 push
4. **mask 日志**: image_gen.py 内部 mask key 中间 80% (仅首尾各 N 字符显示); stderr / stdout 都不会泄漏完整 key
5. **trusted=true 慎用**: 仅用于已知 endpoint 偶尔返 4xx 的合理 provider (例如 ComfyUI 无认证)

## yaml 示例 (3 provider 混合)

```yaml
providers:
  - name: openai-dalle3
    endpoint: https://api.openai.com/v1/images/generations
    api_key_env: OPENAI_API_KEY
    model: dall-e-3
    trusted: false
    timeout_seconds: 120
    extra_body:
      quality: hd
      style: vivid

  - name: siliconflow-flux
    endpoint: https://api.siliconflow.cn/v1/images/generations
    api_key_env: SILICONFLOW_API_KEY
    model: black-forest-labs/FLUX.1-schnell
    trusted: false
    timeout_seconds: 60

  - name: zhipu-glm-image
    endpoint: https://open.bigmodel.cn/api/paas/v4/images/generations
    api_key_env: ZHIPU_API_KEY
    model: glm-image
    trusted: false
    timeout_seconds: 60
    extra_body:
      size: 1280x1280
      quality: hd

  - name: local-comfy
    endpoint: http://localhost:8188/prompt
    api_key: not-used
    model: sdxl-base-1.0
    trusted: true        # local 无认证, 4xx 也不剔除
    timeout_seconds: 300
    notes: "local ComfyUI, custom workflow"

defaults:
  random_selection: true
  output_dir: _assets/images
```
