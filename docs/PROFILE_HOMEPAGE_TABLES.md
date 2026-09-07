# 个人主页数据库表结构（Markdown 表格形式 · 对齐 docs/DATABASE_DESIGN.md 风格）

> 覆盖范围：本轮"个人主页展示"新增 / 变更的 3 张表（2 张新表 + 1 张 users 改列）。
> 字段表格风格：`| 字段 | 类型 | 约束 | 默认值 | 说明 |`
> 索引 / 唯一键 / 外键 单独一节列出，保持与 `DATABASE_DESIGN.md` 一致。

---

## 一、表总览（本次新增 / 变更）

| # | 表名 | 状态 | 所属模块 | 模型文件 |
|---|------|------|----------|----------|
| 1 | **users**（改列） | 🔧改造（+4 冗余计数 + 批量回填） | 认证 / 个人主页 | `app/models/user.py` |
| 2 | **work_view_history** | 🆕新建 | 个人主页·浏览记录 | `app/models/work_view_history.py` |
| 3 | **project_view_history** | 🆕新建 | 个人主页·浏览记录 | `app/models/project_view_history.py` |

> 依赖的其他既有表（不改动，只作为个人主页数据源）：
> `profiles`、`profile_skills`、`skills`（擅长技能）、`follows`（关注关系）、
> `works`（作品列表）、`projects`（项目列表）、`likes`（点赞作品）。

---

## 二、users — 用户表（🔧改造：新增 4 个冗余计数字段）

> 改造动机：个人主页头部"粉丝数 / 关注数 / 作品数 / 项目数"高频展示，避免每次 4 次 COUNT 查询。
> 新增列均为 `INT NOT NULL DEFAULT 0`；已对存量用户按真实行数回填。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 用户ID（不变） |
| phone | VARCHAR(20) | UNIQUE, NOT NULL | — | 手机号（登录凭证；接口层默认脱敏展示 `138****1234`） |
| nickname | VARCHAR(50) |  | `'用户'` | 昵称 |
| avatar | VARCHAR(255) |  | `''` | 头像 URL |
| bio | VARCHAR(500) |  | `''` | 个人简介 |
| level | INT |  | `1` | 等级 |
| exp | INT |  | `0` | 经验值 |
| is_new_user | BOOLEAN |  | `TRUE` | 是否新用户 |
| password_hash | VARCHAR(255) |  | `NULL` | 密码哈希（werkzeug） |
| is_official | BOOLEAN |  | `FALSE` | 0=普通用户 / 1=官方账号（消息模块已用） |
| **🆕 following_count** | **INT** | **NOT NULL** | **`0`** | **我关注的人数**（实时口径：`COUNT(follows WHERE follower_id=users.id)`） |
| **🆕 follower_count**  | **INT** | **NOT NULL** | **`0`** | **粉丝数**（实时口径：`COUNT(follows WHERE followed_id=users.id)`） |
| **🆕 work_count**      | **INT** | **NOT NULL** | **`0`** | **我发布的作品数**（实时口径：`COUNT(works WHERE user_id=users.id AND status!='deleted')`） |
| **🆕 project_count**   | **INT** | **NOT NULL** | **`0`** | **我创建的项目数**（实时口径：`COUNT(projects WHERE user_id=users.id)`） |
| created_at | DATETIME |  | `utcnow` | 注册时间 |
| updated_at | DATETIME |  | `onupdate utcnow` | 最后更新时间 |

**索引 / 键（不变）**：
- 主键：`PRIMARY KEY (id)`
- 唯一键：`UNIQUE KEY phone (phone)`

**回填 SQL（已在真实库执行）**：
```sql
UPDATE users u SET following_count = (SELECT COUNT(*) FROM follows f WHERE f.follower_id = u.id);
UPDATE users u SET follower_count  = (SELECT COUNT(*) FROM follows f WHERE f.followed_id = u.id);
UPDATE users u SET work_count      = (SELECT COUNT(*) FROM works w  WHERE w.user_id = u.id AND w.status <> 'deleted');
UPDATE users u SET project_count   = (SELECT COUNT(*) FROM projects p WHERE p.user_id = u.id);
```

---

## 三、work_view_history — 作品浏览记录表（🆕新建）

> 支撑"个人主页 → 浏览记录 → 作品"Tab。
> 业务约定：同一用户重复浏览同一作品，不新增行，只累加 `view_count` 并刷新 `last_viewed_at`；
> 列表展示按 `last_viewed_at DESC` 排序。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 主键 |
| user_id | INT | FK→users.id, NOT NULL | — | **浏览者**（谁看了） |
| work_id | INT | FK→works.id, NOT NULL | — | **被浏览的作品**（看了哪条） |
| author_id | INT | FK→users.id, NOT NULL | — | **作品作者**（冗余字段，省 JOIN；支持后续"TA被浏览的作品"维度查询） |
| view_count | INT | NOT NULL | `1` | 该 user 对该 work 的**累计浏览次数** |
| last_viewed_at | DATETIME |  | `utcnow` | **最近一次浏览时间**（列表排序主键） |
| created_at | DATETIME |  | `utcnow` | 首次浏览时间（UK 命中后不更新） |

