# 架构设计

Memory 插件的架构设计。

## 存储架构

```
记忆存储
├── SQLite 数据库
│   ├── memories 表
│   ├── tags 表
│   └── index 表
└── 文件缓存
    ├── 快速访问
    └── 版本快照
```

## 数据模型

### Memory

```typescript
interface Memory {
  id: string;           // 唯一标识
  uri: string;          // URI 地址
  content: string;      // 记忆内容
  priority: number;     // 优先级 (0-10)
  domain: string;       // 域名
  tags: string[];       // 标签
  created_at: Date;     // 创建时间
  updated_at: Date;     // 更新时间
  version: number;      // 版本号
}
```

### Tag

```typescript
interface Tag {
  id: string;           // 唯一标识
  name: string;         // 标签名
  memory_id: string;    // 关联记忆
}
```

## 核心组件

### MemoryStore

负责记忆的存储和检索。

```python
class MemoryStore:
    def read(uri: str) -> Memory
    def create(uri: str, content: str) -> Memory
    def update(uri: str, content: str) -> Memory
    def delete(uri: str) -> bool
    def search(query: str) -> List[Memory]
```

### URIResolver

负责 URI 的解析和路由。

```python
class URIResolver:
    def resolve(uri: str) -> str
    def parse(uri: str) -> URIParts
    def build(domain: str, path: str) -> str
```

### HookManager

负责 Hook 的注册和执行。

```python
class HookManager:
    def register(event: str, handler: Callable)
    def trigger(event: str, context: dict)
    def unregister(event: str, handler: Callable)
```

## 性能优化

### 索引策略

- URI 索引：快速定位
- 全文索引：内容搜索
- 标签索引：标签过滤

### 缓存策略

- 热点记忆缓存
- 预加载缓存
- 版本缓存
