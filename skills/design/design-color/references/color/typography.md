# 排版与字体配对速查（Typography）

> 来源：`ui-ux-pro-max-skill/typography.csv`（74 条配对），中文化 + 分组。
> 每行：配对名 / 标题字体 / 正文字体 / 类别 / 关键词 / 最适用于 / 使用要点。
> Google Fonts CSS import / Tailwind config 见原表 — 此处仅迁移决策用字段。

---

## 选型决策速查

| 需求 | 首选配对编号 | 风格 |
|------|------------|------|
| 通用 / 现代 SaaS | 13, 72 | 友好专业 |
| 奢侈 / 时尚 | 1, 12, 32, 50 | 高端衬线 |
| 科技 / 开发者 | 9, 31, 36, 42, 47, 51, 62 | Mono + Sans |
| 儿童教育 | 6, 19, 45, 71 | 圆润友好 |
| 新闻出版 | 14, 35 | 衬线可读 |
| 无障碍优先 | 16, 48 | WCAG 友好 |
| 中文简体 | 25 | Noto Sans SC |
| 中文繁体 | 24 | Noto Serif/Sans TC |
| 日文 | 22 | Noto JP |
| 韩文 | 23 | Noto KR |
| 阿拉伯 RTL | 26 | Noto Arabic |
| 极简主义 | 5, 44, 55 | Inter / Space Grotesk |
| 复古 | 10, 34, 52 | Decorative |

---

## A. 通用 / SaaS / 商务（1-5, 11, 13, 16, 20, 29-31, 40, 72）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 1 | Classic Elegant | Playfair Display | Inter | Serif + Sans | 经典、优雅、高端 | 奢侈品、婚礼、时尚 | 高对比标题 |
| 2 | Modern Professional | Poppins | Open Sans | Sans + Sans | 现代、专业、友好 | 企业、代理、作品集 | 通用安全选 |
| 3 | Tech Startup | Space Grotesk | DM Sans | Sans + Sans | 科技、创新、现代 | 科技初创、SaaS、产品 | 几何标题 |
| 4 | Editorial Classic | Cormorant Garamond | Libre Baskerville | Serif + Serif | 编辑、经典、文学 | 杂志、出版、博客 | 双衬线 |
| 5 | Minimal Swiss | Inter | Inter | Sans 单族 | 极简、瑞士、干净 | 极简品牌、作品集 | 单族变权重 |
| 11 | Geometric Modern | Outfit | Work Sans | Sans + Sans | 几何、现代、平衡 | 通用、作品集、落地页 | 两者几何但 Outfit 标题更独特 |
| 13 | Friendly SaaS | Plus Jakarta Sans | Plus Jakarta Sans | Sans 单族 | 友好、现代、SaaS | SaaS、仪表板、B2B | Inter 的现代替代 |
| 16 | Corporate Trust | Lexend | Source Sans 3 | Sans + Sans | 企业、可信、可访问 | 企业、政府、医疗 | Lexend 为可读性设计 |
| 20 | Premium Sans | Satoshi | General Sans | Sans + Sans | 高端、现代、精致 | 高端品牌、SaaS、初创 | 注：Fontshare 字体，DM Sans 作 Google 替代 |
| 29 | Legal Professional | EB Garamond | Lato | Serif + Sans | 法律、正式、权威 | 律所、合同、正式文档 | EB Garamond 表权威 |
| 30 | Medical Clean | Figtree | Noto Sans | Sans + Sans | 医疗、干净、可访问 | 医疗、诊所、健康应用 | 干净可访问 |
| 31 | Financial Trust | IBM Plex Sans | IBM Plex Sans | Sans 单族 | 金融、可信、专业 | 银行、保险、金融科技 | IBM Plex 传达信任 |
| 40 | E-commerce Clean | Rubik | Nunito Sans | Sans + Sans | 电商、干净、转化 | 电商、产品页、零售 | 产品描述清晰可读 |
| 72 | Enterprise SaaS Mobile | Plus Jakarta Sans | Plus Jakarta Sans | Sans 单族 | 企业、B2B、专业 | B2B SaaS、政府、金融移动端 | 支持 iOS Dynamic Type / Android 字号缩放 |

