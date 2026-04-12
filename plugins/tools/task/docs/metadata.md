## `index.json` 任务索引文件格式说明

路径：`.lazygophers/tasks/index.json`

```json
{
  "任务ID": {
    "id": "任务ID",
    "status": "pending|explore|align|plan|exec|verify|adjust|done|cancel",
    "description": "任务描述",
    "additional": [
      "补充信息 1",
      "补充信息 2"
    ],
    "created_at": 1718000000,
    "updated_at": 1718000000
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 任务唯一标识（中文） |
| status | string | 任务状态，参见 `docs/状态管理.md` |
| description | string | 任务描述 |
| additional | string[] | 补充信息列表 |
| created_at | int | 创建时间（Unix 时间戳） |
| updated_at | int | 最后更新时间（Unix 时间戳） |
