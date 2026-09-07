# 艺联萌后端 · 完整工作日志（接口 + 数据库）

> 生成日期：2026-09-07
> 接口总数：**90**  条；数据库业务表：**37** 张。
> 所有接口前缀统一为 `/api/v1`，除特别说明外均需 JWT（`Authorization: Bearer <token>`）。
> 统一响应体：`{ code:int, message:str, data:object }`；分页统一 `?page=1&per_page=20`，返回 `{ total, page, per_page, list }`。

---

## 一、接口清单（按模块分组）

### 认证模块（`/api/v1/auth`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 1 | POST | `/api/v1/auth/send-code` | `send_code` | auth.py |
| 2 | POST | `/api/v1/auth/register` | `register` | auth.py |
| 3 | POST | `/api/v1/auth/login` | `login` | auth.py |
| 4 | POST | `/api/v1/auth/reset-password` | `reset_password` | auth.py |
| 5 | POST | `/api/v1/auth/refresh` | `refresh_token` | auth.py |
| 6 | GET | `/api/v1/auth/me` | `get_me` | auth.py |
| 7 | POST | `/api/v1/auth/logout` | `logout` | auth.py |

### 私信会话模块（`/api/v1/conversations`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 8 | GET | `/api/v1/conversations` | `list_conversations` | conversations.py |
| 9 | POST | `/api/v1/conversations/with/<int:user_id>` | `get_or_create_with_user` | conversations.py |
| 10 | GET | `/api/v1/conversations/<int:conversation_id>/messages` | `list_messages` | conversations.py |
| 11 | POST | `/api/v1/conversations/<int:conversation_id>/messages` | `send_message` | conversations.py |
| 12 | POST | `/api/v1/conversations/<int:conversation_id>/read` | `mark_conversation_read` | conversations.py |
| 13 | GET | `/api/v1/conversations/official` | `get_official_conversation` | conversations.py |

### 关注模块（`/api/v1`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 14 | POST | `/api/v1/users/<int:user_id>/follow` | `follow_user` | follows.py |
| 15 | DELETE | `/api/v1/users/<int:user_id>/follow` | `unfollow_user` | follows.py |
| 16 | GET | `/api/v1/users/<int:user_id>/follow/status` | `follow_status` | follows.py |
| 17 | GET | `/api/v1/following` | `my_following` | follows.py |
| 18 | GET | `/api/v1/followers` | `my_followers` | follows.py |
| 19 | GET | `/api/v1/users/<int:user_id>/follow/stats` | `follow_stats` | follows.py |

### 群聊模块（`/api/v1/groups`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 20 | GET | `/api/v1/groups` | `list_groups` | groups.py |
| 21 | GET | `/api/v1/groups/<int:group_id>/messages` | `list_group_messages` | groups.py |
| 22 | POST | `/api/v1/groups/<int:group_id>/messages` | `send_group_message` | groups.py |
| 23 | POST | `/api/v1/groups/<int:group_id>/read` | `mark_group_read` | groups.py |
| 24 | GET | `/api/v1/groups/<int:group_id>/members` | `list_group_members` | groups.py |
| 25 | POST | `/api/v1/groups` | `create_group` | groups.py |
| 26 | POST | `/api/v1/groups/<int:group_id>/invite` | `invite_members` | groups.py |
| 27 | POST | `/api/v1/groups/<int:group_id>/leave` | `leave_group` | groups.py |

### 互动模块（`/api/v1`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 28 | POST | `/api/v1/works/<int:work_id>/like` | `like_work` | interactions.py |
| 29 | DELETE | `/api/v1/works/<int:work_id>/like` | `unlike_work` | interactions.py |
| 30 | GET | `/api/v1/works/<int:work_id>/likes` | `get_work_likes` | interactions.py |
| 31 | POST | `/api/v1/works/<int:work_id>/comments` | `create_comment` | interactions.py |
| 32 | GET | `/api/v1/works/<int:work_id>/comments` | `get_work_comments` | interactions.py |
| 33 | DELETE | `/api/v1/comments/<int:comment_id>` | `delete_comment` | interactions.py |
| 34 | GET | `/api/v1/comments/<int:comment_id>/replies` | `get_comment_replies` | interactions.py |

### 消息附件上传（`/api/v1/messages`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 35 | POST | `/api/v1/messages/upload` | `upload_message_file` | messages_upload.py |

### 消息通知模块（`/api/v1/notifications`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 36 | GET | `/api/v1/notifications/unread-counts` | `get_unread_counts` | notifications.py |
| 37 | GET | `/api/v1/notifications/interaction` | `list_interaction` | notifications.py |
| 38 | GET | `/api/v1/notifications/todo` | `list_todo` | notifications.py |
| 39 | POST | `/api/v1/notifications/<int:notification_id>/read` | `mark_read` | notifications.py |
| 40 | POST | `/api/v1/notifications/read-all` | `mark_all_read` | notifications.py |

