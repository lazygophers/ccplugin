---
name: lrpc-cryptox
description: lazygophers/utils cryptox 模块深度解析 - Go 语言加密算法库，提供对称加密、非对称加密、哈希算法、数字签名和密钥交换等完整的密码学功能
---

# lrpc-cryptox: lazygophers/utils cryptox 模块完整指南

## 概述

**cryptox** 是 lazygophers/utils 项目中的加密模块，提供了全面的密码学功能支持。与 Go 标准库的 crypto 包相比，cryptox 提供了更简洁的 API、更完善的错误处理、以及对常用加密模式的封装。

### 与 lazygophers/crypto 的区别

- **lazygophers/cryptox** (utils 仓库): 本模块，提供完整的加密、解密、哈希、签名等密码学功能
- **lazygophers/crypto** (独立仓库，如果存在): 可能是其他密码学相关功能

**cryptox 的独特优势**:
- 简洁易用的 API 设计
- 支持多种加密模式和算法
- 完善的错误处理和参数验证
- 支持 PKCS#7/PKCS#8 PEM 格式
- 类型安全的泛型函数支持
- 全面的测试覆盖

---

## 核心功能模块

### 1. 对称加密 (AES)

cryptox 提供了 AES-256 加密的多种模式支持。

#### 1.1 GCM 模式 (推荐)

GCM (Galois/Counter Mode) 是认证加密模式，提供机密性和完整性保护。

```go
import "github.com/lazygophers/utils/cryptox"

// 加密 - 使用 32 字节密钥
key := []byte("12345678901234567890123456789012") // 必须是 32 字节
plaintext := []byte("Hello, World!")

ciphertext, err := cryptox.Encrypt(key, plaintext)
if err != nil {
    panic(err)
}

// 解密
decrypted, err := cryptox.Decrypt(key, ciphertext)
if err != nil {
    panic(err)
}

fmt.Println(string(decrypted)) // "Hello, World!"
```

**特点**:
- 自动生成随机 nonce
- 认证加密，防止篡改
- 密文包含 nonce，无需单独存储
- 密钥长度固定为 32 字节 (AES-256)

#### 1.2 CBC 模式

CBC (Cipher Block Chaining) 模式，使用初始化向量 (IV)。

```go
// 加密
ciphertext, err := cryptox.EncryptCBC(key, plaintext)
if err != nil {
    panic(err)
}

// 解密
decrypted, err := cryptox.DecryptCBC(key, ciphertext)
if err != nil {
    panic(err)
}
```

**特点**:
- 密文包含 IV (前 16 字节)
- 使用 PKCS#7 填充
- 适合大多数场景

#### 1.3 CFB 模式

CFB (Cipher Feedback) 模式，将块密码转换为流密码。

```go
ciphertext, err := cryptox.EncryptCFB(key, plaintext)
decrypted, err := cryptox.DecryptCFB(key, ciphertext)
```

#### 1.4 CTR 模式

CTR (Counter) 模式，将块密码转换为流密码。

```go
ciphertext, err := cryptox.EncryptCTR(key, plaintext)
decrypted, err := cryptox.DecryptCTR(key, ciphertext)
```

**特点**:
- 加密和解密使用相同操作
- 支持并行处理
- 无需填充

#### 1.5 OFB 模式

OFB (Output Feedback) 模式，将块密码转换为同步流密码。

```go
ciphertext, err := cryptox.EncryptOFB(key, plaintext)
decrypted, err := cryptox.DecryptOFB(key, ciphertext)
```

#### 1.6 ECB 模式 (不推荐)

**警告**: ECB 模式在密码学上是不安全的，相同的明文块会产生相同的密文块。仅用于向后兼容。

```go
// ECB 模式 - 不安全，仅用于兼容性
ciphertext, err := cryptox.EncryptECB(key, plaintext)
decrypted, err := cryptox.DecryptECB(key, ciphertext)
```

### 2. 非对称加密 (RSA)

cryptox 提供完整的 RSA 加密、解密、签名和验证功能。

#### 2.1 生成 RSA 密钥对

```go
// 生成 2048 位 RSA 密钥对
keyPair, err := cryptox.GenerateRSAKeyPair(2048)
if err != nil {
    panic(err)
}

// 获取密钥长度
keySize := cryptox.GetRSAKeySize(keyPair.PublicKey)
fmt.Printf("Key size: %d bits\n", keySize)
```

