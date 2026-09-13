# 工作日志 · 项目卡片/详情增强 + 消息类型扩展 · 2026-09-13

> **任务**：补全 4 项功能——项目卡片展示已招募队友头像、项目详情队长增加技能列表与参与项目次数、私聊支持项目邀请消息、群聊支持互评请求消息。
> **方案**：复用现有表结构，不新增数据库表；通过扩展 `build_project_item` 返回字段、扩展 `msg_type` 枚举实现。

## 一、数据库改动

**无 DDL 改动**，全部复用现有表：

| 复用表 | 用途 |
|--------|------|
| `project_applications` | `status='approved'` 的记录即项目成员，用于统计成员头像与参与次数 |
| `profiles` / `profile_skills` / `skills` | 队长技能列表通过 `Profile → ProfileSkill → Skill` 关联查询 |
| `messages` | `msg_type` 字段扩展 `project_invite` / `rating_request` 取值 |

## 二、代码改动（3 个路由文件）

### 1. `app/routes/projects.py` — `build_project_item` 增强

**import 增加**：`Profile, ProfileSkill`

**返回字段新增**：

```python
item['member_avatars'] = [
    {'user_id': uid, 'avatar': ..., 'nickname': ...},
    ...  # 前 5 个成员（含发起人）
]

item['creator'] = {
    ...creator.to_dict(),
    'skills': [skill.to_dict(), ...],           # 队长技能列表
    'joined_project_count': int                 # 作为 approved 成员的项目数
}
```

**实现逻辑**：
- `member_avatars`：取 `[project.user_id] + approved_apps[:4].user_id`，批量查 User 取 avatar/nickname
- `creator.skills`：通过 `Profile.user_id == creator.id` 找 profile，再查 `ProfileSkill` 关联的 Skill
- `creator.joined_project_count`：`ProjectApplication.query.filter_by(user_id=creator.id, status='approved').count()`

### 2. `app/routes/conversations.py` — 私聊 `project_invite`

**`ALLOWED_MSG_TYPES` 增加** `'project_invite'`

**发送消息流程**：
1. 校验 `project_id` 必填且项目存在
2. `content` 存为 `str(project_id)`
3. 会话预览 `last_message_content = '[项目邀请]'`
4. 响应返回 `project` 摘要：`{project_id, title, cover_url, status}`

### 3. `app/routes/groups.py` — 群聊 `rating_request`

**`ALLOWED_MSG_TYPES` 增加** `'rating_request'`

**发送消息流程**：
1. 校验 `project_id` 必填且项目存在
2. `content` 存为 `str(project_id)`
3. 群预览 `last_message_content = '[互评请求]'`
4. 响应返回 `project` 摘要：`{project_id, title, cover_url, status}`

## 三、接口响应字段变更

### 项目卡片/详情接口（`GET /api/v1/projects/{id}`、列表接口）

`data` 新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `member_avatars` | array | 已招募成员头像列表，最多 5 个（含发起人），每项 `{user_id, avatar, nickname}` |
| `creator.skills` | array | 队长技能列表，每项为 Skill 对象 |
| `creator.joined_project_count` | int | 队长作为已通过成员参与的项目数 |

### 私聊消息接口（`POST /api/v1/conversations/{id}/messages`）

`msg_type='project_invite'` 时响应 `data` 新增：

| 字段 | 类型 | 说明 |
|------|------|------|
| `project` | object | `{project_id, title, cover_url, status}` |

### 群聊消息接口（`POST /api/v1/groups/{id}/messages`）

`msg_type='rating_request'` 时响应 `data` 新增：

| 字段 | 类型 | 说明 |
|------|------|------|
| `project` | object | `{project_id, title, cover_url, status}` |

## 四、测试覆盖矩阵

| 测试用例 | 文件 | 验证点 | 结果 |
|----------|------|--------|------|
| `test_01_member_avatars` | `tests/test_project_message_enhancements.py` | 项目详情返回 2 个成员头像（发起人+1 approved 成员），顺序正确 | ✅ PASS |
| `test_02_creator_skills_and_joined_count` | 同上 | 队长 skills 列表非空，joined_project_count=1 | ✅ PASS |
| `test_03_private_project_invite` | 同上 | 互关用户发送 project_invite，响应含 project 摘要 | ✅ PASS |
| `test_04_group_rating_request` | 同上 | 群成员发送 rating_request，响应含 project 摘要 | ✅ PASS |
| 回归 `test_messages.py`（26 用例） | `tests/test_messages.py` | 私聊/群聊/关注/通知全流程无破坏 | ✅ PASS |
| 回归 `test_project_members_ratings.py`（31 用例） | `tests/test_project_members_ratings.py` | 项目申请/成员/互评全流程无破坏 | ✅ PASS |

> 测试文件 `test_project_message_enhancements.py` 已重写：使用 Bearer Token 鉴权（替代原 session_transaction）、随机手机号避免冲突、每个用例 tearDown 清理数据。

## 五、问题修复记录

| # | 问题 | 原因 | 修复 |
|---|------|------|------|
| 1 | 测试 401 未登录 | 原测试用 `session_transaction` 设置 session，但实际鉴权是 Bearer Token | 改用 `create_token(uid)` + `Authorization: Bearer` 头 |
| 2 | 测试手机号冲突 | 多次运行同一硬编码手机号导致唯一约束冲突 | 改用 `199 + 8位随机数` 生成唯一手机号 |
| 3 | `SkillCategory` 插入失败 | `code` 字段 NOT NULL 且 UNIQUE，未传值 | 测试中传入唯一 `code` |
| 4 | `Skill` 插入 FK 失败 | `creator_id` 默认 0，无对应用户 | 测试中复用已有 Skill，或创建时指定 `creator_id` |
| 5 | `Group` 构造失败 | 模型字段是 `owner_id` 非 `creator_id` | 测试中改用 `owner_id` |
| 6 | 测试间 session 污染 | scoped session 共享，前一个测试失败导致后续 session 脏 | `setUp` 中 `db.session.remove()` 重置 |

## 六、前端提醒

1. **项目卡片**：新增 `member_avatars` 数组（最多 5 项），每项含 `user_id`/`avatar`/`nickname`，可直接渲染头像列表；超过 5 人时展示 "+N"。
2. **项目详情队长区**：`creator` 对象新增 `skills`（技能数组）和 `joined_project_count`（参与项目数），需在队长信息卡片展示。
3. **私聊 `project_invite` 消息**：前端收到 `msg_type='project_invite'` 时，从 `data.project` 取项目摘要渲染项目邀请卡片，点击可跳转项目详情。
4. **群聊 `rating_request` 消息**：前端收到 `msg_type='rating_request'` 时，从 `data.project` 取项目摘要渲染互评请求卡片，点击可跳转互评页面。
5. 两种新消息类型的 `content` 字段存储的是 `project_id` 字符串，前端无需依赖 content 展示，应以 `data.project` 为准。