### 档案模块（`/api/v1/profile`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 41 | GET | `/api/v1/profile/me` | `get_my_profile` | profile.py |
| 42 | PUT | `/api/v1/profile/me` | `update_my_profile` | profile.py |
| 43 | GET | `/api/v1/profile/<int:user_id>` | `get_user_profile` | profile.py |
| 44 | PUT | `/api/v1/profile/skills` | `update_my_skills` | profile.py |
| 45 | GET | `/api/v1/profile/skills/mine` | `get_my_skills` | profile.py |
| 46 | GET | `/api/v1/profile/skills/categories` | `get_skill_categories` | profile.py |
| 47 | GET | `/api/v1/profile/skills` | `get_skills` | profile.py |
| 48 | GET | `/api/v1/profile/style-tags` | `get_style_tags` | profile.py |
| 49 | PUT | `/api/v1/profile/style-tags` | `update_my_style_tags` | profile.py |
| 50 | GET | `/api/v1/profile/style-tags/mine` | `get_my_style_tags` | profile.py |
| 51 | GET | `/api/v1/profile/work-experiences` | `get_my_work_experiences` | profile.py |
| 52 | POST | `/api/v1/profile/work-experiences` | `create_work_experience` | profile.py |
| 53 | PUT | `/api/v1/profile/work-experiences/<int:exp_id>` | `update_work_experience` | profile.py |
| 54 | DELETE | `/api/v1/profile/work-experiences/<int:exp_id>` | `delete_work_experience` | profile.py |
| 55 | GET | `/api/v1/profile/education-experiences` | `get_my_education_experiences` | profile.py |
| 56 | POST | `/api/v1/profile/education-experiences` | `create_education_experience` | profile.py |
| 57 | PUT | `/api/v1/profile/education-experiences/<int:edu_id>` | `update_education_experience` | profile.py |
| 58 | DELETE | `/api/v1/profile/education-experiences/<int:edu_id>` | `delete_education_experience` | profile.py |
| 59 | GET | `/api/v1/profile/ability-proofs` | `get_my_ability_proofs` | profile.py |
| 60 | POST | `/api/v1/profile/ability-proofs` | `create_ability_proof` | profile.py |
| 61 | PUT | `/api/v1/profile/ability-proofs/<int:proof_id>` | `update_ability_proof` | profile.py |
| 62 | DELETE | `/api/v1/profile/ability-proofs/<int:proof_id>` | `delete_ability_proof` | profile.py |
| 63 | POST | `/api/v1/profile/upload` | `upload_file` | profile.py |

### 协作项目模块（`/api/v1/projects`）

> 2026-09-07 更新：新增 6 个接口（成员管理 + 互评），`create_project` / `update_project` 支持新字段 `topic` / `required_level` / `required_project_count` / `contact_visible` / `max_members` / `cover_url`。

| # | Method | Path | 函数 | 文件 | 备注 |
|---|--------|------|------|------|------|
| 64 | POST | `/api/v1/projects/` | `create_project` | projects.py | 改造：接收 6 个新字段 |
| 65 | GET | `/api/v1/projects/` | `list_projects` | projects.py | |
| 66 | GET | `/api/v1/projects/<int:project_id>` | `get_project_detail` | projects.py | |
| 67 | PUT | `/api/v1/projects/<int:project_id>` | `update_project` | projects.py | 改造：支持 6 个新字段更新 |
| 68 | POST | `/api/v1/projects/<int:project_id>/apply` | `apply_project` | projects.py | |
| 69 | POST | `/api/v1/projects/<int:project_id>/applications/<int:app_id>/approve` | `approve_application` | projects.py | |
| 70 | POST | `/api/v1/projects/<int:project_id>/applications/<int:app_id>/reject` | `reject_application` | projects.py | |
| 71 | POST | `/api/v1/projects/<int:project_id>/close` | `close_project` | projects.py | |
| 72 | GET | `/api/v1/projects/user/<int:user_id>` | `get_user_projects` | projects.py | 指定用户的项目列表 |
| 73 | GET | `/api/v1/projects/mine` | `my_projects` | projects.py | |
| 74 | GET | `/api/v1/projects/my-applications` | `my_applications` | projects.py | **新增**：我的申请列表（含动态过期标记） |
| 75 | POST | `/api/v1/projects/<int:project_id>/leave` | `leave_project` | projects.py | **新增**：成员主动退出（status→left） |
| 76 | POST | `/api/v1/projects/<int:project_id>/members/<int:user_id>/remove` | `remove_member` | projects.py | **新增**：队长踢人（status→removed） |
| 77 | POST | `/api/v1/projects/<int:project_id>/finish` | `finish_project` | projects.py | **新增**：结束项目（ongoing→completed） |
| 78 | POST | `/api/v1/projects/<int:project_id>/ratings` | `create_rating` | projects.py | **新增**：提交互评 |
| 79 | GET | `/api/v1/projects/<int:project_id>/ratings` | `list_ratings` | projects.py | **新增**：查看互评列表（匿名脱敏） |

