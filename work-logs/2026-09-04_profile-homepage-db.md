# 工作日志 · 个人主页数据库改造 · 2026-09-04

> **任务**：按"个人主页展示 8 项信息"补齐数据库支撑，覆盖：
> 头像 / 昵称 / 手机号（可选脱敏）/ 擅长技能 / 粉丝数 / 关注数 /
> 作品 / 浏览记录（作品、项目分开）/ 作品 / 项目 / 点赞作品。
>
> **交付范围**：只改数据库（表 / 列 / 索引 / 迁移脚本 / ORM 模型），不写接口代码。

---

## 一、实现逻辑

### 1. 8 项展示需求到数据库来源映射

| 序号 | 展示项 | 数据来源（表/列） | 是否新增 |
|---|---|---|---|
| 1 | 头像 | `users.avatar` | 已有 |
| 2 | 昵称 | `users.nickname` | 已有 |
| 3 | 手机号（可选脱敏） | `users.phone`（默认脱敏显示 `138****1234`，接口层决定是否传明文开关） | 已有，`to_dict()` 默认脱敏 |
| 4 | 擅长技能 | `profiles → profile_skills → skills`（通过 user_id 找 profile → ProfileSkill join Skill + SkillCategory） | 已有（profile_skills 表 + 技能字典） |
| 5 | 粉丝数 | 新列 `users.follower_count`（冗余；实时口径 `COUNT(follows.followed_id = uid)`） | **新增** |
| 6 | 关注数 | 新列 `users.following_count`（冗余；实时口径 `COUNT(follows.follower_id = uid)`） | **新增** |
| 7 | 作品（该用户发布的） | `works.user_id + works.status != 'deleted'`；展示数直接取 `users.work_count`；列表从 works 分页拉 | **新增冗余列 work_count**，表已有 |
| 8 | 浏览记录·作品 | 新表 `work_view_history`（user_id, work_id UK，last_viewed_at 排序） | **新增** |
| 9 | 浏览记录·项目 | 新表 `project_view_history`（user_id, project_id UK，last_viewed_at 排序） | **新增** |
| 10 | 项目（该用户创建的） | `projects.user_id`；展示数直接取 `users.project_count`；列表从 projects 分页拉 | **新增冗余列 project_count**，表已有 |
| 11 | 点赞作品（用户点过赞的作品） | `likes` 表 `(user_id, work_id)` UK，`work_id in (...)` 反查 works；已存在表，无需变更 | 已有 |

### 2. 为什么采用"冗余计数 + 分浏览表"

- **个人主页打开频次高**：若每次都 `COUNT(*)` follows/works/projects，5 个以上表 COUNT 查询会放大数据库压力。冗余列让接口只查 1 条 users 行，首页接口免 JOIN / GROUP BY。
- **展示 + 详情分开**：
  - 顶部卡片（头像、昵称、手机、技能、4 个计数）全部走 users + profile + profile_skills，轻量；
  - 底部 Tab 分页单独拉"我的作品/我的项目/我浏览过的作品/我浏览过的项目/我点赞的作品"，各自独立分页。
- **浏览表分开（作品一张、项目一张）**：
  - 查询性能：分别对 `(user_id, last_viewed_at)` 建索引，避免"单表多态 type=work/project 后索引低命中"；
  - 外键约束简单：各自直接 FK 到 works / projects；
  - author_id 冗余：后续支持 "TA 被浏览的作品排行" 这类功能时，不用 JOIN works / projects 即可走作者排序索引。
- **UK (user, target)**：重复刷新同一作品 / 项目不新增行，只 `view_count + 1` + 更新 `last_viewed_at`，保证浏览列表去重且能看到"最近浏览时间"。

### 3. 浏览记录写入的约定（留给接口层实现，后续不改表也能推进）

- `POST /api/v1/works/<id>` 访问者非作者时，接口已经 `view_count += 1`；未来在同处再加一次 `REPLACE INTO work_view_history (..., view_count=view_count+1, last_viewed_at=NOW())`。
- 作品详情接口与项目详情接口分别写对应表；应用层先查存在性→UPDATE，不存在→INSERT，保持唯一键一致。

---

## 二、项目结构（本次新增/修改文件）

