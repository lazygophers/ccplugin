# Python 数据处理规范

## 核心原则

### ✅ 必须遵守

1. **类型优先** - 使用 Pydantic 确保数据类型安全
2. **惰性求值** - 大数据集使用链式操作，避免中间副本
3. **内存控制** - 使用 chunking 处理大数据
4. **原地操作** - 优先使用 `inplace=True` 减少内存
5. **明确类型** - DataFrame 列必须指定类型
6. **避免循环** - 使用向量化操作而非 Python 循环

### ❌ 禁止行为

- 在 DataFrame 上使用 Python `for` 循环遍历行
- 使用 `pd.append`（已废弃），使用 `pd.concat`
- 忽略 `SettingWithCopyWarning`
- 使用 `object` 类型存储数值
- 一次性加载整个大文件到内存
- 链式赋值：`df[df['a'] > 0]['b'] = 1`

## Pandas 使用规范

### 类型安全

```python
# ✅ 正确 - 使用 Pydantic 定义数据模式
from pydantic import BaseModel, Field, field_validator
from typing import Literal

import pandas as pd
import pandas.api.types as ptypes


class UserDataRow(BaseModel):
    """用户数据行模式."""

    user_id: int = Field(..., ge=1)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    age: int = Field(..., ge=0, le=150)
    status: Literal["active", "inactive", "pending"]
    score: float | None = Field(None, ge=0.0, le=100.0)
    created_at: str  # ISO 格式日期时间

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: str) -> str:
        """验证邮箱格式."""
        if "@" not in v:
            raise ValueError("must contain '@'")
        return v.lower()


# 验证 DataFrame
def validate_dataframe(df: pd.DataFrame, model: type[BaseModel]) -> pd.DataFrame:
    """使用 Pydantic 验证 DataFrame."""
    errors = []

    for idx, row in df.iterrows():
        try:
            model(**row.to_dict())
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    if errors:
        raise ValueError(f"DataFrame validation failed: {errors[:5]}")

    return df


# ✅ 正确 - 指定 DataFrame 列类型
def create_typed_dataframe() -> pd.DataFrame:
    """创建类型安全的 DataFrame."""
    df = pd.DataFrame({
        "user_id": pd.Series([1, 2, 3], dtype="int64"),
        "email": pd.Series(["a@b.com", "c@d.com", "e@f.com"], dtype="string"),
        "age": pd.Series([25, 30, 35], dtype="int8"),
        "score": pd.Series([85.5, 90.0, None], dtype="float32"),
        "is_active": pd.Series([True, False, True], dtype="bool"),
        "created_at": pd.Series([
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ], dtype="datetime64[ns]"),
    })

    return df


# ✅ 正确 - 类型转换
def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """转换 DataFrame 为最佳类型."""
    # pandas 2.0+ 使用 convert_dtypes
    df = df.convert_dtypes()

    # 手动指定类型
    df = df.astype({
        "user_id": "int64",
        "email": "string",
        "age": "int8",
        "score": "float32",
        "is_active": "bool",
    })

    return df
```

### 避免 SettingWithCopyWarning

```python
# ❌ 错误 - 链式索引触发警告
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df_filtered = df[df["a"] > 1]
df_filtered["b"] = 10  # SettingWithCopyWarning!

# ✅ 正确 - 使用 .loc
df.loc[df["a"] > 1, "b"] = 10

# ✅ 正确 - 使用 .copy()
df_filtered = df[df["a"] > 1].copy()
df_filtered["b"] = 10

# ✅ 正确 - 使用 assign
df = df.assign(b=df["b"].where(df["a"] <= 1, 10))
```

### 向量化操作

```python
# ❌ 错误 - 使用 Python 循环
df = pd.DataFrame({"a": range(10000), "b": range(10000)})

# 慢！
for idx, row in df.iterrows():
    df.loc[idx, "c"] = row["a"] + row["b"]

# ✅ 正确 - 向量化操作
df["c"] = df["a"] + df["b"]

# ✅ 正确 - 使用 apply（谨慎使用）
df["c"] = df.apply(lambda row: row["a"] + row["b"], axis=1)  # 慢于向量化

# ✅ 正确 - 使用向量化字符串操作
df["name_upper"] = df["name"].str.upper()
df["email_domain"] = df["email"].str.split("@").str[1]

# ✅ 正确 - 使用 np.where
import numpy as np

df["category"] = np.where(df["score"] >= 60, "pass", "fail")

# ✅ 正确 - 使用 np.select
conditions = [
    df["score"] >= 90,
    df["score"] >= 80,
    df["score"] >= 70,
    df["score"] >= 60,
]
choices = ["A", "B", "C", "D"]
df["grade"] = np.select(conditions, choices, default="F")
```