### 作品/广场模块（`/api/v1/works`）

| # | Method | Path | 函数 | 文件 |
|---|--------|------|------|------|
| 80 | POST | `/api/v1/works` | `create_work` | works.py |
| 81 | PUT | `/api/v1/works/<int:work_id>` | `update_work` | works.py |
| 82 | POST | `/api/v1/works/<int:work_id>/publish` | `publish_work` | works.py |
| 83 | DELETE | `/api/v1/works/<int:work_id>` | `delete_work` | works.py |
| 84 | GET | `/api/v1/works/<int:work_id>` | `get_work_detail` | works.py |
| 85 | GET | `/api/v1/works/mine` | `get_my_works` | works.py |
| 86 | POST | `/api/v1/works/upload` | `upload_file` | works.py |
| 87 | GET | `/api/v1/works/feed` | `get_feed` | works.py |
| 88 | GET | `/api/v1/works/feed/following` | `get_following_feed` | works.py |
| 89 | GET | `/api/v1/works/search` | `search_works` | works.py |
| 90 | GET | `/api/v1/works/by-skill` | `get_works_by_skill` | works.py |
| 91 | POST | `/api/v1/works/<int:work_id>/repost` | `repost_work` | works.py |

---

## 二、数据库表清单（共 37 张）

| # | 表名 | 字段数 | 主键 | 唯一键数 | 外键数 |
|---|------|--------|------|----------|--------|
| 1 | `ability_proof_files` | 7 | `id` | 0 | 1 |
| 2 | `ability_proofs` | 7 | `id` | 0 | 1 |
| 3 | `comments` | 9 | `id` | 0 | 4 |
| 4 | `conversation_reads` | 6 | `id` | 1 | 2 |
| 5 | `conversations` | 6 | `id` | 1 | 2 |
| 6 | `education_experiences` | 11 | `id` | 0 | 1 |
| 7 | `event_participants` | 7 | `id` | 0 | 3 |
| 8 | `events` | 9 | `id` | 0 | 0 |
| 9 | `follows` | 4 | `id` | 1 | 2 |
| 10 | `group_members` | 6 | `id` | 1 | 2 |
| 11 | `group_reads` | 6 | `id` | 1 | 2 |
| 12 | `groups` | 10 | `id` | 0 | 2 |
| 13 | `likes` | 4 | `id` | 1 | 2 |
| 14 | `messages` | 13 | `id` | 0 | 3 |
| 15 | `notifications` | 11 | `id` | 0 | 2 |
| 16 | `profile_skills` | 4 | `id` | 1 | 2 |
| 17 | `profile_style_tags` | 4 | `id` | 1 | 2 |
| 18 | `profiles` | 5 | `id` | 1 | 1 |
| 19 | `project_applications` | 7 | `id` | 0 | 2 |
| 20 | `project_required_skills` | 6 | `id` | 1 | 2 |
| 21 | `project_view_history` | 7 | `id` | 1 | 3 |
| 22 | `projects` | 16 | `id` | 0 | 1 |
| 23 | `rating_tags` | 6 | `id` | 1 | 0 |
| 24 | `ratings` | 9 | `id` | 1 | 3 |
| 25 | `skill_categories` | 5 | `id` | 2 | 0 |
| 26 | `skills` | 6 | `id` | 0 | 2 |
| 27 | `style_tags` | 7 | `id` | 1 | 0 |
| 28 | `transactions` | 6 | `id` | 0 | 1 |
| 29 | `users` | 16 | `id` | 1 | 0 |
| 30 | `wallets` | 7 | `id` | 1 | 1 |
| 31 | `work_experience_images` | 6 | `id` | 0 | 1 |
| 32 | `work_experiences` | 11 | `id` | 0 | 1 |
| 33 | `work_reposts` | 6 | `id` | 1 | 4 |
| 34 | `work_top` | 8 | `id` | 1 | 1 |
| 35 | `work_view_history` | 7 | `id` | 1 | 3 |
| 36 | `work_visibility_rules` | 5 | `id` | 1 | 2 |
| 37 | `works` | 25 | `id` | 0 | 2 |

