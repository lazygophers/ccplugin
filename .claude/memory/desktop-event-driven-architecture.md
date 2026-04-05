---
name: desktop-event-driven-architecture
description: @desktop 事件驱动架构规范 - Rust 核心逻辑与事件通知模式
type: project
---

# @desktop 事件驱动架构规范

**日期**: 2026-04-05
**适用范围**: @desktop (Tauri Desktop Application)
**架构原则**: Rust 实现业务逻辑，事件驱动前端更新

---

## 一、架构原则

### 核心准则

1. **Rust 优先**：所有业务逻辑在 Rust 侧实现，TypeScript 仅负责 UI 渲染
2. **事件驱动**：使用事件系统通知前端状态变化，禁止同步/异步等待结果
3. **单向数据流**：Rust → Event → Frontend State → UI Render
4. **无阻塞 UI**：命令立即返回，后台任务通过事件持续推送进度

### 当前问题

**现状**（需要迁移）：
```typescript
// ❌ 错误模式：Command-and-Wait
const result = await invoke<CommandResult>("install_plugin", { pluginName });
// 前端等待 Rust 完成整个安装过程，UI 阻塞
```

**目标**（应该迁移到）：
```typescript
// ✅ 正确模式：Event-Driven
invoke("install_plugin", { pluginName }); // 立即返回
// Rust 通过事件持续推送进度和结果
const unlisten = await listen<PluginInstallProgress>(
  "plugin-install-progress",
  (event) => updateUI(event.payload)
);
```

---

## 二、事件命名约定

### 命名格式

`<domain>-<entity>-<action>`

### 标准事件列表

| 事件名称 | 方向 | 用途 | Payload 类型 |
|---------|------|------|-------------|
| `plugin-install-progress` | Rust → Front | 安装进度更新 | `PluginInstallProgress` |
| `plugin-install-completed` | Rust → Front | 安装完成通知 | `CommandResult` |
| `plugin-install-failed` | Rust → Front | 安装失败通知 | `{ error: string }` |
| `plugin-uninstall-progress` | Rust → Front | 卸载进度 | `PluginInstallProgress` |
| `plugin-uninstall-completed` | Rust → Front | 卸载完成 | `CommandResult` |
| `plugin-update-progress` | Rust → Front | 更新进度 | `PluginInstallProgress` |
| `plugin-update-completed` | Rust → Front | 更新完成 | `CommandResult` |
| `plugin-list-changed` | Rust → Front | 插件列表变化 | `{ plugins: PluginInfo[] }` |
| `marketplace-refresh-started` | Rust → Front | 市场刷新开始 | `{ }` |
| `marketplace-refresh-completed` | Rust → Front | 市场刷新完成 | `{ plugins: PluginInfo[] }` |
| `cache-clean-completed` | Rust → Front | 缓存清理完成 | `CommandResult` |

### 命名规则

- **全小写**：使用 kebab-case（`plugin-install-progress`，非 `pluginInstallProgress`）
- **动作后缀**：
  - `-progress`：进行中的状态更新（可多次触发）
  - `-started`：操作开始
  - `-completed`：操作成功完成
  - `-failed`：操作失败
  - `-changed`：状态变化

---

## 三、Rust 侧实现模式

### 3.1 Command 定义（立即返回）

**原则**：Command 函数仅启动操作，不等待完成。

```rust
use tauri::{AppHandle, Emitter};
use tokio::task::spawn;

#[tauri::command]
pub async fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    // ✅ 立即发送启动事件
    app_handle.emit("plugin-install-started", &plugin_name)?;

    // ✅ 在后台任务中执行安装
    spawn(async move {
        let bridge = PythonBridge::new(app_handle.clone());
        
        // 发送进度事件
        bridge.emit_progress(&plugin_name, InstallStatus::Downloading, 10, "开始下载...");
        
        match bridge.install_plugin(&plugin_name, &marketplace, &scope).await {
            Ok(result) if result.success => {
                // ✅ 发送完成事件
                let _ = app_handle.emit("plugin-install-completed", &result);
            }
            Ok(result) => {
                // ✅ 发送失败事件
                let _ = app_handle.emit("plugin-install-failed", &json!({
                    "plugin": plugin_name,
                    "error": result.stderr
                }));
            }
            Err(e) => {
                let _ = app_handle.emit("plugin-install-failed", &json!({
                    "plugin": plugin_name,
                    "error": e.to_string()
                }));
            }
        }
    });

    // ✅ 立即返回，不等待
    Ok(())
}
```

