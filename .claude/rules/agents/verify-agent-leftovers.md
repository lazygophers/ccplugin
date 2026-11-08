# agent 回报的「遗留问题」先 grep 核实再转述

agent 回报的遗留项可能是误判。2026-11-09 session 中 agent 报「previousLog 为 undefined
被写成字符串」，主对话 grep 核实不成立（`skills/tools/ask-me/scripts/self-test.mts:45/152`
已先赋值）。转述给用户前，对每条遗留项用 grep / 读代码确认成立，不成立的丢掉并说明。

出处：2026-11-09 ask-me 错误日志 session。