---

## 三、表结构明细（字段 / 类型 / 约束 / 默认值）

### 1. `ability_proof_files`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `ability_proof_id` | `INTEGER` |  | NO | `` |
| `file_url` | `VARCHAR(255)` |  | NO | `` |
| `file_name` | `VARCHAR(200)` |  | YES | `` |
| `file_type` | `VARCHAR(20)` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**索引**：
- `ability_proof_id` (`ability_proof_id`)

**外键**：
- `ability_proof_files_ibfk_1`: `ability_proof_id` → `ability_proofs.id`

---

### 2. `ability_proofs`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `profile_id` | `INTEGER` |  | NO | `` |
| `title` | `VARCHAR(200)` |  | NO | `` |
| `description` | `TEXT` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**索引**：
- `profile_id` (`profile_id`)

**外键**：
- `ability_proofs_ibfk_1`: `profile_id` → `profiles.id`

---

### 3. `comments`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `parent_id` | `INTEGER` |  | YES | `` |
| `content` | `VARCHAR(2000)` |  | NO | `` |
| `is_deleted` | `TINYINT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |
| `reply_to_user_id` | `INTEGER` |  | YES | `` |

**索引**：
- `parent_id` (`parent_id`)
- `reply_to_user_id` (`reply_to_user_id`)
- `user_id` (`user_id`)
- `work_id` (`work_id`)

**外键**：
- `comments_ibfk_1`: `parent_id` → `comments.id`
- `comments_ibfk_2`: `user_id` → `users.id`
- `comments_ibfk_3`: `work_id` → `works.id`
- `comments_ibfk_4`: `reply_to_user_id` → `users.id`

---

### 4. `conversation_reads`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `conversation_id` | `INTEGER` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `unread_count` | `INTEGER` |  | YES | `` |
| `last_read_message_id` | `INTEGER` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_conv_read_user` (`conversation_id, user_id`)

**索引**：
- UNIQUE `uq_conv_read_user` (`conversation_id, user_id`)
- `user_id` (`user_id`)

**外键**：
- `conversation_reads_ibfk_1`: `conversation_id` → `conversations.id`
- `conversation_reads_ibfk_2`: `user_id` → `users.id`

---

### 5. `conversations`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user1_id` | `INTEGER` |  | NO | `` |
| `user2_id` | `INTEGER` |  | NO | `` |
| `last_message_content` | `VARCHAR(500)` |  | YES | `` |
| `last_message_at` | `DATETIME` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_conversation_users` (`user1_id, user2_id`)

**索引**：
- `ix_conv_user1_last` (`user1_id, last_message_at`)
- `ix_conv_user2_last` (`user2_id, last_message_at`)
- UNIQUE `uq_conversation_users` (`user1_id, user2_id`)

**外键**：
- `conversations_ibfk_1`: `user1_id` → `users.id`
- `conversations_ibfk_2`: `user2_id` → `users.id`

---

### 6. `education_experiences`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `profile_id` | `INTEGER` |  | NO | `` |
| `school_level` | `VARCHAR(20)` |  | NO | `` |
| `school_name` | `VARCHAR(100)` |  | NO | `` |
| `start_year` | `INTEGER` |  | NO | `` |
| `end_year` | `INTEGER` |  | YES | `` |
| `degree` | `VARCHAR(20)` |  | YES | `` |
| `major` | `VARCHAR(80)` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**索引**：
- `profile_id` (`profile_id`)

**外键**：
- `education_experiences_ibfk_1`: `profile_id` → `profiles.id`

---

### 7. `event_participants`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `event_id` | `INTEGER` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `rank` | `INTEGER` |  | YES | `` |
| `score` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**索引**：
- `event_id` (`event_id`)
- `user_id` (`user_id`)
- `work_id` (`work_id`)

**外键**：
- `event_participants_ibfk_1`: `event_id` → `events.id`
- `event_participants_ibfk_2`: `user_id` → `users.id`
- `event_participants_ibfk_3`: `work_id` → `works.id`

---

### 8. `events`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `title` | `VARCHAR(200)` |  | NO | `` |
| `description` | `TEXT` |  | YES | `` |
| `cover_url` | `VARCHAR(255)` |  | YES | `` |
| `deadline` | `DATETIME` |  | YES | `` |
| `reward` | `INTEGER` |  | YES | `` |
| `status` | `VARCHAR(20)` |  | YES | `` |
| `participant_count` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

---

### 9. `follows`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `follower_id` | `INTEGER` |  | NO | `` |
| `followed_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_follower_followed` (`follower_id, followed_id`)

**索引**：
- `ix_followed_id` (`followed_id`)
- `ix_follower_id` (`follower_id`)
- UNIQUE `uq_follower_followed` (`follower_id, followed_id`)

**外键**：
- `follows_ibfk_1`: `followed_id` → `users.id`
- `follows_ibfk_2`: `follower_id` → `users.id`

---

### 10. `group_members`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `group_id` | `INTEGER` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `role` | `VARCHAR(10)` |  | YES | `` |
| `joined_at` | `DATETIME` |  | YES | `` |
| `nickname` | `VARCHAR(50)` |  | YES | `` |

**唯一键**：
- `uq_group_member` (`group_id, user_id`)

**索引**：
- UNIQUE `uq_group_member` (`group_id, user_id`)
- `user_id` (`user_id`)

**外键**：
- `group_members_ibfk_1`: `group_id` → `groups.id`
- `group_members_ibfk_2`: `user_id` → `users.id`

---

### 11. `group_reads`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `group_id` | `INTEGER` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `unread_count` | `INTEGER` |  | YES | `` |
| `last_read_message_id` | `INTEGER` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_group_read_user` (`group_id, user_id`)

