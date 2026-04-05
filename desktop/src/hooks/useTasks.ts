import { useEffect, useState, useCallback } from "react";
import {
	getTasks,
	getTaskStatus,
	listenToTaskUpdates,
	type Task,
	type TaskQueueStatus,
	type TaskStatus,
} from "@/services/tauri-commands";

/**
 * 任务队列管理 Hook
 */
export function useTasks() {
	const [tasks, setTasks] = useState<Task[]>([]);
	const [status, setStatus] = useState<TaskQueueStatus>({
		pending: 0,
		running: 0,
		completed: 0,
	});
	const [loading, setLoading] = useState(false);

	// 加载所有任务
	const refreshTasks = useCallback(async () => {
		setLoading(true);
		try {
			const [tasksData, statusData] = await Promise.all([
				getTasks(),
				getTaskStatus(),
			]);
			setTasks(tasksData);
			setStatus(statusData);
		} catch (error) {
			console.error("Failed to load tasks:", error);
		} finally {
			setLoading(false);
		}
	}, []);

	// 初始加载
	useEffect(() => {
		refreshTasks();
	}, [refreshTasks]);

	// 监听任务更新
	useEffect(() => {
		let unlisten: (() => void) | null = null;

		const setupListener = async () => {
			unlisten = await listenToTaskUpdates((updatedTask) => {
				setTasks((prevTasks) => {
					// 更新或添加任务
					const existingIndex = prevTasks.findIndex((t) => t.id === updatedTask.id);
					if (existingIndex >= 0) {
						const newTasks = [...prevTasks];
						newTasks[existingIndex] = updatedTask;
						return newTasks;
					} else {
						// 添加到前面
						return [updatedTask, ...prevTasks];
					}
				});

				// 刷新状态
				getTaskStatus().then(setStatus).catch(console.error);
			});
		};

		setupListener();

		return () => {
			unlisten?.();
		};
	}, []);

	// 按状态筛选任务
	const tasksByStatus = useCallback(
		(taskStatus: TaskStatus) => {
			return tasks.filter((task) => task.status === taskStatus);
		},
		[tasks],
	);

	// 按插件名称筛选任务
	const tasksByPlugin = useCallback(
		(pluginName: string) => {
			return tasks.filter((task) => task.plugin_name === pluginName);
		},
		[tasks],
	);

	// 获取特定任务
	const getTask = useCallback(
		(taskId: string) => {
			return tasks.find((task) => task.id === taskId);
		},
		[tasks],
	);

	return {
		tasks,
		status,
		loading,
		refreshTasks,
		tasksByStatus,
		tasksByPlugin,
		getTask,
	};
}
