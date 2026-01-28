---
name: lrpc-config
description: lazygophers/utils config 模块完整指南 - 多格式配置文件加载、环境变量覆盖、动态配置管理
---

# lazygophers/utils config 模块完整指南

## Overview

`lazygophers/utils/config` 是一个功能强大的 Go 配置管理模块，支持多种配置文件格式、环境变量覆盖、嵌套结构体处理和动态配置热更新。该模块提供统一的 API 来加载、保存和管理应用程序配置。

## 核心特性

- **多格式支持**: JSON、YAML、TOML、INI、XML、Properties、ENV、HCL、JSON5
- **环境变量覆盖**: 通过 `env` 标签实现环境变量对配置文件的覆盖
- **自动格式检测**: 基于文件扩展名自动识别配置格式
- **配置文件搜索**: 智能搜索配置文件路径（环境变量、当前目录、程序目录）
- **嵌套结构体支持**: 支持多层嵌套的配置结构
- **类型转换**: 自动进行基础类型转换（string、int、uint、float、bool）
- **验证集成**: 集成 `go-playground/validator` 进行配置验证
- **自定义解析器**: 支持注册自定义配置格式解析器

## 支持的配置格式

### 1. JSON (.json)

最常用的配置格式，支持嵌套对象和数组。

```go
type Config struct {
    Name  string `json:"name"`
    Port  int    `json:"port"`
    Debug bool   `json:"debug"`
}
```

**配置文件示例** (`config.json`):
```json
{
    "name": "myapp",
    "port": 8080,
    "debug": true
}
```

### 2. YAML (.yaml, .yml)

人类可读的配置格式，支持注释和复杂结构。

```go
type Config struct {
    Name  string `yaml:"name"`
    Port  int    `yaml:"port"`
    Debug bool   `yaml:"debug"`
}
```

**配置文件示例** (`config.yaml`):
```yaml
name: myapp
port: 8080
debug: true
```

### 3. TOML (.toml)

简洁的配置格式，适合层级化配置。

```go
type Config struct {
    Name  string `toml:"name"`
    Port  int    `toml:"port"`
    Debug bool   `toml:"debug"`
}
```

**配置文件示例** (`config.toml`):
```toml
name = "myapp"
port = 8080
debug = true
```

### 4. INI (.ini)

传统的键值对配置格式，支持分节。

```go
type Config struct {
    Name  string `ini:"name"`
    Port  int    `ini:"port"`
    Debug bool   `ini:"debug"`
}
```

**配置文件示例** (`config.ini`):
```ini
name = myapp
port = 8080
debug = true
```

### 5. XML (.xml)

标准的 XML 配置格式。

```go
type Config struct {
    Name  string `xml:"name"`
    Port  int    `xml:"port"`
    Debug bool   `xml:"debug"`
}
```

**配置文件示例** (`config.xml`):
```xml
<Config>
    <name>myapp</name>
    <port>8080</port>
    <debug>true</debug>
</Config>
```

### 6. Properties (.properties)

Java 风格的属性文件格式。

```go
type Config struct {
    Name  string `properties:"name"`
    Port  int    `properties:"port"`
    Debug bool   `properties:"debug"`
}
```

**配置文件示例** (`config.properties`):
```properties
name=myapp
port=8080
debug=true
```

**特性**:
- 支持 `=` 和 `:` 作为分隔符
- 支持 `#` 和 `!` 注释
- 支持转义字符：`\n`、`\t`、`\r`、`\\`

### 7. ENV (.env)

环境变量文件格式。

```go
type Config struct {
    Name  string `env:"name"`
    Port  int    `env:"port"`
    Debug bool   `env:"debug"`
}
```

**配置文件示例** (`.env`):
```env
name="myapp"
port=8080
debug=true
```

**特性**:
- 支持单引号和双引号包围的值
- 支持 `#` 注释
- 自动去除引号

### 8. HCL (.hcl)

HashiCorp Configuration Language 格式。

```go
type Config struct {
    Name  string `hcl:"name"`
    Port  int    `hcl:"port"`
    Debug bool   `hcl:"debug"`
}
```

**配置文件示例** (`config.hcl`):
```hcl
name = "myapp"
port = 8080
debug = true
```

### 9. JSON5 (.json5)