### 3.2 进度事件发射

**关键点**：使用 `Emitter` trait 在操作过程中持续推送状态。

```rust
impl PythonBridge {
    /// 发送进度事件到前端
    fn emit_progress(
        &self,
        plugin_name: &str,
        status: InstallStatus,
        progress: u8,
        message: &str,
    ) {
        let progress_data = PluginInstallProgress {
            plugin_name: plugin_name.to_string(),
            status,
            progress,
            message: message.to_string(),
        };

        // 使用 AppHandle 的 emit 方法
        let _ = self.app_handle.emit("plugin-install-progress", progress_data);
    }
}
```

### 3.3 Rust 状态管理

**推荐**：在 Rust 侧维护插件列表缓存。

```rust
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct PluginState {
    plugins: Arc<RwLock<Vec<PluginInfo>>>,
}

impl PluginState {
    pub async fn refresh_plugins(&self, app_handle: AppHandle) {
        let plugins = MarketplaceService::load_marketplace()?;
        
        // 更新缓存
        *self.plugins.write().await = plugins.clone();
        
        // ✅ 通知前端
        let _ = app_handle.emit("plugin-list-changed", &plugins);
    }
}
```

---

## 四、前端事件监听模式

### 4.1 全局事件监听器

**原则**：在应用顶层注册监听器，状态集中管理。

```typescript
// src/stores/pluginStore.ts
import { listen } from "@tauri-apps/api/event";

interface PluginStore {
  plugins: PluginInfo[];
  installProgress: Map<string, PluginInstallProgress>;
}

export function usePluginStore() {
  const [store, setStore] = useState<PluginStore>({
    plugins: [],
    installProgress: new Map(),
  });

  useEffect(() => {
    const unlisteners: Promise<UnlistenFn>[] = [];

    // 监听安装进度
    unlisteners.push(
      listen<PluginInstallProgress>("plugin-install-progress", (event) => {
        setStore((prev) => ({
          ...prev,
          installProgress: new Map(prev.installProgress).set(
            event.payload.plugin_name,
            event.payload
          ),
        }));
      })
    );

    // 监听安装完成
    unlisteners.push(
      listen<CommandResult>("plugin-install-completed", async () => {
        // ✅ 刷新插件列表
        await invoke("refresh_plugins");
      })
    );

    // 监听插件列表变化
    unlisteners.push(
      listen<PluginInfo[]>("plugin-list-changed", (event) => {
        setStore((prev) => ({
          ...prev,
          plugins: event.payload,
        }));
      })
    );

    // 清理监听器
    return () => {
      unlisteners.forEach(async (unlisten) => {
        (await unlisten)();
      });
    };
  }, []);

  return store;
}
```

### 4.2 调用命令（无等待）

**原则**：调用命令后立即返回，依赖事件更新状态。

```typescript
const handleInstall = (pluginName: string) => {
  // ✅ 仅触发命令，不等待结果
  invoke("install_plugin", {
    pluginName,
    marketplace: "ccplugin-market",
    scope: "user",
  }).catch((error) => {
    console.error("Failed to start installation:", error);
  });
  
  // ✅ UI 将通过事件自动更新
};

// 组件中显示进度
const progress = store.installProgress.get(pluginName);
return <Progress value={progress?.progress ?? 0} />;
```

### 4.3 错误处理

**原则**：通过失败事件捕获错误，而非 try-catch 命令调用。

```typescript
useEffect(() => {
  const unlisten = listen<{ plugin: string; error: string }>(
    "plugin-install-failed",
    (event) => {
      const { plugin, error } = event.payload;
      toast.error(`插件 ${plugin} 安装失败: ${error}`);
      // 清理进度状态
      setStore((prev) => {
        const progress = new Map(prev.installProgress);
        progress.delete(plugin);
        return { ...prev, installProgress: progress };
      });
    }
  );

  return () => {
    unlisten.then((fn) => fn());
  };
}, []);
```

