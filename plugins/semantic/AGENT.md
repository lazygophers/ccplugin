### 代码语义搜索插件

**使用 `semantic` 插件进行代码语义搜索**

当需要使用自然语言查询代码时，使用 `semantic` 插件。其主要功能包括：

- **语义搜索** - 使用自然语言描述查找相关代码
- **代码索引** - 建立代码的向量嵌入索引（支持增量更新）
- **多语言支持** - 支持 17+ 编程语言，针对不同语言优化
- **混合检索** - FastEmbed + CodeModel + Symbol 三引擎融合
- **语言特定优化** - 针对不同语言的解析策略、分块大小、模型推荐

## 使用方式

```bash
# 语义搜索（主要功能）
/semantic-search "如何读取文件"
```

其他管理功能通过 `semantic.py` 脚本使用。

完整的 **skills** 信息位于 `${CLAUDE_PLUGIN_ROOT}/skills/semantic-search/SKILL.md` 文件中。
