# 关联关系

## 一对一（Has One）

```go
type User struct {
    ID      uint
    Profile Profile `gorm:"foreignKey:UserID"`
}

type Profile struct {
    ID     uint
    UserID uint
    Bio    string
}

// 创建
db.Create(&User{
    Profile: Profile{Bio: "Software Developer"},
})

// 查询
var user User
db.Preload("Profile").First(&user, 1)

// 关联操作
db.Model(&user).Association("Profile").Append(&Profile{Bio: "New Bio"})
db.Model(&user).Association("Profile").Replace(&Profile{Bio: "Replaced Bio"})
db.Model(&user).Association("Profile").Delete(&Profile{})
```

## 一对多（Has Many）

```go
type User struct {
    ID    uint
    Posts []Post `gorm:"foreignKey:UserID"`
}

type Post struct {
    ID     uint
    UserID uint
    Title  string
}

// 创建
db.Create(&User{
    Posts: []Post{
        {Title: "First Post"},
        {Title: "Second Post"},
    },
})

// 查询
var user User
db.Preload("Posts").First(&user, 1)

// 关联操作
db.Model(&user).Association("Posts").Append(&Post{Title: "New Post"})
db.Model(&user).Association("Posts").Delete(&Post{})
```

## 多对多（Many To Many）

```go
type User struct {
    ID        uint
    Languages []Language `gorm:"many2many:user_languages;"`
}

type Language struct {
    ID   uint
    Name string
}

// 创建
db.Create(&User{
    Languages: []Language{
        {Name: "Go"},
        {Name: "Python"},
    },
})

// 查询
var user User
db.Preload("Languages").First(&user, 1)

// 关联操作
db.Model(&user).Association("Languages").Append(&Language{Name: "Rust"})
db.Model(&user).Association("Languages").Delete(&Language{})
db.Model(&user).Association("Languages").Replace([]Language{{Name: "Java"}})

// 查找关联
var languages []Language
db.Model(&user).Where("name = ?", "Go").Association("Languages").Find(&languages)

// 计数
db.Model(&user).Association("Languages").Count()
```

## 多态关联

```go
type Image struct {
    ID         uint
    URL        string
    ImageType  string
    ImageID    uint
}

type User struct {
    ID     uint
    Name   string
    Images []Image `gorm:"polymorphic:Image;"`
}

type Product struct {
    ID     uint
    Name   string
    Images []Image `gorm:"polymorphic:Image;"`
}

// 使用
db.Create(&User{
    Name: "John",
    Images: []Image{
        {URL: "avatar.jpg"},
    },
})
```

## 预加载（Eager Loading）

### 基础预加载

```go
// 预加载单个关联
db.Preload("Posts").Find(&users)

// 预加载多个关联
db.Preload("Posts").Preload("Profile").Find(&users)

// 条件预加载
db.Preload("Posts", "status = ?", "published").Find(&users)
```

### 嵌套预加载

```go
// 嵌套预加载
db.Preload("Posts.Comments").Find(&users)

// 多层嵌套
db.Preload("Posts.Comments.Author").Find(&users)

// 带条件
db.Preload("Posts.Comments", "approved = ?", true).Find(&users)
```

### Joins 预加载

```go
// 使用 JOIN 预加载（减少查询次数）
db.Joins("Profile").Find(&users)

// 带条件
db.Joins("Profile").Where("Profile.bio LIKE ?", "%developer%").Find(&users)
```

## 关联模式

```go
var user User
db.First(&user, 1)

// 查找关联
var posts []Post
db.Model(&user).Association("Posts").Find(&posts)

// 添加关联
db.Model(&user).Association("Posts").Append(&Post{Title: "New Post"})

// 替换关联
db.Model(&user).Association("Posts").Replace([]Post{{Title: "Post 1"}})

// 删除关联
db.Model(&user).Association("Posts").Delete(&Post{})

// 清空关联
db.Model(&user).Association("Posts").Clear()

// 计数
count := db.Model(&user).Association("Posts").Count()
```

## 外键约束

```go
type User struct {
    ID    uint
    Posts []Post `gorm:"constraint:OnDelete:CASCADE;"`
}

type Post struct {
    ID     uint
    UserID uint
    Title  string
}

// 约束选项
// OnDelete: CASCADE, SET NULL, SET DEFAULT, RESTRICT, NO ACTION
// OnUpdate: CASCADE, SET NULL, SET DEFAULT, RESTRICT, NO ACTION
```

## 默认关联

```go
type User struct {
    gorm.Model
    Name      string
    CompanyID uint
    Company   Company `gorm:"default:null"`
}

type Company struct {
    ID   uint
    Name string
}
```