增强版 JSON，支持注释和尾随逗号。

```go
type Config struct {
    Name  string `json:"name"`
    Port  int    `json:"port"`
    Debug bool   `json:"debug"`
}
```

**配置文件示例** (`config.json5`):
```json5
{
    // This is a comment
    name: "myapp",
    port: 8080,
    debug: true,
}
```

## 核心 API

### LoadConfig

加载配置文件并进行验证。

```go
func LoadConfig(c any, paths ...string) error
```

**参数**:
- `c`: 配置结构体指针（必须是指针类型）
- `paths`: 可选的配置文件路径列表（支持多个路径，按顺序查找）

**返回**:
- `error`: 加载或验证失败时返回错误

**示例**:
```go
type Config struct {
    Name  string `json:"name" validate:"required"`
    Port  int    `json:"port" validate:"min=1,max=65535"`
    Debug bool   `json:"debug"`
}

var config Config
err := config.LoadConfig(&config, "config.json")
if err != nil {
    log.Fatal("Failed to load config:", err)
}
```

### LoadConfigSkipValidate

加载配置文件但不进行验证。

```go
func LoadConfigSkipValidate(c any, paths ...string) error
```

**参数**:
- `c`: 配置结构体指针
- `paths`: 可选的配置文件路径列表

**返回**:
- `error`: 仅在加载失败时返回错误

**示例**:
```go
var config Config
err := config.LoadConfigSkipValidate(&config, "config.yaml")
if err != nil {
    log.Warn("Using default config:", err)
}
```

### SetConfig

保存配置到文件。

```go
func SetConfig(c any) error
```

**参数**:
- `c`: 配置结构体

**返回**:
- `error`: 保存失败时返回错误

**示例**:
```go
config := Config{
    Name:  "myapp",
    Port:  8080,
    Debug: false,
}

err := config.SetConfig(&config)
if err != nil {
    log.Fatal("Failed to save config:", err)
}
```

**注意**: `SetConfig` 使用之前 `LoadConfig` 找到的配置文件路径。格式与加载时的文件格式相同。

### RegisterParser

注册自定义配置格式解析器。

```go
func RegisterParser(ext string, m Marshaler, u Unmarshaler)
```

**参数**:
- `ext`: 文件扩展名（如 `.custom`）
- `m`: 序列化函数（写入配置）
- `u`: 反序列化函数（读取配置）

**示例**:
```go
func customUnmarshaler(reader io.Reader, v interface{}) error {
    // 自定义解析逻辑
    return nil
}

func customMarshaler(writer io.Writer, v interface{}) error {
    // 自定义序列化逻辑
    return nil
}

config.RegisterParser(".custom", customMarshaler, customUnmarshaler)
```

## 配置文件搜索策略

当不提供路径或提供的路径不存在时，`LoadConfig` 会按以下顺序搜索配置文件：

### 搜索顺序

1. **指定路径**: 优先使用用户提供的路径（`paths` 参数）
2. **环境变量**: 检查 `LAZYGOPHERS_CONFIG` 环境变量
3. **当前目录**: 在当前工作目录查找 `conf.*` 或 `config.*`
4. **程序目录**: 在可执行文件所在目录查找 `conf.*` 或 `config.*`

### 配置文件名优先级

在同一个目录中，`conf.*` 优先于 `config.*`。

**示例**:
```
./conf.json      # 优先级最高
./config.json    # 次优先
./conf.yaml      # 如果 conf.json 不存在，按扩展名字母顺序
./config.yaml
```

### 环境变量指定路径

```bash
# 通过环境变量指定配置文件路径
export LAZYGOPHERS_CONFIG=/path/to/config.json

# 然后直接调用 LoadConfig，不需要提供路径
config.LoadConfig(&cfg)
```

## 环境变量覆盖

### Env Tag 使用

通过 `env` 标签，环境变量可以覆盖配置文件中的值。

**优先级**: 环境变量 > 配置文件 > 默认值

### 基本用法

```go
type Config struct {
    Name  string `json:"name" env:"APP_NAME"`
    Port  int    `json:"port" env:"APP_PORT"`
    Debug bool   `json:"debug" env:"APP_DEBUG"`
}
```

**配置文件** (`config.json`):
```json
{
    "name": "file-app",
    "port": 8080,
    "debug": false
}
```

