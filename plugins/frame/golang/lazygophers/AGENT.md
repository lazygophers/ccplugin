# lazygophers 行为规范

所有使用 lrpc 框架及相关工具库的代码必须遵守以下 Skills 的规范要求。

## 核心框架

### Skills(lazygophers-core)

**使用场景**：

1. **RPC 服务开发**
   - 构建 HTTP/gRPC 服务
   - 实现微服务架构
   - 创建高性能 API 网关

2. **路由管理**
   - 注册静态路由、参数路由、通配符路由、全捕获路由
   - 路由分组和中间件链
   - 路由优先级和匹配规则

3. **客户端调用**
   - 服务发现和负载均衡
   - 连接池管理
   - 超时和重试机制

4. **中间件开发**
   - 认证授权（JWT、Basic Auth）
   - 安全防护（CORS、限流、IP 白名单）
   - 性能优化（压缩、缓存、指标收集）
   - 容错处理（恢复、健康检查）

5. **编解码器**
   - JSON 序列化/反序列化
   - Protobuf 高性能编解码
   - MessagePack 二进制格式
   - 自定义编解码器实现

**必须遵守**：
- 服务端使用 `lrpc.NewServer()` 创建
- 客户端使用 `lrpc.NewClient()` 创建
- 中间件通过 `Use()` 方法注册
- 路由通过 `GET/POST/PUT/DELETE()` 方法注册

## 基础工具模块

### Skills(lazygophers-log)

**使用场景**：

1. **结构化日志**
   - 记录应用运行时状态
   - 错误和异常追踪
   - 分布式追踪（TraceID）

2. **高性能日志**
   - 对象池复用 Entry
   - 异步批量写入
   - 按小时自动轮转

3. **日志级别管理**
   - Debug/Info/Warn/Error/Fatal
   - 动态调整日志级别
   - 条件日志输出

**必须遵守**：
- 使用 `log.GetLogger()` 获取 logger 实例
- 使用结构化字段而非字符串拼接
- 避免在热路径使用 Debug 级别

### Skills(lazygophers-string)

**使用场景**：

1. **零拷贝转换**
   - string ↔ []byte 高性能转换
   - 避免不必要的内存分配
   - 热路径优化

2. **命名转换**
   - CamelCase ↔ SnakeCase 互转
   - KebabCase ↔ PascalCase 互转
   - JSON 标签生成

3. **Unicode 分类**
   - 检测字符串类型（数字、字母、中文等）
   - 输入验证和过滤
   - 文本处理

4. **随机字符串**
   - 临时密码生成
   - Token/Session ID 生成
   - 测试数据生成

**必须遵守**：
- 性能敏感场景使用 `stringx.ToString/ToBytes`
- 命名转换使用 `stringx.Camel2Snake` 等
- Unicode 分类优先使用专用函数

### Skills(lazygophers-json)

**使用场景**：

1. **JSON 序列化/反序列化**
   - API 响应体构建
   - 配置文件解析
   - 数据持久化

2. **文件操作**
   - JSON 文件读写
   - 配置文件管理
   - 数据导入导出

3. **流式处理**
   - 大文件逐行解析
   - 流式 JSON 编码
   - 内存优化

**必须遵守**：
- Linux/macOS/AMD64 自动使用 sonic（2-10x 性能）
- 其他平台使用标准库
- 使用 `jsonx.MarshalToFile/UnmarshalFromFile` 简化文件操作

### Skills(lazygophers-cryptox)

**使用场景**：

1. **对称加密（AES）**
   - 敏感数据存储（密码、令牌）
   - 数据传输加密
   - 文件加密

2. **非对称加密（RSA/ECDSA）**
   - 数字签名和验证
   - 密钥交换（ECDH）
   - 证书管理

3. **哈希计算**
   - 密码哈希（SHA-256/512）
   - 数据完整性校验
   - 文件指纹

4. **HMAC 签名**
   - API 请求签名
   - 消息认证码
   - Token 生成

5. **标识符生成**
   - UUID 生成
   - ULID 生成

**必须遵守**：
- AES 加密使用 GCM 模式（推荐）
- RSA 使用 OAEP 填充（加密）和 PSS 签名
- 密码使用 SHA-256 或更强的哈希
- 初始化向量（IV）必须随机生成

### Skills(lazygophers-network)