**支持的密钥长度**: 1024, 2048, 3072, 4096 (推荐 2048 或更高)

#### 2.2 RSA 加密/解密

**OAEP 填充 (推荐)**:

```go
// 使用公钥加密
message := []byte("Secret message")
ciphertext, err := cryptox.RSAEncryptOAEP(keyPair.PublicKey, message)
if err != nil {
    panic(err)
}

// 使用私钥解密
plaintext, err := cryptox.RSADecryptOAEP(keyPair.PrivateKey, ciphertext)
if err != nil {
    panic(err)
}
```

**PKCS1v15 填充**:

```go
ciphertext, err := cryptox.RSAEncryptPKCS1v15(keyPair.PublicKey, message)
plaintext, err := cryptox.RSADecryptPKCS1v15(keyPair.PrivateKey, ciphertext)
```

**计算最大消息长度**:

```go
// OAEP 模式
maxLen, err := cryptox.RSAMaxMessageLength(keyPair.PublicKey, "OAEP")
if err != nil {
    panic(err)
}
fmt.Printf("Max message length (OAEP): %d bytes\n", maxLen)

// PKCS1v15 模式
maxLen, err = cryptox.RSAMaxMessageLength(keyPair.PublicKey, "PKCS1v15")
```

#### 2.3 RSA 数字签名

**PSS 填充 (推荐)**:

```go
// 使用私钥签名
message := []byte("Important document")
signature, err := cryptox.RSASignPSS(keyPair.PrivateKey, message)
if err != nil {
    panic(err)
}

// 使用公钥验证签名
err = cryptox.RSAVerifyPSS(keyPair.PublicKey, message, signature)
if err != nil {
    fmt.Println("Signature verification failed!")
} else {
    fmt.Println("Signature is valid!")
}
```

**PKCS1v15 填充**:

```go
signature, err := cryptox.RSASignPKCS1v15(keyPair.PrivateKey, message)
err = cryptox.RSAVerifyPKCS1v15(keyPair.PublicKey, message, signature)
```

#### 2.4 PEM 格式转换

```go
// 将私钥转换为 PEM 格式
privatePEM, err := keyPair.PrivateKeyToPEM()
if err != nil {
    panic(err)
}
fmt.Println(string(privatePEM))

// 将公钥转换为 PEM 格式
publicPEM, err := keyPair.PublicKeyToPEM()
if err != nil {
    panic(err)
}

// 从 PEM 加载私钥
loadedPrivateKey, err := cryptox.PrivateKeyFromPEM(privatePEM)
if err != nil {
    panic(err)
}

// 从 PEM 加载公钥
loadedPublicKey, err := cryptox.PublicKeyFromPEM(publicPEM)
if err != nil {
    panic(err)
}
```

**支持的 PEM 格式**:
- 私钥: PKCS#8 ("PRIVATE KEY") 和 PKCS#1 ("RSA PRIVATE KEY")
- 公钥: PKIX ("PUBLIC KEY") 和 PKCS#1 ("RSA PUBLIC KEY")

### 3. 椭圆曲线加密 (ECDSA & ECDH)

#### 3.1 ECDSA 数字签名

ECDSA (Elliptic Curve Digital Signature Algorithm) 提供基于椭圆曲线的数字签名。

**生成 ECDSA 密钥对**:

```go
// 生成 P-256 (secp256r1) 密钥对
keyPair, err := cryptox.GenerateECDSAP256Key()
if err != nil {
    panic(err)
}

// 或者生成 P-384 密钥对
keyPair, err = cryptox.GenerateECDSAP384Key()

// 或者生成 P-521 密钥对
keyPair, err = cryptox.GenerateECDSAP521Key()

// 或者指定任意曲线
import "crypto/elliptic"
keyPair, err = cryptox.GenerateECDSAKey(elliptic.P256())
```

**签名和验证**:

```go
message := []byte("Message to sign")

// 使用 SHA256 签名
r, s, err := cryptox.ECDSASignSHA256(keyPair.PrivateKey, message)
if err != nil {
    panic(err)
}

// 使用 SHA256 验证
isValid := cryptox.ECDSAVerifySHA256(keyPair.PublicKey, message, r, s)
if !isValid {
    fmt.Println("Signature verification failed!")
}
```

