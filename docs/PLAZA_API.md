<!-- ============================================================ -->
<!-- ⚠️  本文档已过时 (DEPRECATED) -->
<!-- 最后更新: 2026-09-13 -->
<!-- 请参阅最新文档：API.md -->
<!-- 本文件保留仅供历史参考，内容与当前代码可能不一致 -->
<!-- ============================================================ -->

# 广场模块接口文档 · Plaza API

> 模块前缀（works）：`/api/v1/works`；其余互动接口前缀：`/api/v1`
> 所有接口均需 JWT：`Authorization: Bearer <token>`；
> 统一响应体：`{ code:200|int, message:str, data:object }`；
> 统一分页：`?page=1&per_page=20`（per_page 最大 100）返回 `{ total:int, page:int, per_page:int, list:[] }`

---

## 一、作品创作 / 管理

### 1. 创建作品 POST /

**功能**：创建一条作品，可同时发布或存草稿。支持 3 种 content_type × 6 种 visibility。

**请求体 JSON**：
```json
{
  "content_type": "original | repost | text_only",   // 必填，默认 original
  "channel":      "writing | visual | video | voice", // 必填，默认 writing
  "title":        "string (max 200)",
  "description":  "string (max 2000, 选填)",
  "text_content": "string (max 5000, text_only 必填)",
  "files":        ["/uploads/works/a.jpg", "..."],   // 最多 9 条
  "cover_url":    "/uploads/works/cover.jpg",         // 选填
  "image_layout": "flip | grid",                      // visual 生效，默认 flip
  "visibility_type": "private|followers|mutual|public|custom_allow|custom_deny", // 默认 public
  "allow_users":  [101, 102],                         // custom_allow 必填，≤20
  "deny_users":   [103],                              // custom_deny 选填，≤20
  "skill_tags":   [1, 2],                             // 最多 5 个有效 ID
  "collaborators":[105],                              // 选填
  "is_collaborative": false,
  "project_id":   12,                                 // 选填
  "location":     "北京·故宫",                         // 选填
  "status":       "draft | published",                // 默认 draft

  "source_work_id":    10,  // content_type=repost 时二选一
  "source_project_id": 10   // 与 source_work_id 互斥
}
```

**响应 200**：`data = Work 对象`（见末节「公共结构」）

**典型错误码**：
- 3001 作品不存在（被转发的 source_work）
- 3004 channel 非法
- 3005 files 超 9 条
- 3006 skill_tags 无效
- 3007 visibility_type 非法
- 3008 allow/deny 用户超 20
- 3009 转发两 source 不满足 XOR

---

### 2. 编辑作品 PUT /\<id\>

**权限**：作者本人；草稿/已发布/软删除均可改（软删后改 status 仍为 deleted，除非额外 restore）。

**请求体**：同创建，字段均可选；`visibility_type` 变更会清空旧的 allow/deny 规则；`allow_users` 仅对 `custom_allow` 生效，`deny_users` 仅对 `custom_deny` 生效。

**响应 200**：`data = Work 对象`

**错误码**：
- 3001/404 作品不存在
- 3002/403 非作者无权

---

### 3. 发布作品 POST /\<id\>/publish

把草稿 `status=draft` 变更为 `published`；`published_at` 为 null 时写入 `utcnow()`。已发布直接返回。

**请求体**：无。

**响应 200**：`data = Work 对象`

---

### 4. 删除作品 DELETE /\<id\>

软删除（`status = deleted`）。作者侧 `/mine?status=deleted` 可见；他人 404。

**响应 200**：`{ code:200, message:'作品已删除' }`

**错误**：3003 作品已删除（重复删除）/ 3002 无权限。

---

### 5. 作品详情 GET /\<id\>

对浏览者做可见性校验；非作者访问时 `view_count + 1`。若作品为转发，附加 `source` 快照。

**响应 200 data = Work 对象（含 author + 可能含 source）**

```json
{
  ...所有作品字段...,
  "author": { "user_id":1,"nickname":"xx","avatar":"","mobile":"138****"},
  "source": {
    "type": "work | project",
    "source_user_id": 3,
    "data": { /*源作品/项目快照，不可见或删除则为 null*/ },
    "reason": "invisible | deleted | not_found"   // data=null 时附原因
  }
}
```

