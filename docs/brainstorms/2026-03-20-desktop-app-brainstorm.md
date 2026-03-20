---
date: 2026-03-20
topic: desktop-app
---

# CCPlugin Desktop - 跨平台桌面应用设计

## 概述

为ccplugin插件市场创建一个功能完整的跨平台桌面应用，提供图形化的插件管理、后台自动更新、系统通知集成等功能。

## 技术栈选择

### 核心框架
- **Tauri 2.x**: 轻量级跨平台框架（<10MB vs Electron 100MB+）
- **前端**: React 18+ + TypeScript 5.x
- **UI库**: Shadcn UI + Tailwind CSS + Radix UI
- **状态管理**: Zustand（轻量级）或 TanStack Query（服务端状态）
- **路由**: React Router v6
- **构建工具**: Vite

### Rust后端
- **Tauri Plugins**:
  - tauri-plugin-shell (调用Python脚本)
  - tauri-plugin-notification (系统通知)
  - tauri-plugin-autostart (开机自启)
  - tauri-plugin-single-instance (单实例)
  - tauri-plugin-store (本地存储)
  - tauri-plugin-updater (应用自更新)
  - tauri-plugin-process (进程管理)
  - tauri-plugin-log (日志)

### Python集成
- **方式**: 通过Shell Command直接调用现有scripts
- **复用**: scripts/install.py, scripts/update.py, scripts/clean.py等
- **通信**: 标准输入输出（JSON格式）+ 进程状态码

## 为什么选择这个方案

### 选择Tauri而非Electron
1. **性能优势**: 内存占用降低80%（30-40MB vs 200-300MB）
2. **体积优势**: 安装包缩小90%（<10MB vs 80-150MB）
3. **安全性**: Rust编译时检查 + 最小权限原则
4. **原生体验**: 使用系统WebView，与系统UI一致

### 选择直接调用Scripts而非HTTP Server
1. **代码复用**: 无需重写Python逻辑，直接复用现有CLI
2. **维护成本**: 单一代码路径，CLI和GUI行为一致
3. **简单性**: 无需管理端口、服务生命周期
4. **权限**: 继承用户权限，无需额外认证

### 选择混合存储模式
1. **一致性**: 核心插件状态读取`~/.claude/plugins/`，与CLI保持同步
2. **灵活性**: UI特定数据（偏好设置、统计、窗口状态）使用Tauri Store
3. **性能**: 缓存CLI数据，减少重复读取

## 项目目录结构

```
ccplugin/desktop/
├── src-tauri/              # Rust后端
│   ├── src/
│   │   ├── main.rs         # 应用入口
│   │   ├── commands/       # Tauri Commands
│   │   │   ├── plugin.rs   # 插件管理命令
│   │   │   ├── notify.rs   # 通知命令
│   │   │   ├── system.rs   # 系统命令
│   │   │   └── mod.rs
│   │   ├── services/       # 业务逻辑
│   │   │   ├── python_bridge.rs  # Python脚本桥接
│   │   │   ├── plugin_watcher.rs # 插件变更监控
│   │   │   ├── auto_updater.rs   # 自动更新服务
│   │   │   └── mod.rs
│   │   ├── models/         # 数据模型
│   │   │   ├── plugin.rs
│   │   │   ├── config.rs
│   │   │   └── mod.rs
│   │   └── utils/          # 工具函数
│   │       ├── logger.rs
│   │       ├── paths.rs
│   │       └── mod.rs
│   ├── Cargo.toml
│   ├── tauri.conf.json     # Tauri配置
│   ├── icons/              # 应用图标
│   └── build.rs
│
├── src/                    # React前端
│   ├── main.tsx           # 入口文件
│   ├── App.tsx            # 根组件
│   ├── routes/            # 路由配置
│   │   └── index.tsx
│   ├── pages/             # 页面组件
│   │   ├── Dashboard/     # 仪表板
│   │   ├── Marketplace/   # 插件市场
│   │   ├── Installed/     # 已安装插件
│   │   ├── Updates/       # 更新中心
│   │   ├── Settings/      # 设置
│   │   ├── Logs/          # 日志查看器
│   │   └── DevTools/      # 开发者工具
│   ├── components/        # 可复用组件
│   │   ├── ui/            # Shadcn UI组件
│   │   ├── PluginCard/
│   │   ├── TrayMenu/
│   │   ├── NotificationCenter/
│   │   └── CommandPalette/
│   ├── hooks/             # 自定义Hooks
│   │   ├── usePlugins.ts
│   │   ├── useNotifications.ts
│   │   ├── useAutoUpdate.ts
│   │   └── usePythonCommand.ts
│   ├── services/          # 前端服务
│   │   ├── tauri-commands.ts  # Tauri命令封装
│   │   ├── plugin-service.ts
│   │   └── notification-service.ts
│   ├── store/             # 状态管理
│   │   ├── plugins.ts
│   │   ├── notifications.ts
│   │   └── settings.ts
│   ├── types/             # TypeScript类型
│   │   ├── plugin.ts
│   │   ├── notification.ts
│   │   └── index.ts
│   ├── lib/               # 工具库
│   │   └── utils.ts
│   └── styles/            # 样式文件
│       └── globals.css
│
├── public/                # 静态资源
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
├── README.md
└── CHANGELOG.md
```