**使用自定义哈希函数**:

```go
import "crypto/sha512"

// 使用 SHA512 签名
r, s, err := cryptox.ECDSASignSHA512(keyPair.PrivateKey, message)

// 使用 SHA512 验证
isValid := cryptox.ECDSAVerifySHA512(keyPair.PublicKey, message, r, s)

// 使用自定义哈希函数
r, s, err := cryptox.ECDSASign(keyPair.PrivateKey, message, sha512.New)
isValid = cryptox.ECDSAVerify(keyPair.PublicKey, message, r, s, sha512.New)
```

**PEM 格式转换**:

```go
// 私钥转 PEM
privatePEM, err := cryptox.ECDSAPrivateKeyToPEM(keyPair.PrivateKey)
if err != nil {
    panic(err)
}

// 公钥转 PEM
publicPEM, err := cryptox.ECDSAPublicKeyToPEM(keyPair.PublicKey)
if err != nil {
    panic(err)
}

// 从 PEM 加载私钥
loadedPrivateKey, err := cryptox.ECDSAPrivateKeyFromPEM(privatePEM)
if err != nil {
    panic(err)
}

// 从 PEM 加载公钥
loadedPublicKey, err := cryptox.ECDSAPublicKeyFromPEM(publicPEM)
if err != nil {
    panic(err)
}
```

**签名 DER 编码/解码**:

```go
// 将签名转换为 DER 编码的字节数组
signatureBytes, err := cryptox.ECDSASignatureToBytes(r, s)
if err != nil {
    panic(err)
}

// 从 DER 编码解析签名
r, s, err := cryptox.ECDSASignatureFromBytes(signatureBytes)
if err != nil {
    panic(err)
}
```

**曲线工具函数**:

```go
// 获取曲线名称
curveName := cryptox.GetCurveName(elliptic.P256()) // "P-256"

// 检查曲线是否有效
isValid := cryptox.IsValidCurve(elliptic.P256()) // true
```

#### 3.2 ECDH 密钥交换

ECDH (Elliptic Curve Diffie-Hellman) 用于安全地交换共享密钥。

**生成 ECDH 密钥对**:

```go
// 生成 P-256 ECDH 密钥对
aliceKeyPair, err := cryptox.GenerateECDHP256Key()
if err != nil {
    panic(err)
}

bobKeyPair, err := cryptox.GenerateECDHP384Key()
```

**计算共享密钥**:

```go
// Alice 使用她的私钥和 Bob 的公钥计算共享密钥
sharedSecret1, err := cryptox.ECDHComputeShared(
    aliceKeyPair.PrivateKey,
    bobKeyPair.PublicKey,
)
if err != nil {
    panic(err)
}

// Bob 使用他的私钥和 Alice 的公钥计算共享密钥
sharedSecret2, err := cryptox.ECDHComputeShared(
    bobKeyPair.PrivateKey,
    aliceKeyPair.PublicKey,
)

// 两个共享密钥应该相同
fmt.Printf("Shared secrets match: %v\n",
    bytes.Equal(sharedSecret1, sharedSecret2))
```

**使用 KDF 派生密钥**:

```go
// 使用 SHA256 KDF 派生 32 字节密钥
derivedKey, err := cryptox.ECDHComputeSharedSHA256(
    aliceKeyPair.PrivateKey,
    bobKeyPair.PublicKey,
    32, // 密钥长度
)
if err != nil {
    panic(err)
}
```

**完整的 ECDH 密钥交换**:

```go
// 执行完整的 ECDH 密钥交换
sharedKey, err := cryptox.ECDHKeyExchange(
    aliceKeyPair.PrivateKey,
    bobKeyPair.PublicKey,
    32, // 派生密钥长度
)
if err != nil {
    panic(err)
}
```

**密钥对验证**:

```go
// 验证 ECDH 密钥对的有效性
err := cryptox.ValidateECDHKeyPair(aliceKeyPair)
if err != nil {
    panic(err)
}
```

**坐标转换**:

```go
import "math/big"

// 从坐标创建公钥
publicKey, err := cryptox.ECDHPublicKeyFromCoordinates(
    elliptic.P256(),
    big.NewInt(123456),
    big.NewInt(789012),
)
if err != nil {
    panic(err)
}

// 从公钥获取坐标
x, y, err := cryptox.ECDHPublicKeyToCoordinates(keyPair.PublicKey)
if err != nil {
    panic(err)
}
```