---

## 五、状态管理架构

### 5.1 推荐模式：Context + Events

```typescript
// src/contexts/PluginContext.tsx
export const PluginContext = createContext<{
  plugins: PluginInfo[];
  installing: Set<string>;
  progress: Map<string, PluginInstallProgress>;
  install: (name: string) => void;
  uninstall: (name: string) => void;
} | null>(null);

export function PluginProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState({
    plugins: [],
    installing: new Set<string>(),
    progress: new Map<string, PluginInstallProgress>(),
  });

  useEffect(() => {
    // 注册所有事件监听器
    const setupListeners = async () => {
      // plugin-install-progress
      const unlisten1 = await listen<PluginInstallProgress>(
        "plugin-install-progress",
        (event) => {
          setState((prev) => ({
            ...prev,
            progress: new Map(prev.progress).set(
              event.payload.plugin_name,
              event.payload
            ),
          }));
        }
      );

      // plugin-install-completed
      const unlisten2 = await listen<CommandResult>(
        "plugin-install-completed",
        () => {
          invoke<PluginInfo[]>("get_plugins").then((plugins) => {
            setState((prev) => ({ ...prev, plugins }));
          });
        }
      );

      return () => {
        unlisten1();
        unlisten2();
      };
    };

    setupListeners();
  }, []);

  const install = (name: string) => {
    setState((prev) => ({
      ...prev,
      installing: new Set(prev.installing).add(name),
    }));
    invoke("install_plugin", { pluginName: name });
  };

  return (
    <PluginContext.Provider value={{ ...state, install, uninstall }}>
      {children}
    </PluginContext.Provider>
  );
}
```

### 5.2 组件使用

```typescript
function PluginCard({ plugin }: { plugin: PluginInfo }) {
  const { installing, progress, install } = usePluginContext();

  const isInstalling = installing.has(plugin.name);
  const currentProgress = progress.get(plugin.name);

  return (
    <Card>
      {isInstalling && (
        <Progress value={currentProgress?.progress ?? 0}>
          {currentProgress?.message}
        </Progress>
      )}
      <Button onClick={() => install(plugin.name)} disabled={isInstalling}>
        安装
      </Button>
    </Card>
  );
}
```

---

## 六、迁移指南

### 6.1 识别需要迁移的代码

**查找模式**：
```typescript
// ❌ 需要迁移
const result = await invoke<CommandResult>("xxx_command");
// 同步等待结果的代码都需要改为事件驱动
```

**迁移步骤**：
1. Rust 侧：修改 Command 为立即返回，后台任务执行
2. Rust 侧：添加事件发射（`app_handle.emit()`）
3. 前端：注册事件监听器（`listen()`）
4. 前端：移除 `await` 调用
5. 前端：通过事件更新状态

### 6.2 迁移示例：`installPlugin`

**Before**（当前实现）：

```typescript
// frontend
const result = await invoke<CommandResult>("install_plugin", { pluginName });
if (result.success) {
  refreshPlugins();
}
```

```rust
// backend
#[tauri::command]
pub async fn install_plugin(...) -> Result<CommandResult, String> {
    let bridge = PythonBridge::new(app_handle);
    bridge.install_plugin(...).await // ❌ 阻塞等待
}
```

**After**（目标架构）：

```typescript
// frontend - 仅触发
useEffect(() => {
  const unlisten = listen<CommandResult>("plugin-install-completed", () => {
    refreshPlugins(); // ✅ 通过事件触发刷新
  });
  return () => unlisten.then(fn => fn());
}, []);

const handleInstall = (name: string) => {
  invoke("install_plugin", { pluginName: name }); // ✅ 无需 await
};
```

