# 艺联萌后端接口文档（全量）

> 更新日期：2026-09-04
> 接口总数：82 个 | 测试覆盖：94/94 全通过
> 基础路径：`/api/v1`
> 认证方式：`Authorization: Bearer <token>`（JWT，7天有效期）
> 响应格式：`{ "code": 200, "message": "success", "data": {...} }`

---

## 目录

| # | 模块 | 接口数 | url_prefix | 测试文件 |
|---|------|--------|------------|----------|
| 1 | [认证 auth](#1-认证-auth) | 7 | /api/v1/auth | test_auth_profile_v2.py |
| 2 | [档案 profile](#2-档案-profile) | 22 | /api/v1/profile | test_auth_profile_v2.py |
| 3 | [作品 works](#3-作品-works) | 9 | /api/v1/works | test_all_modules.py |
| 4 | [互动 interactions](#4-互动-interactions) | 7 | /api/v1 | test_all_modules.py |
| 5 | [协作项目 projects](#5-协作项目-projects) | 9 | /api/v1/projects | test_all_modules.py |
| 6 | [通知 notifications](#6-通知-notifications) | 5 | /api/v1/notifications | test_messages.py |
| 7 | [关注 follows](#7-关注-follows) | 6 | /api/v1 | test_messages.py |
| 8 | [私聊 conversations](#8-私聊-conversations) | 6 | /api/v1/conversations | test_messages.py |
| 9 | [群聊 groups](#9-群聊-groups) | 8 | /api/v1/groups | test_messages.py |
| 10 | [消息上传 messages_upload](#10-消息上传-messages_upload) | 1 | /api/v1/messages | test_messages.py |

---

## 1. 认证 auth

> 路由文件：`app/routes/auth.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 1 | POST | `/auth/send-code` | 否 | 发送验证码 |
| 2 | POST | `/auth/register` | 否 | 注册 |
| 3 | POST | `/auth/login` | 否 | 登录（密码） |
| 4 | POST | `/auth/reset-password` | 否 | 重置密码 |
| 5 | POST | `/auth/refresh` | 是 | 刷新Token |
| 6 | GET | `/auth/me` | 是 | 获取当前用户 |
| 7 | POST | `/auth/logout` | 是 | 退出登录 |

### 接口详情

**1. POST /auth/send-code** — 发送验证码
```
Body: { "phone": "139xxxxxxxx", "scene": "register|reset" }
返回: { "dev_code": "123456" }  // 开发环境返回验证码
限制: 60秒一次，验证码5分钟有效
错误码: 1001(手机号格式错误) 1008(scene不合法) 1009(60秒内重复)
```

**2. POST /auth/register** — 注册
```
Body: { "phone": "...", "code": "...", "password": "...", "nickname": "..." }
密码规则: 8-20位含字母+数字
返回: { "token": "...", "user": {...}, "is_new_user": true }
注册时自动创建空档案
错误码: 1002(验证码错误) 1003(已注册) 1004(密码格式错误)
```

**3. POST /auth/login** — 登录
```
Body: { "phone": "...", "password": "..." }
返回: { "token": "...", "user": {...}, "is_new_user": false }
错误码: 1005(用户不存在) 1006(密码错误)
```

**4. POST /auth/reset-password** — 重置密码
```
Body: { "phone": "...", "code": "...", "new_password": "..." }
错误码: 1002(验证码错误) 1004(密码格式错误)
```

**5. POST /auth/refresh** — 刷新Token
```
Header: Authorization: Bearer <token>
返回: { "token": "新token" }
```

**6. GET /auth/me** — 获取当前用户
```
返回: { "id": 1, "phone": "...", "nickname": "...", "avatar": "...", "bio": "...",
        "level": 1, "exp": 0, "is_new_user": false, "created_at": "...", "updated_at": "..." }
```

**7. POST /auth/logout** — 退出登录
```
仅记录日志，客户端清token即可
```

---

## 2. 档案 profile

> 路由文件：`app/routes/profile.py`

### 2.1 档案基础

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 8 | GET | `/profile/me` | 是 | 获取我的完整档案 |
| 9 | PUT | `/profile/me` | 是 | 更新档案基础信息 |
| 10 | GET | `/profile/<user_id>` | 是 | 查看他人档案 |

**9. PUT /profile/me** — 更新档案
```
Body: { "identity": "学生|艺术爱好者|艺术相关工作者" }
错误码: 2001(identity不合法)
```

### 2.2 技能

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 11 | PUT | `/profile/skills` | 是 | 更新我的技能（覆盖式，上限5） |
| 12 | GET | `/profile/skills/mine` | 是 | 我的技能列表 |
| 13 | GET | `/profile/skills/categories` | 否 | 技能分类字典 |
| 14 | GET | `/profile/skills` | 否 | 技能扁平列表 |

**11. PUT /profile/skills**
```
Body: { "skill_ids": [1, 2, 3] }  // 最多5个
错误码: 2002(技能不存在) 2003(超过5个上限)
```

**13. GET /profile/skills/categories**
```
Query: 无
返回: { "categories": [{ "id": 1, "name": "写作", "skills": [...] }] }
```

**14. GET /profile/skills**
```
Query: category_id(可选)
```

### 2.3 风格词汇

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 15 | GET | `/profile/style-tags` | 否 | 风格词汇字典 |
| 16 | PUT | `/profile/style-tags` | 是 | 更新我的风格词汇（覆盖式，上限5） |
| 17 | GET | `/profile/style-tags/mine` | 是 | 我的风格词汇 |

**16. PUT /profile/style-tags**
```
Body: { "style_tag_ids": [1, 2] }  // 最多5个
错误码: 2004(风格词汇不存在) 2005(超过5个上限)
```

### 2.4 工作经历

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 18 | GET | `/profile/work-experiences` | 是 | 工作经历列表 |
| 19 | POST | `/profile/work-experiences` | 是 | 新增工作经历 |
| 20 | PUT | `/profile/work-experiences/<exp_id>` | 是 | 编辑工作经历 |
| 21 | DELETE | `/profile/work-experiences/<exp_id>` | 是 | 删除工作经历 |

**19. POST /profile/work-experiences**
```
Body: {
  "company_name": "公司名",
  "position": "职位",
  "start_date": "2020-01-01",
  "end_date": "2023-01-01",        // 可选，is_current=true时可不传
  "is_current": false,
  "description": "描述",
  "sort_order": 0,
  "images": [{ "image_url": "...", "caption": "...", "sort_order": 0 }]  // 最多5张
}
```

### 2.5 教育经历

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 22 | GET | `/profile/education-experiences` | 是 | 教育经历列表 |
| 23 | POST | `/profile/education-experiences` | 是 | 新增教育经历 |
| 24 | PUT | `/profile/education-experiences/<edu_id>` | 是 | 编辑教育经历 |
| 25 | DELETE | `/profile/education-experiences/<edu_id>` | 是 | 删除教育经历 |

**23. POST /profile/education-experiences**
```
Body: {
  "school_level": "小学|中学|大学",
  "school_name": "学校名",
  "start_year": 2020,
  "end_year": 2024,
  "degree": "学位",
  "major": "专业",
  "sort_order": 0
}
```

### 2.6 能力证明

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 26 | GET | `/profile/ability-proofs` | 是 | 能力证明列表 |
| 27 | POST | `/profile/ability-proofs` | 是 | 新增能力证明 |
| 28 | PUT | `/profile/ability-proofs/<proof_id>` | 是 | 编辑能力证明 |
| 29 | DELETE | `/profile/ability-proofs/<proof_id>` | 是 | 删除能力证明 |

**27. POST /profile/ability-proofs**
```
Body: {
  "title": "证明标题",
  "description": "描述",
  "sort_order": 0,
  "files": [{ "file_url": "...", "file_name": "...", "file_type": "image|pdf|doc|video", "sort_order": 0 }]  // 最多10个
}
```

### 2.7 文件上传

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 30 | POST | `/profile/upload` | 是 | 档案文件上传 |

```
Form: file(图片/视频/PDF/DOC)
返回: { "url": "/uploads/profile/xxx.jpg", "file_name": "...", "file_type": "image|pdf|doc|video" }
```

---

## 3. 作品 works

> 路由文件：`app/routes/works.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 31 | POST | `/works/` | 是 | 创建作品 |
| 32 | PUT | `/works/<work_id>` | 是 | 编辑作品 |
| 33 | POST | `/works/<work_id>/publish` | 是 | 发布作品 |
| 34 | DELETE | `/works/<work_id>` | 是 | 删除作品（软删除） |
| 35 | GET | `/works/<work_id>` | 是 | 作品详情 |
| 36 | GET | `/works/mine` | 是 | 我的作品列表 |
| 37 | GET | `/works/feed` | 是 | 首页推荐推流 |
| 38 | GET | `/works/search` | 是 | 搜索作品 |
| 39 | GET | `/works/by-skill` | 是 | 按技能筛选 |

### 接口详情

**31. POST /works/** — 创建作品
```
Body: {
  "title": "标题",
  "description": "描述",
  "channel": "writing|visual|video|voice",
  "files": ["url1", "url2"],        // 最多9个
  "cover_url": "...",
  "is_collaborative": false,
  "collaborators": [],
  "skill_tags": [1, 2],              // 最多5个
  "status": "draft|published"
}
返回: { "work_id": 1, "user_id": 1, "title": "...", ... }
错误码: 3001(标题为空) 3002(channel不合法) 3003(files超9个) 3004(skill_tags超5个)
```

**32. PUT /works/<work_id>** — 编辑作品（部分更新）
```
Body: 同创建，所有字段可选
权限: 仅作者可编辑
```

**33. POST /works/<work_id>/publish** — 发布作品
```
草稿 → 已发布
权限: 仅作者
```

**34. DELETE /works/<work_id>** — 删除作品
```
软删除（status=deleted）
权限: 仅作者
```

**36. GET /works/mine** — 我的作品
```
Query: page(默认1), per_page(默认20), status(draft/published/deleted, 可选)
返回: { "list": [...], "total": 10, "page": 1, "page_size": 20, "total_pages": 1 }
```

**37. GET /works/feed** — 首页推流
```
Query: page, per_page, sort(latest|hot, 默认latest), channel(可选), exclude_self(默认true)
hot排序: like_count*2 + view_count 倒序
返回: 分页列表
```

**38. GET /works/search** — 搜索
```
Query: q(必填), channel(可选), page, per_page
```

**39. GET /works/by-skill** — 按技能筛选
```
Query: skill_id(必填), sort(latest|hot), page, per_page
```

### 作品上传

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 40 | POST | `/works/upload` | 是 | 作品文件上传 |

```
Form: file(图片/视频)
返回: { "url": "/uploads/works/xxx.jpg", "file_name": "...", "file_type": "image|video" }
```

---

## 4. 互动 interactions

> 路由文件：`app/routes/interactions.py`（url_prefix=/api/v1）

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 41 | POST | `/works/<work_id>/like` | 是 | 点赞作品 |
| 42 | DELETE | `/works/<work_id>/like` | 是 | 取消点赞 |
| 43 | GET | `/works/<work_id>/likes` | 是 | 点赞用户列表 |
| 44 | POST | `/works/<work_id>/comments` | 是 | 发表评论/回复 |
| 45 | GET | `/works/<work_id>/comments` | 是 | 评论列表（一级） |
| 46 | DELETE | `/comments/<comment_id>` | 是 | 删除评论（软删除） |
| 47 | GET | `/comments/<comment_id>/replies` | 是 | 回复列表 |

### 接口详情

**41. POST /works/<work_id>/like** — 点赞
```
返回: { "like_count": 10 }
错误码: 4001(作品不存在) 4002(无权操作) 4003(已点赞)
```

**44. POST /works/<work_id>/comments** — 发表评论
```
Body: { "content": "评论内容", "parent_id": null }
parent_id 不传 = 一级评论; 传 = 回复（仅支持二级回复，三级被拒）
返回: { "comment_id": 1, "content": "...", "user_id": 1, ... }
错误码: 4004(内容为空) 4005(评论不存在) 4006(无权删除) 4007(回复层级超限)
```

**45. GET /works/<work_id>/comments** — 评论列表
```
Query: page, per_page
返回一级评论（parent_id IS NULL），含 reply_count
```

**47. GET /comments/<comment_id>/replies** — 回复列表
```
按时间正序返回
```

---

## 5. 协作项目 projects

> 路由文件：`app/routes/projects.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 48 | POST | `/projects/` | 是 | 发起协作项目 |
| 49 | GET | `/projects/` | 是 | 项目列表 |
| 50 | GET | `/projects/<project_id>` | 是 | 项目详情 |
| 51 | PUT | `/projects/<project_id>` | 是 | 编辑项目 |
| 52 | POST | `/projects/<project_id>/apply` | 是 | 申请加入 |
| 53 | POST | `/projects/<project_id>/applications/<app_id>/approve` | 是 | 通过申请 |
| 54 | POST | `/projects/<project_id>/applications/<app_id>/reject` | 是 | 拒绝申请 |
| 55 | POST | `/projects/<project_id>/close` | 是 | 关闭项目 |
| 56 | GET | `/projects/mine` | 是 | 我的项目 |

### 接口详情

**48. POST /projects/** — 发起项目
```
Body: {
  "title": "项目标题",
  "description": "描述",
  "required_skills": [1, 2],       // 技能ID列表，最多10个
  "mode": "free|paid",
  "budget": 0,
  "deadline": "2026-12-31T00:00:00"
}
返回: { "project_id": 1, "user_id": 1, "title": "...", "required_skills": [...], ... }
错误码: 5001(参数错误) 5002(技能不存在)
```

**49. GET /projects/** — 项目列表
```
Query: page, per_page, status(recruiting/ongoing/completed/closed), mode(free/paid), skill_id
返回: 分页列表
```

**50. GET /projects/<project_id>** — 项目详情
```
发起人可见申请列表；其他用户可见成员列表（ongoing/completed状态）
返回: { "project_id": 1, "creator": {...}, "member_count": 3, "required_skills": [...], ... }
```

**51. PUT /projects/<project_id>** — 编辑项目
```
仅 recruiting 状态可编辑，仅发起人可操作
Body: 同创建，所有字段可选
```

**52. POST /projects/<project_id>/apply** — 申请加入
```
Body: { "message": "申请理由" }  // 最多500字
不能申请自己的项目，不能重复申请
返回: { "id": 1, "project_id": 1, "status": "pending", ... }
错误码: 5003(项目不存在) 5004(不能申请自己的项目) 5005(已申请过)
```

**53. POST /projects/<project_id>/applications/<app_id>/approve** — 通过申请
```
仅发起人可操作，仅 recruiting 状态可审批
通过后项目自动转为 ongoing
返回: { "id": 1, "status": "approved", ... }
错误码: 5006(申请不存在) 5007(申请已处理)
```

**56. GET /projects/mine** — 我的项目
```
Query: role(all|created|joined, 默认all)
返回: 分页列表
```

---

## 6. 通知 notifications

> 路由文件：`app/routes/notifications.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 57 | GET | `/notifications/unread-counts` | 是 | 三个Tab未读数 |
| 58 | GET | `/notifications/interaction` | 是 | 互动消息列表 |
| 59 | GET | `/notifications/todo` | 是 | 待办事项列表 |
| 60 | POST | `/notifications/<notification_id>/read` | 是 | 标记单条已读 |
| 61 | POST | `/notifications/read-all` | 是 | 批量已读 |

### 接口详情

**57. GET /notifications/unread-counts** — 未读数
```
返回: { "official": 0, "interaction": 3, "todo": 1 }
official: 与官方账号的私聊未读数
interaction: 点赞/评论/关注通知未读数
todo: 待办事项未读数
```

**58. GET /notifications/interaction** — 互动消息
```
Query: page, per_page, subtype(可选: like/comment/follow)
返回: 列表含 sender 发送者信息
```

**59. GET /notifications/todo** — 待办事项
```
Query: page, per_page
```

**61. POST /notifications/read-all** — 批量已读
```
Body: { "type": "interaction|todo" }  // 不传则全部已读
```

---

## 7. 关注 follows

> 路由文件：`app/routes/follows.py`（url_prefix=/api/v1）

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 62 | POST | `/users/<user_id>/follow` | 是 | 关注某人 |
| 63 | DELETE | `/users/<user_id>/follow` | 是 | 取消关注 |
| 64 | GET | `/users/<user_id>/follow/status` | 是 | 关注状态 |
| 65 | GET | `/following` | 是 | 我的关注列表 |
| 66 | GET | `/followers` | 是 | 我的粉丝列表 |
| 67 | GET | `/users/<user_id>/follow/stats` | 否 | 关注数/粉丝数 |

### 接口详情

**62. POST /users/<user_id>/follow** — 关注
```
不能关注自己
返回: { "is_following": true, "is_mutual": false }
同时给被关注者发互动通知
错误码: 3005(不能关注自己) 3006(已关注)
```

**64. GET /users/<user_id>/follow/status** — 关注状态
```
返回: { "is_following": true, "is_followed_by": false, "is_mutual": false }
```

**67. GET /users/<user_id>/follow/stats** — 关注/粉丝数
```
无需登录
返回: { "following_count": 10, "followers_count": 5 }
```

---

## 8. 私聊 conversations

> 路由文件：`app/routes/conversations.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 68 | GET | `/conversations/` | 是 | 最近联系人列表 |
| 69 | POST | `/conversations/with/<user_id>` | 是 | 获取/创建与某用户的会话 |
| 70 | GET | `/conversations/<conversation_id>/messages` | 是 | 私聊消息记录 |
| 71 | POST | `/conversations/<conversation_id>/messages` | 是 | 发送私聊消息 |
| 72 | POST | `/conversations/<conversation_id>/read` | 是 | 标记会话已读 |
| 73 | GET | `/conversations/official` | 是 | 获取官方会话 |

### 接口详情

**68. GET /conversations/** — 联系人列表
```
排除官方账号（官方走 /conversations/official）
按 last_message_at 倒序
返回: [{
  "conversation_id": 1,
  "contact": { "user_id": 2, "nickname": "...", "avatar": "..." },
  "last_message": "...",
  "last_message_at": "...",
  "unread_count": 3
}]
```

**69. POST /conversations/with/<user_id>** — 获取/创建会话
```
不能和自己对话
返回: { "conversation_id": 1 }
```

**70. GET /conversations/<conversation_id>/messages** — 消息记录
```
Query: page, per_page
按时间倒序
```

**71. POST /conversations/<conversation_id>/messages** — 发送消息
```
Body: {
  "msg_type": "text|image|voice|file",
  "content": "...",
  "file_name": "...",        // file类型
  "file_size": 1024,         // file类型
  "voice_duration": 30       // voice类型
}
返回: { "message_id": 1, "msg_type": "text", "content": "...", "created_at": "..." }
权限规则:
  - 官方账号(is_official=1): 自由发
  - 互关: 自由发
  - 单方面关注(任一方向): sender已发数 <= receiver已发数 + 1
    即被关注方可回复，关注方只能发1条，对方回复后可再发1条
  - 陌生人(互不关注): 拒绝
错误码: 3001(陌生人) 3002(单关注超限) 3003(会话不存在) 3007(msg_type不支持)
```

**72. POST /conversations/<conversation_id>/read** — 标记已读
```
清零未读数，更新 last_read_message_id
```

**73. GET /conversations/official** — 官方会话
```
返回: {
  "conversation_id": 1,
  "official": { "user_id": 9, "nickname": "艺联官方", "avatar": "..." },
  "unread_count": 0,
  "last_message": "...",
  "last_message_at": "..."
}
```

---

## 9. 群聊 groups

> 路由文件：`app/routes/groups.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 74 | GET | `/groups/` | 是 | 我加入的群聊列表 |
| 75 | GET | `/groups/<group_id>/messages` | 是 | 群聊消息记录 |
| 76 | POST | `/groups/<group_id>/messages` | 是 | 发送群聊消息 |
| 77 | POST | `/groups/<group_id>/read` | 是 | 标记群聊已读 |
| 78 | GET | `/groups/<group_id>/members` | 是 | 群成员列表 |
| 79 | POST | `/groups/` | 是 | 创建群聊 |
| 80 | POST | `/groups/<group_id>/invite` | 是 | 邀请加入群聊 |
| 81 | POST | `/groups/<group_id>/leave` | 是 | 退出群聊 |

### 接口详情

**74. GET /groups/** — 群聊列表
```
按 last_message_at 倒序
返回: [{
  "group_id": 1, "name": "...", "avatar": "...",
  "last_message": "...", "last_message_at": "...",
  "unread_count": 2, "member_count": 5
}]
```

**76. POST /groups/<group_id>/messages** — 发送群消息
```
Body: 同私聊（msg_type + content + 可选file_name/file_size/voice_duration）
其他群成员未读数 +1
权限: 仅群成员可发
错误码: 3004(非群成员)
```

**78. GET /groups/<group_id>/members** — 群成员
```
返回: [{
  "user_id": 1, "nickname": "...", "avatar": "...",
  "role": "owner|admin|member", "joined_at": "...", "group_nickname": "..."
}]
```

**79. POST /groups/** — 创建群聊
```
Body: { "name": "群名称", "avatar": "...", "member_ids": [2, 3] }
创建者自动成为 owner
返回: { "group_id": 1 }
```

**80. POST /groups/<group_id>/invite** — 邀请加入
```
Body: { "user_ids": [4, 5] }
仅群主/管理员可操作
```

**81. POST /groups/<group_id>/leave** — 退出群聊
```
群主不能直接退出（需先转让或解散）
错误码: 3008(群主不能直接退出)
```

---

## 10. 消息上传 messages_upload

> 路由文件：`app/routes/messages_upload.py`

### 接口列表

| # | 方法 | 路径 | 登录 | 说明 |
|---|------|------|:----:|------|
| 82 | POST | `/messages/upload` | 是 | 上传消息附件 |

```
Form: file
支持类型:
  图片: jpg/jpeg/png/gif/webp
  视频: mp4/mov
  语音: mp3/wav/m4a
  文件: pdf/doc/docx/zip/rar
限制: 20MB
返回: { "file_url": "/uploads/messages/xxx.jpg", "file_name": "...", "file_size": 1024, "file_type": "image|voice|video|file" }
```

---

## 附录

### 通用分页

```
Query: page(默认1), per_page 或 page_size(默认20, 范围1-100)
返回: { "list": [...], "total": 100, "page": 1, "page_size": 20, "total_pages": 5 }
```

### 错误码汇总

| 模块 | 错误码 | 说明 |
|------|--------|------|
| 通用 | 400/401/403/404/500 | HTTP标准 |
| 认证 | 1001-1009 | 手机号/验证码/密码/scene相关 |
| 档案 | 2001-2005 | 身份/技能/风格词汇相关 |
| 作品 | 3001-3004 | 标题/channel/files/skill_tags |
| 关注 | 3005-3006 | 关注自己/已关注 |
| 私聊 | 3001-3003/3007 | 陌生人/单关注/会话/msg_type |
| 群聊 | 3004/3008 | 非成员/群主退群 |
| 互动 | 4001-4007 | 作品/权限/已赞/评论/回复层级 |
| 项目 | 5001-5007 | 参数/技能/项目/权限/申请/状态 |

### 数据库表（共33张）

| 表名 | 说明 |
|------|------|
| users | 用户表（含is_official官方标记） |
| profiles | 档案表 |
| skills | 技能表 |
| skill_categories | 技能分类表 |
| profile_skills | 用户-技能关联表 |
| style_tags | 风格词汇表 |
| profile_style_tags | 用户-风格词汇关联表 |
| works | 作品表（软删除） |
| likes | 点赞表（唯一约束 user_id+work_id） |
| comments | 评论表（软删除，parent_id支持二级回复） |
| projects | 协作项目表 |
| project_applications | 项目申请表 |
| project_required_skills | 项目所需技能表 |
| ratings | 评价表 |
| rating_tags | 评价标签表 |
| follows | 关注关系表（follower_id+followed_id唯一） |
| notifications | 通知表（interaction/todo分类） |
| conversations | 私聊会话表（user1_id < user2_id唯一） |
| conversation_reads | 私聊未读记录表 |
| messages | 消息表（私聊+群聊合并，msg_type区分类型） |
| groups | 群聊表 |
| group_members | 群成员表（role: owner/admin/member） |
| group_reads | 群聊未读记录表 |
| work_experiences | 工作经历表 |
| work_experience_images | 工作经历图片表 |
| education_experiences | 教育经历表 |
| ability_proofs | 能力证明表 |
| ability_proof_files | 能力证明文件表 |
| events | 活动表 |
| event_participants | 活动参与表 |
| wallets | 钱包表 |
| transactions | 交易记录表（分为分单位） |
| alembic_version | 迁移版本表 |

### 测试文件

| 文件 | 覆盖模块 | 测试数 |
|------|----------|--------|
| test_auth_profile_v2.py | 认证+档案 | 39 |
| test_messages.py | 通知+关注+私聊+群聊+上传 | 26 |
| test_all_modules.py | 作品+互动+项目 | 29 |
| **合计** | **10模块82接口** | **94全通过** |