### 4. 哈希算法

cryptox 提供了全面的哈希算法支持，使用 Go 泛型实现类型安全。

#### 4.1 基础哈希函数

```go
// MD5 (不安全，仅用于兼容性)
md5Hash := cryptox.Md5("Hello, World!")
fmt.Printf("MD5: %s\n", md5Hash)

// SHA-1 (不安全，仅用于兼容性)
sha1Hash := cryptox.SHA1("Hello, World!")
fmt.Printf("SHA-1: %s\n", sha1Hash)

// SHA-224
sha224Hash := cryptox.Sha224("Hello, World!")
fmt.Printf("SHA-224: %s\n", sha224Hash)

// SHA-256 (推荐)
sha256Hash := cryptox.Sha256("Hello, World!")
fmt.Printf("SHA-256: %s\n", sha256Hash)

// SHA-384
sha384Hash := cryptox.Sha384("Hello, World!")
fmt.Printf("SHA-384: %s\n", sha384Hash)

// SHA-512
sha512Hash := cryptox.Sha512("Hello, World!")
fmt.Printf("SHA-512: %s\n", sha512Hash)

// SHA-512/224
sha512_224Hash := cryptox.Sha512_224("Hello, World!")
fmt.Printf("SHA-512/224: %s\n", sha512_224Hash)

// SHA-512/256
sha512_256Hash := cryptox.Sha512_256("Hello, World!")
fmt.Printf("SHA-512/256: %s\n", sha512_256Hash)
```

**泛型支持**: 所有哈希函数支持 `string | []byte` 类型参数

```go
// 使用字符串
hash1 := cryptox.Sha256("Hello")

// 使用字节切片
hash2 := cryptox.Sha256([]byte("Hello"))

// hash1 == hash2
```

#### 4.2 HMAC (基于哈希的消息认证码)

```go
key := "secret-key"
message := "Important message"

// HMAC-MD5 (不推荐)
hmacMd5 := cryptox.HMACMd5(key, message)

// HMAC-SHA1 (不推荐)
hmacSha1 := cryptox.HMACSHA1(key, message)

// HMAC-SHA256 (推荐)
hmacSha256 := cryptox.HMACSHA256(key, message)
fmt.Printf("HMAC-SHA256: %s\n", hmacSha256)

// HMAC-SHA384
hmacSha384 := cryptox.HMACSHA384(key, message)

// HMAC-SHA512
hmacSha512 := cryptox.HMACSHA512(key, message)
```

**用途**:
- API 签名验证
- 消息完整性校验
- 密码存储 (配合盐值)
- 令牌生成

#### 4.3 CRC 校验

```go
// CRC32 校验和
crc32Value := cryptox.CRC32("Hello, World!")
fmt.Printf("CRC32: %d\n", crc32Value)

// CRC64 校验和 (ECMA 标准)
crc64Value := cryptox.CRC64("Hello, World!")
fmt.Printf("CRC64: %d\n", crc64Value)
```

**用途**:
- 数据完整性校验
- 文件校验
- 快速哈希表
- 错误检测

#### 4.4 FNV 哈希

```go
// FNV-1 32 位哈希
hash32 := cryptox.Hash32("Hello, World!")
fmt.Printf("FNV-1 32-bit: %d\n", hash32)

// FNV-1a 32 位哈希 (改进版本，分布更均匀)
hash32a := cryptox.Hash32a("Hello, World!")
fmt.Printf("FNV-1a 32-bit: %d\n", hash32a)

// FNV-1 64 位哈希
hash64 := cryptox.Hash64("Hello, World!")
fmt.Printf("FNV-1 64-bit: %d\n", hash64)

// FNV-1a 64 位哈希
hash64a := cryptox.Hash64a("Hello, World!")
fmt.Printf("FNV-1a 64-bit: %d\n", hash64a)
```

**用途**:
- 哈希表实现
- 快速非加密哈希
- 数据去重
- 负载均衡

### 5. DES 和 3DES (不推荐)

**警告**: DES 和 3DES 已被密码学界认为是不安全的加密算法。这些函数仅用于向后兼容性，可能会在未来版本中被移除。