**环境变量**:
```bash
export APP_NAME="env-app"
export APP_PORT="9000"
export APP_DEBUG="true"
```

**结果**:
- `Name`: "env-app" (来自环境变量)
- `Port`: 9000 (来自环境变量)
- `Debug`: true (来自环境变量)

### 嵌套结构体环境变量覆盖

环境变量可以直接覆盖嵌套结构体中的字段。

```go
type Config struct {
    Name  string `json:"name" env:"APP_NAME"`
    Database struct {
        Host     string `json:"host" env:"DB_HOST"`
        Port     int    `json:"port" env:"DB_PORT"`
        Username string `json:"username" env:"DB_USER"`
        Password string `json:"password" env:"DB_PASS"`
    } `json:"database"`
}
```

**配置文件** (`config.json`):
```json
{
    "name": "myapp",
    "database": {
        "host": "localhost",
        "port": 5432,
        "username": "user",
        "password": "pass"
    }
}
```

**环境变量**:
```bash
export DB_HOST="prod.example.com"
export DB_PORT="3306"
```

**结果**:
- `Database.Host`: "prod.example.com" (环境变量覆盖)
- `Database.Port`: 3306 (环境变量覆盖)
- `Database.Username`: "user" (来自配置文件)
- `Database.Password`: "pass" (来自配置文件)

### 环境变量覆盖规则

1. **非空值覆盖**: 只有非空的环境变量才会覆盖配置文件值
2. **类型转换**: 自动将字符串环境变量转换为目标类型
3. **错误处理**: 转换失败时保留配置文件值，并记录 Debug 日志
4. **部分覆盖**: 可以只设置部分环境变量，未设置的保留配置文件值

**类型转换示例**:
```go
type Config struct {
    Port     int     `json:"port" env:"PORT"`
    Rate     float64 `json:"rate" env:"RATE"`
    Enabled  bool    `json:"enabled" env:"ENABLED"`
}
```

```bash
export PORT="8080"        # 转换为 int 8080
export RATE="0.95"        # 转换为 float64 0.95
export ENABLED="true"     # 转换为 bool true
```

### 环境变量格式

**支持的布尔值**:
- `true`: `1`, `t`, `T`, `TRUE`, `true`, `True`
- `false`: `0`, `f`, `F`, `FALSE`, `false`, `False`

**支持的数值**:
- 整数: `123`, `-456`
- 浮点数: `3.14`, `-0.001`, `1e10`

## 嵌套结构体支持

### 多层嵌套

config 模块支持任意深度的嵌套结构体。

```go
type Config struct {
    Server struct {
        Host struct {
            IP   string `json:"ip" env:"HOST_IP"`
            Port int    `json:"port" env:"HOST_PORT"`
        } `json:"host"`
        Timeout int `json:"timeout" env:"TIMEOUT"`
    } `json:"server"`
}
```

**配置文件** (`config.json`):
```json
{
    "server": {
        "host": {
            "ip": "127.0.0.1",
            "port": 8080
        },
        "timeout": 30
    }
}
```

**环境变量**:
```bash
export HOST_IP="192.168.1.1"
export HOST_PORT="9000"
```

### Properties 格式嵌套

对于 Properties 和 ENV 格式，使用点号表示嵌套。

**config.properties**:
```properties
server.host.ip=127.0.0.1
server.host.port=8080
server.timeout=30
```

## 配置验证

### 使用 Validator 标签

集成 `go-playground/validator` 进行配置验证。

```go
type Config struct {
    Name     string `json:"name" validate:"required"`
    Port     int    `json:"port" validate:"min=1,max=65535,required"`
    Host     string `json:"host" validate:"ip"`
    Email    string `json:"email" validate:"email"`
    URL      string `json:"url" validate:"url"`
    Password string `json:"password" validate:"min=8,max=32"`
}
```

**验证规则示例**:
- `required`: 必填字段
- `min=X,max=Y`: 数值或字符串长度范围
- `email`: 邮箱格式
- `url`: URL 格式
- `ip`: IP 地址格式

### 验证流程

