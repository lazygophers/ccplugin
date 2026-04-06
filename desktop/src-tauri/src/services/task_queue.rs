use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter};
use tauri_plugin_notification::NotificationExt;

use crate::events::{emit_plugin_event, PluginEventType};
use crate::services::PythonBridge;

/// 任务状态
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskStatus {
    Pending,   // 等待执行
    Running,   // 执行中
    Completed, // 完成
    Failed,    // 失败
    Cancelled, // 已取消
}

/// 任务类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskType {
    Install,   // 安装插件
    Update,    // 更新插件
    Uninstall, // 卸载插件
}

/// 任务信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub task_type: TaskType,
    pub plugin_name: String,
    pub marketplace: Option<String>,
    pub scope: Option<String>,
    pub status: TaskStatus,
    pub progress: u8,
    pub message: String,
    pub error: Option<String>,
    pub created_at: u64,
    pub started_at: Option<u64>,
    pub completed_at: Option<u64>,
}

impl Task {
    /// 创建新任务
    pub fn new(
        task_type: TaskType,
        plugin_name: String,
        marketplace: Option<String>,
        scope: Option<String>,
    ) -> Self {
        let id = format!("{}-{}", task_type.as_str(), plugin_name);
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        Task {
            id,
            task_type,
            plugin_name,
            marketplace,
            scope,
            status: TaskStatus::Pending,
            progress: 0,
            message: "等待执行...".to_string(),
            error: None,
            created_at: now,
            started_at: None,
            completed_at: None,
        }
    }
}

impl TaskType {
    pub fn as_str(&self) -> &'static str {
        match self {
            TaskType::Install => "install",
            TaskType::Update => "update",
            TaskType::Uninstall => "uninstall",
        }
    }
}

/// 任务队列服务
pub struct TaskQueue {
    queue: Arc<Mutex<VecDeque<Task>>>,
    running: Arc<Mutex<Vec<Task>>>,
    completed: Arc<Mutex<Vec<Task>>>,
    max_concurrent: usize,
}

impl TaskQueue {
    /// 创建新的任务队列
    pub fn new(max_concurrent: usize) -> Self {
        TaskQueue {
            queue: Arc::new(Mutex::new(VecDeque::new())),
            running: Arc::new(Mutex::new(Vec::new())),
            completed: Arc::new(Mutex::new(Vec::new())),
            max_concurrent,
        }
    }

    /// 添加任务到队列
    pub fn add_task(&self, task: Task) -> Result<(), String> {
        let mut queue = self.queue.lock().map_err(|e| e.to_string())?;
        queue.push_back(task);
        Ok(())
    }

    /// 获取所有任务（包括队列中、运行中、已完成的）
    pub fn get_all_tasks(&self) -> Result<Vec<Task>, String> {
        let queue = self.queue.lock().map_err(|e| e.to_string())?;
        let running = self.running.lock().map_err(|e| e.to_string())?;
        let completed = self.completed.lock().map_err(|e| e.to_string())?;

        let mut all_tasks = Vec::new();
        all_tasks.extend(queue.iter().cloned());
        all_tasks.extend(running.iter().cloned());
        all_tasks.extend(completed.iter().cloned());

        // 按创建时间排序（新的在前）
        all_tasks.sort_by(|a, b| b.created_at.cmp(&a.created_at));

        Ok(all_tasks)
    }

    /// 获取队列状态
    pub fn get_status(&self) -> Result<TaskQueueStatus, String> {
        let queue = self.queue.lock().map_err(|e| e.to_string())?;
        let running = self.running.lock().map_err(|e| e.to_string())?;
        let completed = self.completed.lock().map_err(|e| e.to_string())?;

        Ok(TaskQueueStatus {
            pending: queue.len(),
            running: running.len(),
            completed: completed.len(),
        })
    }

