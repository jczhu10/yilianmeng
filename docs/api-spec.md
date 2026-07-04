# 艺联萌 - API 接口规范文档 v0.1

> **状态**：草稿阶段（技能标签体系、UI 页面细节待产品确认后补充）
>
> **前后端联调参考**：所有接口均遵循本文档定义的格式与规范。

---

## 1. 通用约定

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:8080/api/v1` |
| 请求体格式 | `Content-Type: application/json` |
| 文件上传 | `Content-Type: multipart/form-data` |
| 字符编码 | UTF-8 |

### 1.2 认证方式

- 除登录/注册接口外，所有接口需携带 JWT Token
- 请求头格式：

```
Authorization: Bearer <token>
```

- Token 有效期：7 天（可配置）
- 过期后前端引导用户重新登录

### 1.3 统一响应格式

所有接口返回 JSON，结构如下：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 业务状态码（200=成功，其他=失败） |
| `message` | string | 提示信息 |
| `data` | object/array/null | 返回数据 |

### 1.4 状态码约定

| code | 含义 |
|------|------|
| 200 | 请求成功 |
| 400 | 参数校验失败 |
| 401 | 未登录或 Token 过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 数据冲突（如重复注册） |
| 500 | 服务器内部错误 |

### 1.5 分页格式

分页接口请求参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |

分页接口返回格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [ ... ],
    "total": 128,
    "page": 1,
    "page_size": 20,
    "total_pages": 7
  }
}
```

---

## 2. 接口清单（按模块）

### 2.1 用户认证模块

#### 2.1.1 注册/发送验证码

```
POST /auth/send-code
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |

```json
// 请求示例
{ "phone": "13800000000" }

// 响应
{ "code": 200, "message": "验证码已发送", "data": null }
```

#### 2.1.2 手机号+验证码登录/注册

```
POST /auth/login
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| code | string | 是 | 验证码 |

```json
// 响应
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOi...",
    "user_id": 1,
    "is_new_user": true
  }
}
```

> `is_new_user = true` 时，前端引导填写创作者档案

#### 2.1.3 刷新 Token

```
POST /auth/refresh
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 旧 Token |

```json
// 响应
{ "code": 200, "message": "success", "data": { "token": "eyJhbGciOi..." } }
```

#### 2.1.4 获取当前用户信息

```
GET /auth/me
```

```json
// 响应
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "nickname": "创作者小明",
    "avatar": "/uploads/avatar/1.jpg",
    "phone": "138****0000",
    "level": 3,
    "bio": "一名热爱的剪辑师"
  }
}
```

#### 2.1.5 登出

```
POST /auth/logout
```

```json
// 响应
{ "code": 200, "message": "已退出登录", "data": null }
```

---

### 2.2 创作者档案模块

#### 2.2.1 获取我的档案

```
GET /profile
```

```json
// 响应
{
  "code": 200,
  "message": "success",
  "data": {
    "identity_type": "professional",   // professional | amateur
    "skills": [
      {
        "skill_name": "剪辑",
        "skill_level": 4,
        "proof_url": "https://..."
      }
    ],
    "style_tags": ["治愈系", "快节奏"],
    "work_history": "3年剪辑经验...",
    "created_at": "2026-07-01T..."
  }
}
```

> ⚠️ `skills` 字段的具体标签枚举，待产品侧确认技能清单后补充。

#### 2.2.2 更新/创建创作者档案

```
PUT /profile
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| identity_type | string | 是 | professional / amateur |
| skills | array | 是 | 技能标签列表（待定） |
| style_tags | array | 否 | 创作风格标签 |
| work_history | string | 否 | 工作资历描述 |

#### 2.2.3 修改个人信息（昵称/头像/简介）

```
PATCH /profile/info
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar | file | 否 | 头像文件 |
| bio | string | 否 | 个人简介 |

---

### 2.3 作品发布模块

#### 2.3.1 发布作品

```
POST /works
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 作品标题 |
| description | string | 否 | 作品介绍 |
| channel | string | 是 | 频道：short_video/long_video/comic/short_drama/film/anime |
| files | file[] | 是 | 作品文件（图片/视频） |
| is_collaborative | bool | 否 | 是否协作作品（默认false） |
| collaborators | array | 否 | 协作成员ID列表 |

```json
// 响应
{
  "code": 200,
  "message": "发布成功",
  "data": { "work_id": 42 }
}
```

#### 2.3.2 获取作品列表（"我的"模块）

```
GET /works?page=1&page_size=20
```

```json
// 响应 data.list[0]
{
  "work_id": 42,
  "title": "我的猫片",
  "cover_url": "/uploads/works/42/cover.jpg",
  "channel": "short_video",
  "is_collaborative": false,
  "view_count": 1280,
  "like_count": 86,
  "created_at": "2026-07-01T..."
}
```

#### 2.3.3 获取作品详情

```
GET /works/:work_id
```

#### 2.3.4 删除作品

```
DELETE /works/:work_id
```

---

### 2.4 创作广场模块

#### 2.4.1 获取广场作品流（默认短视频频道）

```
GET /square/feed?channel=short_video&page=1&page_size=20
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel | string | 否 | 频道筛选（默认 short_video） |

#### 2.4.2 频道分类列表

```
GET /square/channels
```

```json
// 响应
{
  "code": 200,
  "message": "success",
  "data": [
    { "key": "short_video", "name": "短视频" },
    { "key": "long_video", "name": "长视频" },
    { "key": "comic", "name": "漫画" },
    { "key": "short_drama", "name": "短剧" },
    { "key": "film", "name": "影视" },
    { "key": "anime", "name": "动漫动画" }
  ]
}
```

#### 2.4.3 发起协作项目

```
POST /square/projects
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 项目标题 |
| description | string | 是 | 项目介绍/要求 |
| required_skills | array | 是 | 招募技能标签列表 |
| mode | string | 是 | 付费模式：paid / free |
| budget | int | 否 | 预算（付费模式时必填，单位：元） |
| deadline | string | 否 | 截止日期 ISO 8601 |