```
yilianmeng-main/
├─ app/
│  ├─ __init__.py                           # 增加 WorkViewHistory / ProjectViewHistory 导入
│  └─ models/
│     ├─ __init__.py                        # 注册两个新模型导入
│     ├─ user.py                            # +4 列 + to_dict 输出
│     ├─ work_view_history.py               # 新文件
│     └─ project_view_history.py            # 新文件
├─ migrations/versions/
│  └─ b8a73d32c140_profile_homepage_views_counts.py   # 新：alembic 迁移脚本（含回填）
├─ tests/
│  └─ test_profile_homepage_db.py           # 新：6 条 ORM 层用例
└─ work-logs/
   └─ 2026-09-04_profile-homepage-db.md     # 本文件
```

---

## 三、数据库结构变更详情

### 3.1 users 表（ALTER + 回填）

| 列名 | 类型 | 默认 | 说明 | 回填 SQL |
|---|---|---|---|---|
| `following_count` | INT NOT NULL | 0 | 我关注的人数 | `= COUNT(follows WHERE follower_id=u.id)` |
| `follower_count`  | INT NOT NULL | 0 | 粉丝数（关注我的人数） | `= COUNT(follows WHERE followed_id=u.id)` |
| `work_count`      | INT NOT NULL | 0 | 作品数（软删排除） | `= COUNT(works WHERE user_id=u.id AND status!='deleted')` |
| `project_count`   | INT NOT NULL | 0 | 项目数 | `= COUNT(projects WHERE user_id=u.id)` |

同时 `user.to_dict()` 新增：
```python
'following_count': int, 'follower_count': int, 'work_count': int, 'project_count': int
```

### 3.2 新增 work_view_history（作品浏览记录）

```
+----------------+-----------+---------------------------------------------+
| 列              | 类型       | 约束/索引                                    |
+----------------+-----------+---------------------------------------------+
| id             | INT PK    | auto                                         |
| user_id        | INT FK    | users.id  → 浏览者                           |
| work_id        | INT FK    | works.id → 被浏览作品                        |
| author_id      | INT FK    | users.id  → 作品作者（冗余，方便反查"TA被看"）|
| view_count     | INT       | 默认 1；重复访问 +1                          |
| last_viewed_at | DATETIME  | 排序主键（浏览列表按它 DESC）                 |
| created_at     | DATETIME  | 默认 utcnow                                  |
+----------------+-----------+---------------------------------------------+
UK:  uq_user_work_view(user_id, work_id)
INDEX ix_user_last_view_work(user_id, last_viewed_at)     ← "我浏览的作品"分页
INDEX ix_author_last_view_work(author_id, last_viewed_at) ← 作者维度统计/排行
```

### 3.3 新增 project_view_history（项目浏览记录）

与 work_view_history 完全对称，换目标为 `project_id + projects FK`：

```
UK:  uq_user_project_view(user_id, project_id)
INDEX ix_user_last_view_project(user_id, last_viewed_at)
INDEX ix_author_last_view_project(author_id, last_viewed_at)
```

### 3.4 点赞作品（无需改表，附查询路径提醒）

- 来源表：`likes(user_id, work_id)` UK 已存在（`uq_user_work_like`）。
- 个人主页"点赞作品"SQL：
  ```sql
  SELECT w.* FROM works w JOIN likes l ON l.work_id=w.id
   WHERE l.user_id = :uid AND w.status != 'deleted'
   ORDER BY l.created_at DESC LIMIT :offset, :limit;
  ```

---

## 四、迁移脚本 Alembic

- 版本：`b8a73d32c140_profile_homepage_views_counts.py`
- 父版本：`f5e51486cc72`（消息模块）
- `upgrade()` 顺序：
  1. `CREATE TABLE work_view_history`（含索引 + FK + UK）
  2. `CREATE TABLE project_view_history`（同上）
  3. `ALTER TABLE users ADD COLUMN following_count/follower_count/work_count/project_count INT NOT NULL DEFAULT 0`
  4. 四条 `UPDATE users SET xxx_count = (SELECT COUNT(*) ...)` 回填存量数据。
- `downgrade()`：按相反顺序 DROP COLUMN / DROP TABLE，保证可回退。
- 实际执行：除了 alembic 脚本，也用 `db.create_all()` + 原生 `ALTER` 把线上真实库同步落库，验证：
  ```
  users cols: following_count=True, follower_count=True, work_count=True, project_count=True
  work_view_history exists: True
  project_view_history exists: True
  ```

