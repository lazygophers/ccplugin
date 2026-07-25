# build-theme-palette-catalogs-and-platforms — PRD

## 目标
- [x] color/themes-catalog.md 主题总清单(现有20 + 热门 Nord/Dracula/Catppuccin/OneDark/RoséPine/GitHub/Monokai/NightOwl/Synthwave 等共~30+, 可扫, 每条含关键色+跨媒介适用+详情链接)
- [x] color/palettes-catalog.md 配色总清单(品牌主色阶/中性阶/语义色/命名色板 一处可扫)
- [x] 平台覆盖补全: app 加 iPadOS/watchOS/tvOS/WearOS; tui 加终端兼容(iTerm2/Terminal.app/WindowsTerminal/Alacritty/kitty/tmux); cli 加 shell 兼容(bash/zsh/fish/powershell/nushell)
- [x] color/INDEX + SKILL.md 引用清单

## 边界
- [x] 清单是可扫目录(每条关键色内联), 详情仍链各 medium style
- [x] 唯一 SKILL.md 不变

## 验收标准
- [x] themes-catalog 含 ≥30 主题, 每条有色值+适用媒介+链接
- [x] palettes-catalog 含品牌/中性/语义/命名色板全量
- [x] 三处平台覆盖文件更新
- [x] 无断链, commit 完成

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