## 核心功能设计

### 1. Python脚本集成

#### 调用方式
```rust
// src-tauri/src/services/python_bridge.rs
use tauri::api::shell::Command;

pub async fn install_plugin(plugin_name: &str, marketplace: &str) -> Result<String, String> {
    let output = Command::new("uvx")
        .args(&[
            "--from",
            "git+https://github.com/lazygophers/ccplugin.git@master",
            "install",
            "lazygophers/ccplugin",
            &format!("{}@{}", plugin_name, marketplace)
        ])
        .output()
        .await
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
```

#### 支持的命令
- `install`: 安装插件
- `update`: 更新插件
- `clean`: 清理缓存
- `info`: 查看插件信息
- `check`: 检查插件状态

#### 进度反馈
```typescript
// src/services/tauri-commands.ts
import { listen } from '@tauri-apps/api/event';

export async function installPluginWithProgress(
  pluginName: string,
  onProgress: (message: string) => void
) {
  const unlisten = await listen('plugin-install-progress', (event) => {
    onProgress(event.payload as string);
  });

  try {
    await invoke('install_plugin', { pluginName });
  } finally {
    unlisten();
  }
}
```

### 2. 通知系统集成

#### 架构设计

**问题**: 现有notify插件使用Python实现，桌面app需要接管通知

**解决方案**: IPC通知桥接

```
Claude Code CLI/Plugins
        ↓
检测桌面App是否运行
        ↓
   是 → 发送到Desktop App (通过文件/socket)
   否 → 使用原Python通知
        ↓
Desktop App处理并显示
```

#### 实现方式

**方式A: Socket通信（推荐）**
```rust
// src-tauri/src/services/notification_server.rs
// 启动本地socket服务器，监听端口37428
// Python notify插件检测到Desktop App运行时，发送通知到此端口
```

**方式B: 文件监控**
```rust
// 监控 ~/.claude/notifications.fifo
// Python写入通知JSON，Desktop App读取并显示
```

#### Python notify插件修改
```python
# plugins/tools/notify/scripts/notify.py
import socket
import json

def send_to_desktop_app(title, message, **kwargs):
    """尝试发送到桌面应用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(('localhost', 37428))
        sock.send(json.dumps({
            'title': title,
            'message': message,
            'kwargs': kwargs
        }).encode())
        sock.close()
        return True  # 成功发送到桌面App
    except:
        return False  # 桌面App未运行，使用原通知方式
```

### 3. 插件管理核心逻辑

#### 数据流

```
用户操作 (UI)
    ↓
React Component
    ↓
Tauri Command (Rust)
    ↓
Python Script (uvx)
    ↓
Claude Plugins Cache (~/.claude/plugins/)
    ↓
文件系统监控 (Rust)
    ↓
更新UI状态
```

#### 插件状态模型

```typescript
// src/types/plugin.ts
export interface Plugin {
  name: string;
  version: string;
  marketplace: string;
  installed: boolean;
  installedVersion?: string;
  description: string;
  author: string;
  keywords: string[];
  category: 'tools' | 'languages' | 'office' | 'other';

  // 统计信息（从Desktop App本地存储）
  installDate?: Date;
  lastUpdateDate?: Date;
  usageCount?: number;

  // 市场信息
  downloads?: number;
  rating?: number;
  readme?: string;
}

export interface PluginInstallProgress {
  pluginName: string;
  status: 'downloading' | 'installing' | 'completed' | 'failed';
  progress: number; // 0-100
  message: string;
}
```

#### 插件变更监控