---

## B. 奢侈 / 编辑 / 杂志（12, 32-35, 50, 54, 68）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 12 | Luxury Serif | Cormorant | Montserrat | Serif + Sans | 奢侈、高端、时尚 | 时装、奢侈品电商、珠宝 | Cormorant 优雅 + Montserrat 几何 |
| 32 | Real Estate Luxury | Cinzel | Josefin Sans | Serif + Sans | 地产、奢华、精致 | 地产、豪宅、建筑 | Cinzel 表标题优雅 |
| 33 | Restaurant Menu | Playfair Display SC | Karla | Serif + Sans | 餐厅、菜单、美食 | 餐厅、咖啡、美食博客 | 小写 Playfair 做菜单头 |
| 34 | Art Deco | Poiret One | Didact Gothic | Display + Sans | 装饰艺术、1920、奢华 | 复古活动、艺术装饰主题 | Poiret One 仅做大标题 |
| 35 | Magazine Style | Libre Bodoni | Public Sans | Serif + Sans | 杂志、编辑、出版 | 杂志、在线出版物 | Bodoni 编辑优雅 |
| 50 | Luxury Minimalist | Bodoni Moda | Jost | Serif + Sans | 奢侈极简、高端 | 奢侈极简品牌、高端时尚 | Bodoni 高对比 + Jost 几何 |
| 54 | Academic/Archival | EB Garamond | Crimson Text | Serif + Serif | 学术、古典、档案 | 大学、档案、研究论文 | 经典学术美学 |
| 68 | Academia Mobile | Cormorant Garamond | Crimson Pro | Serif + 书衬线 + 雕刻 | 学术、图书馆、古董 | 知识管理、学术阅读、RPG | 三层栈：Cormorant 标题 / Crimson 正文 / Cinzel 全大写标签 |

---

## C. 科技 / 开发者 / 数据（9, 31, 42, 47, 51, 60-63, 66, 69-70）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 9 | Developer Mono | JetBrains Mono | IBM Plex Sans | Mono + Sans | 代码、开发者、技术 | 开发工具、文档、代码编辑器 | JetBrains 写码，IBM Plex 做 UI |
| 42 | Dashboard Data | Fira Code | Fira Sans | Mono + Sans | 仪表板、数据、分析 | 仪表板、分析、数据可视化 | Fira 家族统一 |
| 47 | Science/Tech | Exo | Roboto Mono | Sans + Mono | 科学、技术、研究 | 科学、研究、数据密集站点 | Exo 现代科技感 |
| 51 | Tech/HUD Mono | Share Tech Mono | Fira Code | Mono + Mono | 科技、科幻、HUD、数据 | 科幻界面、开发工具、网络安全 | Share Tech Mono 经典科幻感 |
| 60 | Modern Dark Cinema | Inter | Inter | Sans + Mono | 暗色、电影、精密、开发者 | 开发工具、金融/交易、AI 仪表板 | 单族精密系统；渐变文字 mask-view |
| 61 | SaaS Mobile Boutique | Calistoga | Inter | Display 衬线 + Sans + Mono | SaaS、精品、温暖、编辑 | B2B SaaS 移动、金融科技、分析 | 三层栈；Calistoga 加人味 |
| 62 | Terminal CLI Mono | JetBrains Mono | JetBrains Mono | Mono 单族 | 终端、CLI、黑客 | 开发工具、Web3、黑客美学 | 严格字号 12/14/16，权重仅 400 |
| 63 | Kinetic Brutalism | Space Grotesk | Space Grotesk | Sans 单族 | 动感、粗野、大写、超大 | 音乐/文化应用、体育、品牌旗舰 | Space Grotesk 700-900 全大写 |
| 66 | Neo Brutalism Mobile | Space Grotesk | Space Grotesk | Sans 粗体 | 新粗野、波普、响亮、Gen-Z | 创意工具、Gen-Z 营销 | 仅 700/900，禁 Regular/Light |
| 69 | Cyberpunk Mobile | Orbitron | JetBrains Mono | Tech Display + Mono | 赛博朋克、霓虹、HUD、科幻 | 游戏、金融/加密、数据可视化 | Orbitron 700-900 全大写 + JetBrains Mono 正文 |
| 70 | Web3 Bitcoin DeFi | Space Grotesk | Inter | Sans + Sans + Mono | Web3、比特币、DeFi、金融科技 | DeFi 协议、NFT、元宇宙 | 三层栈；数据用 JetBrains Mono |

