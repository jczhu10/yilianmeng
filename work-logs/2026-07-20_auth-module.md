# 艺联萌后端开发工作日志 - 用户认证模块

## 日期
2026-07-20

## 阶段目标
实现用户认证模块，包括发送验证码、登录/注册、Token刷新、获取用户信息、登出功能

---

## 1. 实现的具体功能

### 1.1 接口清单

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 发送验证码 | POST | `/api/v1/auth/send-code` | 否 | 向手机号发送6位验证码 |
| 登录/注册 | POST | `/api/v1/auth/login` | 否 | 手机号+验证码登录，新用户自动注册 |
| 刷新Token | POST | `/api/v1/auth/refresh` | 是 | 旧Token换新Token |
| 获取用户信息 | GET | `/api/v1/auth/me` | 是 | 获取当前登录用户信息 |
| 登出 | POST | `/api/v1/auth/logout` | 是 | 退出登录 |

### 1.2 核心特性

- **手机号格式校验**：11位数字，1开头，第二位3-9
- **验证码机制**：6位随机数字，5分钟有效期，60秒内不能重复发送
- **自动注册**：新用户首次登录自动创建账号
- **JWT认证**：7天有效期，无状态认证
- **登录装饰器**：`@login_required` 保护需要认证的接口

---

## 2. 如何实现

### 2.1 文件结构

```
app/
├── __init__.py           # 更新：注册auth蓝图
├── routes/
│   ├── __init__.py       # 新建：路由模块初始化
│   └── auth.py           # 新建：用户认证路由
├── utils/
│   ├── __init__.py       # 新建：工具模块初始化
│   └── helpers.py        # 已有：Token工具函数
└── app.py                # 更新：入口文件
```

### 2.2 验证码存储方案

**开发阶段**：使用内存字典存储验证码
```python
verification_codes = {}  # {phone: (code, expire_time, send_time)}
```

**生产环境**：可替换为Redis存储，或接入阿里云短信服务

### 2.3 登录流程

```
1. 用户输入手机号 → POST /auth/send-code
2. 后端生成6位验证码，存入内存，返回验证码（开发模式）
3. 用户输入验证码 → POST /auth/login
4. 后端校验验证码
   ├── 正确 → 查询用户
   │   ├── 存在 → 生成Token，返回登录成功
   │   └── 不存在 → 创建新用户，生成Token，返回登录成功
   └── 错误 → 返回错误信息
```

### 2.4 JWT Token 机制

**Token 生成**（helpers.py）：
```python
def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
```

**Token 验证装饰器**：
```python
@login_required
def some_api():
    user = request.user  # 当前登录用户
    ...
```

### 2.5 安全措施

| 风险 | 应对措施 |
|------|----------|
| 验证码暴力破解 | 验证后立即清除，5分钟过期 |
| 频繁发送验证码 | 60秒内限制重复发送 |
| 手机号格式错误 | 后端正则校验 `^1[3-9]\d{9}$` |
| 未认证访问 | `@login_required` 装饰器拦截，返回401 |
| Token过期 | JWT自带exp字段，自动校验 |

---

## 3. 测试结果

### 3.1 发送验证码
```bash
POST /api/v1/auth/send-code
{"phone": "13800000000"}
```
**响应**：
```json
{
    "code": 200,
    "data": {"dev_code": "949515"},
    "message": "验证码已发送"
}
```

### 3.2 登录（新用户）
```bash
POST /api/v1/auth/login
{"phone": "13800000000", "code": "949515"}
```
**响应**：
```json
{
    "code": 200,
    "data": {
        "is_new_user": true,
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "user_id": 1
    },
    "message": "登录成功"
}
```

### 3.3 获取用户信息
```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```
**响应**：
```json
{
    "code": 200,
    "data": {
        "avatar": "",
        "bio": "",
        "created_at": "2026-07-20T10:45:28",
        "is_new_user": true,
        "level": 1,
        "nickname": "用户0000",
        "phone": "138****0000",
        "user_id": 1
    },
    "message": "success"
}
```

### 3.4 刷新Token
```bash
POST /api/v1/auth/refresh
Authorization: Bearer <token>
```
**响应**：
```json
{
    "code": 200,
    "data": {"token": "eyJhbGciOiJIUzI1NiIs..."},
    "message": "Token刷新成功"
}
```

### 3.5 登出
```bash
POST /api/v1/auth/logout
Authorization: Bearer <token>
```
**响应**：
```json
{
    "code": 200,
    "data": null,
    "message": "已退出登录"
}
```

### 3.6 未认证访问
```bash
GET /api/v1/auth/me  (不带Token)
```
**响应**：
```json
{
    "code": 401,
    "data": null,
    "message": "未登录或Token过期"
}
```

---

## 4. 与前端的对接

### 4.1 前端使用流程

```
1. App启动 → 检查本地是否有Token
   ├── 有Token → 调用 /auth/me 验证
   │   ├── 成功 → 进入主页
   │   └── 失败(401) → 跳转登录页
   └── 无Token → 跳转登录页

2. 登录页 → 用户输入手机号
   ├── 调用 /auth/send-code 发送验证码
   └── 用户输入验证码
       └── 调用 /auth/login 登录
           ├── is_new_user=true → 跳转档案填写页
           └── is_new_user=false → 进入主页

3. Token管理
   ├── 存储Token到localStorage
   ├── 每次请求自动携带 Authorization: Bearer <token>
   ├── 收到401响应 → 清除Token，跳转登录页
   └── Token即将过期 → 调用 /auth/refresh 刷新
```

### 4.2 前端注意事项

1. **Token存储**：登录成功后将Token存入 localStorage
2. **请求拦截器**：每次请求自动添加 `Authorization` 头
3. **响应拦截器**：收到401时清除Token并跳转登录页
4. **验证码倒计时**：发送验证码后前端显示60秒倒计时
5. **手机号脱敏**：后端返回的手机号已脱敏（138****0000）
6. **新用户引导**：`is_new_user=true` 时跳转档案填写页

---

## 总结

本阶段完成了用户认证模块的全部功能：

1. **5个API接口**：发送验证码、登录/注册、Token刷新、获取用户信息、登出
2. **安全机制**：手机号校验、验证码防刷、JWT认证
3. **测试通过**：所有接口测试正常，包括错误处理
4. **自动注册**：新用户首次登录自动创建账号

**下一步计划**：实现创作者档案模块
