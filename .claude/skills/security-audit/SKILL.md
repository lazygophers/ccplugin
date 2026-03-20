---
name: security-audit
description: 安全审计 - OWASP Top 10检查、依赖安全扫描、敏感信息检测、安全配置审查
user-invocable: false
context: fork
model: sonnet
---

# 安全审计（Security Audit）

本 Skill 提供系统化的安全审计指导，从OWASP Top 10到依赖安全，确保应用安全可靠。

## 概览

**核心能力**：
1. **OWASP Top 10检查** - 常见Web安全漏洞检测
2. **依赖安全扫描** - 第三方库漏洞检测
3. **敏感信息检测** - API密钥、密码泄露检测
4. **安全配置审查** - HTTPS、CORS、CSP配置
5. **代码安全审查** - 注入漏洞、XSS、CSRF

**安全等级**：
- **严重**（Critical）：立即修复
- **高危**（High）：24小时内修复
- **中危**（Medium）：1周内修复
- **低危**（Low）：下次迭代修复

## 执行流程

### 阶段1：OWASP Top 10检查

**目标**：检测常见Web安全漏洞

**步骤**：
1. **A01:2021 - Broken Access Control**（访问控制失效）
   ```python
   # ❌ 不安全：未检查权限
   @app.route('/api/users/<user_id>/delete')
   def delete_user(user_id):
       User.query.filter_by(id=user_id).delete()
       return {"status": "deleted"}

   # ✅ 安全：权限检查
   @app.route('/api/users/<user_id>/delete')
   @require_admin  # 装饰器检查管理员权限
   def delete_user(user_id):
       # 进一步检查：只能删除自己或下属
       if not can_delete_user(current_user, user_id):
           abort(403)
       User.query.filter_by(id=user_id).delete()
       return {"status": "deleted"}
   ```

2. **A02:2021 - Cryptographic Failures**（加密失败）
   ```python
   # ❌ 不安全：明文存储密码
   user.password = request.form['password']

   # ✅ 安全：使用bcrypt加密
   from bcrypt import hashpw, gensalt
   user.password = hashpw(request.form['password'].encode(), gensalt())

   # ✅ 安全：使用HTTPS传输敏感数据
   # ✅ 安全：使用AES-256加密数据库敏感字段
   ```

3. **A03:2021 - Injection**（注入）
   ```python
   # ❌ 不安全：SQL注入
   query = f"SELECT * FROM users WHERE email = '{email}'"
   db.execute(query)

   # ✅ 安全：参数化查询
   query = "SELECT * FROM users WHERE email = ?"
   db.execute(query, (email,))

   # ✅ 安全：ORM（自动防注入）
   User.query.filter_by(email=email).first()
   ```

4. **A04:2021 - Insecure Design**（不安全设计）
   - 缺少速率限制
   - 缺少多因素认证
   - 缺少安全日志

5. **A05:2021 - Security Misconfiguration**（安全配置错误）
   ```python
   # ❌ 不安全：DEBUG模式在生产环境
   app.config['DEBUG'] = True

   # ✅ 安全：根据环境配置
   app.config['DEBUG'] = os.getenv('ENV') == 'development'

   # ✅ 安全：隐藏错误详情
   app.config['PROPAGATE_EXCEPTIONS'] = False
   ```

6. **A06:2021 - Vulnerable Components**（易受攻击的组件）
   - 使用已知漏洞的第三方库
   - 使用过时版本的依赖

7. **A07:2021 - Authentication Failures**（认证失败）
   ```python
   # ❌ 不安全：弱密码策略
   if len(password) < 6:
       return "Password too short"

   # ✅ 安全：强密码策略
   if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$', password):
       return "密码必须包含大小写字母、数字、特殊字符，且长度≥12"

   # ✅ 安全：实施账户锁定（防暴力破解）
   if login_attempts >= 5:
       lock_account(user_id, duration=timedelta(minutes=30))
   ```

8. **A08:2021 - Software and Data Integrity Failures**（完整性失败）
   - 未验证第三方代码
   - 未使用数字签名