### 链式操作

```python
# ✅ 正确 - 使用链式操作
result = (
    df[df["age"] >= 18]
    .groupby("department")
    .agg(
        avg_salary=("salary", "mean"),
        max_salary=("salary", "max"),
        count=("employee_id", "count"),
    )
    .sort_values("avg_salary", ascending=False)
    .reset_index()
)

# ✅ 正确 - 使用 query 方法
result = df.query("age >= 18 and salary > 50000").groupby("department").size()

# ✅ 正确 - 使用 pipe 传递参数
def add_columns(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """添加列."""
    for col, value in kwargs.items():
        df[col] = value
    return df


result = df.pipe(add_columns, total=100, status="active")
```

## 大数据处理

### 分块读取

```python
# ✅ 正确 - 分块读取大文件
def process_large_csv(
    filepath: str,
    chunk_size: int = 10000,
) -> pd.DataFrame:
    """分块处理大 CSV 文件."""
    results = []

    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        # 处理每个 chunk
        processed = process_chunk(chunk)
        results.append(processed)

    # 合并结果
    return pd.concat(results, ignore_index=True)


# ✅ 正确 - 分块聚合
def aggregate_large_csv(
    filepath: str,
    chunk_size: int = 10000,
) -> pd.DataFrame:
    """对大文件进行聚合."""
    aggregations = []

    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        # 对每个 chunk 进行聚合
        agg = chunk.groupby("category").agg({
            "value": "sum",
            "count": "count",
        })
        aggregations.append(agg)

    # 合并后再次聚合
    combined = pd.concat(aggregations)
    return combined.groupby(level=0).sum()


# ✅ 正确 - 流式处理（不存储所有数据）
def stream_process_csv(
    filepath: str,
    output_path: str,
    chunk_size: int = 10000,
) -> None:
    """流式处理 CSV，避免内存溢出."""
    first_chunk = True

    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        processed = process_chunk(chunk)

        # 追加模式写入
        processed.to_csv(
            output_path,
            mode="a",
            header=first_chunk,
            index=False,
        )
        first_chunk = False
```

### 内存优化

```python
# ✅ 正确 - 使用适当的数据类型
def optimize_memory(df: pd.DataFrame) -> pd.DataFrame:
    """优化 DataFrame 内存使用."""
    memory_before = df.memory_usage(deep=True).sum() / 1024**2

    # 转换数值类型
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")

    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    # 转换字符串类型
    for col in df.select_dtypes(include=["object"]).columns:
        if df[col].nunique() / len(df[col]) < 0.5:  # 低基数
            df[col] = df[col].astype("category")

    memory_after = df.memory_usage(deep=True).sum() / 1024**2
    print(f"Memory: {memory_before:.2f}MB -> {memory_after:.2f}MB")

    return df


# ✅ 正确 - 使用分类类型减少内存
def use_categorical(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """将指定列转换为分类类型."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


# ✅ 正确 - 稀疏数据类型
def use_sparse(df: pd.DataFrame) -> pd.DataFrame:
    """对稀疏数据使用稀疏类型."""
    for col in df.columns:
        # 如果 90% 以上是 NaN 或 0
        if df[col].isna().mean() > 0.9 or (df[col] == 0).mean() > 0.9:
            df[col] = df[col].astype(pd.SparseDtype("float", fill_value=0))
    return df


# ✅ 正确 - 原地操作
def inplace_operations(df: pd.DataFrame) -> pd.DataFrame:
    """使用原地操作减少内存."""
    # 排序
    df.sort_values("date", inplace=True)

    # 删除列
    df.drop(columns=["temp1", "temp2"], inplace=True)

    # 重命名
    df.rename(columns={"old_name": "new_name"}, inplace=True)

    return df
```

### 迭代器模式