```rust
// backend - 立即返回 + 后台任务
#[tauri::command]
pub async fn install_plugin(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    spawn(async move {
        let bridge = PythonBridge::new(app_handle.clone());
        match bridge.install_plugin(...).await {
            Ok(result) => {
                app_handle.emit("plugin-install-completed", &result).ok(); // ✅ 事件通知
            }
            Err(e) => {
                app_handle.emit("plugin-install-failed", &e.to_string()).ok();
            }
        }
    });
    Ok(()) // ✅ 立即返回
}
```

### 6.3 迁移优先级

**高优先级**（立即迁移）：
- ✅ `install_plugin` - 已有进度事件，改为完全事件驱动
- ✅ `update_plugin` - 同上
- ✅ `uninstall_plugin` - 同上

**中优先级**（下一阶段）：
- `get_marketplace_plugins` - 改为启动时缓存 + `plugin-list-changed` 事件
- `get_installed_plugins` - 同上

**低优先级**（可保持现状）：
- `clean_cache` - 执行时间短，可保持 command-and-wait
- `get_plugin_info` - 同上

---

## 七、性能优化

### 7.1 事件节流

对于高频事件（如进度更新），在 Rust 侧节流：

```rust
use std::time::{Duration, Instant};
use tokio::time::sleep;

pub struct ThrottledEmitter {
    last_emit: Instant,
    min_interval: Duration,
}

impl ThrottledEmitter {
    pub fn emit_if_ready(&mut self, app_handle: &AppHandle, event: &str, payload: &impl Serialize) {
        let now = Instant::now();
        if now.duration_since(self.last_emit) >= self.min_interval {
            let _ = app_handle.emit(event, payload);
            self.last_emit = now;
        }
    }
}
```

### 7.2 状态批量更新

前端使用 `requestAnimationFrame` 批量更新 UI：

```typescript
let updateScheduled = false;

listen("plugin-install-progress", (event) => {
  if (!updateScheduled) {
    updateScheduled = true;
    requestAnimationFrame(() => {
      setStore((prev) => ({ ...prev, progress: event.payload }));
      updateScheduled = false;
    });
  }
});
```

---

## 八、测试策略

### 8.1 Rust 单元测试

测试事件发射：

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use tauri::test::MockAppHandle;

    #[tokio::test]
    async fn test_install_emits_events() {
        let app_handle = MockAppHandle::new();
        let bridge = PythonBridge::new(app_handle.clone());

        bridge.install_plugin("test", "market", "user").await.unwrap();

        // ✅ 验证事件已发射
        let events = app_handle.get_emitted_events();
        assert!(events.iter().any(|e| e.name == "plugin-install-progress"));
        assert!(events.iter().any(|e| e.name == "plugin-install-completed"));
    }
}
```

### 8.2 前端集成测试

使用 Mock Emitter：

```typescript
import { emit } from "@tauri-apps/api/event";

describe("PluginStore", () => {
  it("updates progress on install-progress event", async () => {
    const { result } = renderHook(() => usePluginStore());

    // 模拟 Rust 事件
    await emit("plugin-install-progress", {
      plugin_name: "test",
      progress: 50,
      message: "Installing...",
    });

    expect(result.current.progress.get("test")?.progress).toBe(50);
  });
});
```

---

## 九、检查清单

### 新功能开发

- [ ] 业务逻辑在 Rust 侧实现
- [ ] Command 函数立即返回（`spawn` 后台任务）
- [ ] 使用 `app_handle.emit()` 发送事件
- [ ] 事件命名遵循 `<domain>-<entity>-<action>` 格式
- [ ] 前端通过 `listen()` 注册监听器
- [ ] 前端调用命令不使用 `await`（除非必需）
- [ ] 状态通过事件更新，而非命令返回值

### 代码审查

- [ ] 无同步等待 Rust 命令的 `await` 调用
- [ ] 所有长时间操作在后台任务中执行
- [ ] 事件监听器在组件卸载时清理
- [ ] 错误通过 `-failed` 事件传递
- [ ] UI 响应事件更新，而非命令结果

---

## 十、参考实现

### 完整流程示例

```rust
// src-tauri/src/commands/plugin.rs