**使用场景**：

1. **IP 地址处理**
   - 获取网卡 IP 地址
   - 判断内网/公网 IP
   - 服务绑定 IP 选择

2. **真实 IP 提取**
   - 从代理头提取客户端真实 IP
   - 支持 CDN/代理（13+ 种头部）
   - IP 白名单验证

3. **URL 处理**
   - URL 查询参数排序
   - 签名验证
   - 缓存键生成

**必须遵守**：
- 使用 `urlx.GetListenIp()` 自动选择绑定 IP
- 使用 `urlx.RealIpFromHeader()` 提取真实 IP
- 签名验证前使用 `urlx.SortQuery()` 排序参数

## 类型与数据模块

### Skills(lazygophers-anyx)

**使用场景**：

1. **类型转换**
   - any 与基础类型互转（Bool/Int/Float64/String/Bytes）
   - 零值安全返回

2. **复杂类型转换**
   - Slice 类型转换（StringSlice/Uint64Slice/Int64Slice）
   - Map 类型转换（Map/MapStringString/MapStringInt64）

3. **嵌套访问**
   - 点号分隔路径访问嵌套字段（`user.profile.name`）
   - 自动类型推断

4. **线程安全**
   - 基于 sync.Map 的并发安全设计

**必须遵守**：
- 优先使用泛型方法（Get[T]()）而非反射
- 检查错误返回值
- 注意零值和"值不存在"的区分

### Skills(lazygophers-candy)

**使用场景**：

1. **类型转换函数**
   - ToInt/ToFloat64/ToString/ToBytes 等
   - ToPtr 泛型指针创建

2. **泛型工具函数**
   - 数学运算：Max/Min/Sum/Average/Abs
   - 切片操作：First/Last/Unique/Reverse/Shuffle/Sort/Chunk
   - 过滤映射：Filter/Map/Reduce/Contains/Index
   - 遍历函数：All/Any/Each

3. **结构体操作**
   - Pluck 系列：提取切片元素的字段
   - KeyBy 系列：按字段值索引
   - SliceField2Map：字段值提取为集合

4. **深度操作**
   - DeepCopy/Clone：深度复制
   - DeepEqual：深度比较

**必须遵守**：
- 优先使用泛型版本而非反射版本
- 预分配切片容量提高性能
- 注意结构体未导出字段的处理

### Skills(lazygophers-human)

**使用场景**：

1. **字节大小格式化**
   - Bytes/B/KB/MB/GB/TB/PB（1024 进制）
   - 网络速度格式化（Bps/Kbps/Mbps，1000 进制）

2. **时间间隔格式化**
   - 自然语言（"3分钟前"）
   - 时钟格式（"2:30:15"）

3. **多语言支持**
   - 中文、英文、日文、韩文等 8+ 种语言
   - 语言回退机制

**必须遵守**：
- 根据场景选择合适的精度
- 使用紧凑模式节省空间
- UI 展示优先使用人类友好格式

### Skills(lazygophers-randx)

**使用场景**：

1. **数字随机数**
   - Int/Int64/Float32/Float64/Uint32/Uint64
   - 范围随机数（Intn/Int64n）

2. **批量操作**
   - BatchIntn/BatchInt64n 批量生成
   - 减少锁竞争提高性能

3. **布尔随机数**
   - Bool/Booln
   - WeightedBool 加权随机

4. **随机选择**
   - Choose/ChooseN 从集合选择
   - WeightedChoose 加权选择
   - Shuffle 洗牌

5. **时间随机化**
   - Jitter 抖动（指数退避）
   - RandomDuration/RandomTime
   - SleepRandom 随机延迟

**必须遵守**：
- 注意：非加密安全，需加密安全使用 crypto/rand
- 批量操作优先以提高性能
- 边界条件处理

### Skills(lazygophers-validator)

**使用场景**：

1. **结构体验证**
   - 内置验证器：required、email、phone、url、len、min、max
   - 中国本地化：mobile、idcard、bankcard、chinese_name、strong_password

2. **自定义验证器**
   - 注册自定义验证函数
   - 跨字段验证

3. **国际化**
   - 13+ 种语言错误消息
   - 自定义翻译

**必须遵守**：
- 复用 Validator 实例（并发安全）
- 提供客户端友好的错误消息
- 自定义验证器注意 panic 处理

## 缓存模块