```python
# ✅ 正确 - 使用迭代器处理多文件
from pathlib import Path


def process_multiple_files(directory: Path) -> pd.DataFrame:
    """处理目录中的多个文件."""
    file_paths = Path(directory).glob("*.csv")

    # 使用生成器表达式
    dataframes = (
        pd.read_csv(fp)
        for fp in file_paths
    )

    # 使用 concat 一次性合并
    return pd.concat(dataframes, ignore_index=True)


# ✅ 正确 - 分块写入
def write_large_csv(df: pd.DataFrame, output_path: str, chunk_size: int = 10000) -> None:
    """分块写入大 CSV 文件."""
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    with open(output_path, "w") as f:
        # 写入第一块（带表头）
        chunks[0].to_csv(f, index=False)

        # 写入剩余块（不带表头）
        for chunk in chunks[1:]:
            chunk.to_csv(f, mode="a", header=False, index=False)
```

## NumPy 最佳实践

### 基础操作

```python
import numpy as np


# ✅ 正确 - 预分配数组
def preallocate_arrays(n: int) -> None:
    """预分配数组."""
    # 明确类型
    arr = np.zeros(n, dtype=np.float64)
    arr = np.ones(n, dtype=np.int32)
    arr = np.empty(n, dtype=np.complex128)

    # 多维数组
    matrix = np.zeros((n, n), dtype=np.float32)


# ✅ 正确 - 向量化操作
def vectorized_operations(arr: np.ndarray) -> np.ndarray:
    """向量化操作."""
    # 逐元素操作
    result = np.sqrt(arr)
    result = np.log(arr + 1)
    result = np.where(arr > 0, arr, 0)  # ReLU

    # 矩阵运算
    matrix1 = np.random.rand(100, 100)
    matrix2 = np.random.rand(100, 100)
    result = np.matmul(matrix1, matrix2)  # 或 matrix1 @ matrix2

    return result


# ❌ 错误 - 在 NumPy 数组上使用 Python 循环
arr = np.random.rand(1000000)

# 慢！
result = [x ** 2 for x in arr]

# ✅ 正确 - 向量化
result = arr ** 2
```

### 广播机制

```python
# ✅ 正确 - 利用广播
def broadcast_operations() -> None:
    """广播操作."""
    # 标量与数组
    arr = np.array([1, 2, 3])
    result = arr * 10  # [10, 20, 30]

    # 不同形状的数组
    matrix = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
    vec = np.array([10, 20, 30])  # (3,)
    result = matrix + vec  # (2, 3)

    # 使用 newaxis 调整维度
    vec = np.array([1, 2])  # (2,)
    matrix = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
    result = matrix + vec[:, np.newaxis]  # (2, 3)


# ✅ 正确 - 外积操作
def outer_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """计算外积."""
    return a[:, np.newaxis] * b[np.newaxis, :]
```

### 内存视图

```python
# ✅ 正确 - 使用视图避免复制
def view_vs_copy(arr: np.ndarray) -> None:
    """视图 vs 副本."""
    # reshape 创建视图（不复制数据）
    arr = np.arange(100)
    matrix = arr.reshape(10, 10)  # 视图

    # 切片创建视图
    submatrix = matrix[1:3, 1:3]  # 视图
    submatrix[:] = 0  # 修改会影响原数组

    # 使用 copy 创建副本
    arr_copy = arr.copy()
    submatrix = matrix[1:3, 1:3].copy()  # 副本
    submatrix[:] = 0  # 修改不影响原数组


# ✅ 正确 - 转置操作
def transpose_operations(matrix: np.ndarray) -> np.ndarray:
    """转置操作."""
    # 转置创建视图
    transposed = matrix.T  # 或 matrix.transpose()

    # 交换轴
    swapped = matrix.swapaxes(0, 1)

    return transposed
```

### 高级索引

```python
# ✅ 正确 - 布尔索引
def boolean_indexing(arr: np.ndarray) -> np.ndarray:
    """布尔索引."""
    # 条件筛选
    result = arr[arr > 0]  # 所有正数
    result = arr[(arr > 0) & (arr < 1)]  # 0 < x < 1
    result = arr[np.isin(arr, [1, 2, 3])]  # 在 [1,2,3] 中

    return result


# ✅ 正确 - 花式索引
def fancy_indexing(arr: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """花式索引."""
    # 使用整数数组索引
    result = arr[indices]

    # 多维索引
    result = arr[[0, 2, 4], [1, 3, 5]]

    return result
```

## 数据验证

### Schema 验证