```go
key := []byte("12345678") // DES 需要 8 字节密钥
tripleKey := []byte("123456789012345678901234") // 3DES 需要 24 字节密钥
plaintext := []byte("Secret message")

// DES ECB 模式 (不安全)
ciphertext, err := cryptox.DESEncryptECB(key, plaintext)
decrypted, err := cryptox.DESDecryptECB(key, ciphertext)

// DES CBC 模式 (不安全)
ciphertext, err = cryptox.DESEncryptCBC(key, plaintext)
decrypted, err = cryptox.DESDecryptCBC(key, ciphertext)

// 3DES ECB 模式 (不安全)
ciphertext, err = cryptox.TripleDESEncryptECB(tripleKey, plaintext)
decrypted, err = cryptox.TripleDESDecryptECB(tripleKey, ciphertext)

// 3DES CBC 模式 (不安全)
ciphertext, err = cryptox.TripleDESEncryptCBC(tripleKey, plaintext)
decrypted, err = cryptox.TripleDESDecryptCBC(tripleKey, ciphertext)
```

### 6. 标识符生成

#### 6.1 UUID (Universally Unique Identifier)

```go
// 生成 UUID (无连字符)
uuid := cryptox.UUID()
fmt.Printf("UUID: %s\n", uuid) // 输出类似: "550e8400e29b41d4a716446655440000"
```

#### 6.2 ULID (Universally Unique Lexicographically Sortable Identifier)

```go
// 生成 ULID
ulid := cryptox.ULID()
fmt.Printf("ULID: %s\n", ulid)

// 生成 ULID 并获取时间戳
ulid, timestamp := cryptox.ULIDWithTimestamp()
fmt.Printf("ULID: %s, Timestamp: %d\n", ulid, timestamp)

// 从 ULID 提取时间戳
timestamp, err := cryptox.GetULIDTimestamp(ulid)
if err != nil {
    panic(err)
}
fmt.Printf("Timestamp: %d\n", timestamp)

// Must 版本 (panic on error)
timestamp = cryptox.MustGetULIDTimestamp(ulid)
```

**ULID vs UUID**:
- ULID 可排序，UUID 不可排序
- ULID 包含时间戳，UUID 不包含
- ULID 字符串格式更紧凑 (26 字符 vs 32 字符)
- UUID 随机性更好，防止时间侧信道攻击

---

## 加密模式对比

### 对称加密模式对比

| 模式 | 安全性 | 性能 | 并行 | 完整性 | 推荐场景 |
|------|--------|------|------|--------|----------|
| **GCM** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 内置 | **首选**，大多数场景 |
| **CBC** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ | ❌ 需 HMAC | 向后兼容 |
| **CFB** | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | ❌ 需 HMAC | 流密码场景 |
| **CTR** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ❌ 需 HMAC | 高性能场景 |
| **OFB** | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | ❌ 需 HMAC | 流密码场景 |
| **ECB** | ⭐ | ⭐⭐⭐⭐ | ✅ | ❌ | **不推荐**，仅兼容 |

### 哈希算法对比

| 算法 | 输出长度 | 安全性 | 速度 | 推荐场景 |
|------|----------|--------|------|----------|
| **MD5** | 128 bit | ❌ 已破解 | ⭐⭐⭐⭐⭐ | 不推荐，仅兼容 |
| **SHA-1** | 160 bit | ❌ 已破解 | ⭐⭐⭐⭐ | 不推荐，仅兼容 |
| **SHA-224** | 224 bit | ⭐⭐⭐ | ⭐⭐⭐ | 中等安全需求 |
| **SHA-256** | 256 bit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **首选**，大多数场景 |
| **SHA-384** | 384 bit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 高安全需求 |
| **SHA-512** | 512 bit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 最高安全需求 |
| **SHA-512/256** | 256 bit | ⭐⭐⭐⭐ | ⭐⭐⭐ | 替代 SHA-256 |
| **SHA-512/224** | 224 bit | ⭐⭐⭐ | ⭐⭐⭐ | 替代 SHA-224 |

### 非对称加密算法对比

