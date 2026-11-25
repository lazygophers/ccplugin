# SKILL.md 正文压在 5K token 截断线内：整节移 references + 原位留节名指针

progressive disclosure 机制下，SKILL.md 正文超过 compaction 重挂的 5K token
截断线会被截断（code.claude.com/docs/en/skills，第 1 类）。

压缩只认一种被验证安全的形态：**整节移入 `references/<名>.md`，原位留一行
「<节名>：见 [references/<名>.md](references/<名>.md)」指针**。
不删速查表 / 反模式表 / 字段规则表改指针。
