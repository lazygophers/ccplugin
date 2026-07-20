---
name: oss-license
description: '开源协议(License)选择与合规决策框架。覆盖 60+ 协议(MIT/Apache/BSD/ISC/GPL/LGPL/AGPL/MPL/EPL/CDDL/EUPL/CeCILL 及 BSL/SSPL/Elastic/FSL/PolyForm 等 source-available),归为 permissive / 弱copyleft / 强copyleft / 网络copyleft / 源码可见非OSI 五大家族。两类用途: 为自己项目选 License、审查第三方依赖的兼容与合规。给决策树、兼容方向(谁能并入谁)、商业策略(双授权 / AGPL 防 SaaS 白嫖 / BSL 延迟开源)、近年 relicensing 案例。触发词: 开源协议、License 选哪个、MIT 还是 Apache、GPL 传染、copyleft、AGPL、协议兼容、协议冲突、依赖合规、能不能商用闭源、SaaS 白嫖、SPDX、relicensing'

argument-hint: '[要选协议的项目情况, 或待审查的依赖+其协议; 附约束如 商用/闭源/SaaS/分发方式]'
arguments: '[要选协议的项目情况, 或待审查的依赖+其协议; 附约束如 商用/闭源/SaaS/分发方式]'
---

# oss-license — 开源协议选择与合规框架

开源协议的本质是**版权许可合同**: 它规定别人拿到你的代码后能做什么、必须回报什么。选错或用错的代价不是"风格问题",而是**法律义务**——可能被迫开源闭源代码、丢掉专利防御、或踩中"无协议=保留全部权利"导致根本不可用。本 skill 把这套判断落地为可执行的选择 / 合规流程。

> ⚠️ 本 skill 提供**工程决策框架**, 不是法律意见。涉及收购、诉讼、重大商业授权时, 咨询执业律师。协议事实核对至 2026-06。

## 待分析的协议问题

$ARGUMENTS

## 核心戒律(一句话)

**先问"代码要去哪、要换回什么"——分发方式(闭源分发 / SaaS / 内部 / 库)决定义务是否触发, 协议家族决定义务有多重。** 脱离分发场景谈"哪个协议好"是空话。

## 第一动作: 分流

| 你的处境 | 走哪条 |
| --- | --- |
| 我要发布 / 开源一个**自己的**项目, 选哪个协议 | **工作流 A** |
| 我项目里**用了第三方依赖**, 担心合规 / 能否商用闭源 | **工作流 B** |
| 我想用协议做**商业护城河**(防云厂商白嫖 / 延迟开源) | A + `references/commercial.md` |
| 只想查某个具体协议的权责 / SPDX 标识 | `references/registry.md`(60+ 全表) |

## 工作流 A: 为自己项目选 License(按序)

| 步 | 动作 | 关键问题 |
| --- | --- | --- |
| 1 | **定目标** | 最大化被采用 / 要求衍生回馈 / 防商业白嫖——三选一, 决定大方向 |
| 2 | **走决策树**(见下) | 据"是否允许闭源商用"逐层收敛到具体协议 |
| 3 | **查依赖约束** | 你引入的库里若有 copyleft, **你的协议不能比它更宽松**(见工作流 B 红线) |
| 4 | **落地标识** | 加 `LICENSE` 文件 + 源文件头写 `SPDX-License-Identifier: <id>`; 包管理 `license` 字段填 SPDX |
| 5 | **多文件项目自检** | 第三方代码的原协议声明必须保留(尤其 Apache NOTICE / BSD 署名); monorepo 勿一刀切单协议, 用 REUSE 规范每文件 `SPDX-License-Identifier` 头标清来源协议 |

### 决策树(选自己项目的协议)

