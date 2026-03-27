# Risk Classifier - 风险分级规则

## 三级风险分类

| 级别 | 评分 | 操作类型 | 行为 |
|------|------|---------|------|
| **auto** | 0-3 | 只读(Read/Glob/Grep/WebSearch)、测试(test/lint)、生成(代码/文档)、分析 | 自动执行 |
| **review** | 4-6 | 文件修改(Edit/Write)、依赖安装(npm/pip/go get)、配置变更、普通git操作、资源创建 | 需用户审查 |
| **mandatory** | 7-10 | 破坏性删除(rm -rf)、强制覆盖(force push/reset --hard)、生产部署、权限变更(sudo)、外部影响(发消息/创建PR)、敏感数据(.env/密钥) | 强制审批 |

## 分级决策树

1. 包含破坏性关键字(rm -rf/DROP TABLE/--force/reset --hard/sudo)？→ mandatory
2. 只读工具(Read/Glob/Grep/WebSearch)？→ auto
3. 外部写入(SendMessage/WebFetch POST/PUT/DELETE)？→ mandatory
4. 生产环境？→ mandatory
5. 敏感文件(.env/id_rsa/private/secrets)？→ mandatory
6. 写入工具(Edit/Write/Bash)？→ review
7. 默认→ auto

## 风险评分量化

四维度加权：可逆性×40%(完全可逆0/部分5/不可逆10) + 影响范围×30%(单文件0/多文件3/跨系统7/生产10) + 敏感性×20%(公开0/内部5/敏感10) + 外部影响×10%(无0/读取3/修改10)

## 特殊场景

- **批量操作**：风险取所有子操作最高级
- **用户覆盖**：`.claude/task.local.md` 中 hitl_overrides 可覆盖特定pattern的风险等级
- **信任模式**：review→auto，mandatory不变

## 接口

输入：tool/command/files/method/environment/user_trust_mode
输出：level(auto/review/mandatory)/score(0-10)/reasons[]/requires_approval/approval_policy(timeout/default_action)

日志：记录到`.claude/plans/{task_hash}-approval-log.json`，含operation/risk_classification/approval。
