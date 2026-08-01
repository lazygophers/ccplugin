// Tailwind 预构建配置 — 替代原 cdn.tailwindcss.com 运行时 JIT (省 ~400KB JS + 首屏 JIT 编译)。
// 改了 src/ 里的 class 后重新生成 src/tailwind.css:
//   cd assets/webapp && npx tailwindcss@3 -c tailwind.config.js -i tailwind.in.css -o src/tailwind.css --minify
// 注: 色值是裸 var(--x), 故 `bg-card/60` 这类透明度修饰符不生成 (CDN JIT 同样不生成, 行为对齐)。
module.exports = {
  content: {
    files: ['./src/new/**/*.{html,js}', './src/*.js'],
    // h() 的 tag 简写里响应式类写成 'div.lg\\:grid-cols-3' (运行时脱掉反斜杠)。
    // 扫描器按字面看到 `lg\:grid-cols-3` 不认作候选 → 响应式类一个都不生成。先脱转义再扫。
    transform: { js: (c) => c.replace(/\\+:/g, ':') },
  },
  darkMode: ['class', '[data-theme="skein-dark"]'],
  theme: {
    extend: {
      colors: {
        amber: {
          50: 'var(--amber-50)', 100: 'var(--amber-100)', 200: 'var(--amber-200)',
          300: 'var(--amber-300)', 400: 'var(--amber-400)', 500: 'var(--amber-500)',
          600: 'var(--amber-600)', 700: 'var(--amber-700)', 800: 'var(--amber-800)',
          900: 'var(--amber-900)', 950: 'var(--amber-950)',
        },
        slate: {
          50: 'var(--slate-50)', 100: 'var(--slate-100)', 200: 'var(--slate-200)',
          300: 'var(--slate-300)', 400: 'var(--slate-400)', 500: 'var(--slate-500)',
          600: 'var(--slate-600)', 700: 'var(--slate-700)', 800: 'var(--slate-800)',
          900: 'var(--slate-900)', 950: 'var(--slate-950)',
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
