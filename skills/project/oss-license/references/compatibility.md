# 兼容性矩阵 + 依赖合规审查

## 铁律: permissive → copyleft 单向流入

MIT / BSD / Apache 代码**可被并入** GPL 项目(结果整体受 GPL 约束); 反之 GPL 代码**不能**并入并仍标 permissive。copyleft 是"只进不出"的单向阀。

## 兼容方向速查(谁能并入谁)

| 来源协议 | 能并入 → | 不能并入 ✗ |
| --- | --- | --- |
| `MIT` / `BSD-2/3` / `ISC` | 几乎所有项目(含 GPL/Apache/闭源) | — |
| `Apache-2.0` | GPLv3 项目(结果 GPLv3)、闭源、permissive | **GPLv2**(专利条款冲突) |
| `MPL-2.0` | GPL 项目(含次级许可机制)、permissive 组合 | — |
| `LGPL` | 被闭源程序**动态链接**调用 | 静态链接不让替换则违规 |
| `GPL-2.0-only` | 仅 GPLv2 项目 | Apache-2.0、GPLv3、permissive 闭源 |
| `GPL-3.0` | GPLv3 / AGPLv3 项目 | GPLv2-only、permissive 闭源 |
| `AGPL-3.0` | AGPLv3 项目 | 任何不愿开源服务端的产品 |
| `CDDL` | 独立模块分发 | **GPL 静态合并**(ZFS/Linux) |
| source-available(BSL/SSPL/Elastic) | 看具体条款; 多数禁竞品/转售 | 通常不能并入 OSI 开源项目而仍称开源 |

## 三个经典不兼容(高频踩坑)

### Apache-2.0 × GPLv2 — 不兼容
FSF 认为 Apache-2.0 的专利终止与赔偿条款, 构成 GPLv2 "no further restrictions" 禁止的额外限制。**后果**: 不能合并 Apache-2.0 与 GPLv2 代码再分发。
- **规避**: 找 `GPL-2.0-or-later` 版本(可升 GPLv3, 与 Apache 兼容); 或用 MIT 替代件; 或上游提供 `Apache-2.0 WITH LLVM-exception`(LLVM 范式)。
- **注意**: Apache-2.0 → **GPLv3 是兼容的**(单向, 结果须 GPLv3)。
- 学术界有异见认为该不兼容法律上未必成立, 但**业界一律按不兼容操作**。

### CDDL × GPL — 不兼容
CDDL 是逐文件弱 copyleft, 不允许把 CDDL 文件改授为 GPL; GPL 要求整体同协议 → 冲突。经典案例: ZFS(CDDL)不能静态合入 Linux 内核(GPLv2), 只能作为独立内核模块分发。

### EPL-1.0 × GPL — 不兼容(EPL-2.0 可解)
EPL-2.0 可声明 "Secondary License" 实现 GPL 兼容; EPL-1.0 不行。

## EUPL-1.2 的附录兼容机制(特例)

EUPL-1.2 当并入更大作品时, 可改用 Article 5 **附录所列兼容协议**分发, 化解冲突。附录含: GPL-2.0/3.0、AGPL-3.0、OSL-2.1/3.0、EPL-1.0、CeCILL-2.0/2.1、MPL-2.0、LGPL-2.1/3.0、CC-BY-SA-3.0(仅非软件)、EUPL-1.1/1.2、LiLiQ-R/R+。欧盟委员会可不发新版即更新附录。目的是**解决冲突而非背书**, 故只收 copyleft, 不收最宽松协议。

## 依赖合规审查流程(工作流 B 展开)

1. **生成 SBOM**: SPDX 或 CycloneDX 格式的软件物料清单。
2. **扫描协议**: ScanCode Toolkit(开源)/ FOSSA(商业)自动识别每个依赖的协议。
3. **归家族**: 对照 `registry.md` 标注 permissive / copyleft / network / source-available。
4. **定分发方式**(决定义务是否触发):
   - 纯内部使用(不对外分发)→ copyleft 义务几乎不触发。
   - 闭源二进制分发 → GPL/AGPL 依赖触发整体开源 = 红线。
   - SaaS → AGPL 依赖触发(第 13 条)。
   - 链接 LGPL → 区分静态/动态。
5. **过红线**(见 SKILL.md 合规红线表)→ 替换 / 隔离 / 履行义务 / 买授权。
6. **持续监控**: relicensing 会让新版本违规。锁版本 + 定期重扫 + 订阅上游协议变更。

## 工具与标准

| 工具/标准 | 用途 |
| --- | --- |
| **SPDX**(spdx.org/licenses) | 机器可读协议标识; 源文件头 `SPDX-License-Identifier:` |
| **OSI**(opensource.org) | "开源"权威定义(OSD 10 条); 唯一权威认证机构 |
| **choosealicense.com** | GitHub 维护的选协议向导(面向"为自己项目选") |
| **REUSE 规范**(reuse.software) | 每文件 SPDX 头 + LICENSES/ 目录; `reuse lint` 校验。monorepo / 多来源项目必备 |
| **SBOM**(SPDX / CycloneDX) | 依赖与协议合规审计清单 |
| **ScanCode**(开源)/ **FOSSA**(商业) | 依赖协议扫描 |
