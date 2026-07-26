# examples/index.html 加 timeline tab + antd 全组件样例 — PRD (主入口)

## 目标
- [ ] 配色扩色阶: ocean 5 阶 (浅海/近海/深海/深海沟/夜海); sand 拆 white-sand (珍珠白/贝壳) + gold-sand (浅金/暖金/深金); 加 wave 渐变 + foam 浪花白; 背景用白沙滩→浅海渐变体现海滩感
- [ ] 新增 timeline tab: 任务生命周期 5 态竖向时间轴 (创建/就绪/起始/检查/完成, 与 board.js cardStepper 同源) + 通用 timeline 组件变体 (竖向/自定义节点/颜色/时间)
- [ ] 组件 tab 扩展覆盖 antd 全组件 6 类 (General/Layout/Navigation/DataEntry/DataDisplay/Feedback), 每类按 antd 文档顺序列出代表组件样例
- [ ] 保留现有 tab (色卡/图表/动效) 不破, 主题切换 (明暗) 在所有 tab 生效
- [ ] 成功: 浏览器打开, 6 tab 可切换, 配色有海滩感, 组件全, timeline 完整
## 边界
- [ ] docs/examples/index.html 单文件改: 扩 tailwind.config 色板 / 加 timeline tab / 扩展组件 tab / 调背景渐变
- [ ] 保留 Tailwind CDN + font-awesome CDN, 不引 antd 库 (用纯 HTML+Tailwind 模拟 antd 组件外观)
- [ ] 不改 webapp 真实前端 / sample-skein / README
- [ ] 不引第三方图表/动效库
## 验收标准
- [x] tailwind.config ocean 扩 5 阶 + sand 拆 white-sand/gold-sand + wave/foam 色定义齐全
- [x] 背景渐变体现白沙滩→大海层次 (非纯色背景)
- [x] timeline tab 含任务生命周期 5 态时间轴 + 通用 timeline 变体
- [x] 组件 tab 覆盖 antd 6 类 (General/Layout/Navigation/DataEntry/DataDisplay/Feedback) 各类 ≥3 代表组件
- [x] 5 tab (色卡/组件/图表/动效/timeline) 可切换, 主题明暗双模全 tab 生效
- [x] 浏览器打开无 JS 报错, tab 切换流畅
- [x] HTML 结构完整 (标签闭合平衡)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list examples-timeline-antd`)