**索引**：
- UNIQUE `uq_group_read_user` (`group_id, user_id`)
- `user_id` (`user_id`)

**外键**：
- `group_reads_ibfk_1`: `group_id` → `groups.id`
- `group_reads_ibfk_2`: `user_id` → `users.id`

---

### 12. `groups`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `name` | `VARCHAR(50)` |  | NO | `` |
| `avatar` | `VARCHAR(255)` |  | YES | `` |
| `owner_id` | `INTEGER` |  | NO | `` |
| `project_id` | `INTEGER` |  | YES | `` |
| `member_count` | `INTEGER` |  | YES | `` |
| `last_message_content` | `VARCHAR(500)` |  | YES | `` |
| `last_message_at` | `DATETIME` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**索引**：
- `owner_id` (`owner_id`)
- `project_id` (`project_id`)

**外键**：
- `groups_ibfk_1`: `owner_id` → `users.id`
- `groups_ibfk_2`: `project_id` → `projects.id`

---

### 13. `likes`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_user_work_like` (`user_id, work_id`)

**索引**：
- UNIQUE `uq_user_work_like` (`user_id, work_id`)
- `work_id` (`work_id`)

**外键**：
- `likes_ibfk_1`: `user_id` → `users.id`
- `likes_ibfk_2`: `work_id` → `works.id`

---

### 14. `messages`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `content` | `TEXT` |  | NO | `` |
| `related_id` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `conversation_type` | `VARCHAR(10)` |  | NO | `` |
| `conversation_id` | `INTEGER` |  | YES | `` |
| `group_id` | `INTEGER` |  | YES | `` |
| `sender_id` | `INTEGER` |  | NO | `` |
| `msg_type` | `VARCHAR(20)` |  | NO | `` |
| `file_name` | `VARCHAR(200)` |  | YES | `` |
| `file_size` | `BIGINT` |  | YES | `` |
| `voice_duration` | `INTEGER` |  | YES | `` |
| `related_type` | `VARCHAR(20)` |  | YES | `` |

**索引**：
- `ix_messages_created_at` (`created_at`)
- `ix_msg_conv_time` (`conversation_id, created_at`)
- `ix_msg_group_time` (`group_id, created_at`)
- `ix_msg_sender_time` (`sender_id, created_at`)

**外键**：
- `messages_ibfk_1`: `sender_id` → `users.id`
- `messages_ibfk_2`: `group_id` → `groups.id`
- `messages_ibfk_3`: `conversation_id` → `conversations.id`

---