| 算法 | 密钥长度 | 安全性 | 性能 (加密) | 性能 (签名) | 用途 |
|------|----------|--------|-------------|-------------|------|
| **RSA-2048** | 2048 bit | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 加密、签名 |
| **RSA-3072** | 3072 bit | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | 高安全需求 |
| **RSA-4096** | 4096 bit | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | 最高安全需求 |
| **ECDSA P-256** | 256 bit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 签名、密钥交换 |
| **ECDSA P-384** | 384 bit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 高安全签名 |
| **ECDSA P-521** | 521 bit | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 最高安全签名 |

---

## 实用示例

### 示例 1: 文件加密

```go
package main

import (
    "io"
    "os"
    "github.com/lazygophers/utils/cryptox"
)

func encryptFile(inputPath, outputPath, key string) error {
    // 读取文件
    plaintext, err := os.ReadFile(inputPath)
    if err != nil {
        return err
    }

    // 加密
    ciphertext, err := cryptox.Encrypt([]byte(key), plaintext)
    if err != nil {
        return err
    }

    // 写入文件
    return os.WriteFile(outputPath, ciphertext, 0644)
}

func decryptFile(inputPath, outputPath, key string) error {
    // 读取文件
    ciphertext, err := os.ReadFile(inputPath)
    if err != nil {
        return err
    }

    // 解密
    plaintext, err := cryptox.Decrypt([]byte(key), ciphertext)
    if err != nil {
        return err
    }

    // 写入文件
    return os.WriteFile(outputPath, plaintext, 0644)
}
```

### 示例 2: API 签名验证

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "github.com/lazygophers/utils/cryptox"
)

// 生成 API 签名
func GenerateAPISignature(secretKey, method, path string, params map[string]string, timestamp int64) string {
    // 构造签名字符串
    str := method + path + serializeParams(params) + fmt.Sprintf("%d", timestamp)

    // 使用 HMAC-SHA256
    return cryptox.HMACSHA256(secretKey, str)
}

// 验证 API 签名
func VerifyAPISignature(secretKey, method, path string, params map[string]string, timestamp int64, signature string) bool {
    expectedSignature := GenerateAPISignature(secretKey, method, path, params, timestamp)
    return hmac.Equal([]byte(signature), []byte(expectedSignature))
}
```

### 示例 3: 密码哈希存储

```go
package main

import (
    "crypto/rand"
    "encoding/base64"
    "github.com/lazygophers/utils/cryptox"
)

// 生成盐值
func GenerateSalt() (string, error) {
    salt := make([]byte, 32)
    _, err := rand.Read(salt)
    if err != nil {
        return "", err
    }
    return base64.StdEncoding.EncodeToString(salt), nil
}

// 哈希密码
func HashPassword(password, salt string) string {
    // 使用 HMAC-SHA512 哈希密码
    return cryptox.HMACSHA512(salt, password)
}

// 验证密码
func VerifyPassword(password, salt, hash string) bool {
    expectedHash := HashPassword(password, salt)
    return expectedHash == hash
}
```

### 示例 4: 安全密钥交换 (ECDH + AES)

```go
package main

import (
    "bytes"
    "crypto/elliptic"
    "github.com/lazygophers/utils/cryptox"
)

// Alice 和 Bob 进行安全的密钥交换
func SecureKeyExchange() error {
    // 1. Alice 生成 ECDH 密钥对
    aliceKeyPair, err := cryptox.GenerateECDHP256Key()
    if err != nil {
        return err
    }

    // 2. Bob 生成 ECDH 密钥对
    bobKeyPair, err := cryptox.GenerateECDHP256Key()
    if err != nil {
        return err
    }

    // 3. Alice 计算共享密钥
    sharedSecret1, err := cryptox.ECDHComputeSharedSHA256(
        aliceKeyPair.PrivateKey,
        bobKeyPair.PublicKey,
        32, // AES-256 需要 32 字节密钥
    )
    if err != nil {
        return err
    }

    // 4. Bob 计算共享密钥
    sharedSecret2, err := cryptox.ECDHComputeSharedSHA256(
        bobKeyPair.PrivateKey,
        aliceKeyPair.PublicKey,
        32,
    )
    if err != nil {
        return err
    }

    // 5. 验证共享密钥相同
    if !bytes.Equal(sharedSecret1, sharedSecret2) {
        return fmt.Errorf("shared secrets do not match")
    }

    // 6. 使用共享密钥加密消息
    message := []byte("Secret message from Alice to Bob")
    ciphertext, err := cryptox.Encrypt(sharedSecret1, message)
    if err != nil {
        return err
    }

    // 7. Bob 使用共享密钥解密消息
    decrypted, err := cryptox.Decrypt(sharedSecret2, ciphertext)
    if err != nil {
        return err
    }

    fmt.Printf("Decrypted message: %s\n", string(decrypted))
    return nil
}
```

### 示例 5: 数字签名系统

```go
package main

