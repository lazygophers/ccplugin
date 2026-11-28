# 水印

## 显性水印

全页斜向 -30° 平铺文字（SVG data URI 背景），默认文字 `{author} · {date}`、透明度 0.06；`pointer-events: none`，不拦截点击和选中；`print-color-adjust: exact`，打印时保留。程序员风用白字，其余风格用黑字。配置见 [config.md](config.md) 的 `watermark.visible.*`。

## 隐水印

载荷为 JSON：`{"id": "<随机 UUID>", "author": "<author.name>", "version": <文档版本>, "time": "<ISO 生成时间>"}`。四种写法各有开关（`watermark.hidden.*`）：

| 写法 | 位置 | 编码 | 写入时机 |
|---|---|---|---|
| `zeroWidth` | 每个 `paragraph` 与 `summary.text` 的首字之后 | U+2060 起止，中间每比特一个字符：0 = U+200B、1 = U+200C；比特流为载荷 UTF-8 字节，高位在前 | CLI 渲染时写入内容 |
| `meta` | `<head>` | `<meta name="show-me:<键>" content="…">`（键为 id、author、version、time） 与 `<!-- show-me:<base64 载荷> -->` | CLI 渲染时写入模板 |
| `pattern` | 全页固定背景层 | 首行实心定位条，之后按方阵逐比特画 3px 方块（1 = 有块），`fill-opacity: 0.01`；截图后提高对比度可见 | 浏览器渲染时生成 |
| `images` 位图 | `image` 块与 logo 的 png/jpg/gif/webp | 比特流 = 4 字节大端长度 + 载荷 UTF-8；逐像素写入 R、G、B 最低位，跳过 alpha < 255 的像素；写入后以 PNG 替换 `src`（容量不足时保留原图） | 浏览器渲染时经 canvas 写入 |
| `images` SVG | SVG 根元素首个子节点 | `<metadata>show-me:<base64 载荷></metadata>` | CLI 内联时写入 |

## decode

```bash
node <skill 目录>/scripts/show-me.mjs decode <file>   # HTML、SVG、PNG 或含零宽字符的文本文件
pbpaste | node <skill 目录>/scripts/show-me.mjs decode -   # 粘贴文本
```

输出一行 JSON：`{"via": "meta" | "comment" | "svg-metadata" | "zero-width" | "png-lsb", "payload": {…}}`。读取顺序：PNG 签名 → 最低位；否则依次 meta、HTML 注释、SVG metadata、零宽字符。找不到载荷时退出码 2，stderr `未找到 show-me 水印载荷`。

PNG 解码器只支持 8 位 RGB / RGBA、非隔行（浏览器另存的图片即此格式）；其他格式报错退出码 2。

限制：零宽字符在纯文本粘贴中保留，经富文本编辑器清洗或 OCR 后丢失；位图最低位经有损压缩（JPEG 重存、截图缩放）后丢失，此时只剩背景图案可目测。
