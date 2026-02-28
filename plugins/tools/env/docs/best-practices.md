# 最佳实践

Env 插件的最佳实践和建议。

## 环境分离

### 开发环境

```bash
# .claude/.env.local
API_URL=http://localhost:3000
DEBUG=true
LOG_LEVEL=debug
```

### 生产环境

```bash
# .claude/.env
API_URL=https://api.example.com
DEBUG=false
LOG_LEVEL=info
```

## 敏感信息处理

### 不要提交敏感信息

```gitignore
# .gitignore
.claude/.env.local
*.env.local
```

### 使用示例文件

```bash
# .claude/.env.example
API_KEY=your_api_key_here
DATABASE_URL=postgresql://localhost:5432/mydb
DEBUG=false
```

## 变量命名规范

### 推荐命名

```bash
# 大写蛇形命名
API_KEY=xxx
DATABASE_URL=xxx
DEBUG=true

# 带前缀的命名
APP_NAME=myapp
APP_VERSION=1.0.0
APP_ENV=development
```

### 避免命名

```bash
# 小写命名
api_key=xxx  # 不推荐

# 驼峰命名
apiKey=xxx  # 不推荐
```

## 常见配置

### API 配置

```bash
API_KEY=your_api_key
API_URL=https://api.example.com
API_TIMEOUT=30000
```

### 数据库配置

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
DATABASE_POOL_SIZE=10
```

### 日志配置

```bash
LOG_LEVEL=info
LOG_FORMAT=json
LOG_OUTPUT=stdout
```

## 故障排除

### 变量未加载

1. 检查文件位置是否正确
2. 检查文件格式是否正确
3. 检查变量名是否正确

### 变量值错误

1. 检查优先级规则
2. 检查是否有重复定义
3. 检查是否有特殊字符