9. **A09:2021 - Logging and Monitoring Failures**（日志和监控失败）
   ```python
   # ✅ 安全：记录安全事件
   logger.warning(f"Failed login attempt for user {email} from IP {request.remote_addr}")

   # ✅ 安全：监控异常行为
   if login_attempts >= 3:
       alert_security_team(f"Multiple failed logins for {email}")
   ```

10. **A10:2021 - Server-Side Request Forgery (SSRF)**
    ```python
    # ❌ 不安全：未验证URL
    url = request.args.get('url')
    response = requests.get(url)

    # ✅ 安全：白名单验证
    ALLOWED_DOMAINS = ['api.example.com']
    domain = urlparse(url).netloc
    if domain not in ALLOWED_DOMAINS:
        abort(403)
    response = requests.get(url)
    ```

### 阶段2：依赖安全扫描

**目标**：检测第三方库漏洞

**步骤**：
1. **使用安全扫描工具**：
   ```bash
   # Python
   pip-audit  # 检查Python依赖漏洞
   safety check  # 另一个Python安全工具

   # JavaScript
   npm audit  # 检查npm依赖漏洞
   npm audit fix  # 自动修复已知漏洞

   # Go
   go list -json -m all | nancy sleuth  # 检查Go依赖漏洞
   ```

2. **CI集成**：
   ```yaml
   # GitHub Actions
   name: Security Audit
   on: [push, pull_request]
   jobs:
     audit:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run security audit
           run: npm audit --audit-level=moderate
         - name: Check for vulnerabilities
           run: |
             if npm audit --audit-level=high; then
               echo "No high-severity vulnerabilities found"
             else
               echo "High-severity vulnerabilities detected!"
               exit 1
             fi
   ```

3. **依赖更新策略**：
   - 定期更新依赖（每月）
   - 订阅安全公告
   - 使用Dependabot自动更新

### 阶段3：敏感信息检测

**目标**：防止敏感信息泄露

**步骤**：
1. **检测硬编码敏感信息**：
   ```bash
   # 使用 truffleHog 检测
   trufflehog git file://. --only-verified

   # 使用 gitleaks 检测
   gitleaks detect --source . --verbose
   ```

2. **常见敏感信息**：
   - API密钥：AWS_ACCESS_KEY、GOOGLE_API_KEY
   - 密码：DB_PASSWORD、ADMIN_PASSWORD
   - 私钥：RSA private key、SSH private key
   - Token：GitHub token、Slack token

3. **安全存储**：
   ```python
   # ❌ 不安全：硬编码
   DB_PASSWORD = "supersecret123"

   # ✅ 安全：环境变量
   import os
   DB_PASSWORD = os.getenv('DB_PASSWORD')

   # ✅ 安全：密钥管理服务
   from cloud_secrets import get_secret
   DB_PASSWORD = get_secret('db-password')
   ```

4. **.gitignore配置**：
   ```
   # 敏感文件
   .env
   .env.local
   secrets.json
   *.key
   *.pem
   ```

### 阶段4：安全配置审查

**目标**：确保安全配置正确

**步骤**：
1. **HTTPS配置**：
   ```nginx
   # Nginx配置
   server {
       listen 443 ssl http2;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       # 使用强加密套件
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

       # HSTS（强制HTTPS）
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   }

   # 重定向HTTP到HTTPS
   server {
       listen 80;
       return 301 https://$host$request_uri;
   }
   ```

2. **CORS配置**：
   ```python
   from flask_cors import CORS

   # ❌ 不安全：允许所有来源
   CORS(app, resources={r"/*": {"origins": "*"}})

   # ✅ 安全：白名单
   CORS(app, resources={
       r"/api/*": {
           "origins": ["https://example.com", "https://app.example.com"],
           "methods": ["GET", "POST"],
           "allow_headers": ["Content-Type", "Authorization"]
       }
   })
   ```

3. **CSP（Content Security Policy）**：
   ```python
   # Flask示例
   @app.after_request
   def set_csp(response):
       response.headers['Content-Security-Policy'] = (
           "default-src 'self'; "
           "script-src 'self' https://cdn.example.com; "
           "style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data: https:;"
       )
       return response
   ```

4. **安全响应头**：
   ```python
   @app.after_request
   def set_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
       return response
   ```

### 阶段5：代码安全审查

**目标**：识别代码层面的安全问题

