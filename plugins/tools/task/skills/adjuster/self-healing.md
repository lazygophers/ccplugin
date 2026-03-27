# 自愈机制（Self-Healing）指南

## 概述

Level 1.5 自动修复层，针对17类可预测错误即时修复，在 Level 1 Retry 之前执行。

**流程**：失败检测→错误分类→匹配自愈目录→提取参数→HITL决策→执行修复→验证→成功则继续/失败则降级Retry

## 可自愈错误目录（17类）

| # | 错误类型 | 错误特征（正则） | 修复策略 | HITL |
|---|---------|----------------|---------|------|
| 1 | 依赖缺失 | `ModuleNotFoundError`/`ImportError`/`No module named`/`Cannot find package` | 识别项目类型→执行安装命令（pip/npm/cargo） | auto:自动安装; review:确认 |
| 2 | 端口占用 | `Address already in use`/`EADDRINUSE` | lsof查进程→auto:选新端口; review:终止/换端口/手动 | auto:换端口; review:确认 |
| 3 | 目录不存在 | `No such file or directory`/`ENOENT` | 验证路径合法→mkdir -p | auto:用户目录自动; review:系统目录确认 |
| 4 | 权限不足 | `Permission denied`/`EACCES` | 检查权限→chmod(+x/755/644) | auto:用户文件; review:sudo需确认 |
| 5 | 配置缺失 | `Configuration file not found`/`Environment variable.*not set` | 查找.example/.template→复制或生成默认 | auto:默认值; review:敏感信息确认 |
| 6 | 网络超时 | `Connection timeout`/`ETIMEDOUT` | 超时×2(最大120s)→重试3次(指数退避) | auto:自动; review:3次后确认 |
| 7 | API 4xx | `HTTP 4\d{2}`/`Bad Request`/`Unauthorized` | 400/422:修正参数; 401/403:刷新令牌; 404:检查URL | auto:自动; review:认证变更确认 |
| 8 | API 5xx | `HTTP 5\d{2}`/`Internal Server Error` | 指数退避重试3次→降级备用服务→Retry | auto:自动; review:降级确认 |
| 9 | 数据格式 | `JSONDecodeError`/`SyntaxError.*Unexpected token`/`Invalid YAML` | 尝试替代格式(JSON→YAML→CSV)→默认值 | auto:自动; review:默认值确认 |
| 10 | 内存不足 | `MemoryError`/`heap out of memory`/`ENOMEM` | 批次减半→清理缓存→增加max-old-space-size | auto:自动; review:JVM参数确认 |
| 11 | 磁盘不足 | `No space left on device`/`ENOSPC` | 清理临时文件→清理构建产物(dist/build/.cache) | auto:临时文件; review:构建产物确认 |
| 12 | CPU过载 | `CPU time limit exceeded`/`SIGKILL` | 并行度减半→批处理间添加间隔 | auto:自动; review:确认性能影响 |
| 13 | 文件锁 | `resource temporarily unavailable`/`lock file.*exists`/`EAGAIN` | 等待2s重试3次→创建副本操作→替换 | auto:自动等待; review:副本确认 |
| 14 | 数据库锁 | `database is locked`/`SQLITE_BUSY`/`deadlock detected` | 指数退避重试事务→死锁回滚调整顺序 | auto:自动; review:事务顺序确认 |
| 15 | 环境变量 | `environment variable.*not set`/`KeyError:.*ENV` | 查找.env.example默认值→有则设置/无则提示 | auto:默认值; review:敏感变量确认 |
| 16 | 版本不兼容 | `version.*incompatible`/`requires.*version` | 优先升级兼容最新→失败则降级上一稳定版 | auto:自动; review:主版本变更确认 |
| 17 | 系统依赖 | `command not found`/`not recognized as.*command` | 识别OS→生成安装命令(brew/apt)→提示安装 | auto:提示不执行sudo; review:全部确认 |

## HITL 模式联动

| HITL模式 | 低风险(创建目录/调超时) | 中风险(装依赖/改权限) | 高风险(kill进程/sudo) |
|---------|---------------------|--------------------|--------------------|
| auto | 自动执行 | 自动执行 | 需确认 |
| review | 需确认 | 需确认 | 需确认 |
| manual | 需确认 | 需确认 | 需确认 |

## 执行流程

1. **错误匹配**：正则匹配17类错误模式，返回错误类型ID
2. **提取参数**：从错误信息正则提取修复参数（包名/端口/路径等）
3. **HITL决策**：manual总是确认；auto下高风险确认/低风险自动；review默认确认
4. **执行修复**：按错误类型调用对应修复函数，5秒超时
5. **验证修复**：按类型验证（import/端口可用/文件存在/权限正确等），失败降级Retry

## 输出格式

- **成功**：`status:"healed"`, `healing_details`(error_type/action_taken/verification), `retry_config`(backoff_seconds:0)
- **待确认**：`status:"healing_pending"`, `healing_proposal`(error_type/detected_issue/options[]/recommended)
- **失败**：`status:"healing_failed"`, `healing_details`(error_type/action_tried/failure_reason/next_strategy:"retry")

## 最佳实践

优先自愈低风险错误；5秒未完成立即降级；修复后必须验证；记录所有操作历史；仅限用户工作区不改系统。

## 降级条件

错误不在目录中/参数提取失败/用户拒绝/超时>5秒/执行失败/验证失败/同错误自愈2次失败 → 降级 Level 1 Retry。