import (
    "github.com/lazygophers/utils/cryptox"
)

// 签署文档
func SignDocument(document []byte, privateKey *cryptox.ECDSAKeyPair) (string, error) {
    // 使用 SHA256 哈希文档
    r, s, err := cryptox.ECDSASignSHA256(privateKey.PrivateKey, document)
    if err != nil {
        return "", err
    }

    // 将签名转换为 DER 编码
    signature, err := cryptox.ECDSASignatureToBytes(r, s)
    if err != nil {
        return "", err
    }

    return base64.StdEncoding.EncodeToString(signature), nil
}

// 验证文档签名
func VerifyDocument(document []byte, signatureBase64 string, publicKey *ecdsa.PublicKey) (bool, error) {
    // 解码签名
    signature, err := base64.StdEncoding.DecodeString(signatureBase64)
    if err != nil {
        return false, err
    }

    // 从 DER 编码解析签名
    r, s, err := cryptox.ECDSASignatureFromBytes(signature)
    if err != nil {
        return false, err
    }

    // 验证签名
    isValid := cryptox.ECDSAVerifySHA256(publicKey, document, r, s)
    return isValid, nil
}
```

---

## 最佳实践

### 1. 加密模式选择

**对称加密**:
- ✅ **首选**: GCM 模式 (认证加密)
- ✅ 备选: CBC + HMAC (需要额外完整性保护)
- ❌ 避免: ECB 模式 (不安全)
- ❌ 避免: DES/3DES (已过时)

**非对称加密**:
- ✅ **加密**: RSA-OAEP 或 ECDSA
- ✅ **签名**: RSA-PSS 或 ECDSA-SHA256
- ❌ 避免: RSA-PKCS1v15 (存在安全漏洞)
- ❌ 避免: 密钥长度 < 2048 位

### 2. 密钥管理

**密钥长度**:
- AES: 256 位 (32 字节)
- RSA: ≥ 2048 位 (推荐 4096 位)
- ECDSA: P-256 或更高

**密钥存储**:
```go
// ✅ 好的做法: 使用环境变量或密钥管理服务
key := os.Getenv("ENCRYPTION_KEY")

// ❌ 坏的做法: 硬编码密钥
key := "12345678901234567890123456789012"

// ✅ 好的做法: 使用密钥派生函数
import "golang.org/x/crypto/pbkdf2"
key := pbkdf2.Key([]byte(password), salt, 100000, 32, sha256.New)
```

### 3. 随机数生成

```go
// ✅ 使用 cryptographically secure RNG
import crypto/rand "crypto/rand"
nonce := make([]byte, 12)
_, err := rand.Read(nonce)

// ❌ 避免使用伪随机数生成器
import mathrand "math/rand"
nonce := make([]byte, 12)
mathrand.Read(nonce) // 不安全!
```

### 4. 错误处理

```go
// ✅ 好的做法: 检查并处理所有错误
ciphertext, err := cryptox.Encrypt(key, plaintext)
if err != nil {
    log.Printf("Encryption failed: %v", err)
    return err
}

// ❌ 坏的做法: 忽略错误
ciphertext, _ := cryptox.Encrypt(key, plaintext)
```

### 5. 时间常量比较

```go
// ✅ 使用时间常量比较防止时序攻击
import crypto/subtle "crypto/subtle"
if subtle.ConstantTimeCompare(expected, actual) == 1 {
    // 验证成功
}

