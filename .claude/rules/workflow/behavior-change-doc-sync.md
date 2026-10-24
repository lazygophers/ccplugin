# 行为改动后 grep 文档旧描述：清单内验证抓不到清单外的文档漂移

审计 / 验证 agent 核对的是提案清单内的项；清单外的文档漂移（描述旧行为的句子）
没人负责。2026-10-24 ask-me session：P7 把 complete 回显瘦身后，workflow 验证
agent 全绿，SKILL.md:61 仍写着「complete 输出已读取的答案」，靠主对话验收
grep 才抓到。

行为改动的收尾固定加一步：grep 受影响 skill / 插件的全部文档（SKILL.md、
README、references/），搜被删 / 改名的字段名和旧行为动词短语（「输出…」
「返回…」），确认每处描述与新行为一致。这一步不放进 agent 的验证清单，由
主对话验收时自己跑。

出处：.scratch/memory/2026-10-24.md 第 3 条决策。
