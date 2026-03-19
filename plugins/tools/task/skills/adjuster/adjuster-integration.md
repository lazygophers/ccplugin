# Adjuster 集成示例

<overview>

本文档是 Adjuster 集成文档的索引。Adjuster 的集成主要发生在 Loop 的失败调整阶段，但也支持独立使用。按使用复杂度拆分为两个层级：基础集成覆盖 Loop 内的标准用法，高级集成覆盖自定义场景和停滞检测。

</overview>

<navigation>

## 基础集成

文件：[adjuster-integration-basic.md](adjuster-integration-basic.md)

包含最常见的集成场景：Loop 命令中的使用（标准调用方式和结果处理）、辅助函数实现（应用调整建议 apply_adjustments、深度诊断 apply_debug_fixes、显示重新规划选项、应用用户指导 apply_user_guidance）。大多数情况下只需参考基础集成。

## 高级集成

文件：[adjuster-integration-advanced.md](adjuster-integration-advanced.md)

包含进阶使用场景：自定义场景集成（单次失败处理、批量失败处理、条件调整）、停滞检测的实现（错误签名比对和相似度计算）、指数退避的完整实现、错误处理和异常恢复。

</navigation>