**键与索引**：

| 类型 | 名称 | 字段 | 作用 |
|------|------|------|------|
| 主键 | `PRIMARY` | `id` | — |
| 唯一键 | `uq_user_work_view` | `(user_id, work_id)` | 同一人对同一作品只保留 1 行，保证浏览去重 & `view_count` 累加语义 |
| 普通索引 | `work_id` | `work_id` | MySQL FK 自动辅助索引 |
| 普通索引 | `ix_user_last_view_work` | `(user_id, last_viewed_at)` | **核心查询索引**："我浏览过的作品"分页，无需回表排序 |
| 普通索引 | `ix_author_last_view_work` | `(author_id, last_viewed_at)` | 预留：按作者维度查询最近被浏览的作品 |

**外键**：
- `FOREIGN KEY (user_id)   REFERENCES users(id)`
- `FOREIGN KEY (work_id)   REFERENCES works(id)`
- `FOREIGN KEY (author_id) REFERENCES users(id)`

---

## 四、project_view_history — 项目浏览记录表（🆕新建）

> 支撑"个人主页 → 浏览记录 → 项目"Tab。结构与 `work_view_history` 完全对称，仅目标实体从作品改为项目。
> 相同业务约定：同一 (user, project) 不新增行，仅 `view_count + 1`、`last_viewed_at = NOW()`。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 主键 |
| user_id | INT | FK→users.id, NOT NULL | — | **浏览者**（谁看了） |
| project_id | INT | FK→projects.id, NOT NULL | — | **被浏览的项目**（看了哪个） |
| author_id | INT | FK→users.id, NOT NULL | — | **项目创建者**（冗余字段） |
| view_count | INT | NOT NULL | `1` | 该 user 对该 project 的**累计浏览次数** |
| last_viewed_at | DATETIME |  | `utcnow` | **最近一次浏览时间**（列表排序主键） |
| created_at | DATETIME |  | `utcnow` | 首次浏览时间 |

**键与索引**：

| 类型 | 名称 | 字段 | 作用 |
|------|------|------|------|
| 主键 | `PRIMARY` | `id` | — |
| 唯一键 | `uq_user_project_view` | `(user_id, project_id)` | 同一人对同一项目只保留 1 行 |
| 普通索引 | `project_id` | `project_id` | MySQL FK 自动辅助索引 |
| 普通索引 | `ix_user_last_view_project` | `(user_id, last_viewed_at)` | **核心查询索引**："我浏览过的项目"分页 |
| 普通索引 | `ix_author_last_view_project` | `(author_id, last_viewed_at)` | 预留：作者维度统计 |

**外键**：
- `FOREIGN KEY (user_id)    REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES projects(id)`
- `FOREIGN KEY (author_id)  REFERENCES users(id)`

---

## 五、个人主页 8 项展示 ↔ 表/字段查询路径总表（便于复核）

| 展示项 | 表名 | 字段 / 关联路径 | 分页 / 排序 |
|---|---|---|---|
| 头像 / 昵称 / 手机号 | users | `avatar` / `nickname` / `phone`（手机号接口层按 viewer 是否本人决定明文或脱敏） | — |
| 擅长技能 | profiles → profile_skills → skills + skill_categories | `profiles.user_id = uid` → `profile_skills.profile_id` → `skills.id` → `skill_categories.id` | 最多 5 条；按 `skill_categories.sort_order, skills.sort_order` |
| 粉丝数 / 关注数 | users | `follower_count` / `following_count`（冗余列；实时值兜底同 follows COUNT） | — |
| 作品（TA 的作品） | works | `works.user_id = uid AND works.status != 'deleted'`，展示总数直接取 `users.work_count` | 按 `published_at DESC`，分页；需套用 `visible_works_query(viewer_id)` 权限过滤 |
| 浏览·作品（仅"我"可见） | work_view_history → works | `WHERE user_view_history.user_id = 我.id` JOIN works | 按 `last_viewed_at DESC` 分页 |
| 浏览·项目（仅"我"可见） | project_view_history → projects | `WHERE user_project_view.user_id = 我.id` JOIN projects | 按 `last_viewed_at DESC` 分页 |
| 项目（TA 创建的项目） | projects | `WHERE projects.user_id = uid`，展示总数直接取 `users.project_count` | 按 `created_at DESC` 分页 |
| 点赞作品（TA 点过赞的作品） | likes → works | `WHERE likes.user_id = uid` JOIN works，且 `works.status != 'deleted'` | 按 `likes.created_at DESC` 分页（likes 表未改，`uq_user_work_like` 已保证去重） |

---

## 六、存储引擎 / 字符集（与其他表一致）

- `ENGINE=InnoDB`
- `DEFAULT CHARSET=utf8mb4`
- `COLLATE=utf8mb4_unicode_ci`
- Alembic 迁移脚本：`migrations/versions/b8a73d32c140_profile_homepage_views_counts.py`（含 `upgrade()` 建表/加列/回填 与 对等 `downgrade()` 回退）
