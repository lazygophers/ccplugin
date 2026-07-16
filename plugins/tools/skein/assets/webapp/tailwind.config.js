/** SKEIN webapp Tailwind config (standalone binary, buildless).
 *  语义色/圆角/字型 = board/base.css 令牌契约的薄别名 (真实值定义在 src/input.css @layer base 的 CSS 变量,
 *  oklch 派生 + data-theme 主题覆盖)。此处不烘焙具体配色, 只把变量暴露成 Tailwind token,
 *  故 10 主题切换纯走 <html data-theme> 变量交换, 无需 Tailwind dark class。
 *  状态色 (st-*) 色相语义固定 (pending 蓝/active 橙/check 青/done 绿/failed 红)。
 */
module.exports = {
  content: ['./index.html', './src/**/*.{js,html}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        card: 'var(--card)',
        fg: 'var(--fg)',
        head: 'var(--head)',
        muted: 'var(--muted)',
        brd: 'var(--brd)',
        line: 'var(--line)',
        accent: 'var(--accent)',
        accent2: 'var(--accent2)',
        st: {
          pending: 'var(--st-pending)',
          active: 'var(--st-active)',
          check: 'var(--st-check)',
          done: 'var(--st-done)',
          failed: 'var(--st-failed)',
        },
      },
      borderColor: { DEFAULT: 'var(--brd)' },
      borderRadius: { DEFAULT: 'var(--radius)' },
      fontFamily: { sans: 'var(--font)' },
    },
  },
  plugins: [],
};
