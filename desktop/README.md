# CCPlugin Desktop

跨平台插件管理工具 - 基于 Tauri 2.x + React + TypeScript

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run tauri dev
```

首次启动需要编译Rust代码（约1-2分钟），后续启动会快很多。

### 3. 构建生产版本

```bash
npm run tauri build
```

## 项目结构

```
desktop/
├── src/                    # React前端代码
│   ├── components/         # 可复用组件
│   │   ├── ui/            # Shadcn UI组件
│   │   └── Layout/        # 布局组件
│   ├── pages/             # 页面组件
│   ├── hooks/             # 自定义Hooks
│   ├── services/          # 服务层
│   ├── types/             # TypeScript类型
│   ├── lib/               # 工具库
│   └── styles/            # 样式文件
├── src-tauri/             # Rust后端代码
│   ├── src/
│   │   ├── commands/      # Tauri Commands
│   │   ├── services/      # 业务服务
│   │   ├── models/        # 数据模型
│   │   └── lib.rs         # 入口文件
│   ├── Cargo.toml         # Rust依赖
│   └── tauri.conf.json    # Tauri配置
├── TESTING.md             # 测试指南
└── README.md              # 本文件
```

## 技术栈

### 前端
- **React 18** - UI框架
- **TypeScript 5.x** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS 4.x** - CSS框架
- **Shadcn UI** - UI组件库
- **React Router** - 路由管理
- **Lucide React** - 图标库

### 后端
- **Tauri 2.x** - 跨平台框架
- **Rust** - 系统语言
- **Tokio** - 异步运行时

### Tauri Plugins
- `tauri-plugin-shell` - Shell命令执行
- `tauri-plugin-notification` - 系统通知
- `tauri-plugin-autostart` - 开机自启
- `tauri-plugin-single-instance` - 单实例
- `tauri-plugin-store` - 本地存储
- `tauri-plugin-log` - 日志
- `tauri-plugin-process` - 进程管理

## 已实现功能

### Phase 1: 核心框架 ✅
- [x] Tauri + React项目初始化
- [x] Tailwind CSS + Shadcn UI配置
- [x] 7个页面布局和路由
- [x] 系统托盘（显示/隐藏/退出）
- [x] 单实例模式
- [x] 开机自启动
- [x] 窗口关闭行为（隐藏到托盘）

### Phase 2: Python集成 ✅
- [x] Rust后端Python桥接服务
- [x] 调用uvx命令执行Python脚本
- [x] 支持install/update/clean/info命令
- [x] 实时进度反馈
- [x] 前端TypeScript类型定义
- [x] React Hook状态管理
- [x] Marketplace测试UI

## 待实现功能

### Phase 3: 插件管理 🚧
- [ ] 读取marketplace.json
- [ ] 检测已安装插件
- [ ] 插件卡片列表UI
- [ ] 搜索和分类过滤
- [ ] 插件详情弹窗
- [ ] README渲染

### Phase 4: 通知集成
- [ ] Socket通知服务器
- [ ] 修改Python notify插件
- [ ] Desktop App通知显示
- [ ] 通知历史记录

### Phase 5: 高级功能
- [ ] Dashboard仪表板
- [ ] 自动更新功能
- [ ] 日志查看器
- [ ] 开发者工具

### Phase 6: 打包分发
- [ ] 跨平台打包
- [ ] 代码签名
- [ ] GitHub Release自动化

## 测试

详细测试指南请查看 [TESTING.md](./TESTING.md)

### 快速测试

1. **启动应用**：`npm run tauri dev`
2. **测试托盘**：点击系统托盘图标
3. **测试Python**：进入Marketplace页面，点击"安装插件"

### 核心测试清单
- [ ] 应用正常启动
- [ ] 7个页面可访问
- [ ] 系统托盘正常工作
- [ ] Python命令可以执行
- [ ] 进度反馈正常显示

## 开发指南

### 添加新页面

1. 创建页面组件：`src/pages/NewPage/index.tsx`
2. 在路由中注册：`src/routes/index.tsx`
3. 在侧边栏添加导航：`src/components/Layout/Sidebar.tsx`

### 添加Tauri Command

1. 在Rust中定义command：`src-tauri/src/commands/`
2. 注册到invoke_handler：`src-tauri/src/lib.rs`
3. 在前端调用：`src/services/tauri-commands.ts`

### 添加UI组件

1. 安装Shadcn组件：`npx shadcn-ui@latest add <component>`
2. 组件会自动添加到：`src/components/ui/`

## 性能指标

- **安装包大小**: < 10MB（vs Electron 80-150MB）
- **内存占用**: 30-40MB空闲（vs Electron 200-300MB）
- **启动时间**: < 0.5秒
- **首次编译**: 1-2分钟（后续增量编译 < 10秒）

## 环境要求

- **Node.js**: >= 18.0.0
- **Rust**: >= 1.90.0
- **Python**: >= 3.11（用于插件管理）
- **uv**: 最新版本

## 常见问题

### Q: 启动报错 "command not found: cargo"
A: 需要安装Rust：`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### Q: npm run tauri dev 卡住不动
A: 首次编译需要1-2分钟，请耐心等待。查看终端输出确认是否在编译。

### Q: 系统托盘图标不显示
A: macOS上可能需要授予通知权限。前往 系统设置 > 通知 > CCPlugin Desktop

### Q: Python命令执行失败
A: 确保已安装uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`

## 许可证

AGPL-3.0-or-later

## 贡献

欢迎提交Issue和Pull Request！

## 相关链接

- [Tauri文档](https://tauri.app/)
- [React文档](https://react.dev/)
- [Shadcn UI](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