```rust
// src-tauri/src/services/plugin_watcher.rs
use notify::{Watcher, RecursiveMode};
use tauri::Window;

pub fn watch_plugin_directory(window: Window) -> Result<(), Box<dyn std::error::Error>> {
    let claude_dir = home::home_dir()
        .ok_or("Cannot find home directory")?
        .join(".claude/plugins");

    let mut watcher = notify::recommended_watcher(move |res| {
        if let Ok(event) = res {
            window.emit("plugin-changed", event).ok();
        }
    })?;

    watcher.watch(&claude_dir, RecursiveMode::Recursive)?;
    Ok(())
}
```

### 4. UI页面结构

#### 主布局
```typescript
// src/App.tsx
<Layout>
  <Sidebar>
    <TrayIcon />
    <NavLinks>
      - Dashboard (仪表板)
      - Marketplace (市场)
      - Installed (已安装)
      - Updates (更新)
      - Settings (设置)
      - Logs (日志)
      - DevTools (开发者工具)
    </NavLinks>
  </Sidebar>

  <MainContent>
    <TopBar>
      <SearchBar />
      <NotificationBell />
      <UserMenu />
    </TopBar>
    <Routes />
  </MainContent>
</Layout>
```

#### 页面详细设计

**1. Dashboard (仪表板)**
- 已安装插件统计卡片
- 最近安装/更新的插件
- 待更新插件提醒
- 使用趋势图表（Chart.js/Recharts）
- 快速操作区

**2. Marketplace (插件市场)**
- 分类标签（工具/语言/Office/其他）
- 搜索和过滤（名称、关键词、作者）
- 插件卡片网格视图
- 插件详情抽屉/模态框（README、安装命令、版本历史）
- 一键安装按钮

**3. Installed (已安装插件)**
- 已安装插件列表（表格或卡片视图）
- 批量操作（更新、卸载）
- 插件详情（安装时间、版本、文件路径）
- 启用/禁用插件（如果支持）

**4. Updates (更新中心)**
- 待更新插件列表
- 更新日志显示（CHANGELOG）
- 批量更新功能
- 自动更新设置（开启/关闭、检查频率）
- 更新历史记录

**5. Settings (设置)**
```typescript
interface Settings {
  // 通用设置
  general: {
    theme: 'light' | 'dark' | 'system';
    language: 'zh-CN' | 'en-US';
    autoStart: boolean;
    minimizeToTray: boolean;
  };

  // 更新设置
  updates: {
    autoCheck: boolean;
    checkInterval: '1h' | '6h' | '24h' | 'weekly';
    autoInstall: boolean;
    notifyOnUpdate: boolean;
  };

  // 通知设置
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
    inApp: boolean;
  };

  // 高级设置
  advanced: {
    pythonPath?: string;
    uvxPath?: string;
    maxConcurrentInstalls: number;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
  };
}
```

**6. Logs (日志查看器)**
- 实时日志流
- 日志级别过滤（Debug/Info/Warn/Error）
- 日志搜索和高亮
- 导出日志功能
- 清空日志

**7. DevTools (开发者工具)**
- 本地插件测试（加载本地目录）
- 插件结构验证
- 插件性能分析
- 依赖关系图谱
- 调试控制台

### 5. 跨平台特性处理

#### 系统托盘

```rust
// src-tauri/src/main.rs
use tauri::{SystemTray, SystemTrayMenu, SystemTrayMenuItem, CustomMenuItem};

fn create_system_tray() -> SystemTray {
    let show = CustomMenuItem::new("show".to_string(), "显示窗口");
    let hide = CustomMenuItem::new("hide".to_string(), "隐藏窗口");
    let quit = CustomMenuItem::new("quit".to_string(), "退出");

    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(hide)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);

    SystemTray::new().with_menu(tray_menu)
}
```

#### 开机自启

```rust
use tauri_plugin_autostart::MacosLauncher;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_autostart::init(
            MacosLauncher::LaunchAgent,
            Some(vec!["--minimized"])
        ))
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### 单实例模式

```rust
use tauri_plugin_single_instance::init;

