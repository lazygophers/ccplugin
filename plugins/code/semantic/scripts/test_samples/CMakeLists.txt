# CMake 测试文件

cmake_minimum_required(VERSION 3.10)

# 项目定义
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)

# 函数定义
function(add_custom_target target_name)
    add_executable(${target_name} main.cpp)
    target_link_libraries(${target_name} PRIVATE utils)
endfunction()

# 宏定义
macro(configure_output output_dir)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${output_dir})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${output_dir})
endmacro()

# 创建库
add_library(utils STATIC utils.cpp)

# 创建可执行文件
add_executable(app main.cpp)

# 链接库
target_link_libraries(app PRIVATE utils)

# 包含目录
target_include_directories(app PRIVATE ${CMAKE_SOURCE_DIR}/include)

# 编译选项
target_compile_options(app PRIVATE -Wall -Wextra)

# 配置输出
configure_output(${CMAKE_BINARY_DIR}/bin)

# 添加自定义目标
add_custom_target(custom_app)