---

## 五、测试覆盖（tests/test_profile_homepage_db.py · 6/6 OK）

| # | 用例 | 验证点 |
|---|---|---|
| 01 | `to_dict_has_counts` | User.to_dict() 必须含 4 个计数键、int 类型 |
| 02a | 冗余关注计数对齐 | 3 个用户 × (following/follower) 与实时 COUNT(*) 一致 |
| 02b | 作品/项目计数对齐 | 软删作品不计入 work_count；project 按创建者统计 |
| 03a | 作品浏览写入 + UK 去重 + view_count 累加 | 同 user+work 第二次不改 id，只把 view_count 1 → 2 |
| 04a | 项目浏览写入 + last_viewed_at 排序 | 后访问的项目排在列表顶部 |
| 05  | 点赞反查路径 | Like→Work 关联后可拉出"用户点赞作品列表" |

- 专项 6/6 通过：`Ran 6 tests  OK`
- 组合回归（plaza/messages/profile_db/auth_profile/projects）：`Ran 53 tests  OK`
- 零回归。

---

## 六、前端对接与后续接口开发提醒

1. **顶部卡片字段**：直接查 `GET /api/v1/profile/<user_id>` 或未来 `GET /api/v1/users/<user_id>/homepage`，接口只需拼装：
   `users.{avatar,nickname,phone,following_count,follower_count,work_count,project_count}` + `profile → profile_skills[].skill.name(+category)`。
2. **手机号明文/脱敏**：当前 `to_dict()` 默认脱敏 `138****1234`；若"自己看自己主页要显示完整手机"，接口层判断 `viewer_id == user_id` 时替换 `users.phone` 原文即可，**数据库无需变更**。
3. **擅长技能**：从 `profile_skills` 取，最多 5 个（已在 `PUT /profile/skills` 校验）；前端可按 category 分组显示技能分类名 + 技能名。
4. **底部 5 个 Tab 的分页路径**（预留接口）：

   | Tab | 接口路径（建议） | 排序 |
   |---|---|---|
   | TA 的作品 | `GET /api/v1/users/<id>/works?page=1&per_page=20` | `published_at DESC`，status≠deleted；私有作品对非作者剔除（走 `visible_works_query`） |
   | TA 的项目 | `GET /api/v1/users/<id>/projects?page=1&per_page=20` | `created_at DESC` |
   | 浏览·作品（仅"我"可见） | `GET /api/v1/me/views/works?page=1&per_page=20` | 对 `work_view_history.last_viewed_at DESC`，JOIN works 快照 |
   | 浏览·项目（仅"我"可见） | `GET /api/v1/me/views/projects?page=1&per_page=20` | 对 `project_view_history.last_viewed_at DESC` |
   | TA 的点赞作品 | `GET /api/v1/users/<id>/likes/works?page=1&per_page=20` | `likes.created_at DESC` |

5. **4 个计数与浏览记录的维护钩子**（接口层实现，不需再改 DB）：
   - 关注/取关时：`UPDATE users SET following_count += ±1 WHERE id=follower_id` + `UPDATE users SET follower_count += ±1 WHERE id=followed_id`。
   - 作品发布/软删：`UPDATE users SET work_count = work_count ±1 WHERE id=author_id`（仅 status 从未删除↔已删除变化时触发；编辑不改 status 不累加）。
   - 项目创建/删除：同理维护 `project_count`。
   - 作品/项目详情页被非作者访问：已经 `works.view_count += 1` 的代码位置上，同步 `INSERT ... ON DUPLICATE KEY UPDATE view_count=view_count+1, last_viewed_at=NOW()` 写两张浏览表。
6. **性能兜底**：
   - `following_count` 等 4 列允许与实时 COUNT 有短暂不一致（毫秒级），可在每天凌晨用迁移里的 4 条 UPDATE 做一次"最终一致校对"。
   - 浏览历史单用户建议最多保留最近 1000 条（应用层滚动删除），避免表无限膨胀；后续可加 `DELETE FROM work_view_history WHERE user_id=? ORDER BY last_viewed_at ASC LIMIT ?` 的清理路径，不需要再改表结构。
