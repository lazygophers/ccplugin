// 渲染期隐水印：背景编码图案与位图最低位。编码规则与 scripts/show-me.mjs 的 decode 一致
const bytes = (s: string) => new TextEncoder().encode(s)

// 比特流 = 4 字节大端长度 + UTF-8 载荷；逐像素写入 R、G、B 最低位，跳过 alpha < 255 的像素（预乘 alpha 会改写最低位）
export function embedLsb(px: Uint8ClampedArray, payload: string): boolean {
  const data = bytes(payload), n = data.length
  const all = new Uint8Array(4 + n)
  all.set([n >>> 24, (n >>> 16) & 255, (n >>> 8) & 255, n & 255]); all.set(data, 4)
  const bits = all.length * 8
  let b = 0
  for (let p = 0; p < px.length && b < bits; p += 4) {
    if (px[p + 3] !== 255) continue
    for (let c = 0; c < 3 && b < bits; c++, b++) px[p + c] = (px[p + c] & 254) | ((all[b >> 3] >> (7 - (b & 7))) & 1)
  }
  return b === bits
}

// 背景编码图案：载荷比特按方阵排布，1 位画 3px 方块；fill-opacity 0.01，提高对比度后可见
export function patternUrl(payload: string, dark: boolean) {
  const data = bytes(payload), bits = data.length * 8, side = Math.ceil(Math.sqrt(bits + 8)), cell = 3
  let d = "M0 0h" + cell * side + "v" + cell + "h-" + cell * side + "z" // 首行实心：定位标记
  for (let b = 0; b < bits; b++) {
    if (!((data[b >> 3] >> (7 - (b & 7))) & 1)) continue
    const k = b + side, x = (k % side) * cell, y = Math.floor(k / side) * cell
    d += "M" + x + " " + y + "h" + cell + "v" + cell + "h-" + cell + "z"
  }
  const w = side * cell, h = (Math.ceil(bits / side) + 1) * cell
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '"><path d="' + d + '" fill="' + (dark ? "#fff" : "#000") + '" fill-opacity="0.01"/></svg>'
  return 'url("data:image/svg+xml,' + encodeURIComponent(svg) + '")'
}

// 位图 data: URI 经 canvas 写入最低位后改为 PNG；失败时保留原图
export function watermarkImage(src: string, payload: string): Promise<string> {
  if (!/^data:image\/(png|jpe?g|webp|gif);/.test(src)) return Promise.resolve(src)
  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => {
      const c = document.createElement("canvas")
      c.width = img.naturalWidth; c.height = img.naturalHeight
      const x = c.getContext("2d")
      if (!x || !c.width) return resolve(src)
      x.drawImage(img, 0, 0)
      const d = x.getImageData(0, 0, c.width, c.height)
      if (!embedLsb(d.data, payload)) return resolve(src)
      x.putImageData(d, 0, 0)
      resolve(c.toDataURL("image/png"))
    }
    img.onerror = () => resolve(src)
    img.src = src
  })
}
