# Make 测试文件 - 包含变量、规则、模式、函数

# 项目信息
PROJECT := semantic_search
VERSION := 1.0.0
DESCRIPTION := Semantic Search Application

# 目录
SRC_DIR := src
INCLUDE_DIR := include
BUILD_DIR := build
BIN_DIR := bin
TEST_DIR := tests
DOC_DIR := docs

# 编译器
CC := gcc
CXX := g++
CFLAGS := -Wall -Wextra -std=c11 -I$(INCLUDE_DIR)
CXXFLAGS := -Wall -Wextra -std=c++17 -I$(INCLUDE_DIR)
LDFLAGS := -lpthread -lssl -lcrypto

# 源文件
SOURCES := $(shell find $(SRC_DIR) -name '*.cpp')
HEADERS := $(shell find $(INCLUDE_DIR) -name '*.h')
OBJECTS := $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/%.o,$(SOURCES))

# 主程序
TARGET := $(BIN_DIR)/$(PROJECT)

# 测试程序
TEST_SOURCES := $(shell find $(TEST_DIR) -name '*.cpp')
TEST_OBJECTS := $(patsubst $(TEST_DIR)/%.cpp,$(BUILD_DIR)/test/%.o,$(TEST_SOURCES))
TEST_TARGET := $(BIN_DIR)/run_tests

# 颜色输出
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m

# 默认目标
.PHONY: all
all: $(TARGET)

# 创建目录
$(BUILD_DIR) $(BIN_DIR):
	@mkdir -p $@

# 链接主程序
$(TARGET): $(OBJECTS) | $(BIN_DIR)
	@echo "$(COLOR_BLUE)[LINK]$(COLOR_RESET) $@"
	$(CXX) $(OBJECTS) -o $@ $(LDFLAGS)

# 编译源文件
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	@echo "$(COLOR_GREEN)[CC]$(COLOR_RESET) $<"
	$(CXX) $(CXXFLAGS) -c $< -o $@

# 编译测试文件
$(BUILD_DIR)/test/%.o: $(TEST_DIR)/%.cpp | $(BUILD_DIR)
	@echo "$(COLOR_GREEN)[TEST CC]$(COLOR_RESET) $<"
	$(CXX) $(CXXFLAGS) -c $< -o $@

# 链接测试程序
$(TEST_TARGET): $(TEST_OBJECTS) $(filter-out $(BUILD_DIR)/main.o,$(OBJECTS)) | $(BIN_DIR)
	@echo "$(COLOR_BLUE)[LINK TEST]$(COLOR_RESET) $@"
	$(CXX) $^ -o $@ $(LDFLAGS)

# 模式规则：编译 C 文件
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@echo "$(COLOR_GREEN)[CC]$(COLOR_RESET) $<"
	$(CC) $(CFLAGS) -c $< -o $@

# 自动依赖生成
-include $(OBJECTS:.o=.d)

$(BUILD_DIR)/%.d: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	@$(CXX) $(CXXFLAGS) -MM -MT $(BUILD_DIR)/%.o $< > $@

# 清理
.PHONY: clean
clean:
	@echo "$(COLOR_YELLOW)[CLEAN]$(COLOR_RESET) Removing build artifacts"
	rm -rf $(BUILD_DIR) $(BIN_DIR)

# 清理所有（包括文档）
.PHONY: cleanall
cleanall: clean
	@echo "$(COLOR_YELLOW)[CLEAN]$(COLOR_RESET) Removing documentation"
	rm -rf $(DOC_DIR)/html

# 运行
.PHONY: run
run: $(TARGET)
	@echo "$(COLOR_BOLD)Running $(PROJECT) $(VERSION)$(COLOR_RESET)"
	$(TARGET)

# 测试
.PHONY: test
test: $(TEST_TARGET)
	@echo "$(COLOR_BOLD)Running tests$(COLOR_RESET)"
	$(TEST_TARGET)

# 调试版本
.PHONY: debug
debug: CXXFLAGS += -g -O0 -DDEBUG
debug: $(TARGET)

# 发布版本
.PHONY: release
release: CXXFLAGS += -O3 -DNDEBUG
release: $(TARGET)

