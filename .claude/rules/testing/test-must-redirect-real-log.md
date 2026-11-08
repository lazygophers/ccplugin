# 给真实日志/真实路径加写入，测试必须同时重定向；用前后行数不变验收

ask-me 错误日志改写 `/tmp/ask-me.log` 后，首轮 11 个 `test-*.mts` 故意制造的错误
全写进真实日志（34 条 error 大多是测试噪音），靠主对话统计 `where` 字段才发现，
第二轮才在 self-test 设 `ASK_ME_LOG` 修掉。

- 新增对真实路径（日志、缓存、`/tmp/<skill>.*`）的写入时，同一改动里让所有测试入口
  （self-test、各 test-*.mts、pytest）把该路径重定向到临时文件（环境变量或参数）。
- 验收：跑测试前后各数一次真实日志行数（`wc -l`），必须不变。

出处：.scratch/memory/2026-11-09.md ask-me 错误日志 session。