---

## D. 表达 / 创意 / 风格化（6-8, 10, 15, 17-19, 37-39, 43-46, 52-53, 56-59, 67, 71, 73）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 6 | Playful Creative | Fredoka | Nunito | Display + Sans | 俏皮、友好、创意 | 儿童应用、教育、游戏 | 圆润友好 |
| 7 | Bold Statement | Bebas Neue | Source Sans 3 | Display + Sans | 大胆、冲击力、戏剧 | 营销、作品集、活动、体育 | Bebas Neue 仅大标题全大写 |
| 8 | Wellness Calm | Lora | Raleway | Serif + Sans | 平静、健康、有机 | 健康、冥想、瑜伽、有机品牌 | Lora 有机曲线 + Raleway 优雅 |
| 10 | Retro Vintage | Abril Fatface | Merriweather | Display + Serif | 复古、怀旧、装饰 | 复古品牌、餐厅、创意作品集 | Abril Fatface 仅 hero 标题 |
| 15 | Handwritten Charm | Caveat | Quicksand | Script + Sans | 手写、个人、温暖 | 个人博客、邀请、创意作品集 | Caveat 少量点缀 |
| 17 | Brutalist Raw | Space Mono | Space Mono | Mono 单族 | 粗野、原始、技术 | 粗野设计、开发作品集、实验 | 全 mono，权重有限 |
| 18 | Fashion Forward | Syne | Manrope | Sans + Sans | 时尚、前卫、艺术 | 时尚品牌、创意代理、画廊 | Syne 标题独特 |
| 19 | Soft Rounded | Varela Round | Nunito Sans | Sans + Sans | 柔软、圆润、友好 | 儿童产品、宠物、软 UI | 圆润友好 |
| 37 | Gaming Bold | Russo One | Chakra Petch | Display + Sans | 游戏、大胆、电竞、能量 | 游戏、电竞、动作、竞技 | Russo One 冲击 + Chakra Petch 科技正文 |
| 38 | Indie/Craft | Amatic SC | Cabin | Display + Sans | 独立、手工、艺术 | 手工品牌、独立产品、有机 | Amatic 手写感 |
| 39 | Startup Bold | Clash Display | Satoshi | Sans + Sans | 初创、大胆、创新、自信 | 初创、路演 deck、产品发布 | 注：Clash Display 在 Fontshare，Outfit 作 Google 替代 |
| 43 | Music/Entertainment | Righteous | Poppins | Display + Sans | 音乐、娱乐、活力 | 音乐平台、活动、节日 | Righteous 大胆娱乐头 |
| 44 | Minimalist Portfolio | Archivo | Space Grotesk | Sans + Sans | 极简、作品集、设计师 | 设计作品集、创意专业 | Space Grotesk 独特标题 |
| 45 | Kids/Education | Baloo 2 | Comic Neue | Display + Sans | 儿童、教育、俏皮 | 儿童应用、教育游戏 | Comic Neue 可读漫画风 |
| 46 | Wedding/Romance | Great Vibes | Cormorant Infant | Script + Serif | 婚礼、浪漫、优雅、请柬 | 婚礼、邀请、浪漫品牌 | Great Vibes 优雅点缀 |
| 52 | Pixel Retro | Press Start 2P | VT323 | Display + Sans | 像素、复古、8-bit、游戏 | 像素艺术游戏、复古网站 | Press Start 2P 极宽大；VT323 做正文 |
| 53 | Neubrutalist Bold | Lexend Mega | Public Sans | Display + Sans | 新粗野、响亮、几何、奇特 | 新粗野设计、Gen-Z 品牌、大胆营销 | Lexend Mega 可变权重独特 |
| 56 | Kinetic Motion | Syncopate | Space Mono | Display + Mono | 动感、未来、速度、宽 | 音乐节、汽车、高能品牌 | Syncopate 宽姿态配动感效果 |
| 57 | Gen Z Brutal | Anton | Epilogue | Display + Sans | 粗野、响亮、模因、互联网 | Gen-Z 营销、街头、病毒营销 | Anton 冲击力强、贴纸徽章 |
| 58 | Bauhaus Geometric | Outfit | Outfit | 几何 Sans 单族 | 包豪斯、几何、建构、建筑 | 包豪斯移动应用、大胆编辑、设计品牌 | 单族：Outfit 900 全大写 hero / 700 按钮 / 500 正文 |
| 59 | Minimalist Monochrome Editorial | Playfair Display | Source Serif 4 | Serif + Serif + Mono 三层栈 | 单色、编辑、极简、高对比 | 奢侈时尚移动、编辑出版、展览 | 三层栈：Playfair hero / Source Serif 4 正文 / JetBrains Mono 标签；无 sans-serif |
| 67 | Bold Typography Mobile | Inter | Playfair Display | Sans + 衬线 Display + Mono | 大胆排版、编辑、海报、奢侈 | 创意品牌旗舰、阅读平台、活动 | 三层栈；Playfair 仅斜体引用；5:1 H1:Body 硬性比 |
| 71 | Claymorphism Mobile | Nunito | DM Sans | Display 圆 + 几何 Sans | 黏土、圆润、俏皮、糖果、3D | 儿童教育、青少年社交、品牌吉祥物 | Nunito 标题必 900/800；DM Sans 做正文 |
| 73 | Sketch Hand-Drawn Mobile | Kalam | Patrick Hand | 手写 + 手写 | 手绘、手写、不完美、有机 | 日记应用、原型工具、儿童画书 | Kalam 标题 / Patrick Hand 正文；禁金融法律正文 |

