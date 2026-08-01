// Tailwind 预构建配置 — Ocean & Sand 设计系统 (nd_design_system.html 移植)
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
        // Ocean & Sand 设计系统色板
        ocean: {
          50: 'var(--oc-ocean-50)', 100: 'var(--oc-ocean-100)', 200: 'var(--oc-ocean-200)',
          300: 'var(--oc-ocean-300)', 400: 'var(--oc-ocean-400)', 500: 'var(--oc-ocean-500)',
          600: 'var(--oc-ocean-600)', 700: 'var(--oc-ocean-700)', 800: 'var(--oc-ocean-800)',
          900: 'var(--oc-ocean-900)', 950: 'var(--oc-ocean-950)',
        },
        sand: {
          50: 'var(--oc-sand-50)', 100: 'var(--oc-sand-100)', 200: 'var(--oc-sand-200)',
          300: 'var(--oc-sand-300)', 400: 'var(--oc-sand-400)', 500: 'var(--oc-sand-500)',
          600: 'var(--oc-sand-600)', 700: 'var(--oc-sand-700)', 800: 'var(--oc-sand-800)',
          900: 'var(--oc-sand-900)', 950: 'var(--oc-sand-950)',
        },
        coral: {
          50: 'var(--oc-coral-50)', 100: 'var(--oc-coral-100)', 200: 'var(--oc-coral-200)',
          300: 'var(--oc-coral-300)', 400: 'var(--oc-coral-400)', 500: 'var(--oc-coral-500)',
          600: 'var(--oc-coral-600)', 700: 'var(--oc-coral-700)', 800: 'var(--oc-coral-800)',
          900: 'var(--oc-coral-900)', 950: 'var(--oc-coral-950)',
        },
        seaweed: {
          50: 'var(--oc-seaweed-50)', 100: 'var(--oc-seaweed-100)', 200: 'var(--oc-seaweed-200)',
          300: 'var(--oc-seaweed-300)', 400: 'var(--oc-seaweed-400)', 500: 'var(--oc-seaweed-500)',
          600: 'var(--oc-seaweed-600)', 700: 'var(--oc-seaweed-700)', 800: 'var(--oc-seaweed-800)',
          900: 'var(--oc-seaweed-900)', 950: 'var(--oc-seaweed-950)',
        },
        shell: {
          50: 'var(--oc-shell-50)', 100: 'var(--oc-shell-100)', 200: 'var(--oc-shell-200)',
          300: 'var(--oc-shell-300)', 400: 'var(--oc-shell-400)', 500: 'var(--oc-shell-500)',
          600: 'var(--oc-shell-600)', 700: 'var(--oc-shell-700)', 800: 'var(--oc-shell-800)',
          900: 'var(--oc-shell-900)', 950: 'var(--oc-shell-950)',
        },
        sunset: {
          50: 'var(--oc-sunset-50)', 100: 'var(--oc-sunset-100)', 200: 'var(--oc-sunset-200)',
          300: 'var(--oc-sunset-300)', 400: 'var(--oc-sunset-400)', 500: 'var(--oc-sunset-500)',
          600: 'var(--oc-sunset-600)', 700: 'var(--oc-sunset-700)', 800: 'var(--oc-sunset-800)',
          900: 'var(--oc-sunset-900)', 950: 'var(--oc-sunset-950)',
        },
        deepsea: {
          50: 'var(--oc-deepsea-50)', 100: 'var(--oc-deepsea-100)', 200: 'var(--oc-deepsea-200)',
          300: 'var(--oc-deepsea-300)', 400: 'var(--oc-deepsea-400)', 500: 'var(--oc-deepsea-500)',
          600: 'var(--oc-deepsea-600)', 700: 'var(--oc-deepsea-700)', 800: 'var(--oc-deepsea-800)',
          900: 'var(--oc-deepsea-900)', 950: 'var(--oc-deepsea-950)',
        },
        foam: {
          50: 'var(--oc-foam-50)', 100: 'var(--oc-foam-100)', 200: 'var(--oc-foam-200)',
          300: 'var(--oc-foam-300)', 400: 'var(--oc-foam-400)', 500: 'var(--oc-foam-500)',
          600: 'var(--oc-foam-600)', 700: 'var(--oc-foam-700)', 800: 'var(--oc-foam-800)',
          900: 'var(--oc-foam-900)', 950: 'var(--oc-foam-950)',
        },
        reef: {
          50: 'var(--oc-reef-50)', 100: 'var(--oc-reef-100)', 200: 'var(--oc-reef-200)',
          300: 'var(--oc-reef-300)', 400: 'var(--oc-reef-400)', 500: 'var(--oc-reef-500)',
          600: 'var(--oc-reef-600)', 700: 'var(--oc-reef-700)', 800: 'var(--oc-reef-800)',
          900: 'var(--oc-reef-900)', 950: 'var(--oc-reef-950)',
        },
        neutral: {
          50: 'var(--oc-neutral-50)', 100: 'var(--oc-neutral-100)', 200: 'var(--oc-neutral-200)',
          300: 'var(--oc-neutral-300)', 400: 'var(--oc-neutral-400)', 500: 'var(--oc-neutral-500)',
          600: 'var(--oc-neutral-600)', 700: 'var(--oc-neutral-700)', 800: 'var(--oc-neutral-800)',
          900: 'var(--oc-neutral-900)', 950: 'var(--oc-neutral-950)',
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
        sans: ['Maple Mono', 'Maple Mono NF', 'Maple Mono SC', 'monospace'],
        mono: ['Maple Mono', 'Maple Mono NF', 'Maple Mono SC', 'monospace'],
      },
      borderRadius: { DEFAULT: 'var(--radius)', sm: 'var(--radius-sm)', lg: 'var(--radius-lg)' },
    },
  },
};
