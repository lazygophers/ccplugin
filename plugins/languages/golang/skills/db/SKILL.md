---
name: golang-db
description: Go 数据库规范——GORM Model 命名 ModelXxx、表名单数、枚举 uint8 + 常量、索引 idx_ 前缀 + deleted_at leading column、禁 time.Time 统一 int64 unix、禁指针/nullable 字段、TEXT/BLOB/JSON 禁 default、AutoMigrate 禁改主键。设计 DB model、写 GORM tag、建索引、做 migration 审查时触发。
---

# Go 数据库规范

## 六条铁律

1. **Model 命名 `ModelXxx`**，表名单数，如 `user`、`order`，非 `users`。
2. **枚举字段 `uint8`** + 常量分组，禁裸 magic number。
3. **索引必须 `idx_` 前缀**（含唯一），复合索引带 `deleted_at`。
4. **禁 `time.Time`**，时间统一 `int64` unix 秒。
5. **禁指针/nullable 字段**，零值=不传，全 `omitempty`。
6. **TEXT/BLOB/JSON 禁 `default` tag**，MySQL 不支持。

## Model 定义模板

```go
type ModelUser struct {
    Id        uint64 `gorm:"primaryKey" json:"id"`
    Username  string `gorm:"type:varchar(64);uniqueIndex:idx_username,where:deleted_at=0" json:"username"`
    State     uint8  `gorm:"type:tinyint unsigned;default:0" json:"state"`
    CreatedAt int64  `gorm:"autoCreateTime" json:"created_at"`
    UpdatedAt int64  `gorm:"autoUpdateTime" json:"updated_at"`
    DeletedAt int64  `gorm:"index" json:"deleted_at"`
}
```

### 字段顺序

1. 主键 `Id`
2. 业务唯一键（username/email 等）
3. 业务字段
4. 状态/枚举
5. 时间戳（CreatedAt/UpdatedAt/DeletedAt）

## 枚举字段

```go
type ModelUser struct {
    // ...
    State uint8 `gorm:"type:tinyint unsigned;default:0" json:"state"`
}

const (
    UserStateNil      uint8 = 0
    UserStateActive   uint8 = 1
    UserStateDisabled uint8 = 2
)

// 判断用常量，禁裸数字
if user.State == UserStateActive { ... }
```

## 索引规范

```go
// 唯一索引（带 deleted_at）
Username string `gorm:"uniqueIndex:idx_username,where:deleted_at=0"`

// 复合索引（deleted_at 作为 leading column priority:1）
Username  string `gorm:"index:idx_username_deleted,priority:2,where:deleted_at=0"`
DeletedAt int64  `gorm:"index:idx_username_deleted,priority:1"`

// 普通索引
State uint8 `gorm:"index:idx_state"`
```

规则：
- 所有索引必须 `idx_` 前缀命名
- 唯一索引也要命名，禁裸 `uniqueIndex` 无名
- 软删场景，唯一/复合索引必须包含 `deleted_at`
- 复合索引 `deleted_at` 作 leading column（priority:1）

## 时间字段

```go
CreatedAt int64 `gorm:"autoCreateTime" json:"created_at"`
UpdatedAt int64 `gorm:"autoUpdateTime" json:"updated_at"`
DeletedAt int64 `gorm:"index" json:"deleted_at"` // 软删，0=未删
```

禁 `time.Time`、禁 `*time.Time`、禁 `gorm.Model`。统一 int64 unix 秒。

## Struct tag 规范

```go
type ModelOrder struct {
    Id       uint64 `gorm:"primaryKey" json:"id"`
    Name     string `gorm:"type:varchar(128)" json:"name,omitempty"`
    Amount   int64  `gorm:"type:bigint" json:"amount,omitempty"`
    Settings string `gorm:"type:json" json:"settings,omitempty"`
    State    uint8  `gorm:"type:tinyint unsigned;default:0" json:"state"`
    CreatedAt int64 `gorm:"autoCreateTime" json:"created_at"`
    UpdatedAt int64 `gorm:"autoUpdateTime" json:"updated_at"`
    DeletedAt int64 `gorm:"index" json:"deleted_at"`
}
```

- 全字段 `json` tag，snake_case
- 业务字段加 `omitempty`
- 状态/时间字段不加 `omitempty`（零值有意义）
- `gorm:"type:xxx"` 显式声明列类型

## 禁止项

| 模式 | 替代 |
| --- | --- |
| `time.Time` / `*time.Time` | `int64` unix 秒 |
| `*string` / `*int64` 指针字段 | 零值表示不传 + omitempty |
| `gorm:"default:'xxx'"` on TEXT/BLOB/JSON | 移除 default tag |
| 裸 `uniqueIndex` 无名 | `uniqueIndex:idx_xxx` |
| 裸数字判断 `if state == 1` | 常量 `UserStateActive` |
| `gorm.Model` 嵌入 | 显式定义字段 |

## Migration 注意

- AutoMigrate 不能改主键，PK 变更需手动 `DROP` + `ALTER`
- 破坏性变更（删列/改类型）不写自动迁移，手动 SQL
- 禁 legacy migration / 兼容代码，不写 `preMigrateLegacy` 类函数

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "time.Time 更标准" | 全部 int64 unix？ |
| "指针区分零值和缺失" | omitempty + 零值=不传？ |
| "索引名无所谓" | 全 idx_ 前缀？ |
| "gorm.Model 方便" | 显式定义字段？ |
| "magic number 看得懂" | 全用常量？ |
| "TEXT 加 default 更安全" | MySQL 不支持？ |

## 检查清单

- [ ] Model 命名 `ModelXxx`
- [ ] 表名单数
- [ ] 枚举 `uint8` + 常量
- [ ] 索引全 `idx_` 前缀
- [ ] 唯一/复合索引带 `deleted_at`
- [ ] 时间字段全 `int64`
- [ ] 无指针字段
- [ ] TEXT/BLOB/JSON 无 `default`
- [ ] 显式定义字段，无 `gorm.Model`
- [ ] json tag snake_case + omitempty