# 格式化代码
.PHONY: format
format:
	@echo "$(COLOR_YELLOW)[FORMAT]$(COLOR_RESET) Formatting source code"
	clang-format -i $(SOURCES) $(HEADERS)

# 静态分析
.PHONY: analyze
analyze:
	@echo "$(COLOR_YELLOW)[ANALYZE]$(COLOR_RESET) Running static analysis"
	cppcheck --enable=all --suppress=missingIncludeSystem $(SRC_DIR)

# 内存检查
.PHONY: memcheck
memcheck: $(TARGET)
	@echo "$(COLOR_YELLOW)[MEMCHECK]$(COLOR_RESET) Running memory check"
	valgrind --leak-check=full --show-leak-kinds=all $(TARGET)

# 性能分析
.PHONY: profile
profile: CXXFLAGS += -pg
profile: LDFLAGS += -pg
profile: clean $(TARGET)
	@echo "$(COLOR_YELLOW)[PROFILE]$(COLOR_RESET) Running profiler"
	$(TARGET)
	gprof $(TARGET) gmon.out > $(DOC_DIR)/profile.txt

# 文档
.PHONY: docs
docs:
	@echo "$(COLOR_YELLOW)[DOCS]$(COLOR_RESET) Generating documentation"
	doxygen Doxyfile

# 安装
.PHONY: install
install: $(TARGET)
	@echo "$(COLOR_YELLOW)[INSTALL]$(COLOR_RESET) Installing $(PROJECT)"
	install -d $(DESTDIR)/usr/local/bin
	install -m 755 $(TARGET) $(DESTDIR)/usr/local/bin/$(PROJECT)

# 卸载
.PHONY: uninstall
uninstall:
	@echo "$(COLOR_YELLOW)[UNINSTALL]$(COLOR_RESET) Uninstalling $(PROJECT)"
	rm -f $(DESTDIR)/usr/local/bin/$(PROJECT)

# 打包
.PHONY: package
package: clean
	@echo "$(COLOR_YELLOW)[PACKAGE]$(COLOR_RESET) Creating distribution package"
	tar czf $(PROJECT)-$(VERSION).tar.gz \
		--exclude=$(BUILD_DIR) \
		--exclude=$(BIN_DIR) \
		--exclude=.git \
		.

# 依赖检查
.PHONY: deps
deps:
	@echo "$(COLOR_YELLOW)[DEPS]$(COLOR_RESET) Checking dependencies"
	@command -v $(CC) >/dev/null 2>&1 || echo "$(COLOR_BOLD)Missing: $(CC)$(COLOR_RESET)"
	@command -v $(CXX) >/dev/null 2>&1 || echo "$(COLOR_BOLD)Missing: $(CXX)$(COLOR_RESET)"
	@command -v clang-format >/dev/null 2>&1 || echo "$(COLOR_BOLD)Missing: clang-format$(COLOR_RESET)"

# 显示帮助
.PHONY: help
help:
	@echo "$(COLOR_BOLD)$(PROJECT) $(VERSION) - $(DESCRIPTION)$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Available targets:$(COLOR_RESET)"
	@echo "  all       - Build the project (default)"
	@echo "  clean     - Remove build artifacts"
	@echo "  cleanall  - Remove everything including docs"
	@echo "  run       - Build and run the program"
	@echo "  test      - Build and run tests"
	@echo "  debug     - Build debug version"
	@echo "  release   - Build release version"
	@echo "  format    - Format source code"
	@echo "  analyze   - Run static analysis"
	@echo "  memcheck  - Run memory checker"
	@echo "  profile   - Run profiler"
	@echo "  docs      - Generate documentation"
	@echo "  install   - Install the program"
	@echo "  uninstall - Uninstall the program"
	@echo "  package   - Create distribution package"
	@echo "  deps      - Check dependencies"
	@echo "  help      - Show this help message"

# 显示变量（调试用）
.PHONY: vars
vars:
	@echo "SOURCES = $(SOURCES)"
	@echo "OBJECTS = $(OBJECTS)"
	@echo "HEADERS = $(HEADERS)"
	@echo "CXXFLAGS = $(CXXFLAGS)"
	@echo "LDFLAGS = $(LDFLAGS)"
