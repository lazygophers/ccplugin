pub mod python_bridge;
pub mod marketplace;
pub mod notification_service;
pub mod database;
pub mod task_queue;

pub use python_bridge::*;
pub use marketplace::*;
pub use notification_service::*;
pub use task_queue::*;

use std::sync::OnceLock;
use tauri::AppHandle;

/// 全局任务队列实例
static TASK_QUEUE: OnceLock<task_queue::TaskQueue> = OnceLock::new();

/// 初始化任务队列
pub fn init_task_queue(max_concurrent: usize) -> Result<(), String> {
    TASK_QUEUE
        .set(task_queue::TaskQueue::new(max_concurrent))
        .map_err(|_| "任务队列已初始化".to_string())
}

/// 获取任务队列引用
pub fn task_queue() -> Option<&'static task_queue::TaskQueue> {
    TASK_QUEUE.get()
}
