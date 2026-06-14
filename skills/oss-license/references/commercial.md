# 商业策略与 relicensing 案例史

协议是商业模式的一部分。"防白嫖"、"延迟开源"、"留商业授权口子"都靠协议设计实现。但 relicensing 既有开源项目会触发社区信任崩塌与 fork——下方案例是前车之鉴。

## 三种商业护城河手法

### 1. 双授权(Dual Licensing)
同一代码同时以 (a) copyleft 开源协议 + (b) 商业协议发布。开源用户受 copyleft 约束(衍生须开源); 不愿开源者付费买商业授权。典型: MySQL(GPL + 商业)、Qt。
- **要点**: 必须持有全部版权(或 CLA 收齐贡献者授权)才能双授权。

### 2. AGPL 防 SaaS 白嫖
GPL 仅在分发二进制时触发开源; 云厂商跑成 SaaS、不分发即可绕开。AGPL-3.0 第 13 条把"网络交互提供服务"也设为触发点, 强制 SaaS 运营方向用户提供源码——迫使竞争对手要么开源其服务栈, 要么付费买商业授权。
- **优势**: 仍是 **OSI 认证的开源协议**, 不背"非开源"骂名。
- Redis 2025、Elastic 2024 回归开源时正是选 AGPL 保留这层护城河。

### 3. Source-available 延迟 / 限制开源
接受"现在不算开源"以换商业控制:
- **BSL-1.1**: 非竞争限制, N 年后(默认 4)自动转 Change License(Apache/MPL)。
- **FSL**: BSL 简化版, 非竞争期仅 2 年, 到期转 MIT/Apache。
- **Elastic-2.0 / SSPL / Confluent**: 禁托管转售竞品。
- **代价**: 失去 OSI"开源"标签 + 极易被社区 fork(见下)。

## 近年 relicensing 案例史(年份已核实, 2026-06)

| 项目 | 时间 | 变更 | fork / 后续 |
| --- | --- | --- | --- |
| **MongoDB** | 2018-10 | AGPL-3.0 → SSPL | Debian/RHEL/Fedora 移除; OSI 审查后撤回 SSPL 申请 |
| **CockroachDB** | 2019-06 转 BSL; 2024-08 再转自有 CCL | Apache-2.0 → BSL → 取消自托管 Core(年营收 <$1000万免费) | 仍 source-available; 强制遥测争议 |
| **Elasticsearch/Kibana** | 2021-01: Apache-2.0 → SSPL+ELv2 双授权 | — | AWS fork **OpenSearch**(Apache-2.0); **2024-09 新增 AGPL-3.0**, 重回 OSI 开源 |
| **HashiCorp**(Terraform/Vault 等) | 2023-08: MPL-2.0 → BSL-1.1 | C&D 争议 | 社区 fork **OpenTofu**(Linux Foundation, MPL-2.0); **IBM 2025-02 完成收购($64 亿)** |
| **Redis** | 2024-03: BSD-3 → RSALv2+SSPL 双授权 | — | Linux Foundation fork **Valkey**(BSD-3, AWS/Google/Oracle 支持); **2025-05(Redis 8)新增 AGPL-3.0**, 成三授权, 宣布"重回开源" |
| **Sentry/Codecov** | 2023-11 转自创 FSL | — | FSL 定位 BSL 简化版, 2 年转 MIT/Apache |

**Redis 版本边界(精确)**: 7.2.x 及更早 = BSD-3; 7.4.x–7.8.x = RSALv2/SSPL 双授权; 8.0+ = RSALv2/SSPL/AGPL 三授权。

## 从案例提炼的策略教训

1. **relicensing 既有开源项目几乎必触发 fork**: Terraform→OpenTofu、Redis→Valkey、Elasticsearch→OpenSearch。云厂商有动机也有资源接盘。
2. **上线前就定策略, 别事后改**: 一开始就用 AGPL / BSL 比"开源吸引用户后再收紧"信任成本低得多。
3. **趋势是 source-available 后回摆 AGPL**: Elastic(2024)、Redis(2025)发现 SSPL/专有协议口碑代价过高, 又加回 OSI 认证的 AGPL——既防白嫖又保住"开源"标签。
4. **双授权优于单方 relicense**: 双授权从一开始给出商业口子, 不破坏既有开源承诺。
5. **想清楚护城河是不是真需要**: 多数项目不会被云厂商盯上; 过早用限制性协议反而压低采用率。先用 Apache/MIT 把生态做大, 真遇白嫖威胁再考虑 AGPL / 双授权。