### 15. `notifications`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `type` | `VARCHAR(20)` |  | NO | `` |
| `subtype` | `VARCHAR(30)` |  | NO | `` |
| `title` | `VARCHAR(100)` |  | YES | `` |
| `content` | `VARCHAR(500)` |  | NO | `` |
| `sender_id` | `INTEGER` |  | YES | `` |
| `related_type` | `VARCHAR(20)` |  | YES | `` |
| `related_id` | `INTEGER` |  | NO | `` |
| `is_read` | `TINYINT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**索引**：
- `ix_noti_user_created` (`user_id, created_at`)
- `ix_noti_user_type_read` (`user_id, type, is_read`)
- `ix_notifications_created_at` (`created_at`)
- `sender_id` (`sender_id`)

**外键**：
- `notifications_ibfk_1`: `sender_id` → `users.id`
- `notifications_ibfk_2`: `user_id` → `users.id`

---

### 16. `profile_skills`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `profile_id` | `INTEGER` |  | NO | `` |
| `skill_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_profile_skill` (`profile_id, skill_id`)

**索引**：
- `skill_id` (`skill_id`)
- UNIQUE `uq_profile_skill` (`profile_id, skill_id`)

**外键**：
- `profile_skills_ibfk_1`: `profile_id` → `profiles.id`
- `profile_skills_ibfk_2`: `skill_id` → `skills.id`

---

### 17. `profile_style_tags`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `profile_id` | `INTEGER` |  | NO | `` |
| `style_tag_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_profile_style_tag` (`profile_id, style_tag_id`)

**索引**：
- `style_tag_id` (`style_tag_id`)
- UNIQUE `uq_profile_style_tag` (`profile_id, style_tag_id`)

**外键**：
- `profile_style_tags_ibfk_1`: `profile_id` → `profiles.id`
- `profile_style_tags_ibfk_2`: `style_tag_id` → `style_tags.id`

---

### 18. `profiles`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |
| `identity` | `VARCHAR(30)` |  | NO | `` |

**唯一键**：
- `user_id` (`user_id`)

**索引**：
- UNIQUE `user_id` (`user_id`)

**外键**：
- `profiles_ibfk_1`: `user_id` → `users.id`

---

### 19. `project_applications`

> 2026-09-07 说明：`status` 取值扩展为 `pending` / `approved` / `rejected` / `left`（主动退出）/ `removed`（被踢）。无 DDL 改动。

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `project_id` | `INTEGER` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `message` | `TEXT` |  | YES | `` |
| `status` | `VARCHAR(20)` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `processed_at` | `DATETIME` |  | YES | `` |

**索引**：
- `project_id` (`project_id`)
- `user_id` (`user_id`)

**外键**：
- `project_applications_ibfk_1`: `project_id` → `projects.id`
- `project_applications_ibfk_2`: `user_id` → `users.id`

---

### 20. `project_required_skills`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `project_id` | `INTEGER` |  | NO | `` |
| `skill_id` | `INTEGER` |  | NO | `` |
| `required_count` | `INTEGER` |  | NO | `` |
| `filled_count` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_project_skill` (`project_id, skill_id`)

**索引**：
- `skill_id` (`skill_id`)
- UNIQUE `uq_project_skill` (`project_id, skill_id`)

**外键**：
- `project_required_skills_ibfk_1`: `project_id` → `projects.id`
- `project_required_skills_ibfk_2`: `skill_id` → `skills.id`

---

### 21. `project_view_history`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `project_id` | `INTEGER` |  | NO | `` |
| `author_id` | `INTEGER` |  | NO | `` |
| `view_count` | `INTEGER` |  | YES | `` |
| `last_viewed_at` | `DATETIME` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_user_project_view` (`user_id, project_id`)

**索引**：
- `ix_author_last_view_project` (`author_id, last_viewed_at`)
- `ix_user_last_view_project` (`user_id, last_viewed_at`)
- `project_id` (`project_id`)
- UNIQUE `uq_user_project_view` (`user_id, project_id`)

**外键**：
- `project_view_history_ibfk_1`: `user_id` → `users.id`
- `project_view_history_ibfk_2`: `project_id` → `projects.id`
- `project_view_history_ibfk_3`: `author_id` → `users.id`

---

### 22. `projects`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `title` | `VARCHAR(200)` |  | NO | `` |
| `description` | `TEXT` |  | YES | `` |
| `mode` | `VARCHAR(20)` |  | YES | `` |
| `budget` | `INTEGER` |  | YES | `` |
| `deadline` | `DATETIME` |  | YES | `` |
| `status` | `VARCHAR(20)` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |
| `max_members` | `INTEGER` |  | YES | `` |
| `cover_url` | `VARCHAR(255)` |  | YES | `` |
| `topic` | `VARCHAR(100)` |  | YES | `` |
| `required_level` | `INTEGER` |  | YES | `` |
| `required_project_count` | `INTEGER` |  | YES | `` |
| `contact_visible` | `TINYINT(1)` |  | YES | `` |

> 2026-09-07 新增 4 列：`topic` / `required_level` / `required_project_count` / `contact_visible`。

**索引**：
- `user_id` (`user_id`)

**外键**：
- `projects_ibfk_1`: `user_id` → `users.id`

---

### 23. `rating_tags`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `name` | `VARCHAR(30)` |  | NO | `` |
| `category` | `VARCHAR(20)` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `is_active` | `TINYINT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `name` (`name`)

**索引**：
- UNIQUE `name` (`name`)

---