```python
# ✅ 正确 - 使用 pandera 验证
import pandera as pa
from pandera.typing import DataFrame, Series


class UserSchema(pa.DataFrameModel):
    """用户数据 Schema."""

    user_id: Series[int] = pa.Field(ge=1)
    email: Series[str] = pa.Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    age: Series[int] = pa.Field(ge=0, le=150)
    score: Series[float] = pa.Field(ge=0, le=100, nullable=True)
    status: Series[str] = pa.Field(isin=["active", "inactive", "pending"])

    class Config:
        strict = True  # 不允许额外列
        coerce = True  # 自动类型转换


@pa.check_types
def process_users(df: DataFrame[UserSchema]) -> DataFrame[UserSchema]:
    """处理用户数据（自动验证）."""
    return df[df["status"] == "active"]


# 或者手动验证
def validate_with_pandera(df: pd.DataFrame) -> pd.DataFrame:
    """使用 pandera 验证."""
    try:
        UserSchema.validate(df, lazy=True)
        return df
    except pa.errors.SchemaErrors as e:
        print(f"Validation failed: {e}")
        raise
```

### 数据质量检查

```python
# ✅ 正确 - 数据质量检查函数
def check_data_quality(df: pd.DataFrame) -> dict:
    """检查数据质量."""
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": df.duplicated().sum(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
    }

    # 检查数值列的范围
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        report["numeric_ranges"] = {}
        for col in numeric_cols:
            report["numeric_ranges"][col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
            }

    # 检查分类列的基数
    categorical_cols = df.select_dtypes(include=["category", "object"]).columns
    if len(categorical_cols) > 0:
        report["cardinality"] = {}
        for col in categorical_cols:
            report["cardinality"][col] = int(df[col].nunique())

    return report


# ✅ 正确 - 清理数据
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清理数据."""
    # 删除重复行
    df = df.drop_duplicates()

    # 处理缺失值
    for col in df.columns:
        if df[col].dtype in ["float64", "int64"]:
            df[col].fillna(df[col].median(), inplace=True)
        else:
            df[col].fillna("unknown", inplace=True)

    # 删除全为 NaN 的列
    df = df.dropna(axis=1, how="all")

    # 删除全为 NaN 的行
    df = df.dropna(axis=0, how="all")

    return df
```

## 性能优化技巧

### 使用 eval 加速表达式

```python
# ✅ 正确 - 使用 eval 加速复杂表达式
def fast_eval_expression(df: pd.DataFrame) -> pd.DataFrame:
    """使用 eval 加速."""
    # 复杂表达式
    df.eval("total = price * quantity", inplace=True)
    df.eval("discounted = price * (1 - discount_rate)", inplace=True)

    # 多个表达式
    df.eval(
        """
        total = price * quantity
        tax = total * 0.1
        final = total + tax
        """,
        inplace=True,
    )

    return df


# ✅ 正确 - 使用 query 代替布尔索引
def fast_query(df: pd.DataFrame) -> pd.DataFrame:
    """使用 query 加速."""
    # 慢
    result = df[(df["age"] > 18) & (df["status"] == "active")]

    # 快
    result = df.query("age > 18 and status == 'active'")

    return result
```

### 分类操作优化

```python
# ✅ 正确 - 分类操作优化
def optimize_categorical_operations(df: pd.DataFrame) -> pd.DataFrame:
    """优化分类操作."""
    # 转换为分类
    df["category"] = df["category"].astype("category")

    # 使用 cat accessor
    categories = df["category"].cat.categories
    codes = df["category"].cat.codes

    # 重命名分类
    df["category"] = df["category"].cat.rename_categories({
        "A": "Alpha",
        "B": "Beta",
        "C": "Gamma",
    })

    return df
```

## 检查清单

提交数据处理代码前，确保：

- [ ] DataFrame 列有明确的数据类型
- [ ] 没有使用 Python 循环遍历 DataFrame 行
- [ ] 大文件使用 chunksize 分块处理
- [ ] 使用向量化操作而非逐元素操作
- [ ] 没有 SettingWithCopyWarning
- [ ] 数值列使用最小的数据类型（int8, float32 等）
- [ ] 低基数字符串列使用 category 类型
- [ ] 使用 Pydantic 或 pandera 验证数据
- [ ] 操作使用 inplace=True 减少内存
- [ ] 复杂表达式使用 eval/query 优化