// ❌ 避免直接比较
if expected == actual {
    // 容易受到时序攻击
}
```

---

## 安全注意事项

### 已弃用/不安全的算法

1. **MD5**: 已被证明存在碰撞攻击，仅用于兼容性
2. **SHA-1**: 已被证明存在碰撞攻击，仅用于兼容性
3. **DES**: 密钥长度过短 (56 位)，容易被暴力破解
4. **3DES**: 虽然比 DES 安全，但性能较差，已被 NIST 弃用
5. **RSA-PKCS1v15**: 存在 Bleichenbacher 攻击，应使用 OAEP
6. **ECB 模式**: 不提供语义安全，相同的明文块产生相同的密文块

### 推荐的算法组合

**对称加密**:
- AES-256-GCM

**非对称加密**:
- RSA-4096-OAEP (加密)
- RSA-4096-PSS (签名)
- ECDSA-P-256 (签名)
- ECDH-P-256 (密钥交换)

**哈希**:
- SHA-256 (通用)
- SHA-384 (高安全需求)
- SHA-512 (最高安全需求)

**HMAC**:
- HMAC-SHA256 (通用)
- HMAC-SHA512 (高安全需求)

---

## 性能考虑

### 加密算法性能 (从快到慢)

1. **HMAC**: ⭐⭐⭐⭐⭐ (最快)
2. **AES-GCM**: ⭐⭐⭐⭐
3. **AES-CBC/CFB/CTR/OFB**: ⭐⭐⭐
4. **SHA-256**: ⭐⭐⭐⭐
5. **ECDSA**: ⭐⭐⭐
6. **RSA-2048**: ⭐⭐
7. **RSA-4096**: ⭐ (最慢)

### 优化建议

1. **复用加密上下文**: 对于频繁加密/解密，复用 cipher.Block
2. **并行处理**: 使用 CTR 模式支持并行加密/解密
3. **批量操作**: 减少函数调用次数
4. **内存池**: 使用 sync.Pool 减少 GC 压力

---

## 依赖项

cryptox 模块的依赖项:

```go
// 标准库
import (
    "crypto"
    "crypto/aes"
    "crypto/cipher"
    "crypto/des"
    "crypto/ecdsa"
    "crypto/elliptic"
    "crypto/hmac"
    "crypto/md5"
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha1"
    "crypto/sha256"
    "crypto/sha512"
    "crypto/x509"
    "encoding/pem"
    "hash/crc32"
    "hash/crc64"
    "hash/fnv"
    "io"
)

// 外部依赖 (用于 ULID/UUID)
import (
    "github.com/google/uuid"
    "github.com/oklog/ulid/v2"
    "github.com/lazygophers/log"
    "github.com/lazygophers/utils"
)
```

---

## 测试覆盖率

cryptox 模块拥有全面的测试覆盖:

- **aes_test.go**: AES 加密/解密测试 (33,887 字节)
- **des_test.go**: DES/3DES 加密/解密测试 (22,324 字节)
- **ecdh_test.go**: ECDH 密钥交换测试 (28,370 字节)
- **ecdsa_test.go**: ECDSA 签名/验证测试 (20,274 字节)
- **hash_basic_test.go**: 基础哈希测试 (12,015 字节)
- **hash_crc_test.go**: CRC 校验测试 (12,044 字节)
- **hash_fnv_test.go**: FNV 哈希测试 (13,432 字节)
- **hash_hmac_test.go**: HMAC 测试 (15,168 字节)
- **rsa_test.go**: RSA 加密/签名测试 (43,374 字节)
- **uuid_test.go**: UUID 生成测试 (3,675 字节)

**总测试代码**: ~204,563 字节

---

## 参考资源

### 官方文档
- [Go crypto 包](https://pkg.go.dev/crypto)
- [NIST 加密标准](https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines)
- [RFC 2104 - HMAC](https://tools.ietf.org/html/rfc2104)
- [RFC 5114 - 椭圆曲线加密](https://tools.ietf.org/html/rfc5114)

### 相关项目
- [lazygophers/utils](https://github.com/lazygophers/utils) - 主项目仓库
- [lazygophers/log](https://github.com/lazygophers/log) - 日志库
- [golang.org/x/crypto](https://golang.org/x/crypto) - Go 扩展加密库

### 推荐阅读
- [Applied Cryptography](https://www.schneier.com/books/applied_cryptography/) - Bruce Schneier
- [Cryptography Engineering](https://www.schneier.com/books/cryptography_engineering/) - Niels Ferguson, Bruce Schneier
- [Introduction to Modern Cryptography](https://www.cs.umd.edu/~jkatz/imc.html) - Jonathan Katz, Yehuda Lindell