### Skills(in-memory-cache)

**使用场景**：

1. **纯内存缓存**（lazygophers/cache）
   - 单机应用热数据缓存
   - 本地计算结果缓存
   - 高性能键值存储（LRU 87M+ ops/sec）

2. **11 种缓存算法**
   - LRU：通用场景，默认推荐
   - LFU：访问频率差异大
   - TinyLFU：高并发/突发流量
   - ARC：负载突发、自适应
   - SLRU：分段缓存（probation + protected）
   - LRU-K：跟踪 K 次访问历史
   - MRU：反向访问模式
   - FBR/ALFU：特定场景优化

3. **泛型接口**
   - 类型安全的缓存 API
   - 零分配缓存命中
   - 线程安全（sync.RWMutex）

**必须遵守**：
- 根据访问模式选择算法（LRU 默认）
- 使用泛型接口 `cache.New[Type, K, V](size)`
- 缓存大小根据内存限制合理设置

### Skills(lazygophers-redis-cache)

**使用场景**：

1. **第三方缓存中间件**（lazygophers/middleware/cache）
   - Redis 分布式缓存
   - Memcached 缓存
   - 多级缓存架构

2. **缓存模式**
   - CacheAside：先读缓存，未命中读数据库，再写缓存
   - WriteThrough：同时写缓存和数据库
   - WriteBehind：先写缓存，异步批量写数据库

3. **缓存保护**
   - 缓存穿透：布隆过滤器、空值缓存
   - 缓存击穿：互斥锁、逻辑过期
   - 缓存雪崩：随机 TTL、多级缓存、缓存预热

4. **分布式锁**
   - Redis 单节点锁
   - Redlock 多节点锁
   - 锁续约机制

5. **批量操作**
   - MGET/MGET 批量获取
   - Pipeline 减少网络往返
   - 连接池管理

**必须遵守**：
- Key 设计层级清晰（如 `user:123`）
- TTL 根据数据更新频率设置
- 缓存更新优先使用 CacheAside + Delete
- 大对象分片存储或压缩

### Skills(lazygophers-utils-cache)

**使用场景**：

1. **纯缓存算法**（lazygophers/utils/cache）
   - 11 种缓存策略实现（算法级别）
   - 无 TTL、无监控，专注算法设计

2. **算法选择**
   - 通用场景：LRU、LFU
   - 高并发：TinyLFU、Window-TinyLFU
   - 自适应：ARC、Adaptive LFU
   - 数据库：LRU-K
   - 顺序扫描：MRU

**必须遵守**：
- 与 in-memory-cache 的区别：这是算法实现，in-memory-cache 是功能完整缓存
- 研究算法特性时使用此模块

## 并发与运行时模块

### Skills(lazygophers-wait)

**使用场景**：

1. **信号量池（Pool）**
   - 并发控制（API 限流、数据库连接池）
   - Lock/Unlock 获取/释放信号量
   - Sync 同步执行保护

2. **Worker 工作池**
   - 固定协程池处理任务队列
   - 批量数据处理、消息队列消费者

3. **Async 系列**
   - Async/AsyncUnique 批量异步任务编排
   - 唯一性任务去重

**必须遵守**：
- Key 命名规范清晰
- 合理设置并发数
- defer 确保 Unlock
- 避免死锁

### Skills(lazygophers-routine)

**使用场景**：

1. **协程启动**
   - Go：基础错误处理
   - GoWithRecover：Panic 恢复 + 堆栈追踪
   - GoWithMustSuccess：关键任务错误时退出

2. **生命周期钩子**
   - BeforeRoutine：协程启动前（分布式追踪）
   - AfterRoutine：协程结束后（追踪清理）

3. **协程缓存**
   - 泛型协程本地数据缓存

**必须遵守**：
- 注意闭包变量捕获
- 关键任务使用 GoWithMustSuccess
- 危险操作使用 GoWithRecover

### Skills(lazygophers-hystrix)

**使用场景**：

1. **熔断器**
   - CircuitBreaker：功能完整，环形缓冲区
   - FastCircuitBreaker：超轻量，极致性能
   - BatchCircuitBreaker：批量处理，高吞吐

2. **熔断状态**
   - Closed：正常状态，请求通过
   - Open：熔断状态，直接降级
   - HalfOpen：探测状态，尝试恢复