---

### 6. 我的作品列表 GET /mine

**Query**：
- `status`（选填）：draft / published / deleted；不传则排除 deleted
- `page` / `per_page`

**排序**：已发布按 `published_at DESC`；草稿 `published_at=NULL` 排在全部已发布之后（等价 NULLS LAST）；同层再按 `created_at DESC`。

**响应 200**：分页 + `list: [Work 对象]`

---

### 7. 作品文件上传 POST /upload

**Content-Type**：`multipart/form-data`，字段 `file`。

**允许类型**：jpg/jpeg/png/gif/webp/mp4/mov。

**响应 200**：`data = { "url": "/uploads/works/<uuid>.<ext>" }`

---

## 二、推流 / 搜索 / 筛选

> 全部对列表结果自动套 `visible_works_query(current_user_id)` 权限过滤，无需前端再做可见性后处理。

### 8. 推荐推流 GET /feed

**Query**：
| 参数 | 取值 | 说明 |
|---|---|---|
| `sort` | `latest`（默认） / `hot` | latest=按发布时间；hot=热度分 |
| `channel` | `writing / visual / video / voice` | 选填 |
| `content_type` | `original / repost / text_only` | 选填 |
| `exclude_self` | `true`（默认） / `false` | 是否排除自己发的作品 |
| `page` / `per_page` | 标准分页 | 最大 100 |

- **hot 热度公式**：`like_count * 2 + view_count + repost_count * 1.5`；相同热度按 `published_at DESC`。
- 列表项 **附加字段**：`author:User对象`、`is_liked:bool`、`source`（转发帖附带，规则同详情）。

**响应 200**：标准分页 + `list: [WorkListItem]`

---

### 9. 关注 Tab 推流 GET /feed/following

**Query**：`page` / `per_page`

**过滤**：`Work.user_id IN (我关注的人)`，再套权限层。

**排序**：`published_at DESC`（纯时间线，无热度）。

**响应 200**：标准分页 + `list: [WorkListItem]`；未关注任何人 → `total=0`。

---

### 10. 搜索作品 GET /search

**Query**：
- `q` 必填，≤100 字（匹配 title/description/text_content）
- `channel` / `content_type` 选填
- `page` / `per_page`

**响应 200**：标准分页 + `list: [WorkListItem]`，按 `published_at DESC`。

---

### 11. 按技能标签筛选 GET /by-skill

**Query**：
- `skill_id` 必填（int）
- `sort=latest/hot`（默认 latest）
- `page` / `per_page`

使用 MySQL `JSON_CONTAINS(works.skill_tags, CAST(skill_id AS JSON))` 匹配。

**响应 200**：标准分页 + `list: [WorkListItem]`

---

## 三、互动接口（路径前缀 /api/v1，在 interactions.py）

### 12. 点赞 / 取消点赞

| 方法 | 路径 | 说明 |
|---|---|---|
| POST   | `/works/<id>/like`   | 点赞成功 → 作品 like_count +1；已点赞幂等不重复加 |
| DELETE | `/works/<id>/like`   | 取消点赞 → like_count -1（如已点） |
| GET    | `/works/<id>/likes`  | 点赞用户列表（page/per_page） |

POST/DELETE 响应 200：`data = { "liked": true/false, "like_count": n }`

GET 响应 200：分页 list = `[{ user_id, nickname, avatar, liked_at }]`

---

