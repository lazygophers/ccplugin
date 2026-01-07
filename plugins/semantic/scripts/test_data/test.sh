#!/bin/bash
# Bash 测试脚本 - 包含函数、数组、条件判断

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"
LOG_FILE="${SCRIPT_DIR}/app.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
}

# 用户创建函数
create_user() {
    local id=$1
    local name=$2
    local email=$3

    if [[ -z "${id}" || -z "${name}" || -z "${email}" ]]; then
        log "ERROR" "Missing required parameters"
        return 1
    fi

    log "INFO" "Creating user: ${name} (${email})"
    echo "User created: ID=${id}, Name=${name}, Email=${email}"
}

# 用户认证函数
authenticate() {
    local username=$1
    local password=$2

    if [[ -z "${password}" ]]; then
        log "ERROR" "Password cannot be empty"
        return 1
    fi

    # 模拟认证逻辑
    if [[ "${username}" == "admin" && "${password}" == "secret" ]]; then
        log "INFO" "User ${username} authenticated successfully"
        return 0
    else
        log "WARNING" "Authentication failed for user ${username}"
        return 1
    fi
}

# 会话创建函数
create_session() {
    local user_id=$1
    local session_file="${SCRIPT_DIR}/sessions/${user_id}.session"

    if [[ ! -d "${SCRIPT_DIR}/sessions" ]]; then
        mkdir -p "${SCRIPT_DIR}/sessions"
    fi

    local timestamp=$(date +%s)
    echo "${user_id}|${timestamp}" > "${session_file}"

    log "INFO" "Session created for user: ${user_id}"
    echo "Session created: ${session_file}"
}

# 检查会话有效性
is_session_valid() {
    local user_id=$1
    local session_file="${SCRIPT_DIR}/sessions/${user_id}.session"

    if [[ ! -f "${session_file}" ]]; then
        return 1
    fi

    local session_content=$(cat "${session_file}")
    local session_time=$(echo "${session_content}" | cut -d'|' -f2)
    local current_time=$(date +%s)
    local elapsed=$((current_time - session_time))

    # 会话有效期 24 小时 (86400 秒)
    if [[ ${elapsed} -lt 86400 ]]; then
        return 0
    else
        return 1
    fi
}

# 数组处理示例
process_users() {
    local users=(
        "1:Alice:alice@example.com"
        "2:Bob:bob@example.com"
        "3:Charlie:charlie@example.com"
    )

    for user_info in "${users[@]}"; do
        IFS=':' read -r id name email <<< "${user_info}"
        create_user "${id}" "${name}" "${email}"
    done
}

# 循环示例
print_menu() {
    local options=("Create User" "Authenticate" "Create Session" "Exit")
    local i=1

    echo "Menu:"
    for option in "${options[@]}"; do
        echo "  ${i}. ${option}"
        ((i++))
    done
}

# 错误处理
error_handler() {
    local line_number=$1
    log "ERROR" "Error on line ${line_number}"
    echo -e "${RED}Error occurred at line ${line_number}${NC}"
}

trap 'error_handler ${LINENO}' ERR

# 主函数
main() {
    log "INFO" "Application started"

    # 创建测试用户
    create_user 1 "Alice" "alice@example.com"
    create_user 2 "Bob" "bob@example.com"

    # 测试认证
    if authenticate "admin" "secret"; then
        echo -e "${GREEN}Authentication successful${NC}"
        create_session 1
    else
        echo -e "${RED}Authentication failed${NC}"
    fi

    # 检查会话
    if is_session_valid 1; then
        echo -e "${GREEN}Session is valid${NC}"
    else
        echo -e "${YELLOW}Session is invalid or expired${NC}"
    fi

    log "INFO" "Application finished"
}

# 执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
