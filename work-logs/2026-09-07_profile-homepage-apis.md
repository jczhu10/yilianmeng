# 工作日志 · 个人主页接口补齐 · 2026-09-07

> **任务**：补全个人主页所需的全部接口——聚合主页、他人作品/项目列表、点赞作品、浏览记录（写入+查询）。数据库零改动，全部基于已有表。

## 一、数据库改动

**零改动。** 所有表和字段均已存在（上一轮个人主页数据库改造已建好）：
- `users`：avatar / nickname / phone / level / follower_count / following_count / work_count / project_count
- `profiles` + `profile_skills` + `skills`：擅长技能
- `works` / `projects`：用户作品/项目
- `likes`：点赞关系
- `work_view_history` / `project_view_history`：浏览记录

## 二、接口改动（4 个文件，新增 6 个接口 + 改 2 处写入逻辑）

### 1. `app/models/user.py` — to_dict 增加手机可见性控制

`to_dict(self, show_full_phone=False)`：
- `show_full_phone=True` → 返回完整手机号（自己看自己）
- `show_full_phone=False`（默认）→ 脱敏 `138****1234`（他人查看）

### 2. `app/routes/profile.py` — 新增 3 个接口

| Method | Path | 说明 |
|--------|------|------|
| GET | `/profile/homepage/<user_id>` | 个人主页聚合：头像/昵称/手机/技能/计数/关注关系（is_following/is_followed_by/is_mutual/is_self） |
| GET | `/profile/views/works` | 我浏览过的作品列表（按 last_viewed_at 倒序，含作品摘要+作者） |
| GET | `/profile/views/projects` | 我浏览过的项目列表（同上） |

聚合接口返回结构：
```json
{
  "user": { "user_id", "nickname", "avatar", "phone", "level", "follower_count", "following_count", "work_count", "project_count" },
  "profile": { "identity", "skills": [...], "style_tags": [...] },
  "is_following": false,
  "is_followed_by": false,
  "is_mutual": false,
  "is_self": false
}
```

### 3. `app/routes/works.py` — 新增 2 个接口 + 详情页写浏览记录

| Method | Path | 说明 |
|--------|------|------|
| GET | `/works/user/<user_id>` | 他人作品列表（复用 `visible_works_query` 做可见性过滤，私密/权限作品不返回） |
| GET | `/works/user/<user_id>/liked` | 该用户点赞过的作品（JOIN likes，按点赞时间倒序） |

`get_work_detail()` 改动：非作者访问已发布作品时，除 `view_count+1` 外，同步写 `work_view_history`（UPSERT：已存在则 `view_count+1` + 更新 `last_viewed_at`，不存在则新建）。

### 4. `app/routes/projects.py` — 新增 1 个接口 + 详情页写浏览记录

| Method | Path | 说明 |
|--------|------|------|
| GET | `/projects/user/<user_id>` | 他人项目列表（按创建时间倒序） |

`get_project_detail()` 改动：非发起人访问时写 `project_view_history`（同样 UPSERT）。

## 三、边界处理

| 场景 | 处理 |
|------|------|
| 自己看自己主页 | `is_self=true`，手机号完整显示 |
| 他人看主页 | 手机号脱敏，`is_self=false` |
| 自己浏览自己作品/项目 | 不写浏览记录 |
| 重复浏览同一作品/项目 | 不新增行，`view_count` 累加 + `last_viewed_at` 更新 |
| 他人作品列表可见性 | 复用 `visible_works_query`，私密/无权限作品不返回 |
| 点赞作品列表 | 只返回 `published` 且未删除的作品 |

## 四、测试覆盖（tests/test_profile_homepage.py · 9/9 OK）

| # | 用例 | 验证点 |
|---|------|--------|
| 01 | 他人视角主页聚合 | 返回头像/昵称/脱敏手机/计数/互关关系 |
| 02 | 自己视角主页聚合 | `is_self=true`，手机号完整 |
| 03 | 单向关注视角 | `is_following=true, is_followed_by=false, is_mutual=false` |
| 04 | 他人作品列表 | A 的公开作品出现在列表中 |
| 05 | 点赞作品列表 | B 点赞后，A 查 B 的 liked 列表含该作品 |
| 06 | 作品浏览记录 | B 浏览 A 作品两次 → view_count=2，浏览记录接口可见 |
| 07 | 项目浏览记录 | B 浏览 A 项目 → 记录写入，接口可见 |
| 08 | 他人项目列表 | A 的项目出现在列表中 |
| 09 | 自浏览不写记录 | A 浏览自己作品 → 无浏览记录 |

**回归测试**：`test_profile_homepage + test_plaza + test_interactions + test_projects + test_notification_triggers + test_messages` → **Ran 63 tests · OK**

## 五、前端对接提醒

1. **个人主页顶部**：调 `GET /api/v1/profile/homepage/<user_id>` 一次拿全（头像/昵称/手机/技能/4个计数/关注关系），无需拼多个接口。
2. **关注按钮状态**：根据返回的 `is_following` 控制"关注/已关注"，`is_mutual` 可显示"互相关注"。
3. **作品 Tab**：`GET /api/v1/works/user/<user_id>`（带可见性过滤，私密作品不会泄露）。
4. **项目 Tab**：`GET /api/v1/projects/user/<user_id>`。
5. **点赞 Tab**：`GET /api/v1/works/user/<user_id>/liked`。
6. **浏览记录 Tab**：分两个子 Tab，分别调 `/profile/views/works` 和 `/profile/views/projects`。
7. **浏览记录自动写入**：作品详情 `GET /works/<id>` 和项目详情 `GET /projects/<id>` 已自动写浏览记录，前端无需额外调用。
