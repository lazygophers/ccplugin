package examples

import (
	"errors"
	"fmt"
	"log"
	"os"
)

// ValidationError 自定义验证错误
type ValidationError struct {
	Field   string
	Message string
}

// Error 实现 error 接口
func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation error in field %q: %s", e.Field, e.Message)
}

// Unwrap 支持错误链（Go 1.13+）
func (e *ValidationError) Unwrap() error {
	return nil
}

// NotFoundError 自定义未找到错误
type NotFoundError struct {
	Resource string
	ID       interface{}
}

// Error 实现 error 接口
func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s with id %v not found", e.Resource, e.ID)
}

// ✅ 示例 1：基本错误处理
func ExampleBasicErrorHandling() error {
	// 读取文件
	data, err := os.ReadFile("config.json")
	if err != nil {
		// ✅ 正确：多行处理 + 日志 + 错误包装
		log.Printf("err:%v", err)
		return fmt.Errorf("read config file: %w", err)
	}

	// 处理数据
	_ = data
	return nil
}

// ✅ 示例 2：错误类型判断
func ExampleErrorTypeChecking(id int64) (*User, error) {
	// 模拟读取用户
	if id == 0 {
		// 使用自定义错误类型
		return nil, &NotFoundError{
			Resource: "user",
			ID:       id,
		}
	}

	// 模拟验证错误
	if id < 0 {
		return nil, &ValidationError{
			Field:   "user_id",
			Message: "user id must be positive",
		}
	}

	// 成功返回
	return &User{ID: id}, nil
}

// ✅ 示例 3：错误检查和处理
func ExampleErrorHandlingPattern(id int64) error {
	// 获取用户
	user, err := ExampleErrorTypeChecking(id)
	if err != nil {
		// 使用 errors.Is 检查特定错误
		var notFoundErr *NotFoundError
		if errors.As(err, &notFoundErr) {
			log.Printf("resource not found: %s", notFoundErr.Error())
			return fmt.Errorf("user not found: %w", err)
		}

		// 使用 errors.Is 检查错误值
		if errors.Is(err, os.ErrNotExist) {
			log.Printf("err:%v", err)
			return fmt.Errorf("file not found: %w", err)
		}

		// 通用错误处理
		log.Printf("err:%v", err)
		return fmt.Errorf("operation failed: %w", err)
	}

	_ = user
	return nil
}

// ✅ 示例 4：Defer 和错误处理
func ExampleDeferErrorHandling() error {
	// 打开文件
	file, err := os.Open("data.txt")
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("open file: %w", err)
	}

	// ✅ 简单关闭不检查错误
	defer file.Close()

	// 处理文件...
	return nil
}

// ✅ 示例 5：复杂的 Defer 错误处理
func ExampleComplexDeferErrorHandling() error {
	// 打开文件
	file, err := os.Open("data.txt")
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("open file: %w", err)
	}

	// ✅ 复杂操作才在 defer 中检查错误
	defer func() {
		if err := file.Close(); err != nil {
			log.Printf("err:%v", err)
		}
	}()

	// 处理文件...
	return nil
}

// ✅ 示例 6：多步骤操作的错误处理
func ExampleMultiStepErrorHandling() error {
	// 步骤 1：打开文件
	file, err := os.Open("config.json")
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("step 1 - open file: %w", err)
	}
	defer file.Close()

	// 步骤 2：读取数据
	data := make([]byte, 1024)
	n, err := file.Read(data)
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("step 2 - read file: %w", err)
	}

	// 步骤 3：处理数据
	if n == 0 {
		return fmt.Errorf("step 3 - empty file")
	}

	return nil
}

// ✅ 示例 7：初始化中的错误处理
func ExampleInitializationErrorHandling() error {
	// 在初始化中加载配置
	configData, err := os.ReadFile("config.json")
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("load config: %w", err)
	}

	if len(configData) == 0 {
		log.Printf("err:%v", errors.New("empty config"))
		return fmt.Errorf("parse config: invalid format")
	}

	return nil
}

// ✅ 示例 8：错误信息上下文
func ExampleErrorContextHandling(userID int64, filePath string) error {
	// 包含上下文信息的错误处理
	file, err := os.Open(filePath)
	if err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("load user config (user_id=%d, path=%q): %w", userID, filePath, err)
	}
	defer file.Close()

	return nil
}

// ❌ 反面例子 - 应该避免的模式

// ❌ 错误 1：忽略错误
func ExampleWrongIgnoreError() {
	// ❌ 不要这样做
	_ = os.ReadFile("config.json")
	// 错误被忽略了！
}

// ❌ 错误 2：单行 if 处理
func ExampleWrongOneLineError() error {
	data, err := os.ReadFile("config.json")
	// ❌ 不要这样做
	if err != nil { return err }

	_ = data
	return nil
}

// ❌ 错误 3：多次包装错误
func ExampleWrongDoubleWrap() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		// ❌ 不要这样做 - 错误被包装两次
		return fmt.Errorf("load: %w", fmt.Errorf("read file: %w", err))
	}

	_ = data
	return nil
}

// ❌ 错误 4：丢失原始错误
func ExampleWrongLoseError() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		// ❌ 不要这样做 - 原始错误信息丢失
		return fmt.Errorf("something went wrong")
	}

	_ = data
	return nil
}

// ❌ 错误 5：无日志的错误返回
func ExampleWrongNoLog() error {
	data, err := os.ReadFile("config.json")
	if err != nil {
		// ❌ 不要这样做 - 没有日志记录
		return err
	}

	_ = data
	return nil
}