fn main() {
    tauri::Builder::default()
        .plugin(init(|app, argv, cwd| {
            // 已有实例在运行，聚焦现有窗口
            if let Some(window) = app.get_window("main") {
                window.show().ok();
                window.set_focus().ok();
            }
        }))
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### 平台特定功能

```rust
// src-tauri/src/commands/system.rs
#[tauri::command]
pub fn get_platform_info() -> PlatformInfo {
    PlatformInfo {
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        family: std::env::consts::FAMILY.to_string(),
    }
}

// 平台特定路径
pub fn get_config_dir() -> PathBuf {
    #[cfg(target_os = "macos")]
    return home_dir().unwrap().join("Library/Application Support/CCPlugin");

    #[cfg(target_os = "windows")]
    return dirs::config_dir().unwrap().join("CCPlugin");

    #[cfg(target_os = "linux")]
    return home_dir().unwrap().join(".config/ccplugin");
}
```

## 核心技术挑战与解决方案

### 挑战1: Python环境依赖
**问题**: 用户可能没有安装uv或Python
**解决方案**:
1. 首次启动检测uv/python是否安装
2. 提供一键安装引导（链接到安装脚本）
3. 配置页面允许自定义Python/uv路径

### 挑战2: 通知系统切换
**问题**: 需要在Python notify插件和Desktop App之间无缝切换
**解决方案**:
1. Desktop App启动时创建标记文件`~/.claude/desktop-app.lock`
2. Python notify插件检测该文件，决定是否转发通知
3. 使用socket通信（端口37428），超时回退到系统通知

### 挑战3: 插件状态同步
**问题**: CLI和GUI同时操作时状态不一致
**解决方案**:
1. Desktop App通过文件系统监控检测CLI变更
2. 使用Rust的notify库监控`~/.claude/plugins/`
3. 检测到变更时重新加载插件列表

### 挑战4: 大量插件的性能
**问题**: 插件市场有数十个插件，全量加载慢
**解决方案**:
1. 虚拟滚动（react-window）只渲染可见项
2. 懒加载插件README和详情
3. 插件列表分页或无限滚动
4. 缓存已加载的数据

## 开发阶段划分

### Phase 1: 核心框架（1-2周）
- [ ] 初始化Tauri + React项目
- [ ] 配置TypeScript + Tailwind + Shadcn UI
- [ ] 实现基础布局和路由
- [ ] 系统托盘 + 单实例 + 开机自启

### Phase 2: Python集成（1周）
- [ ] 实现Python脚本桥接服务
- [ ] 封装install/update/clean命令
- [ ] 进度反馈和错误处理
- [ ] 单元测试

### Phase 3: 插件管理（2周）
- [ ] 插件列表读取（marketplace.json + ~/.claude/plugins）
- [ ] 插件安装/更新/卸载UI
- [ ] 插件详情展示
- [ ] 搜索和过滤功能
- [ ] 文件系统监控

### Phase 4: 通知集成（1周）
- [ ] Socket通知服务器
- [ ] 修改notify插件支持转发
- [ ] Desktop App通知显示组件
- [ ] 通知历史记录

### Phase 5: 高级功能（2周）
- [ ] Dashboard仪表板和统计
- [ ] 自动更新功能
- [ ] 日志查看器
- [ ] 开发者工具
- [ ] 设置页面

### Phase 6: 打包和分发（1周）
- [ ] 配置Tauri打包脚本
- [ ] 生成各平台安装包（.dmg/.exe/.AppImage）
- [ ] 代码签名（macOS/Windows）
- [ ] GitHub Release自动化
- [ ] 更新服务器配置

## 未解决的问题

1. **更新策略**: Desktop App自身的更新机制（Tauri Updater vs 手动下载）
2. **认证**: 是否需要GitHub认证来访问私有插件仓库？
3. **国际化**: 是否支持多语言（当前只考虑中文）？
4. **插件评分**: 是否添加用户评分和评论功能（需要后端服务）？
5. **崩溃报告**: 是否集成Sentry等错误追踪服务？

## 下一步

1. **确认设计**: 用户review本文档，确认功能范围
2. **创建项目**: 初始化Tauri + React项目结构
3. **实现MVP**: Phase 1 + Phase 2（核心框架 + Python集成）
4. **迭代开发**: 按照Phase 3-6逐步实现功能
5. **测试发布**: 跨平台测试，打包发布第一个版本

---

## 设计决策总结

| 决策点 | 选择 | 原因 |
|--------|------|------|
| 框架 | Tauri 2.x | 轻量、快速、原生体验 |
| 前端 | React + TS | 生态强大、团队熟悉 |
| UI库 | Shadcn UI | 现代化、可定制、轻量 |
| Python集成 | Shell Command | 代码复用、维护简单 |
| 数据存储 | 混合模式 | 平衡一致性和灵活性 |
| 通知 | Socket桥接 | 无缝集成、性能好 |
| 打包 | Tauri打包 | 自动化、跨平台支持 |