### 24. `ratings`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `project_id` | `INTEGER` |  | NO | `` |
| `from_user_id` | `INTEGER` |  | NO | `` |
| `to_user_id` | `INTEGER` |  | NO | `` |
| `score` | `INTEGER` |  | NO | `` |
| `comment` | `TEXT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `tags` | `TEXT` |  | YES | `` |
| `is_anonymous` | `TINYINT` |  | YES | `` |

**唯一键**：
- `uq_project_from_to` (`project_id, from_user_id, to_user_id`)

**索引**：
- `from_user_id` (`from_user_id`)
- `to_user_id` (`to_user_id`)
- UNIQUE `uq_project_from_to` (`project_id, from_user_id, to_user_id`)

**外键**：
- `ratings_ibfk_1`: `from_user_id` → `users.id`
- `ratings_ibfk_2`: `project_id` → `projects.id`
- `ratings_ibfk_3`: `to_user_id` → `users.id`

---

### 25. `skill_categories`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `name` | `VARCHAR(50)` |  | NO | `` |
| `code` | `VARCHAR(20)` |  | NO | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `code` (`code`)
- `name` (`name`)

**索引**：
- UNIQUE `code` (`code`)
- UNIQUE `name` (`name`)

---

### 26. `skills`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `category_id` | `INTEGER` |  | NO | `` |
| `name` | `VARCHAR(50)` |  | NO | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `creator_id` | `INTEGER` |  | YES | `` |

**索引**：
- `category_id` (`category_id`)
- `creator_id` (`creator_id`)

**外键**：
- `skills_ibfk_1`: `category_id` → `skill_categories.id`
- `skills_ibfk_2`: `creator_id` → `users.id`

---

### 27. `style_tags`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `name` | `VARCHAR(30)` |  | NO | `` |
| `description` | `VARCHAR(200)` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `is_active` | `TINYINT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `name` (`name`)

**索引**：
- UNIQUE `name` (`name`)

---

### 28. `transactions`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `type` | `VARCHAR(20)` |  | NO | `` |
| `amount` | `INTEGER` |  | NO | `` |
| `description` | `VARCHAR(200)` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**索引**：
- `user_id` (`user_id`)

**外键**：
- `transactions_ibfk_1`: `user_id` → `users.id`

---

### 29. `users`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `phone` | `VARCHAR(20)` |  | NO | `` |
| `nickname` | `VARCHAR(50)` |  | YES | `` |
| `avatar` | `VARCHAR(255)` |  | YES | `` |
| `bio` | `VARCHAR(500)` |  | YES | `` |
| `level` | `INTEGER` |  | YES | `` |
| `exp` | `INTEGER` |  | YES | `` |
| `is_new_user` | `TINYINT` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |
| `password_hash` | `VARCHAR(255)` |  | YES | `` |
| `is_official` | `TINYINT` |  | YES | `` |
| `following_count` | `INTEGER` |  | NO | `` |
| `follower_count` | `INTEGER` |  | NO | `` |
| `work_count` | `INTEGER` |  | NO | `` |
| `project_count` | `INTEGER` |  | NO | `` |

**唯一键**：
- `phone` (`phone`)

**索引**：
- UNIQUE `phone` (`phone`)

---

### 30. `wallets`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `balance` | `INTEGER` |  | YES | `` |
| `total_earned` | `INTEGER` |  | YES | `` |
| `total_withdrawn` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `user_id` (`user_id`)

**索引**：
- UNIQUE `user_id` (`user_id`)

**外键**：
- `wallets_ibfk_1`: `user_id` → `users.id`

---

### 31. `work_experience_images`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `work_experience_id` | `INTEGER` |  | NO | `` |
| `image_url` | `VARCHAR(255)` |  | NO | `` |
| `caption` | `VARCHAR(200)` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**索引**：
- `work_experience_id` (`work_experience_id`)

**外键**：
- `work_experience_images_ibfk_1`: `work_experience_id` → `work_experiences.id`

---

### 32. `work_experiences`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `profile_id` | `INTEGER` |  | NO | `` |
| `company_name` | `VARCHAR(100)` |  | NO | `` |
| `position` | `VARCHAR(80)` |  | NO | `` |
| `start_date` | `DATE` |  | NO | `` |
| `end_date` | `DATE` |  | YES | `` |
| `is_current` | `TINYINT` |  | YES | `` |
| `description` | `TEXT` |  | YES | `` |
| `sort_order` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |

**索引**：
- `profile_id` (`profile_id`)

**外键**：
- `work_experiences_ibfk_1`: `profile_id` → `profiles.id`

---