```go
var config Config

// LoadConfig: 加载配置 + 验证
err := config.LoadConfig(&config, "config.json")
if err != nil {
    // 验证失败时会返回详细错误信息
    log.Fatal("Config validation failed:", err)
}

// LoadConfigSkipValidate: 仅加载配置，跳过验证
err = config.LoadConfigSkipValidate(&config, "config.json")
if err != nil {
    log.Fatal("Failed to load config:", err)
}

// 手动验证（如果使用 LoadConfigSkipValidate）
err = validator.Struct(&config)
if err != nil {
    log.Fatal("Validation failed:", err)
}
```

## 完整使用示例

### 示例 1: 基本使用

```go
package main

import (
    "log"
    "github.com/lazygophers/utils/config"
)

type Config struct {
    Name     string `json:"name" validate:"required"`
    Port     int    `json:"port" validate:"min=1,max=65535"`
    Debug    bool   `json:"debug"`
    LogLevel string `json:"log_level" validate:"required,oneof=debug info warn error"`
}

func main() {
    var cfg Config

    // 加载并验证配置
    err := config.LoadConfig(&cfg, "config.json")
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }

    log.Printf("Loaded config: %+v", cfg)
}
```

**config.json**:
```json
{
    "name": "myapp",
    "port": 8080,
    "debug": false,
    "log_level": "info"
}
```

### 示例 2: 环境变量覆盖

```go
package main

import (
    "log"
    "github.com/lazygophers/utils/config"
)

type Config struct {
    AppName  string `json:"app_name" env:"APP_NAME"`
    HTTPPort int    `json:"http_port" env:"HTTP_PORT"`
    Database struct {
        Host     string `json:"host" env:"DB_HOST"`
        Port     int    `json:"port" env:"DB_PORT"`
        Username string `json:"username" env:"DB_USERNAME"`
        Password string `json:"password" env:"DB_PASSWORD"`
    } `json:"database"`
}

func main() {
    var cfg Config

    // 加载配置（环境变量会自动覆盖配置文件值）
    err := config.LoadConfigSkipValidate(&cfg, "config.json")
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }

    log.Printf("App: %s, Port: %d", cfg.AppName, cfg.HTTPPort)
    log.Printf("DB: %s@%s:%d", cfg.Database.Username, cfg.Database.Host, cfg.Database.Port)
}
```

**config.json**:
```json
{
    "app_name": "dev-app",
    "http_port": 8080,
    "database": {
        "host": "localhost",
        "port": 5432,
        "username": "devuser",
        "password": "devpass"
    }
}
```

**环境变量** (生产环境):
```bash
export APP_NAME="prod-app"
export HTTP_PORT="9000"
export DB_HOST="prod-db.example.com"
export DB_PORT="3306"
export DB_USERNAME="produser"
export DB_PASSWORD="prodpass"
```

### 示例 3: 多格式支持

```go
package main

import (
    "log"
    "path/filepath"
    "github.com/lazygophers/utils/config"
)

type Config struct {
    Name string `yaml:"name" json:"name" toml:"name" validate:"required"`
    Port int    `yaml:"port" json:"port" toml:"port" validate:"min=1,max=65535"`
}

func main() {
    var cfg Config

    // 尝试多个配置文件格式
    paths := []string{
        "config.yaml",
        "config.json",
        "config.toml",
    }

    // 自动查找第一个存在的配置文件
    err := config.LoadConfig(&cfg, paths...)
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }

    log.Printf("Loaded from %s: %+v", filepath.Base(config.GetConfigPath()), cfg)
}
```

### 示例 4: 动态配置保存

```go
package main

import (
    "log"
    "github.com/lazygophers/utils/config"
)

type Config struct {
    Name     string `json:"name"`
    Port     int    `json:"port"`
    Debug    bool   `json:"debug"`
    Settings struct {
        Timeout int    `json:"timeout"`
        Rate    float64 `json:"rate"`
    } `json:"settings"`
}

func main() {
    var cfg Config

    // 加载现有配置
    err := config.LoadConfigSkipValidate(&cfg, "config.json")
    if err != nil {
        log.Warn("Using default config:", err)
        // 设置默认值
        cfg.Name = "myapp"
        cfg.Port = 8080
        cfg.Debug = false
        cfg.Settings.Timeout = 30
        cfg.Settings.Rate = 0.95
    }

    // 修改配置
    cfg.Port = 9000
    cfg.Debug = true

    // 保存配置
    err = config.SetConfig(&cfg)
    if err != nil {
        log.Fatal("Failed to save config:", err)
    }

    log.Println("Config saved successfully")
}
```