**步骤**：
1. **输入验证**：
   ```python
   from pydantic import BaseModel, EmailStr, constr

   class UserInput(BaseModel):
       email: EmailStr  # 自动验证邮箱格式
       password: constr(min_length=12)  # 最小长度12
       age: int  # 必须是整数

   # 使用
   try:
       user_data = UserInput(**request.json)
   except ValidationError as e:
       return {"errors": e.errors()}, 400
   ```

2. **XSS防护**：
   ```python
   from markupsafe import escape

   # ❌ 不安全：直接输出用户输入
   return f"<h1>Hello {username}</h1>"

   # ✅ 安全：转义HTML
   return f"<h1>Hello {escape(username)}</h1>"

   # ✅ 安全：使用模板引擎（自动转义）
   return render_template('hello.html', username=username)
   ```

3. **CSRF防护**：
   ```python
   from flask_wtf.csrf import CSRFProtect

   csrf = CSRFProtect(app)

   # 表单中添加CSRF token
   # <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```

## 安全工具集成

### 静态分析工具（SAST）
- **Python**：Bandit、Semgrep
- **JavaScript**：ESLint security plugins、SonarQube
- **Go**：gosec、staticcheck
- **通用**：SonarQube、Checkmarx

### 依赖扫描工具
- **Python**：pip-audit、safety
- **JavaScript**：npm audit、Snyk
- **Go**：nancy、trivy
- **通用**：OWASP Dependency-Check

### 敏感信息检测
- **TruffleHog**：Git历史扫描
- **Gitleaks**：轻量级密钥检测
- **git-secrets**：防止提交密钥

### 动态分析工具（DAST）
- **OWASP ZAP**：Web漏洞扫描
- **Burp Suite**：专业渗透测试
- **Nikto**：Web服务器扫描

## 输出格式

### 安全审计报告

```markdown
## 安全审计报告

### 漏洞统计
- 严重（Critical）：2个
- 高危（High）：5个
- 中危（Medium）：12个
- 低危（Low）：8个

### 严重漏洞（Critical）

#### 1. SQL注入漏洞
- **位置**：`user_controller.py:45`
- **描述**：用户输入未经过滤直接拼接到SQL查询
- **风险**：攻击者可执行任意SQL命令，窃取或篡改数据
- **修复**：使用参数化查询或ORM
- **优先级**：立即修复

#### 2. 敏感信息泄露
- **位置**：`.env`文件已提交到Git
- **描述**：数据库密码和API密钥已泄露
- **风险**：攻击者可访问数据库和第三方服务
- **修复**：
  1. 立即轮换所有密钥
  2. 使用git-filter-repo清理Git历史
  3. 添加.env到.gitignore
- **优先级**：立即修复

### 高危漏洞（High）

#### 3. 缺少速率限制
- **位置**：`/api/login`接口
- **描述**：登录接口无速率限制
- **风险**：暴力破解账户密码
- **修复**：添加速率限制（5次/分钟）
- **优先级**：24小时内修复

### 依赖漏洞

| 依赖 | 版本 | 漏洞 | CVE | 严重度 | 修复版本 |
|------|------|------|-----|--------|----------|
| requests | 2.25.1 | SSRF | CVE-2023-32681 | High | ≥2.31.0 |
| pillow | 9.0.0 | 任意代码执行 | CVE-2023-44271 | Critical | ≥10.0.1 |

### 修复建议

#### 立即修复（Critical + High）
1. 修复SQL注入（`user_controller.py:45`）
2. 轮换泄露的密钥
3. 更新pillow到10.0.1
4. 添加登录速率限制

#### 1周内修复（Medium）
1. 添加CSP响应头
2. 启用HSTS
3. 更新其他依赖
```

## 安全最佳实践

- **最小权限原则**：只授予必要的权限
- **深度防御**：多层安全措施
- **默认安全**：默认配置应该是安全的
- **失败安全**：系统故障时应保持安全
- **定期审计**：每季度进行安全审计
- **安全培训**：提升团队安全意识

## 相关 Skills

- **code-review** - 代码审查（安全代码检查）
- **architecture-review** - 架构评审（安全架构设计）
- **refactoring** - 重构指导（安全重构）
