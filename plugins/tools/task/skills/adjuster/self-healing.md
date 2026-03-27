# 自愈机制（Self-Healing）

Level 1.5 自动修复层，针对17类可预测错误即时修复。流程：失败检测→错误分类→匹配目录→提取参数→HITL决策→执行修复→验证→成功则继续/失败降级Retry。

## 可自愈错误目录（17类）

| # | 错误类型 | 特征 | 修复策略 |
|---|---------|------|---------|
| 1 | 依赖缺失 | `ModuleNotFoundError`/`ImportError` | 识别项目类型→安装(pip/npm/cargo) |
| 2 | 端口占用 | `EADDRINUSE` | lsof→换端口或终止进程 |
| 3 | 目录不存在 | `ENOENT`/`No such file` | 验证路径→`mkdir -p` |
| 4 | 权限不足 | `Permission denied` | 检查→chmod(+x/755/644) |
| 5 | 配置缺失 | `config not found`/`env not set` | 查.example/.template→复制或默认 |
| 6 | 网络超时 | `ETIMEDOUT` | 超时×2(max120s)→重试3次 |
| 7 | API 4xx | `HTTP 4xx` | 400:修正参数; 401:刷新令牌; 404:检查URL |
| 8 | API 5xx | `HTTP 5xx` | 指数退避重试→降级备用 |
| 9 | 数据格式 | `JSONDecodeError`/`Invalid YAML` | 替代格式→默认值 |
| 10 | 内存不足 | `MemoryError`/`ENOMEM` | 批次减半→清缓存→增max-old-space |
| 11 | 磁盘不足 | `ENOSPC` | 清临时文件→清构建产物 |
| 12 | CPU过载 | `SIGKILL` | 并行度减半→添加间隔 |
| 13 | 文件锁 | `EAGAIN`/`lock exists` | 等待2s重试→创建副本→替换 |
| 14 | 数据库锁 | `SQLITE_BUSY`/`deadlock` | 退避重试事务→回滚调整顺序 |
| 15 | 环境变量 | `env not set` | 查.env.example→设默认值 |
| 16 | 版本不兼容 | `version incompatible` | 升级兼容→降级稳定版 |
| 17 | 系统依赖 | `command not found` | 识别OS→生成安装命令 |

## HITL模式

| 模式 | 低风险 | 中风险 | 高风险 |
|------|--------|--------|--------|
| auto | 自动 | 自动 | 确认 |
| review | 确认 | 确认 | 确认 |

## 输出格式

- 成功：`status:"healed"` + healing_details + `backoff_seconds:0`
- 待确认：`status:"healing_pending"` + healing_proposal{options[],recommended}
- 失败：`status:"healing_failed"` + next_strategy:"retry"

## 降级条件

不在目录/参数失败/用户拒绝/超时>5s/执行失败/验证失败/同错误2次失败 → Level 1 Retry