### 示例 5: 自定义配置格式

```go
package main

import (
    "io"
    "encoding/csv"
    "log"
    "github.com/lazygophers/utils/config"
)

type Config struct {
    Fields []string `csv:"field"`
}

// 自定义 CSV 解析器
func csvUnmarshaler(reader io.Reader, v interface{}) error {
    r := csv.NewReader(reader)
    records, err := r.ReadAll()
    if err != nil {
        return err
    }

    cfg := v.(*Config)
    for _, record := range records {
        cfg.Fields = append(cfg.Fields, record...)
    }
    return nil
}

// 自定义 CSV 序列化器
func csvMarshaler(writer io.Writer, v interface{}) error {
    w := csv.NewWriter(writer)
    cfg := v.(*Config)

    err := w.Write(cfg.Fields)
    if err != nil {
        return err
    }

    w.Flush()
    return w.Error()
}

func main() {
    // 注册自定义解析器
    config.RegisterParser(".csv", csvMarshaler, csvUnmarshaler)

    var cfg Config
    err := config.LoadConfigSkipValidate(&cfg, "config.csv")
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }

    log.Printf("Loaded fields: %v", cfg.Fields)
}
```

## 高级特性

### 标签优先级

在字段映射时，标签按以下优先级使用：

**Properties 格式**: `properties` > `env` > `json` > `yaml` > `toml` > `ini`

**HCL 格式**: `hcl` > `json` > `yaml` > `toml` > `ini`

**默认**: 使用小写字段名

```go
type Config struct {
    Field1 string `properties:"prop_name" json:"json_name" yaml:"yaml_name"`
    Field2 string `json:"json_name" yaml:"yaml_name"`
    Field3 string // 无标签，使用 "field3"
}
```

### 忽略字段

使用 `-` 标签值忽略字段：

```go
type Config struct {
    Name     string `json:"name"`
    Password string `json:"-"` // 不序列化此字段
    Internal string `json:"-"` // 不从配置文件读取
}
```

### 标签选项

支持标签选项（逗号分隔）：

```go
type Config struct {
    Field string `json:"field,omitempty"`
}
```

常用选项：
- `omitempty`: 字段为空时省略
- `inline`: 内联到父对象
- `-`: 忽略字段

## 错误处理

### 常见错误类型

1. **文件不存在**: 使用默认配置，不返回错误
2. **格式不支持**: 返回错误，提示不支持的格式
3. **解析失败**: 记录错误日志，继续执行
4. **验证失败**: 返回详细验证错误

### 错误处理示例

```go
var cfg Config

err := config.LoadConfig(&cfg, "config.json")
if err != nil {
    // 检查错误类型
    if strings.Contains(err.Error(), "required") {
        log.Fatal("Missing required field:", err)
    } else if strings.Contains(err.Error(), "unsupported config file format") {
        log.Fatal("Invalid config format:", err)
    } else {
        log.Fatal("Config error:", err)
    }
}
```

## 最佳实践

### 1. 配置文件组织

```go
type Config struct {
    Server   ServerConfig   `json:"server"`
    Database DatabaseConfig `json:"database"`
    Logging  LoggingConfig  `json:"logging"`
}

type ServerConfig struct {
    Host string `json:"host" env:"SERVER_HOST" validate:"required"`
    Port int    `json:"port" env:"SERVER_PORT" validate:"min=1,max=65535"`
}

type DatabaseConfig struct {
    Driver   string `json:"driver" env:"DB_DRIVER" validate:"required"`
    Host     string `json:"host" env:"DB_HOST" validate:"required"`
    Port     int    `json:"port" env:"DB_PORT" validate:"min=1,max=65535"`
    Database string `json:"database" env:"DB_NAME" validate:"required"`
    Username string `json:"username" env:"DB_USER" validate:"required"`
    Password string `json:"password" env:"DB_PASS" validate:"required"`
}

type LoggingConfig struct {
    Level  string `json:"level" env:"LOG_LEVEL" validate:"required,oneof=debug info warn error"`
    Format string `json:"format" env:"LOG_FORMAT" validate="required,oneof=json text"`
}
```

### 2. 环境特定配置