---

## E. 阿拉伯 / 法律 / 通用专业（14, 21, 41, 48-49, 55, 64-65, 74）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 14 | News Editorial | Newsreader | Roboto | Serif + Sans | 新闻、编辑、可信、可读 | 新闻站、博客、杂志 | Newsreader 为长篇阅读设计 |
| 21 | Vietnamese Friendly | Be Vietnam Pro | Noto Sans | Sans + Sans | 越南语、国际、多语言 | 越南语站点、多语言应用 | Be Vietnam Pro 越南语支持优秀 |
| 41 | Academic/Research | Crimson Pro | Atkinson Hyperlegible | Serif + Sans | 学术、研究、可访问 | 大学、研究论文、学术期刊 | Crimson 学术头 + Atkinson 可访问 |
| 48 | Accessibility First | Atkinson Hyperlegible | Atkinson Hyperlegible | Sans 单族 | 无障碍、可读、WCAG、阅读障碍友好 | 无障碍关键站点、政府、医疗 | 为最大可读性设计 |
| 49 | Sports/Fitness | Barlow Condensed | Barlow | Sans + Sans | 体育、健身、运动、能量 | 体育、健身、健身房 | Condensed 冲击头 + Regular 正文 |
| 55 | Spatial Clear | Inter | Inter | Sans 单族 | 空间、可读、玻璃、系统 | 空间计算、AR/VR、玻璃拟态 | 动态背景优化可读 |
| 64 | Flat Design Mobile | Inter | Inter | Sans 单族 | 扁平、干净、系统、跨平台 | 跨平台应用、仪表板、系统 UI | Inter 800 标题大对比；无阴影靠权重 |
| 65 | Material You MD3 | Roboto | Roboto | Sans 系统默认 | Material Design 3、Android、Google | Android 应用、跨平台工具、企业 | MD3 字号阶梯；禁 300-700 外权重 |
| 74 | Neumorphism Mobile | Plus Jakarta Sans | Plus Jakarta Sans | Sans 系统回退 | 新拟态、软 UI、单色、深度 | 智能家居控制、极简工具、仪表板 | 单色 #E0E5EC 表面配 Plus Jakarta |

