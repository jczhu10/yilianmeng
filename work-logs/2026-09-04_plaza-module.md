# 广场模块开发工作日志 · 2026-09-04

> **目标**：基于现有接口清单完成广场（Plaza）模块的代码实现、单元测试与文档归档。
> 模块覆盖「作品发布 4 类型 / 6 种可见权限 / 两套推流 / 点赞评论转发」全链路 MVP 能力。

---

## 一、实现逻辑

### 1. 设计要点

| 维度 | 方案 | 说明 |
|---|---|---|
| 作品类型（content_type） | `original` / `repost` / `text_only` | 原创、转发、纯文字；对应前端 4 种发布入口（图文/视频归类于 `original`） |
| 图片布局（image_layout） | `flip`（小红书翻页） / `grid`（朋友圈并排） | 仅 `channel=visual` 生效 |
| 可见性（visibility_type） | 6 种：`private` / `followers` / `mutual` / `public` / `custom_allow` / `custom_deny` | SQL 层统一通过 `visible_works_query()` 级联过滤 |
| 推流 1（推荐） | `GET /feed?sort=latest\|hot` | latest 按 `published_at DESC`；hot 热度公式 `like*2 + view + repost*1.5` |
| 推流 2（关注） | `GET /feed/following` | 仅我关注作者，纯按 `published_at DESC`，无热度 |
| 转发 | 两种入口：① POST /works content_type=repost ② POST /works/\<id\>/repost 快捷 | 写入 WorkRepost 溯源表；被转发方 repost_count +1 |
| 自定义可见 | allow_users / deny_users 最多 20 人 | 写 WorkVisibilityRule 表（work_id + rule_type + user_id 唯一） |
| 软删除 | status='deleted'，物理不删除；/mine?status=deleted 作者可见 | 与项目其他模型一致 |
| 草稿 published_at | draft 为空，publish 时写入一次 utcnow()；/mine 列表排序用 IF 实现 NULLS LAST | 兼容 MySQL（无原生 NULLS LAST） |

### 2. 可见性过滤核心

```python
# 作品列表类接口统一入口，返回已经对 user_id 可见的 published 作品 Query
q = visible_works_query(user_id)
    .filter(Work.status == 'published')
    .filter(OR(
        user_id == author,        # 作者本人任何权限可见
        visibility=='public',
        AND(visibility=='followers', author IN my_following),
        AND(visibility=='mutual',  author IN my_following AND author IN my_followers),
        AND(visibility=='custom_allow', work_id IN allow_list),
        AND(visibility=='custom_deny',  work_id NOT IN deny_list),
    ))
```

- 详情接口走 `is_work_visible_to()` 单条校验，避免不必要的 JOIN。
- 草稿对非作者一律返回 404（与已删除同表现，避免信息泄露）。

### 3. 转发计数与溯源

- 新增 `Work.repost_count`（被别人转发次数）与 `Work.share_count`（本作品发起的转发次数，MVP 保留字段）。
- `WorkRepost` 一条记录对应一条 content_type=repost 的作品；`source_work_id` XOR `source_project_id` 在应用层校验（SQL 层唯一键难表达，暂不建）。
- 详情/列表返回 `source` 快照时，若源作品已被软删或当前用户不可见，则返回 `data=None` + `reason`，保证列表渲染不出错。

---

## 二、项目结构（本次变更点）

```
yilianmeng-main/
├─ app/
│  ├─ models/
│  │   ├─ work.py                    # 新增 8 字段 + 3 索引
│  │   ├─ work_repost.py             # 新文件：转发溯源
│  │   ├─ work_visibility_rule.py    # 新文件：自定义可见
│  │   ├─ work_top.py                # 新文件：置顶池（MVP 留空）
│  │   └─ __init__.py                # 注册新模型
│  ├─ routes/
│  │   └─ works.py                   # 重写，共 14 个接口
│  └─ __init__.py                    # 注册 works blueprint
├─ tests/
│   └─ test_plaza.py                 # 新增 21 条用例
└─ work-logs/
    └─ 2026-09-04_plaza-module.md    # 本文件
```