**config.dev.json** (开发环境):
```json
{
    "server": {
        "host": "localhost",
        "port": 8080
    },
    "database": {
        "driver": "sqlite",
        "host": "localhost",
        "port": 3306,
        "database": "dev.db",
        "username": "dev",
        "password": "dev"
    },
    "logging": {
        "level": "debug",
        "format": "text"
    }
}
```

**config.prod.json** (生产环境):
```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 80
    },
    "database": {
        "driver": "mysql",
        "host": "prod-db.internal",
        "port": 3306,
        "database": "production",
        "username": "prod_user",
        "password": "prod_password"
    },
    "logging": {
        "level": "info",
        "format": "json"
    }
}
```

**加载逻辑**:
```go
func LoadConfig(env string) (*Config, error) {
    var cfg Config

    // 根据环境选择配置文件
    configFile := fmt.Sprintf("config.%s.json", env)

    err := config.LoadConfig(&cfg, configFile)
    if err != nil {
        return nil, err
    }

    return &cfg, nil
}
```

### 3. 敏感信息处理

```go
type Config struct {
    // 普通配置
    Name string `json:"name" validate:"required"`

    // 敏感信息 - 优先使用环境变量
    APIKey     string `json:"api_key,omitempty" env:"API_KEY"`
    SecretKey  string `json:"secret_key,omitempty" env:"SECRET_KEY"`
    DatabaseURL string `json:"database_url,omitempty" env:"DATABASE_URL"`
}
```

**使用**:
```go
// 配置文件可以不包含敏感信息（或包含默认值）
// 实际值从环境变量读取
export API_KEY="sk_live_1234567890abcdef"
export SECRET_KEY="secret_key_here"
export DATABASE_URL="mysql://user:pass@localhost/db"
```

### 4. 配置热更新

```go
import (
    "os"
    "log"
    "github.com/fsnotify/fsnotify"
)

type ConfigManager struct {
    config *Config
    watcher *fsnotify.Watcher
}

func NewConfigManager(path string) (*ConfigManager, error) {
    watcher, err := fsnotify.NewWatcher()
    if err != nil {
        return nil, err
    }

    cm := &ConfigManager{
        watcher: watcher,
    }

    // 初始加载
    if err := cm.Reload(path); err != nil {
        watcher.Close()
        return nil, err
    }

    // 监控文件变化
    go cm.watch(path)

    return cm, nil
}

func (cm *ConfigManager) Reload(path string) error {
    var cfg Config
    if err := config.LoadConfig(&cfg, path); err != nil {
        return err
    }

    cm.config = &cfg
    log.Println("Config reloaded successfully")
    return nil
}

func (cm *ConfigManager) watch(path string) {
    dir := filepath.Dir(path)
    cm.watcher.Add(dir)

    for {
        select {
        case event, ok := <-cm.watcher.Events:
            if !ok {
                return
            }
            if event.Name == path && event.Op&fsnotify.Write == fsnotify.Write {
                if err := cm.Reload(path); err != nil {
                    log.Printf("Failed to reload config: %v", err)
                }
            }
        case err, ok := <-cm.watcher.Errors:
            if !ok {
                return
            }
            log.Printf("Watcher error: %v", err)
        }
    }
}

func (cm *ConfigManager) GetConfig() *Config {
    return cm.config
}

func (cm *ConfigManager) Close() {
    cm.watcher.Close()
}
```

## 性能考虑

### 1. 缓存配置

```go
var cachedConfig *Config
var configMutex sync.RWMutex

func GetConfig() *Config {
    configMutex.RLock()
    defer configMutex.RUnlock()
    return cachedConfig
}

func UpdateConfig(path string) error {
    var cfg Config
    if err := config.LoadConfig(&cfg, path); err != nil {
        return err
    }

    configMutex.Lock()
    cachedConfig = &cfg
    configMutex.Unlock()

    return nil
}
```

### 2. 延迟加载

```go
type AppConfig struct {
    // 常用配置 - 直接加载
    Name string `json:"name" validate:"required"`
    Port int    `json:"port" validate:"min=1,max=65535"`

    // 不常用配置 - 按需加载
    FeatureFlags map[string]bool `json:"feature_flags,omitempty"`
    Advanced     AdvancedConfig   `json:"advanced,omitempty"`
}
```

