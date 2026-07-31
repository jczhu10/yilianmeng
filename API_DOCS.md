# 艺联萌后端接口文档

**Base URL**: http://localhost:8080/api/v1
**鉴权方式**: 请求头 Authorization: Bearer <token>
**统一响应格式**:
{
  "code": 200,          # 200成功，其他为业务错误码
  "message": "success", # 提示信息
  "data": {...}         # 数据，失败时为 null
}

**HTTP状态码与业务码分离**: HTTP状态码遵循HTTP语义(200/400/401/403/404/429/500)，Body中的code为业务码(200=成功,1xxx=认证类,2xxx=档案类,3xxx=作品类)。

---

## 一、全局业务错误码

| 业务码 | 含义 | HTTP |
|--------|------|------|
| 200 | 成功 | 200 |
| 400 | 参数错误 | 400 |
| 401 | 未登录或Token过期 | 401 |
| 403 | 无权操作 | 403 |
| 404 | 资源不存在 | 404 |
| 429 | 请求过于频繁 | 429 |
| 1001 | 手机号格式不正确 | 400 |
| 1002 | 验证码错误 | 400 |
| 1003 | 验证码已过期 | 400 |
| 1004 | 请先发送验证码 | 400 |
| 2001 | 身份类型不合法 | 400 |
| 2002 | 存在无效的技能ID | 404 |
| 2004 | 技能数量超限 | 400 |
| 3001 | 作品不存在 | 404 |
| 3002 | 无权操作他人作品 | 403 |
| 3003 | 作品已删除 | 400 |
| 3004 | 渠道不合法 | 400 |
| 3005 | 文件数量超限 | 400 |
| 3006 | 技能标签无效 | 400 |

---

# 模块一：认证（auth）  前缀 /api/v1/auth

## 1.1 发送验证码
POST /auth/send-code

请求参数(JSON Body):
- phone (string, 必填) 手机号11位

请求示例: { "phone": "13800138000" }

成功返回:
{ "code": 200, "message": "验证码已发送", "data": { "dev_code": "123456" } }
# 开发模式直接返回验证码，生产环境应调用短信服务

失败返回:
- 60秒内重复: { "code": 429, "message": "验证码发送过于频繁，请60秒后重试" }
- 格式错误: { "code": 1001, "message": "手机号格式不正确" }

## 1.2 登录/注册
POST /auth/login
手机号+验证码登录，新用户自动注册

请求参数(JSON Body):
- phone (string, 必填) 手机号
- code (string, 必填) 验证码

请求示例: { "phone": "13800138000", "code": "123456" }

成功返回:
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "user_id": 4, "nickname": "用户8000", "avatar": "",
      "phone": "138****8000", "level": 1, "bio": "",
      "is_new_user": false, "created_at": "2026-07-31T09:00:00"
    },
    "is_new_user": false
  }
}

失败返回:
- { "code": 1002, "message": "验证码错误" }
- { "code": 1003, "message": "验证码已过期，请重新获取" }
- { "code": 1004, "message": "请先发送验证码" }

## 1.3 刷新Token
POST /auth/refresh  [需登录]
Token过期前调用，获取新Token。无请求参数。

成功返回:
{ "code": 200, "message": "Token刷新成功", "data": { "token": "eyJ..." } }

## 1.4 获取当前用户信息
GET /auth/me  [需登录]

成功返回:
{
  "code": 200, "message": "success",
  "data": {
    "user_id": 4, "nickname": "用户8000", "avatar": "",
    "phone": "138****8000", "level": 1, "bio": "",
    "is_new_user": false, "created_at": "2026-07-31T09:00:00"
  }
}

## 1.5 登出
POST /auth/logout  [需登录]

成功返回: { "code": 200, "message": "已退出登录", "data": null }

---

# 模块二：创作者档案（profile）  前缀 /api/v1/profile

## 2.1 获取我的档案（含技能）
GET /profile/me  [需登录]

成功返回:
{
  "code": 200, "message": "success",
  "data": {
    "id": 1, "user_id": 4,
    "identity_type": "amateur",
    "style_tags": ["搞笑", "治愈"],
    "work_history": "曾在XX公司任职",
    "education": "XX大学",
    "skills": [
      { "id": 1, "name": "小说创作", "category_id": 1, "category_name": "文字创作" },
      { "id": 5, "name": "插画", "category_id": 2, "category_name": "视觉创作" }
    ],
    "created_at": "...", "updated_at": "..."
  }
}