---

## 三、接口清单（14 个 works 相关 + 2 个 interactions 复用）

### 创作 / 管理

| # | Method | Path | 功能 | 鉴权 |
|---|---|---|---|---|
| 1 | POST   | `/api/v1/works/` | 创建作品（含 4 种 content_type + 6 种 visibility + 转发 xor 校验） | ✅ |
| 2 | PUT    | `/api/v1/works/<id>` | 编辑作品（切换 visibility_type 自动清空旧规则） | ✅ 作者 |
| 3 | POST   | `/api/v1/works/<id>/publish` | 草稿 → 发布；首次发布写 published_at | ✅ 作者 |
| 4 | DELETE | `/api/v1/works/<id>` | 软删除（status=deleted） | ✅ 作者 |
| 5 | GET    | `/api/v1/works/<id>` | 作品详情（含作者、转发 source、浏览数 +1） | ✅ |
| 6 | GET    | `/api/v1/works/mine` | 我的作品（支持 status 过滤） | ✅ |
| 7 | POST   | `/api/v1/works/upload` | 图片/视频上传（multipart） | ✅ |

### 推流 / 搜索 / 筛选

| # | Method | Path | 功能 | 鉴权 |
|---|---|---|---|---|
| 8 | GET    | `/api/v1/works/feed` | 推荐推流（sort=latest/hot；channel/content_type 筛选；exclude_self=true） | ✅ |
| 9 | GET    | `/api/v1/works/feed/following` | 关注 Tab 推流（仅关注作者，时间倒序） | ✅ |
| 10| GET    | `/api/v1/works/search` | 关键词搜索（标题/描述/纯文字） | ✅ |
| 11| GET    | `/api/v1/works/by-skill` | 按技能标签筛选（JSON_CONTAINS） | ✅ |

### 互动

| # | Method | Path | 功能 | 鉴权 |
|---|---|---|---|---|
| 12 | POST   | `/api/v1/works/<id>/like`       | 点赞（复用 interactions.py） | ✅ |
| 13 | DELETE | `/api/v1/works/<id>/like`       | 取消点赞（复用 interactions.py） | ✅ |
| 14 | GET    | `/api/v1/works/<id>/likes`      | 点赞列表（复用 interactions.py） | ✅ |
| 15 | POST   | `/api/v1/works/<id>/comments`   | 发表评论（复用 interactions.py） | ✅ |
| 16 | GET    | `/api/v1/works/<id>/comments`   | 评论列表（复用 interactions.py） | ✅ |
| 17 | POST   | `/api/v1/works/<id>/repost`     | **快捷转发**（本次新增） | ✅ |

> 其中 12~16 路由实际注册在 `interactions.py`（url_prefix `/api/v1`）；17 在 `works.py` 中实现。
> 前端文档按「广场页需要的接口」口径一并列出。

---

## 四、测试覆盖（test_plaza.py）

**执行结果**：`Ran 21 tests in 0.697s  OK`

