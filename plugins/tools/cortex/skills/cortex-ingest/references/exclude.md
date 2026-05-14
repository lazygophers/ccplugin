# cortex-ingest — 强制排除清单

> SKILL.md §8 (强制排除清单) 的详细规范。ingest 前 `find` 列树 + 算 R 必须先剔除以下。

---

## 8. 强制排除清单 (build file tree 前先 prune)

ingest 前 `find` 列树 + 算 R **必须**剔除以下:

| 类别 | 模式 |
|------|------|
| 构建产物 | `node_modules/` `vendor/` `dist/` `build/` `__pycache__/` `target/` `.next/` `.nuxt/` `out/` `.cache/` |
| Lock 文件 | `package-lock.json` `yarn.lock` `pnpm-lock.yaml` `go.sum` `Cargo.lock` `Pipfile.lock` `poetry.lock` `*.lock` |
| 二进制资源 | `*.{png,jpg,jpeg,gif,webp,svg,ico,mp4,mov,avi,mp3,wav,ttf,woff,woff2,eot,otf}`; `*.pdf` 除非在 `docs/` |
| 系统 / IDE | `.git/` `.venv/` `.env/` `.idea/` `.vscode/` `.DS_Store` `__MACOSX/` `Thumbs.db` |
| 临时 / 备份 | `*.{bak,swp,tmp,old,orig,backup,~}` `*.swp.*` `.vscode-test/` |
| 压缩包 | `*.{zip,tar,gz,tgz,xz,bz2,rar,7z}` |

参考 `references/extract.md` §4.7 的 `find ... -not -path ... -not -name ...` 已落实该清单; self-check 计 R 时**先剔除以上**再算 `M / R ≥ 0.8`。原始 `find <repo> -type f | wc -l` (不 prune) 仅作 raw size 报告, **不作为下限判定基数**。
