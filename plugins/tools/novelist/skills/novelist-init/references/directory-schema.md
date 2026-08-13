# 小说目录结构规范(唯一事实源)

> novelist-init 据此搭骨架; 所有 skill 的目录归属以本文件为准。改结构先改这里。

## 完整目录树

```
<小说名>/
├── 总览.md                  # 元信息: 标题/类型/简介/进度 + 目录约定表
├── 人物/                    # ← novelist-character 独占
│   ├── _索引.md             # 人物花名册(定位/首次出场/状态)
│   └── <人物名>/
│       ├── 简介.md          # (a) 身份/外貌/性格/动机/说话风格/能力
│       ├── 经历.md          # (b) 按时间段的经历与关键事件(时间线)
│       └── 关系.md          # (c) 与他人交集/是否见过/首次相遇章/态度
├── 世界观/                  # ← novelist-worldview 独占
│   ├── _索引.md
│   ├── 地理.md              # 区域/地标/气候/地图
│   ├── 势力.md              # 国家/组织/派系/势力范围
│   ├── 规则.md              # 力量/科技/魔法体系: 能力边界 + 代价(一致性硬约束)
│   └── 历史.md              # 关键历史事件时间线
├── 设定/                    # ← novelist-worldview 独占
│   └── _索引.md             # 物品/组织/术语, 一设定一文件
├── 大纲/                    # ← novelist-outline 独占
│   ├── 总纲.md              # 核心冲突/三幕分卷/结局走向
│   └── 分卷.md              # 每卷主题/起止章/卷末钩子
├── 情节/                    # ← novelist-outline 独占
│   ├── 主线.md              # 节点→章节→核心冲突
│   ├── 支线.md              # 支线→人物→章节→交汇点
│   └── 伏笔.md              # 伏笔→埋设章→计划回收章→状态
├── 章节/                    # ← novelist-write 新增 / novelist-rewrite 覆盖
│   ├── _索引.md             # 章/标题/字数/状态/备注
│   └── 第NNN章-<标题>.md
└── 元数据/
    ├── 进度.md
    ├── 检查报告/            # ← novelist-check 写
    └── 校对报告/            # ← novelist-proofread 写
```

## 目录归属表(防冲突总表)

| 目录 | 独占写入 skill | 谁可读 |
|---|---|---|
| 人物/ | novelist-character | design/write/check/proofread 读 |
| 世界观/ 设定/ | novelist-worldview | design/write/check 读 |
| 大纲/ 情节/ | novelist-outline | design/write/check 读 |
| 章节/ | novelist-write(新增) / novelist-rewrite(覆盖) | check/proofread 读, proofread 改文字层 |
| 元数据/检查报告/ | novelist-check | —— |
| 元数据/校对报告/ | novelist-proofread | —— |

> 一个目录只有一个"独占写入"skill, 其余 skill 只读。这是整套插件不互相踩踏的根基。novelist-design 是编排者, 不直接写, 只调用上述 skill。
