# 去 AIGC / 去 AI 味方法论

> 调研目标: AIGC 文本检测特征 + 小说去 AI 味方法论, 蒸馏成可操作的去 AI 味创作框架。
> 标注约定: `[原理]` = 检测器/语言模型的客观机制; `[手法归纳]` = 写作社区/编辑经验共识。
> 语境: 以中文小说正文为主, 兼顾通用文本特征。
> 边界提示: 本框架目的是**提升正文的人味与可读性**, 而非单纯欺骗检测器(见末尾「局限与适用边界」)。

---

## 1 检测器原理

检测器看的不是「对不对」, 而是「文本的统计指纹有多像逐 token 高概率采样的产物」。理解它看什么, 才知道改写时往哪个方向破坏指纹。

- **困惑度 perplexity(惊讶度)** `[原理]`: 检测器用一个参考模型(如 GPT-2)逐句算「这串 token 有多出我意料」; LLM 训练目标就是最小化困惑度 → AI 文本系统性偏低(太可预测), 人类文本偏高(用词跳跃、有意外选择)。 | 来源: [GPTZero - perplexity & burstiness](https://gptzero.me/news/perplexity-and-burstiness-what-is-it/), [hastewire](https://hastewire.com/blog/how-ai-detectors-calculate-perplexity-and-burstiness) | 应用: 改写时刻意引入低概率但合理的词/意象(具体专名、方言、不常见动词), 抬高局部困惑度——但别为了生僻而生僻, 否则伤可读性。
- **突发性 burstiness(节奏方差)** `[原理]`: 把每句的困惑度连成曲线看波动幅度。人因短期记忆会本能避免连写相似句, 曲线有尖峰; AI 像节拍器, 句长与「AI 度」回归均值, 曲线平坦。 | 来源: [GPTZero](https://gptzero.me/news/perplexity-and-burstiness-what-is-it/), [GPTZero 官方支持](https://support.gptzero.me/articles/9585228410-how-do-i-interpret-burstiness-or-perplexity) | 应用: 制造句长方差——几句短促接一个长复句, 段落里塞一句两三字的独立句; 这是降检出率性价比最高的单一手段。
- **句长/句式回归均值** `[原理]`: AI 逐 token 在固定上下文窗口内生成 → 倾向收敛到平均句长与统一句法结构, 整体「过分工整」。 | 来源: [hastewire](https://hastewire.com/blog/how-ai-detectors-calculate-perplexity-and-burstiness), [中文去AI味共识](https://github.com/op7418/Humanizer-zh) | 应用: 主动打破句长均匀: 长短句暴力交错、句式结构不重复(陈述句后跟疑问/感叹/省略)。
- **学习型分类器(七层/微调 transformer)** `[原理]`: 现代商用检测器(GPTZero/Originality/Turnitin/Copyleaks)不止看 perplexity, 而是用 RoBERTa/DeBERTa 在「人类 vs AI」百万配对样本上微调, 困惑度/突发性只是其中可解释的一层。 | 来源: [GPTZero - how detectors work](https://gptzero.me/news/how-ai-detectors-work/), [Raschka 综述](https://sebastianraschka.com/blog/2023/detect-ai.html) | 应用: 单破坏 perplexity 不够; 必须同时改掉风格层 tells(过渡词、排比、华丽词、套路结构, 见第 2-3 节), 因为分类器对「风格指纹」同样敏感。

---

## 2 AI 文本可识别特征(通用)

这些是肉眼可辨的风格 tells, 分类器与人类读者都吃这一套。逐条对照正文删改。

- **三段式/三点排比(rule of three)** `[手法归纳]`: AI 默认把任何列举凑成三个(形容词×3、短句×3), 甚至连排三组排比制造「全面感」, 实为掩盖分析空洞。 | 来源: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [vrid.ai 27 red flags](https://vrid.ai/blog/signs-of-ai-writing) | 应用: 见到三连排比就砍, 留一组够了, 或打散成不对称的两项/四项; 中文里「首先/其次/再次/最后」整套排序词一律删。
- **机械过渡词** `[手法归纳]`: 「然而/此外/值得注意的是/总而言之/因此」高频且生硬地黏接句子, 制造伪逻辑流。 | 来源: [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [ETBI 图书馆](https://library.etbi.ie/sources2/aisigns) | 应用: 删掉过渡词后句子若仍通顺就别加回; 中文尤其删「值得注意的是/不难发现/总的来说」。
- **空泛抽象 + 拔高意义(undue emphasis)** `[手法归纳]`: 把「is/are」换成「serves as/represents/标志着/彰显」, 给一切套上「重要的一步/深刻的/范式转移」, 用华丽词(tapestry/landscape/毋庸置疑/不可磨灭)掩盖无信息量。 | 来源: [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | 应用: 用「具体替代抽象」原则——「很多人下班焦虑」→「昨晚十点小李还在地铁上改 PPT, 手里捏着冰凉的易拉罐」; 专名、品牌、型号、数字优于泛指。
- **否定式平行(negative parallelism)** `[手法归纳]`: 「不是 X, 而是 Y」/「不仅 X, 更是 Y」被点名为最常见单一 tell, 用来制造廉价的「反转式深刻」。 | 来源: [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [alyssawiens](https://alyssawiens.com/2025/03/27/how-can-you-tell-if-writing-is-ai-generated/) | 应用: 删掉伪反转, 直接陈述 Y; 整篇最多保留一两处真有张力的对比。
- **破折号滥用 / 翻译腔长定语** `[手法归纳]`: 英文里破折号被滥用作万能停顿(人类一篇 2-3 个, AI 20+); 中文里则是「一个……的……的……」英式长定语 + 多余被字句。 | 来源: [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 应用: 破折号改回逗号/句号; 长定语拆成短句, 被动改主动或无主句。
- **跑步机效应(treadmill / 信息密度低)** `[手法归纳]`: 500 字里只有 100 字新信息, 400 字是换皮重述与铺垫, 单位字数信息量远低于人类。 | 来源: [vrid.ai](https://vrid.ai/blog/signs-of-ai-writing), [tropes.fyi](https://gist.github.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1) | 应用: 删重述、删铺垫性总结句; 一段只推进一件新事。

---

## 3 小说正文特有的 AI 味

小说比通用文本更要命的是「太顺、太干净、情感被喂到嘴边」。这一层是降 AIGC 与提升文学质量重合度最高的部分。

- **对话过于规整、无口语杂质** `[手法归纳]`: AI 笔下人人像上过演讲课——完整句、不打断、不结巴、不说「呃/那个」; 且角色「想什么说什么」, 没有潜台词。 | 来源: [narrator.sh](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix), [sudowrite 对话](https://sudowrite.com/blog/best-ai-for-dialogue-writing-make-characters-sound-human/), [creativindie](https://www.creativindie.com/how-to-humanize-chatgpt-written-content-for-better-fiction-and-to-pass-ai-detection/) | 应用: 加「对话破坏(dialogue disruption)」——互相打断、半句话被噎住、答非所问、停顿与口头禅; 让人物说的≠想的, 留潜台词。
- **「告诉」而非「呈现」(telling not showing) + 情感喂饭** `[手法归纳]`: AI 直接写「她很愤怒」并贴心解释情绪, 完美隐喻落得太干净。 | 来源: [narrator.sh](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix), [Microsoft Copilot humanize](https://www.microsoft.com/en-us/microsoft-copilot/copilot-101/humanize-ai-text) | 应用: 删情感标签与解释, 用动作/身体语言/没说出口的话呈现; 让情绪「埋伏式」地在某句中途突然冒出, 而非被预告。
- **节奏匀速、无起伏** `[手法归纳]`: 句式像流水线, 每段铺陈密度一致, 缺张弛。 | 来源: [中文去AI味共识](https://zhuanlan.zhihu.com/p/692546989)(仅取「句长节奏」方法论, 不引平台观点), [hastewire 7 tips](https://hastewire.com/blog/how-to-make-ai-writing-sound-more-human-7-easy-tips) | 应用: 「节奏暴力变速」——紧张处连用短句, 抒情处放一个长复句; 朗读法自检, 读起来卡的地方就是 AI 味。
- **描写套路化 / 形容词堆砌 / 陈词滥调意象** `[手法归纳]`: 训练数据高频短语被复读(「百感交集的情绪」「a tapestry of emotions」), 形容词成串堆而非动词发力。 | 来源: [narrator.sh](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix), [creativindie](https://www.creativindie.com/how-to-humanize-chatgpt-written-content-for-better-fiction-and-to-pass-ai-detection/) | 应用: 「微观纹理 + 感官不对称」——用角色专属、出人意料的具体细节替代通用描写; 强动词换掉「形容词+副词」堆叠; 见到熟套意象就换。
- **过度全知 / 视角无杂质** `[手法归纳]`: AI 倾向上帝视角把一切交代干净, 缺人类作者特有的偏好、跳跃、漏说。 | 来源: [aistoryhub](https://blog.aistoryhub.co/how-i-built-an-ai-writing-platform-that-doesnt-sound-like-ai/), [narrator.sh](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix) | 应用: 「允许不完美/允许丑」——保留无关细节、半成型的反应、视角人物的偏见与小气念头; 故意不解释某些东西, 留人类式的跳跃与留白。

---

## 4 去 AI 味改写手法

把第 1-3 节的诊断转成动作。改写顺序建议: 先砍 tells(过渡词/排比/华丽词) → 再制造节奏 burstiness → 最后注入具体细节与口语毛刺。

- **制造句长突发性(burstiness)** `[手法归纳]`: 长短句无规律暴力交错, 段中插一两句两三字的独立句, 打破节拍器。 | 来源: [GPTZero 原理](https://gptzero.me/news/perplexity-and-burstiness-what-is-it/) → 反向应用, [hastewire 7 tips](https://hastewire.com/blog/how-to-make-ai-writing-sound-more-human-7-easy-tips) | 应用: 这是单点性价比最高的手法, 同时降 perplexity/burstiness 检出并真实提升可读节奏。
- **加口语毛刺与不完美** `[手法归纳]`: 中文加语气词与转折(「其实」「说实话」「结果呢」「真累」); 对话加打断、结巴、半句; 保留无关半成型反应。 | 来源: [中文去AI味方法论](https://github.com/op7418/Humanizer-zh), [creativindie 编辑手法](https://www.creativindie.com/how-to-humanize-chatgpt-written-content-for-better-fiction-and-to-pass-ai-detection/) | 应用: 毛刺要服务角色性格, 别滥用网络俚语反而出戏。
- **删过渡词与伪结构** `[手法归纳]`: 删「然而/值得注意的是/首先其次最后」; 删收尾的「总而言之」式套路段与「挑战与展望」式模板结构。 | 来源: [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [ETBI](https://library.etbi.ie/sources2/aisigns) | 应用: 删后通顺即不补; 让逻辑靠内容本身衔接, 不靠连接词撑场。
- **具体替代抽象 + 强动词** `[手法归纳]`: 专名/品牌/型号/数字/感官细节替代泛指与华丽词; 强动词替代「形容词+副词」堆叠; 删情感标签改为呈现。 | 来源: [narrator.sh 微观纹理](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix), [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | 应用: 「蛋糕很好吃」→「那蛋糕是我外婆的方子, 一口下去全是小时候的夏天」。
- **节奏错落 + 保留人类式偏好与跳跃** `[手法归纳]`: 各段铺陈密度故意不均; 保留作者偏见、视角漏说、不解释的留白、出人意料的具体选择(抬高局部困惑度)。 | 来源: [aistoryhub](https://blog.aistoryhub.co/how-i-built-an-ai-writing-platform-that-doesnt-sound-like-ai/), [narrator.sh](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix) | 应用: 朗读全段自检, 太顺太干净处就是要弄「脏」的地方。
- **修改阈值: 宁缺毋滥** `[手法归纳]`: 若某段已自然严谨无明显 AI 特征, 保留原文, 不为改而改——过度去味会伤可读性与一致性。 | 来源: [中文去AI味提示词框架](https://blog.csdn.net/wirepuller_king/article/details/144090065)(仅取「修改阈值」原则) | 应用: 每段先判「有没有 AI 味」, 有才改; 把改写当外科手术不当地毯式轰炸。

---

## 局限与适用边界

- **检测器本身不可靠, 不值得为它过度优化** `[原理]`: Stanford(Liang et al. 2023, Patterns)测 7 个检测器, 非母语英语 TOEFL 作文误报率高达 61.3%, 19.8% 被全部检测器一致误判为 AI——全是人写的; 业界误报率普遍 5-15%。 | 来源: [Stanford 研究综述](https://hastewire.com/blog/study-reveals-ai-detectors-false-positives-on-non-native-writers), [San Diego 法学库](https://lawlibguides.sandiego.edu/c.php?g=1443311&p=10721367) | 含义: 别把「过检测器」当唯一目标, 它连人类原创都常误杀。
- **军备竞赛无终局** `[原理]`: 检测与规避持续对抗, 双方都在变强, 学界主流判断是「随 LLM 变强, 可靠检测更不可能」。Google Research 的 Dipper 改写几乎通杀检测器(DetectGPT AUROC 从 96.5% 掉到 59.8%, 接近随机)。 | 来源: [Krishna et al. 2023 (Dipper)](https://arxiv.org/pdf/2303.13408), [Sadasivan et al. 2023 - Can AI Text be Reliably Detected](https://arxiv.org/pdf/2303.11156) | 含义: 今天有效的手法明天可能失效; 框架要锚定「真·人味」而非锚定某个检测器的当下弱点。
- **不同检测器看的特征不同** `[原理]`: DetectGPT 走 log-prob 扰动, GPTZero 走学习型分类器(七层), 商用各家微调样本不同; 对一个检测器有效不保证对另一个有效。 | 来源: [Raschka 综述](https://sebastianraschka.com/blog/2023/detect-ai.html), [GPTZero](https://gptzero.me/news/how-ai-detectors-work/) | 含义: 多检测器交叉时, 唯一稳健策略是普遍提升人味(风格层 + 统计层一起改), 而非针对单一工具调参。
- **去味 ≠ 提升文学质量** `[手法归纳]`: 市面 humanizer 工具多以「过检测器」为卖点, 只换词不懂角色与故事, 反而出戏; 过度去味会伤可读性、损人物声音一致性。 | 来源: [creativindie](https://www.creativindie.com/how-to-humanize-chatgpt-written-content-for-better-fiction-and-to-pass-ai-detection/), [narrator.sh 现实心态](https://narrator.sh/blog/why-ai-fiction-sounds-robotic-fix) | 含义: 正确目标不是「100% 像人」, 而是「好到读者不在乎」; 最可靠工作流是 AI 生成 + 人类精修, craft 手法(呈现/变速/分层对话/具体细节)比自动改写更管用。
