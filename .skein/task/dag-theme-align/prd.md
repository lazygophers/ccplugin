# DAG tab 主题风格适配 — PRD (主入口)

## 目标
- [ ] DAG popover + Modal 配色适配海滩蓝金主题: glass 质感 + 引入 goldSand 暖色 + ocean 阶色变量替代硬编码 + Modal 金线点缀。
- [ ] 成功: DAG tab popover/modal 与 components/Timeline 卡片视觉一致 (glass backdrop-blur + 海蓝金沙滩双色平衡), 明暗双模都自然。

## 边界
范围内:
- [ ] `docs/examples/index.html` 单文件改: DAG CSS 段 (`.dag-pop-inner` / `dialog.dag-modal` / `.dag-pop-*` / `.dag-modal-*`) L362-410。
- [ ] 硬编码 `#fffefb/#162c42/#48bb78/#429cd1/#e53e3e/#74b9e8/#1e293b/#f1f5f9` 等 → 用 glass + ocean/goldSand/night/success/danger token。
- [ ] popover/modal 加 backdrop-blur + 半透 (复用 .glass 范式 L119)。
- [ ] chip/进度条/强调色引入 goldSand 暖金层次。
- [ ] Modal 标题加 goldSand 下划线点缀。

范围外 (非目标):
- [ ] 不改 DAG 节点 4 态色本身 (done/active/failed/default 语义色保留, 只调容器质感)。
- [ ] 不改其他 5 tab。
- [ ] 不改 DAG 布局/拓扑/动画/交互逻辑。
- [ ] 不引第三方库。

## 验收标准
- [x] popover `.dag-pop-inner`: glass backdrop-blur + 半透 (非纯白), 明暗双模。
- [x] Modal `dialog.dag-modal`: glass + 标题下 goldSand 金线点缀。
- [x] chip/进度条/强调色至少 1 处用 goldSand 暖金 (替代纯 ocean 蓝单调)。
- [x] 硬编码 hex 减少 (ocean/goldSand/night token 替代), 暗模色用 night 阶。
- [x] 明暗双模切换 DAG tab popover/modal 都自然不突兀。
- [x] 6 tab 切换无 JS 报错, 视觉与 components/Timeline 卡片一致。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list dag-theme-align`)
