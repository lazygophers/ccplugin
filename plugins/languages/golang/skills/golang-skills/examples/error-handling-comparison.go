// ============================================================================
// GOOD EXAMPLE: 错误处理
// ============================================================================
// 说明：符合 golang-skills 错误处理规范
// 1. 多行处理错误
// 2. 记录日志
// 3. 返回原始错误（不包装）

package main

import (
    "log"
    "os"
)

func ReadConfig(path string) ([]byte, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return data, nil
}

func SaveConfig(path string, data []byte) error {
    err := os.WriteFile(path, data, 0644)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    return nil
}

// ============================================================================
// BAD EXAMPLE: 错误处理
// ============================================================================
// 说明：不符合 golang-skills 错误处理规范
// 1. 单行处理错误
// 2. 没有记录日志
// 3. 包装错误

package main

import (
    "fmt"
    "os"
)

func ReadConfig(path string) ([]byte, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read file: %w", err)
    }
    return data, nil
}

func SaveConfig(path string, data []byte) error {
    if err := os.WriteFile(path, data, 0644); err != nil {
        return err
    }
    return nil
}