### 3. 配置验证优化

```go
// 生产环境使用 LoadConfigSkipValidate，手动验证关键字段
func LoadConfigProd(path string) (*Config, error) {
    var cfg Config
    if err := config.LoadConfigSkipValidate(&cfg, path); err != nil {
        return nil, err
    }

    // 只验证关键字段
    if cfg.Name == "" {
        return nil, errors.New("name is required")
    }
    if cfg.Port < 1 || cfg.Port > 65535 {
        return nil, errors.New("port must be between 1 and 65535")
    }

    return &cfg, nil
}
```

## 调试与日志

### 启用详细日志

config 模块使用 `lazygophers/log` 记录日志。

```go
import (
    "github.com/lazygophers/log"
)

// 设置日志级别
log.SetLogLevel(log.DebugLevel)

// 加载配置时会输出详细日志
config.LoadConfig(&cfg, "config.json")
```

### 日志输出示例

```
[WARN] Try to load config from environment variable(LAZYGOPHERS_CONFIG)
[DEBUG] config file not found:/path/to/config.json
[WARN] Try to load config from /current/directory
[INFO] Config file found, use config from /current/directory/config.json
[DEBUG] Environment variable 'APP_PORT' overrides port field
[INFO] load config success
```

## 依赖项

```go
require (
    github.com/go-playground/validator/v10   // 配置验证
    github.com/hashicorp/hcl/v2              // HCL 格式支持
    github.com/lazygophers/log               // 日志
    github.com/lazygophers/utils/json      // JSON 处理
    github.com/lazygophers/utils/osx         // 操作系统工具
    github.com/lazygophers/utils/runtime     // 运行时信息
    github.com/lazygophers/utils/validator   // 验证器
    github.com/pelletier/go-toml/v2          // TOML 格式
    github.com/yosuke-furukawa/json5         // JSON5 格式
    gopkg.in/ini.v1                          // INI 格式
    gopkg.in/yaml.v3                         // YAML 格式
)
```

## 常见问题

### Q1: 如何在配置文件中使用环境变量？

**A**: 使用 `env` 标签，config 会自动从系统环境变量读取并覆盖配置文件值。

### Q2: 配置文件找不到会发生什么？

**A**: config 不会返回错误，而是使用结构体的默认值（零值）。建议使用 `validate:"required"` 标签确保关键字段存在。

### Q3: 如何支持多种配置格式？

**A**: 同时添加多个格式的标签（`json`、`yaml`、`toml` 等），config 会根据文件扩展名自动选择正确的解析器。

### Q4: 环境变量类型转换失败怎么办？

**A**: 转换失败时保留配置文件值，并记录 Debug 级别日志。不会导致程序崩溃。

### Q5: 如何动态重新加载配置？

**A**: 使用文件监控（如 `fsnotify`）检测配置文件变化，然后调用 `LoadConfig` 重新加载。

### Q6: 配置文件路径如何指定？

**A**: 有三种方式：
1. 直接提供路径: `config.LoadConfig(&cfg, "/path/to/config.json")`
2. 环境变量: `export LAZYGOPHERS_CONFIG=/path/to/config.json`
3. 默认搜索: 在当前目录或程序目录查找 `conf.*` 或 `config.*`

### Q7: 如何忽略某些字段？

**A**: 使用 `-` 标签值：`Field string `json:"-"``

### Q8: 支持数组类型吗？

**A**: 支持，但仅限于内置格式（JSON、YAML、TOML 等）。Properties 和 ENV 格式不支持数组。

## 总结

`lazygophers/utils/config` 模块提供了一个功能完整、易于使用的配置管理解决方案：

**优势**:
- 支持 9 种主流配置格式
- 环境变量覆盖机制灵活
- 嵌套结构体支持完善
- 自动配置文件搜索
- 内置验证集成
- 可扩展的自定义解析器

**适用场景**:
- 微服务配置管理
- 多环境部署（开发/测试/生产）
- 容器化应用配置
- CI/CD 流程配置
- 复杂应用配置管理

**最佳实践**:
- 使用 `env` 标签处理敏感信息
- 使用 `validate` 标签确保配置正确性
- 合理组织配置结构（嵌套、分节）
- 为不同环境准备不同配置文件
- 实现配置热更新机制（生产环境）