---

## F. 多语言 CJK / RTL（22-28）

| # | 配对名 | 标题 | 正文 | 类别 | 关键词 | 最适用于 | 要点 |
|---|--------|------|------|------|--------|---------|------|
| 22 | Japanese Elegant | Noto Serif JP | Noto Sans JP | Serif + Sans | 日文、优雅、传统 + 现代 | 日文站点、日式餐厅、文化 | Noto JP 支持优秀 |
| 23 | Korean Modern | Noto Sans KR | Noto Sans KR | Sans 单族 | 韩文、现代、干净、专业 | 韩文站点、K-beauty、K-pop | 单族权重变化 |
| 24 | Chinese Traditional | Noto Serif TC | Noto Sans TC | Serif + Sans | 中文繁体、传统、优雅 | 繁体中文站点、文化内容、台港市场 | 繁体支持 + 优雅配对 |
| 25 | Chinese Simplified | Noto Sans SC | Noto Sans SC | Sans 单族 | 中文简体、现代、专业 | 简体中文站点、中国大陆市场、商务应用 | 简体支持 + 干净现代 |
| 26 | Arabic Elegant | Noto Naskh Arabic | Noto Sans Arabic | Serif + Sans | 阿拉伯、优雅、RTL、文化 | 阿拉伯站点、中东市场、伊斯兰内容 | RTL 支持；Naskh 传统 / Sans 现代 |
| 27 | Thai Modern | Noto Sans Thai | Noto Sans Thai | Sans 单族 | 泰文、现代、可读 | 泰文站点、东南亚、旅游 | 干净泰文排版 |
| 28 | Hebrew Modern | Noto Sans Hebrew | Noto Sans Hebrew | Sans 单族 | 希伯来、现代、RTL、专业 | 希伯来站点、以色列市场 | RTL 支持 |

---

## Google Fonts 集成指引

每条配对的 `@import` / Tailwind config 完整值见原表 `typography.csv`（11 列）。
通用集成步骤：

1. **Google Fonts URL**：取配对对应 CSS2 URL（含所需权重）
2. **CSS 引入**：`@import url('<URL>');` 放样式表顶部
3. **Tailwind config**：`fontFamily: { heading: [...], body: [...] }`
4. **性能注意**：
   - 仅加载必需权重（每族 ≤ 4 个权重）
   - `display=swap` 防 FOIT
   - 关键字体可 `<link rel="preload">`
5. **Fontshare 字体**（Satoshi / General Sans / Clash Display）：需 Fontshare 账号，或用 Google 替代（见各条「要点」列）

---

## 全局规则

- **权重对比做层级**：标题 600-900 / 正文 400-500，靠权重非字号做首屏层级
- **行高**：标题 1.0-1.2 / 正文 1.4-1.6
- **字间距**：大标题负值（-1 至 -2px）/ 全大写标签正值（+1 至 +2px）
- **可访问性**：金融/医疗/政府优先 Lexend / Atkinson Hyperlegible / IBM Plex
- **单族策略省加载**：Inter / Plus Jakarta Sans / Space Grotesk 单族 + 权重变化，性能优于双族
- **禁混用太多族**：最多 3 层栈（标题 + 正文 + 强调），超出视觉混乱
- **移动端**：尊重 iOS Dynamic Type / Android font scale，禁硬编码像素无回退

---

## 与本目录其他文件的关系

| 本文件提供 | 交叉参考 |
|-----------|---------|
| 字体配对选型（74 条） | [[理论]] — 字体分类理论 |
| Google Fonts 集成步骤 | [[主题-目录]] — 主题如何选配字体 |
| 权重/行高全局规则 | [[调色板-模板]] — 字体如何配配色 |
| 多语言 CJK/RTL 支持 | [[可访问性]] — 可读性 / 阅读障碍友好 |
