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
        sky: {
          50: 'var(--sky-50)', 100: 'var(--sky-100)', 200: 'var(--sky-200)',
          300: 'var(--sky-300)', 400: 'var(--sky-400)', 500: 'var(--sky-500)',
          600: 'var(--sky-600)', 700: 'var(--sky-700)', 800: 'var(--sky-800)',
          900: 'var(--sky-900)', 950: 'var(--sky-950)',
        },
        sand: {
          50: 'var(--sand-50)', 100: 'var(--sand-100)', 200: 'var(--sand-200)',
          300: 'var(--sand-300)', 400: 'var(--sand-400)', 500: 'var(--sand-500)',
          600: 'var(--sand-600)', 700: 'var(--sand-700)', 800: 'var(--sand-800)',
          900: 'var(--sand-900)', 950: 'var(--sand-950)',
        },
        ocean: {
          50: 'var(--ocean-50)', 100: 'var(--ocean-100)', 200: 'var(--ocean-200)',
          300: 'var(--ocean-300)', 400: 'var(--ocean-400)', 500: 'var(--ocean-500)',
          600: 'var(--ocean-600)', 700: 'var(--ocean-700)', 800: 'var(--ocean-800)',
          900: 'var(--ocean-900)', 950: 'var(--ocean-950)',
        },
        stone: {
          50: 'var(--stone-50)', 100: 'var(--stone-100)', 200: 'var(--stone-200)',
          300: 'var(--stone-300)', 400: 'var(--stone-400)', 500: 'var(--stone-500)',
          600: 'var(--stone-600)', 700: 'var(--stone-700)', 800: 'var(--stone-800)',
          900: 'var(--stone-900)', 950: 'var(--stone-950)',
        },
        success: 'var(--success)', warning: 'var(--warning)', danger: 'var(--danger)', info: 'var(--info)',
        bg: 'var(--bg)', card: 'var(--card)', fg: 'var(--fg)', head: 'var(--head)',
        muted: 'var(--muted)', brd: 'var(--brd)', line: 'var(--line)',
        accent: 'var(--accent)', accent2: 'var(--accent2)',
        'bg-canvas': 'var(--bg-canvas)', 'bg-panel': 'var(--bg-panel)',
        'bg-elevated': 'var(--bg-elevated)', 'bg-hover': 'var(--bg-hover)',
        'st-planning': 'var(--st-planning)', 'st-pending': 'var(--st-pending)',
        'st-ready': 'var(--st-ready)', 'st-active': 'var(--st-active)',
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
