# TUI 媒介 · 组件与焦点流转

TUI 组件是字符格栅上的控件。焦点流转是 TUI 可用性核心。布局见 [layout.md](layout.md)，场景见 [scenes.md](scenes.md)，风格见 [style.md](style.md)。

## 组件

| 组件 | 说明 |
|------|------|
| 列表 List | 可选中、可滚动、高亮当前、标记状态 |
| 表格 Table | 列对齐、可排序、长内容截断+省略 |
| 树 Tree | 层级、可折叠 |
| 表单 Form | 输入框、选择、校验、焦点流转 |
| 底栏 StatusBar | 当前模式、光标位置、快捷键提示 |
| 顶栏 TabBar | 多视图切换标记 |
| 弹层 Modal/Overlay | 确认、搜索、命令面板 |
| 进度 Progress | 进度条、spinner |
| 滚动条 | 内容超屏时可见滚动位置 |
| 命令面板 | 搜索执行长尾操作 |

## 状态完整性

default / focused / selected / disabled / loading / empty / error。

（终端无鼠标 hover 态可不覆盖；focus 是主交互态。）

## 焦点流转（TUI 核心）

- **栏间切换**：`Tab` / `Shift+Tab` 正逆向；或 `hjkl` / 方向键
- **栏内导航**：`j/k` 或 `↑↓` 上下，`g/G` 顶底，`PgUp/PgDn` 翻页
- **模态切换**：进入编辑（插入）、退出（ESC）、命令（`:`）
- **焦点可见**：当前焦点栏 / 控件必须有明显视觉标记（反色 / 边框高亮 / 色块）

**焦点不可见 = 用户不知道在哪。这是 TUI 最常见可用性问题。**

## 命令面板（现代 TUI 趋势）

功能多时避免键位爆炸，命令面板（`:` 或 `Ctrl+P` 触发）收纳长尾操作。例：fzf、helm、lazygit。

混合模式：交互式浏览 + 命令面板检索执行。

## 组件 token 化

- 颜色 token：`color-fg / color-bg / color-accent / color-selected`
- 主题切换一处生效
- 边框字符统一（box-drawing 集）

## 自检

- [ ] 焦点始终可见
- [ ] 状态全覆盖（含 empty / error / loading）
- [ ] 全键盘可达
- [ ] 快捷键底栏常驻 + `?` 帮助