3. **降级处理**
   - Fallback 降级函数
   - 半开状态探测机制

**必须遵守**：
- 合理设置阈值（并发数、错误率）
- 提供降级逻辑
- 监控熔断状态

### Skills(lazygophers-runtime)

**使用场景**：

1. **平台检测**
   - IsWindows/IsDarwin/IsLinux
   - 零运行时开销（编译时确定）

2. **路径管理**
   - ExecFile/ExecDir：可执行文件位置
   - Pwd：当前工作目录
   - UserHomeDir/UserConfigDir/UserCacheDir
   - LazyConfigDir/LazyCacheDir：应用特定目录

3. **Panic 处理**
   - CachePanic/CachePanicWithHandle
   - OnPanic：全局 panic 处理器
   - GetStack/PrintStack：堆栈追踪

4. **信号处理与优雅退出**
   - GetExitSign：退出信号通道
   - WaitExit：阻塞直到退出信号
   - Exit：优雅退出

**必须遵守**：
- 使用 WaitExit 实现优雅关闭
- Panic 恢复后记录完整堆栈
- 跨平台路径使用 runtime 模块

## 配置与应用模块

### Skills(lazygophers-app)

**使用场景**：

1. **运行模式**
   - Debug/Test/Alpha/Beta/Release
   - 编译时确定（构建标签）
   - APP_ENV 环境变量覆盖

2. **构建信息**
   - 版本号、提交哈希、分支
   - 构建时间、Go 版本
   - -ldflag 注入

**必须遵守**：
- 使用构建标签而非运行时判断
- 敏感信息使用环境变量

### Skills(lazygophers-config)

**使用场景**：

1. **配置格式支持**（9 种）
   - JSON/YAML/TOML/INI/XML
   - Properties/ENV/HCL/JSON5

2. **配置加载**
   - 自动格式检测
   - 智能配置文件搜索
   - 嵌套结构体支持

3. **环境变量覆盖**
   - env 标签覆盖
   - 类型自动转换

4. **配置验证**
   - Validator 集成
   - 自定义解析器

**必须遵守**：
- 敏感信息使用环境变量
- 配置文件和默认值分离
- 提供配置验证

### Skills(lazygophers-defaults)

**使用场景**：

1. **默认值设置**
   - 结构体字段默认值
   - 支持所有基础类型
   - 指针类型自动初始化

2. **复杂类型**
   - 切片、数组、Map、通道
   - 时间类型（5 种格式）
   - 嵌套结构体

3. **配置选项**
   - 错误处理模式
   - 自定义默认值函数
   - 值覆盖控制

**必须遵守**：
- 结构体设计优先考虑默认值
- 指针字段谨慎使用
- 测试默认值逻辑

### Skills(lazygophers-osx)

**使用场景**：

1. **文件操作**
   - Exist：文件存在性检查（推荐）
   - IsDir/IsFile：类型判断
   - FsHasFile：fs.FS 抽象文件系统支持

2. **文件管理**
   - RenameForce：强制重命名
   - Copy：复制文件

**必须遵守**：
- 使用 Exist 而非 Exists（有 bug）
- 抽象文件系统使用 FsHasFile

### Skills(lazygophers-xtime)

**使用场景**：

1. **时间常量**
   - 基础单位：纳秒到小时
   - 扩展常量：半天、一天
   - 工作日：5 天周、21.5 天月
   - 长周期：周、月、季度、年、十年

2. **时间解析**
   - Parse：多格式自动识别
   - MustParse：解析失败 panic
   - With：包装 time.Time

3. **时间计算**
   - BeginningOfXxx/EndOfXxx：时间范围
   - Quarter：季度计算（1-4）

4. **农历功能**
   - 公历转农历（1900-2100）
   - 生肖计算
   - 汉字格式（二零二三、八月、十五）

5. **节气系统**
   - 24 节气精确计算（1904-3000）
   - NextSolarterm：下一个节气

6. **综合日历**
   - 公历、农历、干支、节气
   - String/DetailedString/ToMap

**必须遵守**：
- 使用时间常量而非硬编码数字
- 农历、节气注意数据范围

## 消息队列模块

### Skills(lazygophers-queue)

**使用场景**：

1. **队列类型**
   - Memory Queue：内存队列，最快性能
   - Redis Streams Queue：持久化、消费者组
   - Kafka Queue：分布式、高吞吐

