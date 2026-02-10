---
name: new
description: 开发新的插件
argument-hint: <需求内容>
---

接下来请转处于处理 `$ARGUMENTS` 的插件开发

1. 切换到 plan 模式，确认需求的详细内容，生成完整的需求说明和开发说明
	1. 如果有不明确的地方，通过 `AskUserQuestion` 询问用户，以获取详细信息
	2. 询问用户前，要先确认当前的现状（代码、文档、常用方案、最佳实践等），可以通过 deep-research/explore 获取
	3. 要尽可能细致的拆分需求，以及不同的需求需要的 skills、agents
	4. 优先使用 agents 完成任务而非直接执行
		1. 开发插件使用 Agents(agent-creator) 或 Agents(plugin)
		2. 开发命令使用 Agents(command)
		3. 编写 Skills 使用 Agents(skill-reviewer) 或 Agents(skill)
		4. 开发 MCP 服务器使用 Agents(mcp)
		5. 开发 LSP 配置使用 Agents(lsp)
		6. 开发 Hooks 使用 Agents(hook)
		7. 开发代理文档使用 Agents(agent)
		8. 开发脚本使用 Agents(script)
2. 根据上述规划的内容，以此执行，但是注意，并行执行的任务不可以超过 2 个，如果超过了，则应该等待其中一个完成后才可以进行下一个任务的启动
3. 完善测试，确保测试通过率为 100%，提高测试覆盖率尽可能的达到 95% 以上
4. 检查所有变更，检查是否有任何不符合规范的内容
5. 完成后，通过 Agents(plugin-validator) 检查

注意：

1. 严格遵守且及时的更新 llms.txt 和 @.claude/skills/
2. 新增的内容必须和原有的代码风格一致
3. 使用 /deep-research 深度研究以确保编写的内容正确、及时、更新、完善
4. 可以使用 chrome 操作浏览器进行网络搜索等操作以获取最新、最准确的数据
5. 如果是新增插件，需要将新增的插件注册到 @.claude-plugin/marketplace.json 中
6. 确保每一个文件的内容都简洁、清晰，并且没有多余的空行和空格
   1. `*.go` 推荐 200～500 行，最大长度 800 行
   2. `*.md` 推荐 100～200 行，最大长度 500 行
   3. `*.py` 推荐 200～500 行，最大长度 800 行