```json
// 响应
{
  "code": 200,
  "message": "项目已发布",
  "data": { "project_id": 7 }
}
```

#### 2.4.4 获取项目列表

```
GET /square/projects?page=1&page_size=20&mode=free
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | string | 否 | 筛选：paid / free |
| skill | string | 否 | 筛选技能标签 |

#### 2.4.5 报名参与项目

```
POST /square/projects/:project_id/apply
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 否 | 报名留言 |

#### 2.4.6 获取我的项目（参与/发起）

```
GET /square/projects/my?role=owner|participant
```

---

### 2.5 协作评分模块

#### 2.5.1 对合作伙伴评分

```
POST /ratings
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | int | 是 | 项目ID |
| to_user_id | int | 是 | 被评分用户ID |
| score | int | 是 | 评分 1-5 |
| comment | string | 否 | 评价内容 |

```json
// 响应
{ "code": 200, "message": "评分成功", "data": null }
```

#### 2.5.2 获取用户评分记录

```
GET /ratings/user/:user_id?page=1&page_size=20
```

```json
// 响应 data.list[0]
{
  "rating_id": 12,
  "from_user": { "user_id": 5, "nickname": "画师小红" },
  "project_id": 7,
  "score": 5,
  "comment": "剪得很好，合作愉快！",
  "created_at": "2026-07-03T..."
}
```

---

### 2.6 用户等级模块

#### 2.6.1 获取我的等级与升级进度

```
GET /level/mine
```

```json
// 响应
{
  "code": 200,
  "message": "success",
  "data": {
    "current_level": 3,
    "level_name": "资深创作者",
    "exp_current": 450,
    "exp_next_level": 600,
    "total_ratings": 28,
    "next_level_badge": "🏅"
  }
}
```

> ⚠️ 等级规则（经验值/评分映射表）待产品侧确认后细化。

---

### 2.7 供需对接模块

#### 2.7.1 发布招聘/求职/找项目信息

```
POST /market/posts
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | job / talent / project |
| title | string | 是 | 标题 |
| description | string | 是 | 详细描述 |
| skills_required | array | 否 | 所需技能 |
| salary_range | string | 否 | 薪资范围（招聘类） |

#### 2.7.2 获取供需帖子列表

```
GET /market/posts?type=job&skill=剪辑&page=1&page_size=20
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | job / talent / project |
| skill | string | 否 | 技能筛选 |

#### 2.7.3 帖子详情

```
GET /market/posts/:post_id
```

#### 2.7.4 投递简历

```
POST /market/posts/:post_id/apply
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| resume_url | string | 否 | 简历链接 |
| message | string | 否 | 附言 |

---

### 2.8 主题活动模块

#### 2.8.1 获取当前活动列表

```
GET /events?status=ongoing&page=1&page_size=20
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | ongoing / ended |

```json
// 响应 data.list[0]
{
  "event_id": 3,
  "title": "一周创作挑战：我的猫",
  "description": "创作一个关于猫的作品...",
  "deadline": "2026-07-15T23:59:59",
  "reward": 100,
  "reward_unit": "艺联币",
  "participant_count": 56,
  "cover_url": "/uploads/events/3.jpg"
}
```

#### 2.8.2 参与活动（提交作品）

```
POST /events/:event_id/submit
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| work_id | int | 是 | 参赛作品ID |

#### 2.8.3 获取活动排行榜

```
GET /events/:event_id/ranking?page=1&page_size=50
```

---

### 2.9 艺联币模块

#### 2.9.1 获取我的钱包

```
GET /wallet
```

```json
// 响应
{
  "code": 200,
  "message": "success",
  "data": {
    "balance": 520,
    "total_earned": 1280,
    "total_withdrawn": 760
  }
}
```

#### 2.9.2 交易记录

```
GET /wallet/transactions?page=1&page_size=20
```

#### 2.9.3 申请提现

```
POST /wallet/withdraw
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| amount | int | 是 | 提现艺联币数量 |
| method | string | 是 | 方式：wechat / alipay |
| account | string | 是 | 收款账号 |

---

## 3. 文件上传规范

| 项目 | 说明 |
|------|------|
| 头像 | 格式 jpg/png/webp，最大 2MB |
| 作品图片 | 格式 jpg/png/webp，最大 10MB/张 |
| 视频作品 | 格式 mp4/mov，最大 500MB |
| 上传路径 | `/api/v1/upload/avatar` `/api/v1/upload/work` 等 |

---

## 4. 暂未确定的接口（待产品/设计确认）

| 模块 | 待确认项 | 影响范围 |
|------|----------|----------|
| 创作者档案 | 技能标签完整枚举列表 | `/profile` 系列接口 |
| 创作广场 | 频道切换交互细节（上滑消失/左滑召唤） | APP端实现，后端无影响 |
| 用户等级 | 7级具体经验值/评分规则 | `/level` 计算逻辑 |
| 艺联币 | 兑换比例（艺联币:人民币） | `/wallet/withdraw` |
| 主题活动 | 活动规则、评审机制 | `/events` 系列 |
| 通知系统 | 消息推送类型（评论/评分/项目邀请等） | 独立通知模块接口 |
| 举报/审核 | 内容审核机制 | 作品审核接口 |

---

> **更新日志**
>
> | 日期 | 版本 | 变更 |
> |------|------|------|
> | 2026-07-04 | v0.1 | 初版草稿，覆盖全部核心模块接口框架 |