| 分组 | 用例 | 说明 |
|---|---|---|
| 创建 4 类型 | 01a 图文 grid 布局 + 9 图 + 定位 | 原创 original visual |
|        | 01b 视频 + 封面 | 原创 original video（不传 description） |
|        | 01c 纯文字长内容 | content_type=text_only，标题自动取前 200 字 |
|        | 01d 转发 via POST /works | 自动生成标题「转发：原文标题」 |
|        | 01e xor 校验 | 传两个 source 返回 400 |
| 可见性 6 种 | 02a private | A 自己可见，B 详情 404 + B feed 不出现 |
|          | 02b followers | B/C（粉丝）200，D（陌生人）404 |
|          | 02c mutual | C（互关）200，B（单向）404 |
|          | 02d custom_allow | C 可见，B/D 404 |
|          | 02e custom_deny | B 404，C/D 200 |
| 详情 7 项 | 03 | 作品本体 / 发布时间 / 作者 / like_count / comment_count / 评论列表接口可用 / 定位 |
| 推流两套 | 04a 推荐 | 包含 A 3 条 public + B 自转发 1 条；每条含 published_at/author/is_liked/like_count/comment_count/repost_count |
|        | 04b 关注 | B 关注 A，作者集合 = {A}；按 published_at DESC |
|        | 04c 无关注用户 D | 关注 Tab 总数为 0 |
| 互动 | 05a 点赞 + 取消 | like_count +1 / -1 |
|      | 05b 评论 + 列表 | 内容回查成功 |
|      | 05c 快捷转发 `/repost` | 内容类型=repost，带 source 快照，被转发 repost_count +1 |
| 管理 | 06a 草稿发布流 | 草稿 published_at=None → publish 后非空 |
|      | 06b 编辑 | title/description/location 更新；未改字段保留 |
|      | 06c 软删除 | 他人 404；作者 /mine?status=deleted 可见 |
|      | 06d mine 排序 | published 按 published_at DESC，草稿 NULL 排在最后 |

### 4.1 修复过的问题

1. **推荐 feed 默认 exclude_self=true 与断言冲突**：
   测试 04a 断言 B 的 feed 里要包含自己刚刚发出的转发帖，而推荐接口默认 `exclude_self=true`，修复为测试显式传 `exclude_self=false`，既保留行为默认值又对齐用例。

2. **MySQL NULLS LAST 兼容**：
   `/works/mine` 采用 `IF(published_at IS NULL,1,0) + published_at DESC + created_at DESC` 排序，避免 SQLite/MySQL 差异。

### 4.2 回归测试

组合执行 6 个测试模块：
- `test_auth_profile_v2` + `test_messages` + `test_plaza` + `test_works` + `test_interactions` + `test_projects`
- 结果：**Ran 47 tests  OK**

---

## 五、数据库变更（广场相关表）

### works 新增字段

| 字段 | 类型 | 说明 |
|---|---|---|
| content_type | VARCHAR(20) | original / repost / text_only |
| image_layout | VARCHAR(20) | flip / grid |
| text_content | TEXT | 纯文字内容 |
| visibility_type | VARCHAR(20) | 6 种权限值 |
| location | VARCHAR(200) | 发布地点 |
| share_count | INT | 发起转发次数 |
| repost_count | INT | 被转发次数 |
| published_at | DATETIME | 排序时间依据 |

新增索引：`(user_id, status, published_at)`、`(status, published_at)`、`(status, channel, published_at)`。

### 新表

1. `work_reposts(id, work_id UK, source_work_id, source_project_id, source_user_id, created_at)`
2. `work_visibility_rules(id, work_id, rule_type, user_id, created_at)` 含 `uq_work_rule_user(work_id, rule_type, user_id)`
3. `work_top(id, work_id UK, weight, started_at, ended_at, reason, is_active, created_at)`（MVP 留空）

---

## 六、前端对接提醒

1. **content_type 语义对齐**：
   - 视频/图文（channel=visual/video/writing）统一走 `original`；
   - 纯文字（类似发微博/朋友圈文字）走 `text_only`；title 可不传，后端自动用 text_content 前 200 字。
2. **快捷转发按钮**：直接调 `POST /api/v1/works/<id>/repost`，body 只需 `description`（可选，作为配文）+ `visibility_type` + `location`/`allow_users`/`deny_users`；title、channel、image_layout、files、skill_tags、cover_url 均继承原作品。
3. **feed 列表字段**：`location`、`repost_count`、`is_liked`、`image_layout` 已在每条直接返回，无需额外拉详情。
4. **可见性选择器**：custom_allow 必传 allow_users 数组（至少 1 人，最多 20）；custom_deny 可选传 deny_users，超出 20 返回 3008。
5. **搜索 / by-skill / feed 分页**：均走 `page + per_page`，默认 per_page=20，最大 100。
6. **published_at 才是"发布时间"**：不要显示 created_at（可能草稿留存很久）。
