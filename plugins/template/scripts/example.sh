#!/usr/bin/env bash
#
# 示例 Bash 脚本
#
# 用于系统操作、文件处理、快速脚本等场景。
#

set -euo pipefail  # 严格模式

# 获取插件根目录
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        log_error "缺少参数"
        echo "Usage: example.sh <command> [args...]"
        echo ""
        echo "命令:"
        echo "  process <file>  处理文件"
        echo "  check <path>    检查路径"
        echo "  status          显示状态"
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        process)
            process_file "$@"
            ;;
        check)
            check_path "$@"
            ;;
        status)
            show_status
            ;;
        *)
            log_error "未知命令: $command"
            exit 1
            ;;
    esac
}

# 处理文件
process_file() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        log_error "文件不存在: $file"
        exit 1
    fi

    log_info "处理文件: $file"

    # 示例：复制文件
    local backup="${file}.backup"
    cp "$file" "$backup"
    log_info "已创建备份: $backup"

    # 示例：行数统计
    local lines
    lines=$(wc -l < "$file")
    log_info "文件行数: $lines"
}

# 检查路径
check_path() {
    local path="$1"

    if [[ -e "$path" ]]; then
        log_info "路径存在: $path"

        if [[ -f "$path" ]]; then
            log_info "类型: 文件"
            log_info "大小: $(stat -f%z "$path" 2>/dev/null || stat -c%s "$path") 字节"
        elif [[ -d "$path" ]]; then
            log_info "类型: 目录"
            log_info "项目数: $(find "$path" -maxdepth 1 | wc -l)"
        fi
    else
        log_error "路径不存在: $path"
        exit 1
    fi
}

# 显示状态
show_status() {
    log_info "插件根目录: $PLUGIN_ROOT"

    # 检查必要文件
    local required_files=(".claude-plugin/plugin.json")
    for file in "${required_files[@]}"; do
        local full_path="$PLUGIN_ROOT/$file"
        if [[ -f "$full_path" ]]; then
            log_info "✓ $file"
        else
            log_warn "✗ $file (缺失)"
        fi
    done

    # 系统信息
    log_info "系统: $(uname -s)"
    log_info "架构: $(uname -m)"
    log_info "Shell: $SHELL"
}

# 执行主函数
main "$@"
