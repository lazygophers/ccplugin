# 安全漏洞记录

本文档记录ccplugin项目中发现的安全漏洞和跟踪状态。

## 活跃漏洞

### protobuf JSON递归深度绕过漏洞 (DoS)

**漏洞ID**: 待分配CVE
**发现日期**: 2025-01-27
**严重程度**: 中等 (CVSS待评估)
**漏洞类型**: 拒绝服务 (DoS)
**受影响包**: protobuf (pip)
**受影响版本**: <= 6.33.4

#### 漏洞描述

`google.protobuf.json_format.ParseDict()` 中存在一个递归深度限制绕过漏洞。当解析嵌套的 `google.protobuf.Any` 消息时，由于缺少内部Any处理逻辑中的递归深度计数，攻击者可以提供深度嵌套的Any结构来绕过预期的递归限制，最终耗尽Python的递归栈并导致 `RecursionError`。

#### 影响范围

**ccplugin项目状态**:
- ✅ **项目未直接使用受影响的API**: `ParseDict()`
- ✅ **protobuf作为传递依赖**: 通过 `onnxruntime` 间接依赖
- ⚠️ **当前版本**: 6.33.4 (受影响版本)
- ⚠️ **风险等级**: 低 (未直接使用受影响API)

**依赖链**:
```
plugins/code/semantic/
└── onnxruntime
    └── protobuf (6.33.4) ← 受影响版本
```

#### 缓解措施

**短期措施**:
1. ✅ 项目未直接使用 `ParseDict()` API，风险较低
2. ✅ 限制接受不可信的JSON输入
3. ✅ 如果需要解析protobuf JSON，验证JSON深度

**长期措施**:
1. 🔜 等待protobuf官方发布修复版本
2. 🔜 一旦有修复版本，立即更新依赖
3. 🔜 测试修复版本的功能兼容性

#### 修复状态

| 项目 | 状态 |
|------|------|
| **官方修复** | ⏳ 待发布 (截至2025-01-27) |
| **ccplugin更新** | ⏳ 等待官方修复后更新 |

#### 监控计划

- [ ] 定期检查protobuf新版本发布
- [ ] 关注[CVE公告](https://github.com/google/protobuf/security/advisories)
- [ ] 订阅[PyPI安全公告](https://pypi.org/project/protobuf/#history)
- [ ] 每周检查uv.lock中protobuf版本

#### 参考链接

- 漏洞报告: [protobuf issue #2](https://github.com/protobuf/protobuf/issues/2)
- PyPI包: https://pypi.org/project/protobuf/
- 安全公告: https://github.com/google/protobuf/security/advisories

---

## 历史漏洞

*暂无历史漏洞记录*

---

## 漏洞报告流程

### 新增漏洞

当发现新的安全漏洞时，按以下流程记录：

1. **评估影响**
   - 检查项目依赖
   - 确认受影响版本
   - 评估使用情况

2. **确定严重性**
   - 评估业务影响
   - 确定优先级
   - 制定修复计划

3. **实施缓解**
   - 短期措施
   - 长期方案
   - 监控跟踪

4. **验证修复**
   - 测试修复版本
   - 确认兼容性
   - 更新依赖

5. **文档记录**
   - 记录到本文件
   - 更新CHANGELOG
   - 通知相关团队

---

**最后更新**: 2025-01-27
**维护者**: lazygophers
**联系方式**: admin@lazygophers.dev
