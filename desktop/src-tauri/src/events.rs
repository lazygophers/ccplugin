use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{AppHandle, Emitter};

/// 插件事件负载
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginEventPayload {
    pub event_type: String,
    pub plugin_name: String,
    pub data: Value,
}

/// 插件事件类型
pub enum PluginEventType {
    // 安装事件
    PluginInstallStarted,
    PluginInstallProgress,
    PluginInstallCompleted,
    PluginInstallFailed,

    // 更新事件
    PluginUpdateStarted,
    PluginUpdateProgress,
    PluginUpdateCompleted,
    PluginUpdateFailed,

    // 卸载事件
    PluginUninstallStarted,
    PluginUninstallProgress,
    PluginUninstallCompleted,
    PluginUninstallFailed,

    // 缓存清理事件
    CacheCleanStarted,
    CacheCleanCompleted,
    CacheCleanFailed,

    // 插件信息获取事件
    PluginInfoCompleted,
    PluginInfoFailed,
}

impl PluginEventType {
    /// 转换为事件名称字符串（遵循 <domain>-<entity>-<action> 格式）
    pub fn as_str(&self) -> &'static str {
        match self {
            PluginEventType::PluginInstallStarted => "plugin-install-started",
            PluginEventType::PluginInstallProgress => "plugin-install-progress",
            PluginEventType::PluginInstallCompleted => "plugin-install-completed",
            PluginEventType::PluginInstallFailed => "plugin-install-failed",

            PluginEventType::PluginUpdateStarted => "plugin-update-started",
            PluginEventType::PluginUpdateProgress => "plugin-update-progress",
            PluginEventType::PluginUpdateCompleted => "plugin-update-completed",
            PluginEventType::PluginUpdateFailed => "plugin-update-failed",

            PluginEventType::PluginUninstallStarted => "plugin-uninstall-started",
            PluginEventType::PluginUninstallProgress => "plugin-uninstall-progress",
            PluginEventType::PluginUninstallCompleted => "plugin-uninstall-completed",
            PluginEventType::PluginUninstallFailed => "plugin-uninstall-failed",

            PluginEventType::CacheCleanStarted => "cache-clean-started",
            PluginEventType::CacheCleanCompleted => "cache-clean-completed",
            PluginEventType::CacheCleanFailed => "cache-clean-failed",

            PluginEventType::PluginInfoCompleted => "plugin-info-completed",
            PluginEventType::PluginInfoFailed => "plugin-info-failed",
        }
    }
}

/// 发送插件事件到前端
pub fn emit_plugin_event(
    app_handle: &AppHandle,
    event_type: PluginEventType,
    plugin_name: &str,
    data: Value,
) {
    let payload = PluginEventPayload {
        event_type: event_type.as_str().to_string(),
        plugin_name: plugin_name.to_string(),
        data,
    };

    let _ = app_handle.emit("plugin-event", Some(payload));
}
