# design 技能分类

设计类 skill 合集: 按产出媒介(medium)拆分，每种媒介一个 skill。

| skill | 媒介 | 用途 |
|---|---|---|
| [html-design](html-design/) | HTML / Web | HTML-first 设计工作台——UI/UX 界面、数据可视化、图像设计、演示排版，所有产出以 HTML 落地后打包导出 |
| [app-design](app-design/) | 原生 App | 移动(iOS/Android)与桌面应用 UI/UX——平台习惯、导航、手势、组件设计 |
| [cli-design](cli-design/) | 命令行 | CLI 接口设计——命令树、flags/args、输出格式、错误信息、帮助文本、配置链 |
| [tui-design](tui-design/) | 终端 UI | 全屏终端应用——布局、组件、色彩约束、焦点流转、键位设计、框架选型 |

## 路由 · 按 medium 选入口

先判产物是什么媒介，再进对应 skill：

```
产物形态？
├─ Web 页面 / 原型 / 可视化 / 图像 / 幻灯片  → html-design
├─ 原生 App(iOS/Android/桌面)               → app-design
├─ 命令行工具(./tool <command>)              → cli-design
└─ 终端全屏交互应用(TUI)                     → tui-design
```

边界判断：

- 网页内跑的 App mockup → html-design（HTML 出原型）
- 跨平台框架(Flutter/RN/Electron)的 App 设计 → app-design
- 命令行工具带交互向导但仍命令式 → cli-design
- 终端里全屏多面板 GUI → tui-design

## 共通原则

四个 skill 共享设计纪律：

- **三方向初稿硬门**：新视觉/接口产出先出三个差异化方向给用户选
- **事实验证先行**：涉及具体产品/技术规格先 WebSearch 验证
- **自检清单**：每个 skill 末尾给可勾验收项
- **token 化 / 一致性**：值取自固定阶，跨场景自适应
