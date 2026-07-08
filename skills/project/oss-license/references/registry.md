# 协议速查库(SPDX 全表, 60+)

格式: `SPDX id` | 定性 | OSI 认证 | 专利条款 | 关键点
OSI 状态以 [opensource.org](https://opensource.org/licenses) 为准; 核对至 2026-06。
源文件头统一用 `SPDX-License-Identifier: <id>`。

## Permissive(宽松型, 均 OSI 认证)

| SPDX | 定性 | OSI | 专利 | 关键点 |
| --- | --- | --- | --- | --- |
| `MIT` | permissive | 是 | 无 | 最简, 保留声明 |
| `MIT-0` | permissive | 是 | 无 | MIT 去掉署名要求 |
| `BSD-2-Clause` | permissive | 是 | 无 | 保留声明 |
| `BSD-3-Clause` | permissive | 是 | 无 | + 禁名背书 |
| `BSD-4-Clause` | permissive | **否** | 无 | **含 advertising clause**(广告须署名), 与 GPL 不兼容, 依赖多则署名爆炸——**已弃用** |
| `Apache-2.0` | permissive | 是 | **有 + 报复终止** | NOTICE 须保留; 与 GPLv2 不兼容 |
| `Apache-1.1` | permissive | 是(历史) | 无 | 旧版含 advertising-style 条款, 已淘汰 |
| `ISC` | permissive | 是 | 无 | 等价 MIT, OpenBSD 默认 |
| `0BSD` | permissive(准公有) | 是 | 无 | 零条件, 无需保留声明 |
| `Zlib` | permissive | 是 | 无 | 须标注修改, 禁谎称原创 |
| `BSL-1.0` | permissive | 是 | 无 | **Boost 协议**; 勿与 Business Source License `BUSL-1.1` 混淆 |
| `Unlicense` | public-domain-equiv | 是 | 无 | 放弃版权; 法域有效性存疑 |
| `X11` | permissive | (MIT 变体) | 无 | MIT 别名/变体 |
| `PostgreSQL` | permissive | 是 | 无 | 类 BSD |
| `NCSA` | permissive | 是 | 无 | MIT+BSD 合体(LLVM 旧协议) |
| `Python-2.0` | permissive | 是 | 无 | PSF; GPL 兼容性曾有争议 |
| `curl` | permissive | (MIT 派生) | 无 | curl 专用, 类 MIT |
| `MirOS` | permissive | 是 | 无 | MirBSD 出品 |
| `Beerware` | permissive(玩笑) | 否 | 无 | "请我喝啤酒", 企业不接受 |

## 弱 / 文件级 copyleft

| SPDX | 定性 | OSI | 专利 | 关键点 |
| --- | --- | --- | --- | --- |
| `LGPL-2.1-only` / `-or-later` | weak-copyleft(库级) | 是 | 隐含 | 动态链接可闭源调用 |
| `LGPL-3.0-only` / `-or-later` | weak-copyleft | 是 | 有 | 同上 + GPLv3 专利条款 |
| `MPL-2.0` | weak-copyleft(文件级) | 是 | 有 | 改 MPL 文件须开源该文件; GPL 兼容 |
| `EPL-1.0` | weak-copyleft | 是 | 有 | 与 GPL 不兼容 |
| `EPL-2.0` | weak-copyleft | 是 | 有 | 可指定 Secondary License 实现 GPL 兼容 |
| `CDDL-1.0` / `CDDL-1.1` | weak-copyleft(逐文件) | 是 | 有 | **与 GPL 不兼容**(ZFS/Linux 案例) |
| `MS-PL` | weak-copyleft | 是 | 有 | Microsoft Public; GPL 不兼容 |
| `Artistic-2.0` | weak/permissive 混合 | 是 | — | Perl 生态 |
| `Artistic-1.0` | 弱 copyleft | 是 | — | 措辞模糊, FSF 不推荐单用 |
| `Vim` | weak-copyleft(含慈善条款) | 是 | — | 鼓励向乌干达儿童捐款, 实务弱约束 |

## 强 copyleft

| SPDX | 定性 | OSI | 专利 | 关键点 |
| --- | --- | --- | --- | --- |
| `GPL-2.0-only` | strong-copyleft | 是 | 隐含 | 锁 v2; 与 Apache-2.0 / GPLv3 不兼容 |
| `GPL-2.0-or-later` | strong-copyleft | 是 | 隐含 | 可升 v3——**默认选这个** |
| `GPL-3.0-only` / `-or-later` | strong-copyleft | 是 | 有 | 反 Tivoization + 专利条款 |
| `OSL-3.0` | strong-copyleft | 是 | 有 | 含网络分发触发; 与 GPL 不兼容 |
| `EUPL-1.2` | strong-copyleft | 是 | — | 欧盟官方, 23 语言等效, 附录兼容机制(见 compatibility.md) |
| `CECILL-2.1` | strong-copyleft | 是 | — | 法国法律框架, 显式声明 GPL 兼容 |

## 网络 copyleft

| SPDX | 定性 | OSI | 专利 | 关键点 |
| --- | --- | --- | --- | --- |
| `AGPL-3.0-only` / `-or-later` | network-copyleft | 是 | 有 | SaaS 触发开源; 防云厂商白嫖 |

## Public domain / 准公有

| SPDX | 定性 | OSI | 关键点 |
| --- | --- | --- | --- |
| `CC0-1.0` | public-domain | **否**(FSF 认可为自由, OSI 因专利免责未认证) | **不适合代码**(无专利授权) |
| `Unlicense` | public-domain-equiv | 是 | 见 permissive |
| `WTFPL` | public-domain-equiv | **否** | 无版权/责任声明, 企业不接受 |

## 文档 / 创意(不适合代码)

| SPDX | 定性 | 关键点 |
| --- | --- | --- |
| `CC-BY-4.0` | 创意-permissive | 文档/素材; 不处理专利与源码, **勿用于代码** |
| `CC-BY-SA-4.0` | 创意-copyleft | ShareAlike; 与 GPLv3 单向兼容(CC-BY-SA-4.0 → GPLv3) |
| `GFDL-1.3` | 文档-copyleft | 含"不变章节"争议条款; 勿用于代码 |
| `OFL-1.1` | 字体-copyleft | SIL Open Font License; 禁单独售卖字体文件, 嵌入文档不受限 |

## Source-available / 非 OSI(均**非开源、非自由软件**)

| SPDX | 定性 | 关键限制 |
| --- | --- | --- |
| `BUSL-1.1` | source-available | 非竞争 N 年(默认4)后转 Change License |
| `SSPL-1.0` | source-available(copyleft 变体) | 服务须开源整个管理栈 |
| `Elastic-2.0` | source-available | 禁托管服务转售 |
| `FSL-1.1-MIT` / `FSL-1.1-Apache-2.0` | source-available | 非竞争 2 年后转 MIT/Apache |
| `Confluent-Community-1.0` | source-available | 禁作为 SaaS 提供 |
| `PolyForm-Noncommercial-1.0.0` 等 | source-available 系列 | 模块化限制(非商业/小企业/防竞争) |
| (Redis) RSALv2 | source-available | 禁竞争性托管; **SPDX 无标准独立 id**, 实务标 `LicenseRef-RSAL-2.0` |
| Commons Clause | **附加条款, 非独立协议** | 包在 MIT/Apache 上加"禁销售"; 一旦附加即令原协议不再开源 |

## 矛盾 / 待核实(合规关键场景须二次核验)

1. **RSALv2 SPDX id**: 官方列表未收录独立标识, 用 `LicenseRef-` 前缀自定义。
2. **CC0 的 OSI 状态**: OSI 从未认证(专利免责条款), FSF 认可为自由——两机构口径不同, 保留矛盾。
3. **Apache-2.0/GPLv2 不兼容的法律效力**: ASF/FSF 持"不兼容", 学术界(Santa Clara 法律期刊)有异见; **业界一律按不兼容操作**。
4. 冷门协议(Vim/Beerware/MirOS 等)精确 OSI 状态以 opensource.org 实时列表为准。
