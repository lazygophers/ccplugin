---
name: testing
description: Python 测试规范：pytest、测试组织、覆盖率。写测试时必须加载。
---

# Python 测试规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | PEP 8、命名规范 |

## pytest 基本用法

```python
import pytest

def test_user_creation():
    user = User(name="test", email="test@example.com")
    assert user.name == "test"
    assert user.email == "test@example.com"

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

## Fixtures

```python
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.close()

@pytest.fixture
def user(db_session):
    user = User(name="test")
    db_session.add(user)
    db_session.commit()
    return user

def test_user_exists(db_session, user):
    found = db_session.query(User).filter_by(id=user.id).first()
    assert found is not None
```

## 测试组织

```
tests/
├── conftest.py
├── unit/
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   └── test_api.py
└── e2e/
    └── test_flows.py
```

## 覆盖率

```bash
pytest --cov=src --cov-report=html
```

## 检查清单

- [ ] 测试文件以 test_ 开头
- [ ] 测试函数以 test_ 开头
- [ ] 使用 pytest.fixture
- [ ] 覆盖率 >80%
