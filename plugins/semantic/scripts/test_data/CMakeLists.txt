# CMake 测试文件 - 包含项目、库、目标、自定义命令

cmake_minimum_required(VERSION 3.15)

# 项目定义
project(SemanticSearch
    VERSION 1.0.0
    DESCRIPTION "Semantic Search Application"
    LANGUAGES C CXX
)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找依赖包
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)

# 包含目录
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

# 源文件
set(SOURCES
    src/main.cpp
    src/user.cpp
    src/session.cpp
    src/database.cpp
)

set(HEADERS
    include/user.h
    include/session.h
    include/database.h
)

# 可执行文件目标
add_executable(semantic_search ${SOURCES} ${HEADERS})

# 链接库
target_link_libraries(semantic_search
    PRIVATE
        Threads::Threads
        OpenSSL::SSL
        OpenSSL::Crypto
)

# 编译定义
target_compile_definitions(semantic_search PRIVATE
    VERSION="${PROJECT_VERSION}"
    BUILD_DATE="${CURRENT_DATE}"
)

# 用户库
add_library(user_lib STATIC
    src/user.cpp
    include/user.h
)

target_link_libraries(user_lib PUBLIC
    Threads::Threads
)

# 会话库
add_library(session_lib SHARED
    src/session.cpp
    include/session.h
)

target_link_libraries(session_lib PUBLIC
    user_lib
)

# 数据库库
add_library(database_lib INTERFACE
    include/database.h
)

target_include_directories(database_lib INTERFACE
    ${CMAKE_SOURCE_DIR}/include
)

# 自定义命令 - 生成版本信息
add_custom_command(
    OUTPUT version_info.cpp
    COMMAND ${CMAKE_COMMAND}
        -DPROJECT_VERSION=${PROJECT_VERSION}
        -DPROJECT_NAME=${PROJECT_NAME}
        -P ${CMAKE_SOURCE_DIR}/cmake/GenerateVersion.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/version_info.cpp
    DEPENDS ${CMAKE_SOURCE_DIR}/cmake/GenerateVersion.cmake
    COMMENT "Generating version info"
)

# 自定义目标 - 格式化代码
add_custom_target(format
    COMMAND clang-format -i ${SOURCES} ${HEADERS}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Formatting source code"
)

# 自定义目标 - 运行测试
enable_testing()
add_custom_target(run_tests
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
    DEPENDS semantic_search
    COMMENT "Running tests"
)

add_test(NAME user_test COMMAND user_test)
add_test(NAME session_test COMMAND session_test)

# 安装规则
install(TARGETS semantic_search
    RUNTIME DESTINATION bin
)

install(TARGETS user_lib session_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include
)

# 配置文件
configure_file(
    ${CMAKE_SOURCE_DIR}/config/config.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/config/config.h
)

# 子目录
add_subdirectory(tests)
add_subdirectory(docs)

# 选项定义
option(BUILD_TESTS "Build tests" ON)
option(BUILD_DOCS "Build documentation" ON)
option(ENABLE_PROFILING "Enable profiling" OFF)

if(ENABLE_PROFILING)
    target_compile_definitions(semantic_search PRIVATE ENABLE_PROFILING)
endif()

# 导出目标
install(EXPORT semantic_search_targets
    FILE semantic_search_targets.cmake
    NAMESPACE semantic_search::
    DESTINATION lib/cmake/semantic_search
)

# 创建配置文件
include(CMakePackageConfigHelpers)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/semantic_search-config-version.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(
    "${CMAKE_SOURCE_DIR}/cmake/semantic_search-config.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/semantic_search-config.cmake"
    INSTALL_DESTINATION lib/cmake/semantic_search
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/semantic_search-config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/semantic_search-config-version.cmake"
    DESTINATION lib/cmake/semantic_search
)

# CPack 配置
set(CPACK_PACKAGE_NAME ${PROJECT_NAME})
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY ${PROJECT_DESCRIPTION})
set(CPACK_PACKAGE_VENDOR "YourCompany")

include(CPack)
