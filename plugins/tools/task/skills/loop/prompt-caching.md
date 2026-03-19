# Loop Prompt Caching 使用指南

<overview>

Prompt Caching 是 Claude API 的特性，可将静态提示词内容缓存起来，减少重复处理，实现 **90% 成本节省**和 **85% 延迟降低**。loop 技能已通过文档结构优化为缓存友好设计。

</overview>

<principles>

## 核心原理

### 缓存机制

Claude API 的 Prompt Caching 将提示词分为可缓存段和动态段：
- **可缓存段**：静态内容（系统提示、工具定义、参考文档），100% 相同时命中缓存
- **动态段**：用户输入、迭代状态等变化内容，每次重新处理

### 成本结构（Claude Sonnet 4.6）

| 操作 | 成本倍数 | 说明 |
|------|---------|------|
| **写入缓存** | 1.25x | 首次缓存内容，略高于基准 |
| **缓存命中** | 0.1x | 读取已缓存内容，节省 90% |
| **未缓存** | 1.0x | 正常处理，基准成本 |

### 最小 Token 要求

| 模型 | 最小缓存块大小 |
|------|---------------|
| Claude Haiku 4.5 | **4096 tokens** |
| Claude Sonnet 4.6 | 1024 tokens |
| Claude Opus 4.6 | 1024 tokens |

### TTL (Time To Live)

- **标准 TTL**：5 分钟
- **扩展 TTL**：1 小时（2026年2月5日新增）

</principles>

<implementation>

## loop 技能的缓存友好设计

### 静态内容标记

loop/SKILL.md 已标记静态内容区域（4800+ tokens）：

```markdown
<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# MindFlow - 迭代式任务编排引擎

<overview>
...核心概念...
</overview>

<execution>
...执行流程...
</execution>

<references>
...子技能与文档...
</references>

<quick_reference>
...快速参考...
</quick_reference>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->
用户任务：$ARGUMENTS
...
<!-- /DYNAMIC_CONTENT -->
```

### planner 技能的缓存友好设计

planner/SKILL.md 已标记静态内容区域（6000+ tokens）：

```markdown
<!-- STATIC_CONTENT: Cacheable (6000+ tokens) -->

# Skills(task:planner) - 计划设计规范

<scope>...</scope>
<core_principles>...</core_principles>
<invocation>...</invocation>
<output_format>...</output_format>
<mermaid_generation_rules>...</mermaid_generation_rules>
<field_reference>...</field_reference>
<references>...</references>
<guidelines>...</guidelines>

<!-- /STATIC_CONTENT -->
```

</implementation>

<best_practices>

## 最佳实践

### 1. 保持静态内容稳定

**✅ 正确做法**：
- 静态内容（overview、execution、references）保持不变
- 只修改动态部分（$ARGUMENTS、用户输入）
- 避免在静态区域添加时间戳、随机数

**❌ 错误做法**：
```python
# 破坏缓存：在静态区域添加时间戳
system_prompt = f"""
当前时间：{datetime.now()}  # ❌ 每次不同，缓存失效
{static_content}
"""
```

### 2. 达到最小 Token 要求

确保缓存块 ≥ 4096 tokens（Haiku）或 1024 tokens（Sonnet/Opus）：

```python
def estimate_tokens(text):
    """粗略估算 tokens（1 token ≈ 4 bytes）"""
    return len(text.encode('utf-8')) // 4

# 检查是否达到最小要求
static_content = read_static_content("loop/SKILL.md")
token_count = estimate_tokens(static_content)

if token_count < 4096:
    print(f"警告：静态内容仅 {token_count} tokens，建议 ≥ 4096")
```

### 3. 避免缓存破坏行为

**破坏缓存的常见操作**：
- 添加/删除 MCP 工具（工具定义变化）
- 修改模型配置（如切换 Sonnet → Opus）
- 更新静态内容中的任何字符（包括空格、换行）
- 在系统提示中嵌入动态变量

**示例：正确分离动态内容**

```python
# ✅ 正确：静态和动态分离
def build_prompt(user_task, iteration):
    static_part = load_static_content("loop/SKILL.md")  # 可缓存
    dynamic_part = f"""
用户任务：{user_task}
迭代编号：{iteration}
    """

    return {
        "system": static_part,      # 缓存命中
        "user": dynamic_part          # 每次不同
    }

# ❌ 错误：混合静态和动态
def build_prompt_wrong(user_task, iteration):
    return f"""
{load_static_content("loop/SKILL.md")}

用户任务：{user_task}  # ❌ 整个prompt变成动态的
迭代编号：{iteration}
    """
```

