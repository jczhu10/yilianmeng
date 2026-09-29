# 工作日志 · 缺失路由补全 + 文档完善 · 2026-09-15

> **任务**：自检未实现功能清单，补全 10 个缺失路由 + 更新 API.md/DATABASE.md 文档

## 一、数据库改动

**无 DDL 改动**，全部复用现有表（`events`、`event_participants`、`rating_tags`、`works`、`work_view_history`、`project_applications` 等）。

## 二、新增路由（10 个）

### 高优先级（前端阻塞，4 个）

| # | 方法 | 路径 | 文件 | 说明 |
|---|------|------|------|------|
| 97 | GET | `/projects/<id>/applications` | projects.py | 项目 owner 查看待审申请列表，支持 status 过滤+分页，复用 `build_application_item` |
| 98 | GET | `/projects/<id>/members` | projects.py | 项目成员列表（owner+approved），返回 role/joined_at |
| 100 | GET | `/events/` | events.py（新建） | 活动列表，分页+status 过滤 |
| 101 | GET | `/events/<id>` | events.py | 活动详情，含 is_joined 标记 |
| 102 | POST | `/events/<id>/join` | events.py | 参与活动（提交作品），校验作品归属+重复参与 |
| 103 | GET | `/profile/rating-tags` | profile.py | 评价标签字典，仅返回 is_active=True |

### 中优先级（功能补全，3 个）

| # | 方法 | 路径 | 文件 | 说明 |
|---|------|------|------|------|
| 104 | POST | `/works/<id>/share` | works.py | 分享计数 share_count+1 |
| 105 | DELETE | `/profile/views/works` | profile.py | 批量删除浏览记录，接受 work_ids 数组 |
| 106 | GET | `/users/search` | users.py（新建） | 用户搜索，按 nickname 模糊匹配 |

### 低优先级（1 个）

| # | 方法 | 路径 | 文件 | 说明 |
|---|------|------|------|------|
| 99 | GET | `/projects/<id>/works` | projects.py | 项目关联作品列表，按 published_at 倒序 |

## 三、新增文件

| 文件 | 说明 |
|------|------|
| `app/routes/events.py` | 活动蓝图（3 个路由 + ErrorCode 6xxx 段） |
| `app/routes/users.py` | 用户搜索蓝图 |

## 四、修改文件

| 文件 | 改动 |
|------|------|
| `app/routes/projects.py` | 追加 3 个路由（applications/members/works） |
| `app/routes/works.py` | 追加 1 个路由（share） |
| `app/routes/profile.py` | 追加 2 个路由（rating-tags / DELETE views/works） |
| `app/__init__.py` | 注册 events + users 蓝图 |
| `API.md` | 接口数 96→106，追加路由详情+上传细节+错误码完整表+字段结构说明 |

## 五、文档补全内容

### API.md 新增章节

1. **路由汇总表**：96→106 行
2. **路由详情**（#97-#106）：请求参数 + 响应结构
3. **上传接口细节**：3 个接口的字段名(file)、格式限制、大小限制、返回 JSON 示例、URL 类型（相对地址）、works.files 存储方式（URL 数组）
4. **错误码完整表**：1xxx/2xxx/3xxx/4xxx/5xxx/6xxx 全码值 + HTTP 状态 + message + 前端处理建议
5. **字段结构说明**：
   - JSON 数组字段：files/skill_tags/collaborators/tags/required_skills
   - Boolean 字段返回格式：is_collaborative=true/false vs is_read=0/1
   - 时间格式：ISO8601 无时区
   - 枚举值完整列表：image_layout、subtype、rating_tags.category 等

## 六、测试覆盖

| 测试 | 结果 |
|------|------|
| `test_messages.py`（26 用例） | ✅ PASS |
| `test_project_members_ratings.py`（31 用例） | ✅ PASS |
| `test_project_message_enhancements.py`（4 用例） | ✅ PASS |
| **合计** | **61 passed** |

## 七、接口清单（106 个）

| 模块 | 接口数 |
|------|--------|
| 认证 | 7 |
| 档案+主页 | 26 |
| 作品+广场 | 19 |
| 互动 | 2 |
| 协作项目 | 18 |
| 私信会话 | 6 |
| 群聊 | 8 |
| 消息附件 | 1 |
| 通知 | 5 |
| 关注 | 6 |
| 活动 | 3 |
| 用户搜索 | 1 |
| **合计** | **106** |

## 八、前端提醒

1. **项目待审列表**：`GET /projects/<id>/applications?status=pending` 获取待审申请，approve/reject 路由需要 `app_id`，从此接口获取
2. **项目成员列表**：`GET /projects/<id>/members` 返回 `role=owner/member` 区分发起人和成员
3. **活动模块**：`/events` 列表 + `/events/<id>` 详情 + `/events/<id>/join` 参与（需传 work_id）
4. **评价标签**：`GET /profile/rating-tags` 返回标签字典，项目互评时使用
5. **分享按钮**：`POST /works/<id>/share` 调用后 share_count+1，无返回作品对象
6. **浏览记录删除**：`DELETE /profile/views/works` body 传 `{ "work_ids": [1, 2, 3] }`
7. **用户搜索**：`GET /users/search?q=关键词` 按昵称模糊匹配
8. **上传接口**：均为单文件上传（字段名 `file`），多文件需循环调用，返回相对 URL
9. **错误码 401**：直接跳登录页，其余弹 message 提示即可
