---
name: web
description: Python Web 开发规范：FastAPI、Pydantic、依赖注入。开发 Web 应用时必须加载。
---

# Python Web 开发规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | PEP 8、命名规范 |
| 异步编程 | Skills(async) | asyncio、并发模式 |

## FastAPI 基本用法

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

@app.post("/users", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return await UserService(db).create(user)

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = await UserService(db).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 依赖注入

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_db(settings: Settings = Depends(get_settings)):
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 项目结构

```
app/
├── main.py
├── config.py
├── models/
├── schemas/
├── services/
├── routers/
└── dependencies.py
```

## 检查清单

- [ ] 使用 Pydantic 模型
- [ ] 使用依赖注入
- [ ] 使用 response_model
- [ ] 正确处理 HTTP 异常