```
要不要允许别人闭源商用你的代码?
├─ 允许(最大化采用) → permissive
│   ├─ 企业级 / 要专利防御 ........ Apache-2.0   (有专利授权+报复终止)
│   ├─ 极简 / 小库 / 生态惯例 ...... MIT 或 ISC
│   ├─ 连署名都不强制 ............. 0BSD / Unlicense (准公有)
│   └─ 同时想兼容 GPLv2 代码 ....... Apache-2.0 OR MIT 双授权(Rust 范式)
│
├─ 要求衍生开源(copyleft) →
│   ├─ 只保护"库本身", 允许被闭源程序链接调用 .. LGPL(库级) 或 MPL-2.0(文件级)
│   ├─ 整个衍生项目都要开源 ................... GPL-3.0(反Tivo+专利) 或 GPL-2.0-or-later
│   └─ 想堵"SaaS 不分发即白嫖"漏洞 ............ AGPL-3.0(网络交互=分发)
│
└─ 不接受被白嫖, 也接受"非开源"标签 → source-available(非 OSI)
    ├─ 愿意 N 年后自动转开源 ........ BSL-1.1(默认4年) / FSL(2年, 转 MIT/Apache)
    ├─ 只想禁"托管转售竞品" ......... Elastic-2.0 / SSPL / Confluent
    └─ 模块化限制(非商业/小企业) .... PolyForm 系列
```

> 🔴 **CHECKPOINT(选定前)**: 确认三件事——(1)该协议是否 OSI 认证(决定能否标"开源", source-available **不是**开源); (2)是否与你的**已有依赖**协议冲突(见工作流 B 红线); (3)若图商业护城河, 是否已读 `references/commercial.md` 的双授权 / relicensing 反噬案例(社区 fork 风险, 如 Terraform→OpenTofu、Redis→Valkey)。

## 工作流 B: 依赖合规审查(按序)

| 步 | 动作 | 工具 / 方法 |
| --- | --- | --- |
| 1 | **列全依赖清单** | 生成 SBOM(SPDX / CycloneDX); 扫描工具 ScanCode(开源)/ FOSSA(商业) |
| 2 | **给每个依赖归家族** | 对照 `references/registry.md` 标 permissive / copyleft / network / source-available |
| 3 | **定你的分发方式** | 闭源二进制分发? SaaS? 纯内部? 静态 vs 动态链接?——这决定哪些义务触发 |
| 4 | **逐条过红线**(见下) | 命中即必须处理: 替换依赖 / 改分发方式 / 履行开源义务 / 买商业授权 |
| 5 | **持续监控** | relicensing 会让旧版合规、新版违规——锁版本 + 定期重扫(见近年案例) |

### 合规红线(命中=必须处理)

| 红线 | 后果 | 处理 |
| --- | --- | --- |
| GPL/AGPL 代码进**闭源分发**产品 | 整个产品被要求按 GPL 开源 | 换 permissive 替代 / 隔离进程 / 或接受开源 |
| **AGPL** 依赖跑成 **SaaS** 还不给源码 | 违反第 13 条网络条款 | 提供源码 / 换依赖 / 买商业授权 |
| **静态链接** LGPL 库且不让用户替换 | 触发更强义务 | 改**动态链接**, 或提供 .o 让用户重链 |
| **Apache-2.0** 与 **GPLv2** 代码混合分发 | 协议不兼容 | 找 GPLv3-or-later 版本 / 用 MIT 替代件 |
| **CDDL** 代码并入 **GPL** 项目(如 ZFS 进内核) | 不兼容 | 分发为独立模块, 不静态合并 |
| **source-available**(BSL/SSPL/Elastic)依赖被用于**竞品/转售** | 违反非竞争条款 | 读具体条款; 多数禁"作为托管服务提供" |
| 依赖**无任何 LICENSE** | 默认保留全部版权=不可合法使用 | 联系作者补协议 / 不用 |

> 兼容性方向的铁律: **permissive → copyleft 单向流入**。MIT/BSD/Apache 可被并入 GPL 项目; 反之 GPL 代码**不能**并入并仍标 permissive。完整兼容矩阵 + Apache/GPLv2 法律争议 + EUPL 附录兼容机制见 `references/compatibility.md`。

## 五大家族速查

| 家族 | 一句话 | 代表(SPDX) | 闭源商用? |
| --- | --- | --- | --- |
| **Permissive 宽松** | 几乎只要求保留声明 | `MIT` `BSD-3-Clause` `Apache-2.0` `ISC` `0BSD` | ✅ 可 |
| **弱 copyleft** | 改了的部分要开源, 其余自由 | `LGPL-3.0`(库级) `MPL-2.0`(文件级) `EPL-2.0` | ✅ 调用方可闭源 |
| **强 copyleft** | 整个衍生作品须同协议开源 | `GPL-2.0` `GPL-3.0` | ❌ 分发即传染 |
| **网络 copyleft** | 连 SaaS 也算分发 | `AGPL-3.0` | ❌ 提供服务即触发 |
| **源码可见 非OSI** | 看得到源码但**不是开源**, 有非竞争限制 | `BUSL-1.1` `SSPL-1.0` `Elastic-2.0` `FSL` | ⚠️ 看具体条款 |