### 33. `work_reposts`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `source_work_id` | `INTEGER` |  | YES | `` |
| `source_project_id` | `INTEGER` |  | YES | `` |
| `source_user_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | NO | `` |

**唯一键**：
- `work_id` (`work_id`)

**索引**：
- `ix_wr_src_project` (`source_project_id`)
- `ix_wr_src_user` (`source_user_id`)
- `ix_wr_src_work` (`source_work_id`)
- UNIQUE `work_id` (`work_id`)

**外键**：
- `fk_wr_src_project`: `source_project_id` → `projects.id`
- `fk_wr_src_user`: `source_user_id` → `users.id`
- `fk_wr_src_work`: `source_work_id` → `works.id`
- `fk_wr_work`: `work_id` → `works.id`

---

### 34. `work_top`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `weight` | `INTEGER` |  | NO | `` |
| `started_at` | `DATETIME` |  | NO | `` |
| `ended_at` | `DATETIME` |  | NO | `` |
| `reason` | `VARCHAR(200)` |  | YES | `` |
| `is_active` | `TINYINT` |  | NO | `` |
| `created_at` | `DATETIME` |  | NO | `` |

**唯一键**：
- `work_id` (`work_id`)

**索引**：
- `ix_wt_active_time` (`is_active, started_at, ended_at`)
- `ix_wt_weight` (`weight`)
- UNIQUE `work_id` (`work_id`)

**外键**：
- `fk_wt_work`: `work_id` → `works.id`

---

### 35. `work_view_history`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `author_id` | `INTEGER` |  | NO | `` |
| `view_count` | `INTEGER` |  | YES | `` |
| `last_viewed_at` | `DATETIME` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |

**唯一键**：
- `uq_user_work_view` (`user_id, work_id`)

**索引**：
- `ix_author_last_view_work` (`author_id, last_viewed_at`)
- `ix_user_last_view_work` (`user_id, last_viewed_at`)
- UNIQUE `uq_user_work_view` (`user_id, work_id`)
- `work_id` (`work_id`)

**外键**：
- `work_view_history_ibfk_1`: `user_id` → `users.id`
- `work_view_history_ibfk_2`: `work_id` → `works.id`
- `work_view_history_ibfk_3`: `author_id` → `users.id`

---

### 36. `work_visibility_rules`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `work_id` | `INTEGER` |  | NO | `` |
| `rule_type` | `VARCHAR(10)` |  | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `created_at` | `DATETIME` |  | NO | `` |

**唯一键**：
- `uq_work_rule_user` (`work_id, rule_type, user_id`)

**索引**：
- `fk_wvr_user` (`user_id`)
- `ix_work_rule` (`work_id, rule_type`)
- UNIQUE `uq_work_rule_user` (`work_id, rule_type, user_id`)

**外键**：
- `fk_wvr_user`: `user_id` → `users.id`
- `fk_wvr_work`: `work_id` → `works.id`

---

### 37. `works`

| 字段 | 类型 | 主键 | 可空 | 默认值 |
|------|------|------|------|--------|
| `id` | `INTEGER` | PK | NO | `` |
| `user_id` | `INTEGER` |  | NO | `` |
| `title` | `VARCHAR(200)` |  | NO | `` |
| `description` | `TEXT` |  | YES | `` |
| `channel` | `VARCHAR(50)` |  | YES | `` |
| `files` | `TEXT` |  | YES | `` |
| `cover_url` | `VARCHAR(255)` |  | YES | `` |
| `is_collaborative` | `TINYINT` |  | YES | `` |
| `collaborators` | `TEXT` |  | YES | `` |
| `view_count` | `INTEGER` |  | YES | `` |
| `like_count` | `INTEGER` |  | YES | `` |
| `created_at` | `DATETIME` |  | YES | `` |
| `skill_tags` | `TEXT` |  | YES | `` |
| `content_type` | `VARCHAR(20)` |  | NO | `` |
| `image_layout` | `VARCHAR(20)` |  | NO | `` |
| `text_content` | `TEXT` |  | YES | `` |
| `visibility_type` | `VARCHAR(20)` |  | NO | `` |
| `location` | `VARCHAR(200)` |  | YES | `` |
| `share_count` | `INTEGER` |  | NO | `` |
| `repost_count` | `INTEGER` |  | NO | `` |
| `published_at` | `DATETIME` |  | YES | `` |
| `status` | `VARCHAR(20)` |  | YES | `` |
| `updated_at` | `DATETIME` |  | YES | `` |
| `project_id` | `INTEGER` |  | YES | `` |
| `comment_count` | `INTEGER` |  | YES | `` |

**索引**：
- `idx_status_channel` (`status, channel, published_at`)
- `idx_status_published` (`status, published_at`)
- `idx_user_status_published` (`user_id, status, published_at`)
- `project_id` (`project_id`)

**外键**：
- `works_ibfk_1`: `user_id` → `users.id`
- `works_ibfk_2`: `project_id` → `projects.id`

---
