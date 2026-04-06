import {
	Bell,
	Check,
	Trash2,
	Info,
	CheckCircle,
	AlertTriangle,
	XCircle,
} from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";
import { type NotificationType } from "@/types";

/**
 * 通知类型对应的图标
 */
function getNotificationIcon(type: NotificationType) {
	switch (type) {
		case "info":
			return <Info className="w-6 h-6 text-blue-500" />;
		case "success":
			return <CheckCircle className="w-6 h-6 text-green-500" />;
		case "warning":
			return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
		case "error":
			return <XCircle className="w-6 h-6 text-red-500" />;
		case "progress":
			return <Info className="w-6 h-6 text-blue-500" />;
	}
}

/**
 * 通知类型对应的样式类
 */
function getNotificationStyle(type: NotificationType): string {
	switch (type) {
		case "info":
			return "border-l-blue-500 bg-blue-50 dark:bg-blue-950";
		case "success":
			return "border-l-green-500 bg-green-50 dark:bg-green-950";
		case "warning":
			return "border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950";
		case "error":
			return "border-l-red-500 bg-red-50 dark:bg-red-950";
		case "progress":
			return "border-l-blue-500 bg-blue-50 dark:bg-blue-950";
	}
}

/**
 * 格式化时间戳
 */
function formatTime(timestamp: number): string {
	const date = new Date(timestamp * 1000);
	const now = new Date();
	const diff = now.getTime() - date.getTime();

	// 小于 1 分钟
	if (diff < 60000) {
		return "刚刚";
	}
	// 小于 1 小时
	if (diff < 3600000) {
		const minutes = Math.floor(diff / 60000);
		return `${minutes} 分钟前`;
	}
	// 小于 1 天
	if (diff < 86400000) {
		const hours = Math.floor(diff / 3600000);
		return `${hours} 小时前`;
	}
	// 小于 7 天
	if (diff < 604800000) {
		const days = Math.floor(diff / 86400000);
		return `${days} 天前`;
	}
	// 显示完整日期时间
	return date.toLocaleString("zh-CN", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
	});
}

export default function NotificationCenterPage() {
	const {
		notifications,
		unreadCount,
		loading,
		markAsRead,
		markAllAsRead,
		deleteNotification,
		clearAll,
	} = useNotifications();

	return (
		<div className="container max-w-4xl mx-auto py-8 px-4">
			{/* 头部 */}
			<div className="flex items-center justify-between mb-6">
				<div>
					<h1 className="text-2xl font-bold">通知中心</h1>
					{unreadCount > 0 && (
						<p className="text-sm text-muted-foreground mt-1">
							{unreadCount} 条未读通知
						</p>
					)}
				</div>
				<div className="flex items-center gap-2">
					{unreadCount > 0 && (
						<button
							onClick={() => markAllAsRead()}
							className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
						>
							全部已读
						</button>
					)}
					{notifications.length > 0 && (
						<button
							onClick={() => clearAll()}
							className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
						>
							清空全部
						</button>
					)}
				</div>
			</div>

			{/* 通知列表 */}
			{loading ? (
				<div className="flex items-center justify-center py-12">
					<div className="text-muted-foreground">加载中...</div>
				</div>
			) : notifications.length === 0 ? (
				<div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
					<Bell className="w-16 h-16 mb-4 opacity-50" />
					<p className="text-lg">暂无通知</p>
				</div>
			) : (
				<div className="space-y-3">
					{notifications.map((notification) => (
						<NotificationCard
							key={notification.id}
							notification={notification}
							onMarkRead={() => markAsRead(notification.id)}
							onDelete={() => deleteNotification(notification.id)}
						/>
					))}
				</div>
			)}
		</div>
	);
}

interface NotificationCardProps {
	notification: import("@/types").Notification;
	onMarkRead: () => void;
	onDelete: () => void;
}

function NotificationCard({ notification, onMarkRead, onDelete }: NotificationCardProps) {
	return (
		<div
			className={`p-4 rounded-lg border-l-4 shadow-sm ${getNotificationStyle(notification.type)} ${
				!notification.read ? "bg-opacity-50" : ""
			} transition-all hover:shadow-md`}
		>
			<div className="flex items-start gap-4">
				{/* 图标 */}
				<div className="flex-shrink-0 mt-1">
					{getNotificationIcon(notification.type)}
				</div>

				{/* 内容 */}
				<div className="flex-1 min-w-0">
					<div className="flex items-start justify-between gap-4">
						<div className="flex-1">
							<h3 className="font-semibold text-lg">{notification.title}</h3>
							<p className="text-muted-foreground mt-1">{notification.message}</p>
							<div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
								<span>创建于 {formatTime(notification.created_at)}</span>
								{notification.updated_at !== notification.created_at && (
									<span>• 更新于 {formatTime(notification.updated_at)}</span>
								)}
							</div>
						</div>

						{/* 操作按钮 */}
						<div className="flex items-center gap-2 flex-shrink-0">
							{!notification.read && (
								<button
									onClick={onMarkRead}
									className="p-2 rounded-md hover:bg-white/50 dark:hover:bg-black/20 transition-colors"
									title="标记为已读"
								>
									<Check className="w-5 h-5 text-muted-foreground" />
								</button>
							)}
							<button
								onClick={onDelete}
								className="p-2 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
								title="删除"
							>
								<Trash2 className="w-5 h-5 text-red-500" />
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
