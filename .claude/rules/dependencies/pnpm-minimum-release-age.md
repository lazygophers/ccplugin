# pnpm minimumReleaseAge：未满 24h 的新版本默认拒装，豁免条目带理由、观察期后移除

skein 前端的 pnpm 供应链策略：发布未满 24h 的包默认拒装（实测报
`ERR_PNPM_MINIMUM_RELEASE_AGE_VIOLATION`）。升级刚发布的版本时，在
plugins/tools/skein/assets/nextjs/pnpm-workspace.yaml 的
`minimumReleaseAgeExclude` 按精确 `包名@版本` 豁免；每条豁免是临时放行不是
配置摆设，堆积会让策略形同虚设。

- 豁免条目写精确版本（`next@16.4.3` 这种，不写裸包名）；同包全家桶（@next/swc-*
  各平台、@next/env、eslint-config-next）每条单独列。
- 观察期（一两周）过后、包龄超 24h 时删掉豁免条目，再跑 `pnpm install` 验证
  无感。

2026-10-25 session 为装 next@16.4.3 豁免了 12 条，尚无移除记录——下次触碰该
文件时先核对哪些包龄已超 24h，顺手清。

出处：2026-10-25 skein dependabot 全清 session。
