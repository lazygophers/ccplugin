.PHONY: integration-test integration-up integration-down

# SKEIN 前后端 docker-compose 集成测试 (单容器真实形态: uvicorn serve + dist 前端)
# 覆盖: API 全链路生命周期 / confirm·design-save·config-hooks 守门 / WS 热重载 / Playwright UI
integration-test:
	@plugins/tools/skein/integration/run.sh

# 手动调试: 只起环境不跑测试, 浏览器开 http://127.0.0.1:8841
integration-up:
	@cd plugins/tools/skein/integration && docker compose up -d --build --wait

integration-down:
	@cd plugins/tools/skein/integration && docker compose down -v