#[tauri::command]
pub async fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    // 1. 立即发送启动事件
    app_handle.emit("plugin-install-started", &json!({
        "plugin": &plugin_name
    }))?;

    // 2. 后台任务执行安装
    tokio::spawn(async move {
        let bridge = PythonBridge::new(app_handle.clone());
        
        // 3. 发送进度
        bridge.emit_progress(&plugin_name, InstallStatus::Downloading, 10, "开始下载...");
        
        // 4. 执行安装
        match bridge.install_plugin(&plugin_name, &marketplace, &scope).await {
            Ok(result) if result.success => {
                bridge.emit_progress(&plugin_name, InstallStatus::Completed, 100, "安装完成");
                app_handle.emit("plugin-install-completed", &result).ok();
            }
            Ok(result) => {
                bridge.emit_progress(&plugin_name, InstallStatus::Failed, 0, &result.stderr);
                app_handle.emit("plugin-install-failed", &json!({
                    "plugin": plugin_name,
                    "error": result.stderr
                })).ok();
            }
            Err(e) => {
                app_handle.emit("plugin-install-failed", &json!({
                    "plugin": plugin_name,
                    "error": e.to_string()
                })).ok();
            }
        }
    });

    // 5. 立即返回
    Ok(())
}
```

```typescript
// src/stores/pluginStore.ts

export function usePluginStore() {
  const [state, setState] = useState({
    plugins: [] as PluginInfo[],
    installing: new Set<string>(),
    progress: new Map<string, PluginInstallProgress>(),
  });

  useEffect(() => {
    let unlisten1: UnlistenFn, unlisten2: UnlistenFn, unlisten3: UnlistenFn;

    const setup = async () => {
      // 监听启动
      unlisten1 = await listen<{ plugin: string }>("plugin-install-started", (event) => {
        setState((prev) => ({
          ...prev,
          installing: new Set(prev.installing).add(event.payload.plugin),
        }));
      });

      // 监听进度
      unlisten2 = await listen<PluginInstallProgress>("plugin-install-progress", (event) => {
        setState((prev) => ({
          ...prev,
          progress: new Map(prev.progress).set(event.payload.plugin_name, event.payload),
        }));
      });

      // 监听完成
      unlisten3 = await listen<CommandResult>("plugin-install-completed", async () => {
        const plugins = await invoke<PluginInfo[]>("get_plugins");
        setState((prev) => ({
          ...prev,
          plugins,
          installing: new Set([...prev.installing].filter(p => 
            !state.progress.has(p) || state.progress.get(p)?.status === 'completed'
          )),
        }));
      });
    };

    setup();

    return () => {
      unlisten1?.();
      unlisten2?.();
      unlisten3?.();
    };
  }, []);

  const install = useCallback((pluginName: string) => {
    invoke("install_plugin", { pluginName, marketplace: "ccplugin-market", scope: "user" })
      .catch(console.error);
  }, []);

  return { ...state, install };
}
```

---

## 十一、常见问题

### Q: 什么时候可以使用 command-and-wait 模式？

**A**: 仅用于执行时间 < 100ms 的简单操作，如：
- 配置读取
- 状态查询
- 简单校验

所有涉及外部命令、网络请求、文件 I/O 的操作必须使用事件驱动。

### Q: 如何处理事件监听器的内存泄漏？

**A**: 
1. 在 `useEffect` 返回清理函数
2. 使用 `useRef` 保存 `UnlistenFn`
3. 组件卸载时调用 `unlisten()`

### Q: Rust 如何向前端发送复杂对象？

**A**: 
1. 定义 `#[derive(Serialize)]` 的结构体
2. 确保类型实现 `serde::Serialize`
3. 使用 `app_handle.emit("event-name", &data)` 自动序列化

---

## 十二、更新日志

**2026-04-05**：初始版本
- 定义事件驱动架构原则
- 规范事件命名约定
- 提供 Rust/前端实现模式
- 添加迁移指南和示例

---

**相关文档**：
- Tauri Events: https://tauri.app/v2/api/concept/events
- Rust `Emitter` trait: `tauri::Emitter`
- 前端 `listen()` API: `@tauri-apps/api/event`