### 4. 监控缓存命中率

```python
# 伪代码：监控缓存效果
def track_caching_metrics(api_response):
    usage = api_response.get("usage", {})

    cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
    cache_read_tokens = usage.get("cache_read_input_tokens", 0)
    input_tokens = usage.get("input_tokens", 0)

    if cache_read_tokens > 0:
        hit_rate = cache_read_tokens / (cache_read_tokens + input_tokens)
        print(f"缓存命中率：{hit_rate:.1%}")
        print(f"节省 tokens：{cache_read_tokens * 0.9:.0f}")

    if cache_creation_tokens > 0:
        print(f"写入缓存：{cache_creation_tokens} tokens")
```

</best_practices>

<examples>

## 使用示例

### 示例 1：loop 调用 planner

```python
iteration = 1

# 静态内容（缓存）
static_planner_context = """
<!-- STATIC_CONTENT -->
{load_file("planner/SKILL.md")}
<!-- /STATIC_CONTENT -->
"""

# 动态内容（每次不同）
dynamic_task = f"""
任务目标：{user_task}
迭代编号：{iteration}
"""

# API 调用（伪代码）
response = claude_api.call(
    model="claude-sonnet-4-6",
    system=static_planner_context,  # 缓存命中（90% 节省）
    user=dynamic_task,               # 正常处理
    cache_control={"type": "ephemeral"}  # 启用缓存
)
```

### 示例 2：检查缓存失效

```python
import hashlib

def check_cache_stability(file_path):
    """检查静态内容是否稳定（通过哈希）"""
    with open(file_path, 'r') as f:
        content = f.read()

    # 提取静态内容
    static_content = extract_between_markers(
        content,
        "<!-- STATIC_CONTENT -->",
        "<!-- /STATIC_CONTENT -->"
    )

    # 计算哈希
    content_hash = hashlib.sha256(static_content.encode()).hexdigest()

    # 与上次对比
    last_hash = load_last_hash(file_path)
    if content_hash != last_hash:
        print(f"警告：{file_path} 静态内容已变化，缓存将失效")
        save_hash(file_path, content_hash)
    else:
        print(f"✓ {file_path} 静态内容稳定，缓存有效")
```

</examples>

<expected_benefits>

## 预期效益

### 成本节省（假设 1000 次/月调用）

| 场景 | Input Tokens | 成本（无缓存） | 成本（有缓存） | 节省 |
|------|-------------|--------------|--------------|------|
| loop 调用 | 6000 | $18 | $2.7 | **$15.3 (85%)** |
| planner 调用 | 8000 | $24 | $3.6 | **$20.4 (85%)** |
| **月度合计** | - | **$42** | **$6.3** | **$35.7 (85%)** |

### 延迟降低

- **首次调用**：正常延迟（写入缓存，略慢 +5%）
- **后续调用**：延迟降低 **85%**（读取缓存）

### 适用场景

**最适合缓存的场景**：
- ✅ 同一用户连续多次调用
- ✅ 静态提示词很大（>4096 tokens）
- ✅ 5分钟内重复调用
- ✅ 系统提示词保持稳定

**不适合缓存的场景**：
- ❌ 静态内容频繁变化
- ❌ 提示词很小（<1024 tokens）
- ❌ 调用间隔 >5分钟（TTL过期）
- ❌ 每次调用都修改工具定义

</expected_benefits>

<references>

## 参考资料

- [Prompt caching - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Prompt Caching Works in Claude Code](https://www.claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code)
- [Prompt Caching Guide 2026](https://www.aifreeapi.com/en/posts/claude-api-prompt-caching-guide)

</references>

<notes>

## 注意事项

1. **当前实现限制**：Claude Code 的 skills 框架可能不直接支持 cache_control API，需要底层支持
2. **文档结构优化**：当前通过标记静态/动态内容区域，为未来缓存实现做准备
3. **间接效益**：即使未启用真实缓存，清晰的静态/动态分离也有助于提升可维护性
4. **版本要求**：Prompt Caching 需要 Claude API 2024-07-15 或更高版本

</notes>