## 2.2 更新我的档案基础信息
PUT /profile/me  [需登录]
部分更新，只传需要改的字段

请求参数(JSON Body, 均可选):
- identity_type (string) 身份类型：amateur(业余)/professional(专业)
- style_tags (string[]) 风格标签，最多10个
- work_history (string) 工作经历，最多2000字
- education (string) 教育背景，最多2000字

请求示例:
{ "identity_type": "professional", "style_tags": ["搞笑","治愈"], "work_history": "2020-2023 XX公司 编剧" }

成功返回: 同2.1档案对象，message为"档案更新成功"
失败: { "code": 2001, "message": "身份类型不合法" }

## 2.3 更新我的技能（覆盖式）
PUT /profile/skills  [需登录]
传入完整技能ID列表，覆盖原有技能，最多20个

请求参数(JSON Body):
- skill_ids (int[], 必填) 技能ID数组

请求示例: { "skill_ids": [1, 2, 5, 6] }

成功返回:
{
  "code": 200, "message": "技能更新成功",
  "data": {
    "skills": [
      { "id": 1, "name": "小说创作", "category_id": 1, "category_name": "文字创作" }
    ]
  }
}
失败: { "code": 2002, "message": "存在无效的技能ID" } / { "code": 2004, "message": "最多选择 20 个技能" }

## 2.4 获取我的技能列表
GET /profile/skills/mine  [需登录]

成功返回:
{ "code": 200, "message": "success", "data": { "skills": [...] } }

## 2.5 获取所有技能分类（含子技能）
GET /profile/skills/categories  [无需登录]
用于前端技能选择器

成功返回:
{
  "code": 200, "message": "success",
  "data": {
    "categories": [
      {
        "id": 1, "name": "文字创作", "code": "writing", "sort_order": 1,
        "skills": [
          { "id": 1, "name": "小说创作", "category_id": 1 },
          { "id": 2, "name": "剧本创作", "category_id": 1 }
        ]
      },
      { "id": 2, "name": "视觉创作", "code": "visual", "skills": [...] }
    ]
  }
}

## 2.6 获取所有技能（扁平列表）
GET /profile/skills  [无需登录]

查询参数:
- category_id (int, 可选) 按分类筛选

请求示例: GET /profile/skills?category_id=1
成功返回: { "code": 200, "data": { "skills": [{ "id": 1, "name": "小说创作", "category_id": 1 }] } }

## 2.7 查看他人档案
GET /profile/<user_id>  [需登录]

路径参数: user_id (int, 必填) 目标用户ID
成功返回: 同2.1档案对象
失败: { "code": 404, "message": "该用户尚未创建档案" }

---

# 模块三：作品（works）  前缀 /api/v1/works

channel枚举: writing(文字)/visual(视觉)/video(影像)/voice(配音)
status枚举: draft(草稿)/published(已发布)/deleted(已删除)

## 3.1 创建作品
POST /works/  [需登录]

请求参数(JSON Body):
- title (string, 必填) 标题，1-200字符
- description (string, 可选) 描述，最多2000字符
- channel (string, 必填) 渠道：writing/visual/video/voice
- files (string[], 可选) 文件URL数组，最多9个
- cover_url (string, 可选) 封面URL
- is_collaborative (bool, 可选) 是否协作作品，默认false
- collaborators (int[], 可选) 协作者用户ID数组
- skill_tags (int[], 可选) 技能标签ID数组，最多5个
- status (string, 可选) 状态：draft(默认)/published

请求示例:
{ "title": "我的第一篇小说", "description": "这是一个关于梦想的故事", "channel": "writing", "files": ["/uploads/works/abc.jpg"], "cover_url": "/uploads/works/cover.jpg", "is_collaborative": false, "skill_tags": [1, 2], "status": "draft" }

成功返回:
{
  "code": 200, "message": "作品创建成功",
  "data": {
    "work_id": 1, "user_id": 4, "title": "我的第一篇小说", "description": "...",
    "channel": "writing", "files": ["/uploads/works/abc.jpg"], "cover_url": "...",
    "is_collaborative": false, "collaborators": [], "skill_tags": [1, 2],
    "status": "draft", "view_count": 0, "like_count": 0,
    "created_at": "...", "updated_at": "..."
  }
}

