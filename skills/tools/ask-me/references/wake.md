# 可选的主动唤醒

Ask Me 为 Claude Code 和 Codex App Server 支持可选的唤醒元数据。把它当增强项，不是必需项。

- 只有在用户同意后才启用自动唤醒。
- Claude Code 需要一个已记录的 session id。
- Codex 需要宿主提供的 thread id。绝不猜测 Codex thread id。
- 适配器失败时，保住答案并回到手动「已提交」流程。
- 直连 `ask` 模式永远不触发唤醒适配器，因为等待中的进程本身就是返回通道。