每个家族的代表协议权责详解见 `references/families.md`; 全 60+ 协议带 SPDX/OSI/专利标注见 `references/registry.md`。

## 关键决策启发式

- **不确定就 Apache-2.0**(库/框架)或 **MIT**(小项目): permissive + 专利防御, 采用阻力最小。
- **想要"用我可以、白嫖不行"**: 不是选更严的开源协议, 而是 **AGPL-3.0**(仍开源)或 **双授权**(AGPL + 商业)。
- **想延迟开源 / 留窗口期**: BSL-1.1 / FSL——但**接受"现在不算开源"**, 且预期可能被社区 fork。
- **CC0 / CC-BY 用于代码 = 错**: Creative Commons 官方明确不建议, 它不处理专利。代码用 MIT/Apache/0BSD。
- **`GPL-2.0-only` vs `GPL-2.0-or-later`**: 前者锁死 v2(与 Apache-2.0、GPLv3 不兼容), 后者可升 v3 化解冲突——**默认选 or-later**。
- **依赖合规先看分发方式再看协议**: 纯内部使用几乎不触发 copyleft 义务; 一旦对外分发或 SaaS, 立刻重审。

## 失败模式(触发 → 一线修复 → 仍失败兜底)

> 与上方「合规红线」区别: 红线是**法律义务触发**, 本表是 **skill 用起来卡壳时怎么办**。

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 依赖清单拉不全(无 SBOM / 传递依赖漏) | 用 ScanCode/FOSSA 扫全树 + 锁文件反推 | 仍不全 → 标「清单不完整, 合规结论仅覆盖已知依赖」, 不给"全绿"保证 |
| 某依赖协议不在 registry / 查不到 | 查 SPDX 官方列表 + 项目 LICENSE 原文归家族 | 无任何 LICENSE 文本 → 按红线「无协议=保留全部版权」, 联系作者补协议或不用 |
| 用户说不清分发方式(闭源分发/SaaS/内部) | 🔴 STOP 用 AskUserQuestion 逐项确认——义务是否触发全看这个 | 用户仍不定 → 按**最严场景**(对外分发)给结论, 标「若仅内部使用可放宽」 |
| source-available 条款(BSL/SSPL/Elastic)读不懂 | 读 `references/commercial.md` 对应条款拆解 + 原文 | 竞争/转售边界仍模糊 → 标「非竞争条款有灰区」, 高风险场景转律师 |
| 高风险(收购/诉讼/重大授权)超工程判断 | 🔴 明确告知「本 skill 是工程框架非法律意见」, 给初判 + 风险点清单 | 用户要拍板结论 → 拒绝替法律背书, 建议执业律师, 只留决策输入 |

## 适用边界

- 本框架覆盖**软件代码协议**的工程决策; 不覆盖商标、专利申请、出口管制、数据合规(GDPR 等)。
- 协议事实(尤其 source-available 与 relicensing)**变动快**, registry 核对至 2026-06; 合规关键场景以 [opensource.org](https://opensource.org/licenses) / [spdx.org/licenses](https://spdx.org/licenses) 实时列表 + 协议原文为准。
- 跨法域的 copyleft 可执行性、"链接是否构成衍生作品"等存在法律灰区, 高风险场景须律师介入。

## 参考集(按需读)

| 文件 | 用途 |
| --- | --- |
| `references/families.md` | 五大家族 + 代表协议逐条权责详解(MIT/Apache/GPL/LGPL/AGPL/MPL/EPL/CDDL 等)、专利条款对比、静态vs动态链接 |
| `references/registry.md` | 全协议 SPDX 速查库(60+, 按家族分组, 标 OSI 认证 / 专利 / 关键限制) |
| `references/compatibility.md` | 兼容性矩阵(谁并入谁)+ 依赖合规审查流程 + Apache/GPLv2 争议 + CDDL/GPL + EUPL 附录兼容 + 工具链 |
| `references/commercial.md` | 商业策略: 双授权 / AGPL 防 SaaS 白嫖 / source-available(BSL/SSPL/Elastic/FSL)/ 近年 relicensing 案例史与 fork 反噬 |