### 13. 评论 / 评论列表

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/works/<id>/comments` | 发评论；body: `{ content, reply_to_comment_id(选填), reply_to_user_id(选填) }` |
| GET  | `/works/<id>/comments` | 评论列表；默认按时间倒序；page/per_page |

POST 200：`data = { comment_id, content, user, reply_to_comment_id, created_at, like_count }`

GET 200：分页 list = 评论项（含 `replies` 子数组，MVP 返回前 3 条）。

---

### 14. 快捷转发 POST /works/\<id\>/repost

**前端"转发"按钮直接调用**。内部等价于：创建一条 `content_type=repost` 作品 + 继承原作品 fields + 写 WorkRepost 溯源 + 被转发方 `repost_count + 1`。

**请求体 JSON**（全选填）：
```json
{
  "description":     "配文（max 2000），不传为空字符串",
  "visibility_type": "public",               // 默认 public
  "location":        "广州",                  // 选填
  "allow_users":     [1,2],                  // visibility_type=custom_allow 必填
  "deny_users":      [3]                     // visibility_type=custom_deny 选填
}
```

**自动继承的字段**（前端无需传）：
- `title`：`描述[:200]` 或 `转发 作品#{src.id}`
- `channel / image_layout / files / skill_tags / cover_url`：全部继承被转发作品

**响应 200 data**：新转发作品 Work 对象（带 `author` + `source` 快照）

---

## 四、公共结构

### Work 对象
```json
{
  "work_id": 101,
  "user_id": 3,
  "title": "标题",
  "description": "",
  "text_content": "纯文字内容（仅 text_only 有值）",
  "channel": "visual",
  "content_type": "original | repost | text_only",
  "image_layout": "flip | grid",
  "visibility_type": "public",
  "location": "北京·故宫",
  "files": ["/uploads/works/a.jpg"],
  "cover_url": "/uploads/works/a.jpg",
  "is_collaborative": false,
  "project_id": null,
  "collaborators": [],
  "skill_tags": [1, 2],
  "status": "published",
  "view_count": 120,
  "like_count": 8,
  "comment_count": 2,
  "share_count": 0,
  "repost_count": 1,
  "published_at": "2026-09-04T06:01:02.000123",
  "created_at": "...",
  "updated_at": "...",
  "author": {            // 列表/详情必返回
    "user_id": 3,
    "nickname": "广场A",
    "avatar": "",
    "mobile": "138****1234"
  },
  "is_liked": true,      // 列表/详情返回，当前用户是否点过赞
  "source": { /* 转发帖带 */ }
}
```

### 错误码一览
| code | 含义 |
|---|---|
| 200  | 成功 |
| 400  | 参数通用错误 |
| 401  | 未登录/Token 失效 |
| 403  | 无权限 |
| 404  | 资源不存在 |
| 3001 | 作品不存在 |
| 3002 | 无权操作他人作品 |
| 3003 | 作品已删除 |
| 3004 | channel 非法 |
| 3005 | files 数量超限（>9） |
| 3006 | skill_tags 无效（>5 或 ID 不存在） |
| 3007 | visibility_type 非法 |
| 3008 | custom allow/deny 用户数超限（>20） |
| 3009 | 转发 source_work_id / source_project_id XOR 不满足 |

---

## 五、接口速查表

| # | Method | Path | 所属文件 |
|---|---|---|---|
| 1 | POST   | `/api/v1/works/`                 | works.py |
| 2 | PUT    | `/api/v1/works/<id>`             | works.py |
| 3 | POST   | `/api/v1/works/<id>/publish`     | works.py |
| 4 | DELETE | `/api/v1/works/<id>`             | works.py |
| 5 | GET    | `/api/v1/works/<id>`             | works.py |
| 6 | GET    | `/api/v1/works/mine`             | works.py |
| 7 | POST   | `/api/v1/works/upload`           | works.py |
| 8 | GET    | `/api/v1/works/feed`             | works.py |
| 9 | GET    | `/api/v1/works/feed/following`   | works.py |
| 10| GET    | `/api/v1/works/search`           | works.py |
| 11| GET    | `/api/v1/works/by-skill`         | works.py |
| 12| POST   | `/api/v1/works/<id>/like`        | interactions.py |
| 13| DELETE | `/api/v1/works/<id>/like`        | interactions.py |
| 14| GET    | `/api/v1/works/<id>/likes`       | interactions.py |
| 15| POST   | `/api/v1/works/<id>/comments`    | interactions.py |
| 16| GET    | `/api/v1/works/<id>/comments`    | interactions.py |
| 17| POST   | `/api/v1/works/<id>/repost`      | works.py |
