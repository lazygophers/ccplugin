---
name: task-management
description: Manage development tasks - create, update, track progress. Use when managing project tasks or work items.
---

# Task Management

## Instructions

When creating tasks:
1. Gather task title, description, and priority from user
2. Use task_create tool with appropriate parameters
3. Confirm creation and provide task ID

When listing tasks:
1. Determine if filtering is needed (by status, priority, tags)
2. Call task_list with filters
3. Present results in clear, organized format

When updating tasks:
1. Confirm which task to update (get task ID)
2. Determine what fields to change
3. Call task_update with changes
4. Confirm the update

When querying ready tasks:
1. Call task_ready to find tasks without blockers
2. Suggest which task to work on next

## Best practices

- Use clear, action-oriented task titles
- Set priorities based on urgency and importance
- Keep descriptions concise but informative
- Update status promptly when work progresses