    /// 启动任务处理器
    pub fn start_processor(&self, app_handle: AppHandle) {
        let queue_clone = self.queue.clone();
        let running_clone = self.running.clone();
        let completed_clone = self.completed.clone();
        let max_concurrent = self.max_concurrent;

        tauri::async_runtime::spawn(async move {
            loop {
                // 检查是否可以启动新任务
                let can_start = {
                    let running = running_clone.lock().unwrap();
                    running.len() < max_concurrent
                };

                if can_start {
                    // 从队列中取出下一个任务
                    let next_task = {
                        let mut queue = queue_clone.lock().unwrap();
                        queue.pop_front()
                    };

                    if let Some(task) = next_task {
                        // 执行任务
                        Self::execute_task(
                            task,
                            app_handle.clone(),
                            queue_clone.clone(),
                            running_clone.clone(),
                            completed_clone.clone(),
                        );
                    }
                }

                // 等待一段时间再检查
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            }
        });
    }

    /// 执行单个任务
    fn execute_task(
        mut task: Task,
        app_handle: AppHandle,
        _queue: Arc<Mutex<VecDeque<Task>>>,
        running: Arc<Mutex<Vec<Task>>>,
        completed: Arc<Mutex<Vec<Task>>>,
    ) {
        tauri::async_runtime::spawn(async move {
            // 更新状态为运行中
            task.status = TaskStatus::Running;
            task.started_at = Some(
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
            );

            // 移动到运行列表
            {
                let mut running_guard = running.lock().unwrap();
                running_guard.push(task.clone());
            }

            // 发送开始事件
            let event_type = match task.task_type {
                TaskType::Install => PluginEventType::PluginInstallStarted,
                TaskType::Update => PluginEventType::PluginUpdateStarted,
                TaskType::Uninstall => PluginEventType::PluginUninstallStarted,
            };

            emit_plugin_event(
                &app_handle,
                event_type,
                &task.plugin_name,
                serde_json::json!({
                    "marketplace": task.marketplace,
                    "scope": task.scope,
                }),
            );

            // 执行任务
            let bridge = PythonBridge::new();
            let result = match task.task_type {
                TaskType::Install => {
                    let scope = task.scope.clone().unwrap_or_else(|| "user".to_string());
                    let marketplace = task.marketplace.clone().unwrap();

                    bridge
                        .install_plugin_with_progress(
                            &task.plugin_name,
                            &marketplace,
                            &scope,
                            |status, progress, message| {
                                // 更新进度
                                task.progress = progress;
                                task.message = message.to_string();

                                let event_type = PluginEventType::PluginInstallProgress;
                                emit_plugin_event(
                                    &app_handle,
                                    event_type,
                                    &task.plugin_name,
                                    serde_json::json!({
                                        "status": status,
                                        "progress": progress,
                                        "message": message
                                    }),
                                );
                            },
                        )
                        .await
                }
                TaskType::Update => {
                    bridge
                        .update_plugin_with_progress(
                            &task.plugin_name,
                            |status, progress, message| {
                                // 更新进度
                                task.progress = progress;
                                task.message = message.to_string();

                                let event_type = PluginEventType::PluginUpdateProgress;
                                emit_plugin_event(
                                    &app_handle,
                                    event_type,
                                    &task.plugin_name,
                                    serde_json::json!({
                                        "status": status,
                                        "progress": progress,
                                        "message": message
                                    }),
                                );
                            },
                        )
                        .await
                }
                TaskType::Uninstall => {
                    bridge
                        .uninstall_plugin_with_progress(
                            &task.plugin_name,
                            |status, progress, message| {
                                // 更新进度
                                task.progress = progress;
                                task.message = message.to_string();

                                let event_type = PluginEventType::PluginUninstallProgress;
                                emit_plugin_event(
                                    &app_handle,
                                    event_type,
                                    &task.plugin_name,
                                    serde_json::json!({
                                        "status": status,
                                        "progress": progress,
                                        "message": message
                                    }),
                                );
                            },
                        )
                        .await
                }
            };

            // 处理结果
            match result {
                Ok(result) => {
                    if result.success {
                        task.status = TaskStatus::Completed;
                        task.progress = 100;
                        task.message = "任务完成".to_string();

                        // 发送完成事件
                        let event_type = match task.task_type {
                            TaskType::Install => PluginEventType::PluginInstallCompleted,
                            TaskType::Update => PluginEventType::PluginUpdateCompleted,
                            TaskType::Uninstall => PluginEventType::PluginUninstallCompleted,
                        };

                        emit_plugin_event(
                            &app_handle,
                            event_type,
                            &task.plugin_name,
                            serde_json::json!({
                                "stdout": result.stdout,
                                "stderr": result.stderr,
                            }),
                        );

                        // 发送系统通知
                        Self::show_system_notification(
                            &app_handle,
                            &task.plugin_name,
                            task.task_type,
                            true,
                        );
                    } else {
                        task.status = TaskStatus::Failed;
                        task.error = Some(result.stderr.clone());

                        // 发送失败事件
                        let event_type = match task.task_type {
                            TaskType::Install => PluginEventType::PluginInstallFailed,
                            TaskType::Update => PluginEventType::PluginUpdateFailed,
                            TaskType::Uninstall => PluginEventType::PluginUninstallFailed,
                        };

                        emit_plugin_event(
                            &app_handle,
                            event_type,
                            &task.plugin_name,
                            serde_json::json!({ "error": result.stderr }),
                        );

                        // 发送系统通知
                        Self::show_system_notification(
                            &app_handle,
                            &task.plugin_name,
                            task.task_type,
                            false,
                        );
                    }
                }
                Err(err) => {
                    task.status = TaskStatus::Failed;
                    task.error = Some(err.clone());

                    // 发送失败事件
                    let event_type = match task.task_type {
                        TaskType::Install => PluginEventType::PluginInstallFailed,
                        TaskType::Update => PluginEventType::PluginUpdateFailed,
                        TaskType::Uninstall => PluginEventType::PluginUninstallFailed,
                    };

                    emit_plugin_event(
                        &app_handle,
                        event_type,
                        &task.plugin_name,
                        serde_json::json!({ "error": err }),
                    );

                    // 发送系统通知
                    Self::show_system_notification(
                        &app_handle,
                        &task.plugin_name,
                        task.task_type,
                        false,
                    );
                }
            }

            task.completed_at = Some(
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
            );

            // 从运行列表移除，添加到完成列表
            {
                let mut running_guard = running.lock().unwrap();
                running_guard.retain(|t| t.id != task.id);
            }

            {
                let mut completed_guard = completed.lock().unwrap();
                // 保留最近100个已完成任务
                if completed_guard.len() >= 100 {
                    completed_guard.remove(0);
                }
                completed_guard.push(task.clone());
            }

            // 通知前端任务状态更新
            let _ = app_handle.emit("task-updated", Some(task));
        });
    }

    /// 显示系统通知
    fn show_system_notification(
        app_handle: &AppHandle,
        plugin_name: &str,
        task_type: TaskType,
        success: bool,
    ) {
        let (title, body) = if success {
            let action = match task_type {
                TaskType::Install => "安装",
                TaskType::Update => "更新",
                TaskType::Uninstall => "卸载",
            };
            (format!("{}成功", action), format!("{} 已成功{}", plugin_name, action))
        } else {
            let action = match task_type {
                TaskType::Install => "安装",
                TaskType::Update => "更新",
                TaskType::Uninstall => "卸载",
            };
            (format!("{}失败", action), format!("{} {}失败，请查看详情", plugin_name, action))
        };

        let _ = app_handle
            .notification()
            .builder()
            .title(title)
            .body(body)
            .show();
    }
}

/// 任务队列状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskQueueStatus {
    pub pending: usize,
    pub running: usize,
    pub completed: usize,
}
