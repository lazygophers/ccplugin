# SKILL.md 正文压在 5K token 截断线内：整节移 references + 原位留节名指针

progressive disclosure 机制下，SKILL.md 正文超过 compaction 重挂的 5K token
截断线会被截断（code.claude.com/docs/en/skills，第 1 类）。2026-10-24 ask-me
实测正文 ~5.8-6.4K token，已在截断线上方。

压缩只认一种被验证安全的形态：**整节移入 `references/<名>.md`，原位留一行
「<节名>：见 [references/<名>.md](references/<名>.md)」指针**。ask-me 的开发
节、唤醒节均此形态落地，验证全过（commit bc19a2c，SKILL.md L139、L177）。
判废形态别再试：删速查表 / 反模式表 / 字段规则表改指针——查表冗余是特性，
judge 一致判退步（2026-10-23 判例，.scratch/memory/2026-10-24.md 第 1 条
决策的「否掉了」项）。

出处：.scratch/memory/2026-10-24.md 研究行。
