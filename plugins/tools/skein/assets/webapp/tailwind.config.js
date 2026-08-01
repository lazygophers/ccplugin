// Tailwind 预构建配置 — 替代原 cdn.tailwindcss.com 运行时 JIT (省 ~400KB JS + 首屏 JIT 编译)。
// 改了 src/ 里的 class 后重新生成 src/tailwind.css:
//   cd assets/webapp && npx tailwindcss@3 -c tailwind.config.js -i tailwind.in.css -o src/tailwind.css --minify
// 注: 色值是裸 var(--x), 故 `bg-card/60` 这类透明度修饰符不生成 (CDN JIT 同样不生成, 行为对齐)。
module.exports = {
  content: {
    files: ['./src/new/**/*.{html,js}', './src/*.js'],
    // h() 的 tag 简写里响应式类写成 'div.lg\\:grid-cols-3', 小数类写成 'div.mb-0\\.5' (运行时脱掉反斜杠)。
    // 扫描器按字面看到 `lg\:grid-cols-3` / `mb-0\.5` 不认作候选 → 响应式类/小数类一个都不生成。先脱转义再扫。
    transform: { js: (c) => c.replace(/\\+:/g, ':').replace(/\\+\./g, '.') },
  },
  darkMode: ['class', '[data-theme="skein-dark"]'],
  theme: {
    extend: {
      colors: {
        ocean:      { foam: 'var(--ocean-foam)', shallow: 'var(--ocean-shallow)', mid: 'var(--ocean-mid)', deep: 'var(--ocean-deep)', abyss: 'var(--ocean-abyss)' },
        whiteSand:  { pearl: 'var(--whiteSand-pearl)', shell: 'var(--whiteSand-shell)', cream: 'var(--whiteSand-cream)' },
        goldSand:   { light: 'var(--goldSand-light)', mid: 'var(--goldSand-mid)', deep: 'var(--goldSand-deep)', sunset: 'var(--goldSand-sunset)' },
        night:      { base: 'var(--night-base)', mid: 'var(--night-mid)', deep: 'var(--night-deep)' },
        success: 'var(--success)', warning: 'var(--warning)', danger: 'var(--danger)',
        bg: 'var(--bg)', card: 'var(--card)', fg: 'var(--fg)', head: 'var(--head)',
        muted: 'var(--muted)', brd: 'var(--brd)', line: 'var(--line)',
        accent: 'var(--accent)', accent2: 'var(--accent2)',
        'st-pending': 'var(--st-pending)', 'st-active': 'var(--st-active)',
        'st-check': 'var(--st-check)', 'st-done': 'var(--st-done)', 'st-failed': 'var(--st-failed)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SF Mono', 'JetBrains Mono', 'monospace'],
      },
      borderRadius: { DEFAULT: 'var(--radius)', sm: 'var(--radius-sm)', lg: 'var(--radius-lg)' },
    },
  },
};