2. **消息模式**
   - 发布订阅：一个 Topic 多个 Channel
   - 点对点：消费者组竞争消费
   - 广播：所有 Channel 都收到消息

3. **重试机制**
   - Handler 返回 Retry 触发重试
   - MaxRetries 限制重试次数
   - Nack 手动重新入队

4. **延迟队列**
   - SetExpires：相对过期时间
   - SetExpiresAt：绝对过期时间
   - 自动过滤过期消息

5. **批量操作**
   - PubBatch/PubMsgBatch 批量发布
   - MaxInFlight 控制并发消费

**必须遵守**：
- 根据场景选择后端
- 设置合理的过期时间
- 处理 Panic 和错误
- 优雅关闭资源

## 中间件模块

### Skills(lazygophers-i18n)

**使用场景**：

1. **国际化支持**
   - 多语言网站和应用
   - 区域化内容管理
   - 语言切换功能

2. **本地化资源**
   - 翻译文件管理（JSON/YAML）
   - 日期、货币格式化
   - 文本方向处理（RTL/LTR）

3. **语言检测**
   - 基于 Accept-Language 自动检测
   - 查询参数/Cookie 手动指定
   - 用户偏好设置持久化

**必须遵守**：
- 翻译键使用层级结构（如 `errors.not_found`）
- 支持参数化翻译（如 `welcome_user` with `{{.name}}`）
- 提供默认值避免翻译缺失
- 翻译文件使用 BCP 47 语言代码（如 `zh-CN`）

### Skills(lazygophers-xerror)

**使用场景**：

1. **错误码管理**
   - 统一的错误码体系（1xxxx 通用、2xxxx 用户、3xxxx 业务）
   - 预定义常用错误码
   - 自定义业务错误码

2. **错误响应**
   - 标准化错误响应格式
   - 多语言错误消息（结合 i18n）
   - 开发模式显示堆栈追踪

3. **错误处理**
   - 业务错误返回客户端
   - 系统错误记录日志并返回通用消息
   - 错误监控和告警集成

**必须遵守**：
- 错误码分段管理（1-5xxxx 不同类型）
- 使用 `xerror.Error()` 创建业务错误
- 使用 `xerror.Wrap()` 包装系统错误
- 提供客户端友好的错误消息

### Skills(lazygophers-database)

**使用场景**：

1. **关系型数据库访问**
   - MySQL、PostgreSQL、SQLite、SQL Server、TiDB
   - 连接池管理
   - 参数化查询防 SQL 注入

2. **CRUD 操作**
   - 插入、查询、更新、删除
   - 批量操作优化
   - 软删除支持

3. **事务处理**
   - 自动事务、嵌套事务
   - SavePoint 支持
   - 事务回滚和提交

4. **分页查询**
   - 自动分页处理
   - 总数统计
   - 游标分页

**必须遵守**：
- 使用参数化查询防止 SQL 注入
- 相关操作使用事务
- 检查所有数据库操作的错误
- 使用预加载解决 N+1 问题
- 为常用查询字段添加索引

### Skills(lazygophers-mongo)

**使用场景**：

1. **文档数据库访问**
   - MongoDB 连接和配置
   - 副本集、分片集群
   - 连接池管理

2. **文档操作**
   - 插入、查询、更新、删除文档
   - 嵌套文档、数组操作
   - 批量写入优化

3. **聚合查询**
   - 聚合管道（$match、$group、$lookup 等）
   - 数据分析和统计
   - 时间序列数据

4. **索引管理**
   - 单字段、复合、唯一索引
   - 文本索引、地理空间索引
   - TTL 索引自动过期

5. **事务支持**
   - 多文档事务（副本集）
   - 会话事务管理
   - 事务回滚和提交

**必须遵守**：
- 使用上下文控制查询超时
- 为常用查询字段创建索引
- 使用结构体而非 bson.M 提高类型安全
- 大量操作使用批量写入
- 使用投影减少返回字段

## 通用规范

1. **错误处理**：所有函数返回 error，必须检查并处理
2. **并发安全**：导出的结构体必须线程安全
3. **性能优先**：热路径使用零拷贝、对象池
4. **测试覆盖**：单元测试覆盖率 ≥ 80%
5. **文档注释**：导出的函数/类型必须有 godoc 注释
