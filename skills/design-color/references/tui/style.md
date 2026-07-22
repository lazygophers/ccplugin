# TUI 媒介 · 色彩与键位风格模板

TUI 风格 = 色彩约束 + 键位风格 + 主题的一致性。本文件给方法论 + **现成主题与键位模板**，复制即用。布局 / 场景 / 组件的结构问题在姊妹 skill `design-uiux`，本文件只管色彩与风格落地。

## 选型流程

1. **定受众**：power user（vim 风）/ 普通（通用风）/ 长期（emacs 风）
2. **出三方向**：主题 + 键位组合，差异化
3. **并排对比**：同界面三套主题实机看
4. **固化**：色 token + 键位表写死，全局一致

## 色彩约束原则

- 终端色滥用易花：默认色为主，强调色点缀
- 背景色只用于焦点 / 选中 / 状态标记
- 全屏彩色背景疲劳，小范围用
- 语义色固定（error 红 / success 绿 / warning 黄 / info 蓝），跨主题一致
- 对比足够：终端字小，低对比更难读

---

## 现成主题模板

### 模板 1 · Gruvbox 暖色（经典 vim 风）

```
bg:          #282828  (dark0_hard)
bg-soft:     #3c3836
fg:          #ebdbb2
fg-muted:    #a89984
border:      #504945
accent:      #fe8019  (orange)
selected:    bg=#fe8019 fg=#282828  (反色)
error:       #fb4934  (red)
success:     #b8bb26  (green)
warning:     #fabd2f  (yellow)
info:        #83a598  (blue)
title:       #d3869b  (purple)
```
气质：暖、复古、vim 用户熟悉。适合开发工具。

### 模板 2 · Tokyo Night 冷色（现代编辑器风）

```
bg:          #1a1b26
bg-soft:     #16161e
fg:          #c0caf5
fg-muted:    #565f89
border:      #2a2e3f
accent:      #7aa2f7  (blue)
selected:    bg=#7aa2f7 fg=#1a1b26
error:       #f7768e  success: #9ece6a  warning: #e0af68  info: #7aa2f7
title:       #bb9af7
```
气质：冷、深、低饱和。适合夜间长期使用。

### 模板 3 · Solarized（科学配色，色盲友好）

```
bg:          #002b36  (base03)
bg-soft:     #073642
fg:          #93a1a1  (base1)
fg-muted:    #586e75
border:      #073642
accent:      #268bd2  (blue)
selected:    bg=#073642 fg=#93a1a1
error:       #dc322f  success: #859900  warning: #b58900  info: #268bd2
title:       #6c71c4
```
气质：感知科学、对比适中、长时间不累。适合数据工具。

### 模板 4 · 极简单色（最大兼容，16 色安全）

```
bg:          default (终端底)
fg:          default
border:      white dim
accent:      cyan
selected:    reverse
error:       red  success: green  warning: yellow  info: blue
```
气质：朴素、任何终端不崩。适合需广泛兼容的工具。

---

## 色域降级表（真彩 → 256 → 16）

| 真彩色 | 256 | 16 | 语义 |
|--------|-----|----|------|
| #fb4934 | 203 | red | error |
| #b8bb26 | 142 | green | success |
| #fabd2f | 214 | yellow | warning |
| #83a598 | 109 | blue | info |
| #fe8019 | 208 | — | accent |

实现：检测 `$COLORTERM` / `$TERM`，选对应表。

## 终端兼容速查

选主题前先确认目标终端的色域与特性支持：

| 终端 | 真彩(TrueColor) | 256 色 | 斜体 | 连字 | 模糊背景 | 备注 |
|------|:---:|:---:|:---:|:---:|:---:|------|
| iTerm2 (macOS) | ✅ | ✅ | ✅ | ✅ | ✅ | 开发者首选 |
| Terminal.app (macOS) | ✅ | ✅ | ⚠️有限 | ❌ | ❌ | 系统 Basic，兼容底线 |
| Windows Terminal | ✅ | ✅ | ✅ | ✅ | ✅ | Win 默认现代终端 |
| Alacritty | ✅ | ✅ | ✅ | ✅ | ❌ | GPU 渲染、极快 |
| kitty | ✅ | ✅ | ✅ | ✅ | ✅ | 图形 / 图片支持 |
| WezTerm | ✅ | ✅ | ✅ | ✅ | ✅ | 跨平台、可编程 |
| GNOME Terminal | ✅ | ✅ | ⚠️需开 | ❌ | ❌ | Linux 桌面默认 |
| tmux 内层 | 继承 | 继承 | 需 `tmux -2` / `set -g default-terminal tmux-256color` + `terminal-overrides` | | | tmux 自身需配 truecolor 透传 |
| Linux TTY (Ctrl+F1) | ❌ | ❌ | ❌ | ❌ | ❌ | 仅 16 色，必须降级到模板 4 极简单色 |
| CI / 日志 / 管道 | ❌ | ❌ | ❌ | ❌ | ❌ | 非 TTY，全关色 |

### 色域检测策略

```
COLORTERM=truecolor   → 用真彩 hex（模板 1/2/3 全色）
TERM=*-256color       → 用 256 色码（见色域降级表）
TERM=linux / TTY      → 16 色（模板 4 极简单色）
非 TTY（管道/CI）      → 关色，纯文本（CLI 同理）
```

实现：启动时检测 `$COLORTERM` / `$TERM` / `isatty(stdout)`，选对应色表。跨终端通用工具默认走「256 色 + 模板 4 降级」最安全。

## 键位风格模板

| 风格 | 导航 | 选定 | 退出 | 模态 | 受众 |
|------|------|------|------|------|------|
| Vim 风 | `hjkl` | `Enter` | `:q` / `ESC` | 插入 `i` / 命令 `:` | 开发者、power user |
| 通用风 | `↑↓←→` / `Tab` | `Enter` | `q` / `ESC` | 少模态 | 普通用户 |
| Emacs 风 | `C-n/C-p/C-f/C-b` | `Enter` | `C-g` | mini-buffer | 长期用户 |

### Vim 风键位表（常用）

```
导航:    j/k 下上  h/l 左右  g/G 顶底  Ctrl-u/d 翻页
栏切换:  Tab / Shift-Tab   或  H/L (窗口左右)
选定:    Enter   标记:  Space / m
操作:    对象键 (d=删, e=编, 按工具自定义)
模态:    i 插入  ESC 回正常  : 命令
帮助:    ?      退出:  :q / q
命令面板:  :  或  Ctrl-P
```

### 通用风键位表

```
导航:    ↑↓ 上下  Tab 切栏  PgUp/PgDn 翻页
选定:    Enter   标记:  Space
操作:    快捷键菜单显示 (底栏)
退出:    q 或 ESC
帮助:    ? 或 F1
```

## 键位设计原则

- 全键盘可达（不依赖鼠标）
- 常用键单键，次级组合键
- 危险操作（删除 / 退出）组合键或确认防误触（`q` 退出小心和输入冲突）
- 快捷键底栏常驻（发现性）
- 支持 `?` 弹快捷键帮助

## 自检

- [ ] 主题色 token 化，亮暗可切
- [ ] 色域降级链就位
- [ ] 键位风格统一（不混 vim/emacs）
- [ ] 快捷键底栏常驻 + `?` 帮助
- [ ] 危险操作有防误触
