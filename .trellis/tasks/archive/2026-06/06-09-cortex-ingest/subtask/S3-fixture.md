---
id: S3
slug: fixture
deliverable: D7
parent-task: 06-09-cortex-ingest
status: planned
execution-layer: main
depends-on: []
blocks: [S5]
estimated-tokens: 2000
---

# S3 · 建 fixture

## 产出

```
tests/fixtures/ingest/
├── inputs.txt
├── local-no-git/
│   └── README.md
└── local-with-git-remote/
    ├── README.md
    └── .git/
        └── config
```

`inputs.txt`:
```
https://github.com/lazygophers/ccplugin
https://gitlab.com/gitlab-org/gitlab
https://docs.python.org/3/library/argparse.html
git@github.com:tokio-rs/tokio.git
plugins/tools/cortex/tests/fixtures/ingest/local-no-git
plugins/tools/cortex/tests/fixtures/ingest/local-with-git-remote
```

`local-with-git-remote/.git/config`:
```ini
[remote "origin"]
    url = https://github.com/foo/bar.git
    fetch = +refs/heads/*:refs/remotes/origin/*
```

## 验证

```bash
test -f plugins/tools/cortex/tests/fixtures/ingest/inputs.txt
test -d plugins/tools/cortex/tests/fixtures/ingest/local-no-git
test -d plugins/tools/cortex/tests/fixtures/ingest/local-with-git-remote/.git
grep -q 'github.com/foo/bar' plugins/tools/cortex/tests/fixtures/ingest/local-with-git-remote/.git/config
```

## 执行细节

main 直接 mkdir + write fixture 文件. 无需 sub-agent.

## 回滚
```bash
rm -rf plugins/tools/cortex/tests/fixtures/ingest/
```
