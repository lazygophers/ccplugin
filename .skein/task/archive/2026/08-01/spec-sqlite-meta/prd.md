# spec SQLite metadata 索引 — PRD (主入口)

## 目标
- [ ] spec 文件级 metadata 持久化到 `.recall.db` 的普通表 `spec_meta`
- [ ] serve 端点直接查 SQLite，支持分页/筛选/搜索
- [ ] 前端按需请求（分页 + 筛选参数），不拉全量
- [ ] `spec.py reindex` 重建 `spec_meta` 表（与现有 FTS5 重建一体）

## 边界
范围内：
- [ ] `spec_meta` 表 schema: path(PK)/title/namespace/category/keywords(JSON)/inclusion/status/mtime
- [ ] `/spec/meta` 支持 page/page_size/namespace/category/keyword 参数
- [ ] `/spec/search` 走 SQLite LIKE (path/title/category/keywords)
- [ ] reindex 时 `_rebuild_fts()` 一并重建 `spec_meta`
- [ ] 删除 `_spec_search_cache` 内存缓存

范围外：
- [ ] 不改 FTS5 `rules` 表（章节粒度，recall 命令专用）
- [ ] 不改 index.md / backlinks.md 生成逻辑
- [ ] 不加新依赖

## User Stories
1. As 看板用户, 打开 spec 页面, 左侧树只拉当前页的 spec 列表, 不全量传输
2. As 看板用户, 搜索 spec, 后端走 SQLite 查询返回匹配项, 不在前端做全量过滤
3. As 看板用户, 按类型/标签筛选, 后端按 namespace/keyword 参数过滤
4. As 看板用户, 编辑/新建/删除 spec 后, reindex 自动更新 `spec_meta` 表
5. As 开发者, serve 重启后无需重建内存缓存, SQLite 已持久化

## 验收标准
- [ ] `spec.py reindex` 后 `.recall.db` 含 `spec_meta` 表, 行数 = spec 文件数（跳 index.md/backlinks.md）
- [ ] `SELECT * FROM spec_meta WHERE namespace = 'core'` 返回正确条目
- [ ] `/spec/meta?page=1&page_size=20` 返回分页结果
- [ ] `/spec/meta?namespace=core&category=arch` 返回筛选结果
- [ ] `/spec/search?q=config` 返回 path/title/category/keywords 匹配项
- [ ] 前端树状列表正常展示，筛选/搜索结果正确
- [ ] `_spec_search_cache` 内存缓存已删除，无残留引用
- [ ] serve lifespan 不再调 `_spec_build_cache()`

## Testing Decisions
- [ ] 验证 `.recall.db` 中 `spec_meta` 表 schema + 行数正确
- [ ] `/spec/meta` 端点分页/筛选返回正确
- [ ] 现有 `test_spec.py` / `test_serve_routes.py` 不回归

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-sqlite-meta`)