失败: { "code": 3004, "message": "渠道不合法" } / { "code": 3005, "message": "文件数量超限" } / { "code": 3006, "message": "存在无效的技能标签ID" }

## 3.2 编辑作品
PUT /works/<work_id>  [需登录，仅作者]
部分更新，只传需要改的字段，不传的保持不变

路径参数: work_id (int, 必填)
请求参数(JSON Body, 均可选): 同3.1所有字段

请求示例: { "title": "修改后的标题", "description": "更新后的描述" }
成功返回: 同3.1作品对象，message为"作品更新成功"
失败: { "code": 3001, "message": "作品不存在" } / { "code": 3002, "message": "无权操作他人作品" }

## 3.3 发布作品
POST /works/<work_id>/publish  [需登录，仅作者]
草稿变为已发布，无请求参数

成功返回: { "code": 200, "message": "作品发布成功", "data": {..., "status": "published"} }
若已是发布状态，返回"作品已是发布状态"

## 3.4 删除作品
DELETE /works/<work_id>  [需登录，仅作者]
软删除，不真正删除数据

成功返回: { "code": 200, "message": "作品已删除", "data": null }
失败: { "code": 3003, "message": "作品已删除" } (重复删除)

## 3.5 获取作品详情
GET /works/<work_id>  [需登录]

说明:
- 草稿仅作者可见，非作者访问返回404（避免泄露存在性）
- 已发布作品访问时view_count自动+1
- 返回数据含author作者信息

成功返回:
{
  "code": 200, "message": "success",
  "data": {
    "work_id": 1, "user_id": 4, "title": "...", "description": "...",
    "channel": "writing", "files": [...], "cover_url": "...",
    "is_collaborative": false, "collaborators": [],
    "skill_tags": [1,2], "status": "published",
    "view_count": 5, "like_count": 0,
    "created_at": "...", "updated_at": "...",
    "author": {
      "user_id": 4, "nickname": "用户8000", "avatar": "",
      "phone": "138****8000", "level": 1, "bio": "",
      "is_new_user": false, "created_at": "..."
    }
  }
}

## 3.6 获取我的作品列表
GET /works/mine  [需登录]

查询参数:
- page (int, 可选) 页码，默认1
- page_size (int, 可选) 每页数量，默认20，最大100
- status (string, 可选) 按状态筛选：draft/published/deleted。不传则返回除已删除外全部

请求示例: GET /works/mine?page=1&page_size=20&status=published

成功返回:
{
  "code": 200, "message": "success",
  "data": {
    "list": [{ "work_id": 1, "title": "...", "status": "published", ... }],
    "total": 2, "page": 1, "page_size": 20, "total_pages": 1
  }
}

## 3.7 文件上传
POST /works/upload  [需登录]

请求参数(multipart/form-data):
- file (File, 必填) 文件，支持 jpg/jpeg/png/gif/webp/mp4/mov，最大500MB

请求示例(curl):
curl -X POST http://localhost:8080/api/v1/works/upload -H "Authorization: Bearer <token>" -F "file=@/path/to/image.png"

成功返回:
{ "code": 200, "message": "上传成功", "data": { "url": "/uploads/works/5cf39421.png" } }

失败: { "code": 400, "message": "不支持的文件类型" } / { "code": 400, "message": "未提供文件" }

# 前端使用流程：先调本接口获取url，再把url放入创建/编辑作品的files数组中

---

# 附录：完整调用流程示例

## 新用户首次使用
1. POST /auth/send-code        { phone }                     -> 获取验证码
2. POST /auth/login            { phone, code }               -> 登录，获取token(is_new_user=true)
3. PUT  /profile/me            { identity_type, style_tags } -> 完善档案
4. GET  /profile/skills/categories                            -> 获取技能列表
5. PUT  /profile/skills        { skill_ids: [1,2,5] }        -> 选择技能
6. POST /works/upload          (file)                        -> 上传文件拿url
7. POST /works/                { title, files:[url], status:"draft" } -> 存草稿
8. POST /works/<id>/publish                                   -> 发布

## Token刷新机制
- Token有效期 7 天
- 过期前调用 POST /auth/refresh 获取新Token
- 过期后需重新登录
