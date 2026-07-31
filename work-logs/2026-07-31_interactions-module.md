# 互动模块开发日志

**日期**: 2026-07-31
**模块**: 互动（Interactions：点赞 + 评论）
**状态**: 已完成开发与接口测试

---

## 一、实现的具体功能

### 1. 数据库新增 2 张表

#### likes 点赞表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 主键 |
| user_id | INT FK(users.id) | 点赞用户 |
| work_id | INT FK(works.id) | 被点赞作品 |
| created_at | DATETIME | 点赞时间 |

> 联合唯一索引 `uq_user_work_like (user_id, work_id)`，数据库层防重复点赞。

#### comments 评论表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 主键 |
| user_id | INT FK(users.id) | 评论人 |
| work_id | INT FK(works.id) | 被评论作品 |
| parent_id | INT FK(comments.id) | 回复的根评论ID，NULL 为一级评论 |
| content | VARCHAR(2000) | 评论内容 |
| is_deleted | BOOLEAN | 软删除标记 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2. 接口（7 个，前缀 /api/v1）
| # | 方法 | 路径 | 功能 | 鉴权 |
|---|------|------|------|------|
| 1 | POST | /works/<work_id>/like | 点赞作品 | 是 |
| 2 | DELETE | /works/<work_id>/like | 取消点赞 | 是 |
| 3 | GET | /works/<work_id>/likes | 获取点赞用户列表（分页） | 是 |
| 4 | POST | /works/<work_id>/comments | 发表评论 / 回复 | 是 |
| 5 | GET | /works/<work_id>/comments | 获取一级评论列表（含回复数，分页） | 是 |
| 6 | DELETE | /comments/<comment_id> | 删除评论（软删除，仅作者） | 是 |
| 7 | GET | /comments/<comment_id>/replies | 获取评论的回复列表（分页） | 是 |

### 3. 业务约束
- 仅已发布（published）作品可被点赞 / 评论，草稿和已删除作品返回 4001
- 每个用户对同一作品只能点赞一次（DB 唯一索引 + 业务校验双重保障）
- 评论内容：1-2000 字符，不能为空
- 回复层级限制：只支持二级回复。parent_id 必须指向一级评论（parent_id IS NULL 的评论），不能对回复再回复
- 评论软删除：删除后内容显示为 "[已删除]"，保留回复链不断裂
- 评论仅作者可删（user_id 匹配），无权删除他人评论返回 4002
- works.like_count 与 likes 表保持同步（点赞 +1，取消 -1，下限为 0）

### 4. 业务错误码
| 业务码 | 含义 | HTTP |
|--------|------|------|
| 400 | 参数错误 | 400 |
| 401 | 未认证 | 401 |
| 4001 | 作品不存在或未发布 | 404 |
| 4002 | 无权删除他人评论 | 403 |
| 4003 | 已点赞过该作品 | 400 |
| 4004 | 未点赞过该作品 | 400 |
| 4005 | 评论/父评论不存在 | 404 |
| 4006 | 评论内容不能为空 | 400 |
| 4007 | 回复层级超限 | 400 |

---

## 二、实现方式

### 1. 模型设计
- Like / Comment 两个独立模型，均放在 app/models/interaction.py
- Comment.parent_id 自引用外键，指向 comments.id，NULL 表示一级评论
- Comment.to_dict 支持注入 user 和 reply_count，软删除时 content 显示为 "[已删除]"

### 2. 点赞去重
- DB 层：联合唯一索引 `uq_user_work_like`
- 业务层：点赞前先查 existing，已点赞返回 4003，避免触发 DB 唯一约束异常
- like_count 冗余字段：维护在 works 表，避免每次查询 count(*)，取消点赞时用 max(count-1, 0) 防负数

### 3. 评论二级回复设计
- 一级评论：parent_id = NULL
- 回复：parent_id = 一级评论 id
- 限制：回复的 parent_id 必须是一级评论（即 parent.parent_id IS NULL），否则返回 4007
- 评论列表只返回一级评论，回复通过 /comments/<id>/replies 单独拉取

### 4. 评论软删除
- 删除评论不真删，置 is_deleted = True
- to_dict 中 is_deleted=True 时 content 显示 "[已删除]"，保留 user 信息和回复链
- 已删除的评论再次删除返回成功（幂等）

### 5. 性能优化
- 点赞列表 / 评论列表 / 回复列表：批量查用户（User.query.filter(id.in_([...]))），避免 N+1 查询
- 评论列表：聚合查询统计每个一级评论的回复数（group_by parent_id + count），一次性返回 reply_count

### 6. 数据库迁移
- 迁移文件：migrations/versions/9de4bb700c38_add_likes_and_comments_tables.py
- 命令：flask db migrate + flask db upgrade

---

## 三、与前端的对接

### 1. 典型对接流程
1. 点赞：POST /api/v1/works/<work_id>/like -> { like_count }
2. 取消点赞：DELETE /api/v1/works/<work_id>/like -> { like_count }
3. 发表评论：POST /api/v1/works/<work_id>/comments body含 content（可选 parent_id 回复）
4. 查看评论：GET /api/v1/works/<work_id>/comments?page=1&page_size=20 -> 一级评论 + reply_count
5. 展开回复：GET /api/v1/comments/<comment_id>/replies?page=1&page_size=20
6. 删除评论：DELETE /api/v1/comments/<comment_id>
7. 查看点赞用户：GET /api/v1/works/<work_id>/likes?page=1&page_size=20

### 2. 响应格式（统一）
成功：{ code: 200, message: "...", data: {...} }
失败：{ code: 4003, message: "已点赞过该作品", data: null }

### 3. 关键数据结构
- 点赞对象：{ like_id, user_id, work_id, created_at, user }
- 评论对象：{ comment_id, user_id, work_id, parent_id, content, is_deleted, created_at, updated_at, user, reply_count }
- 软删除评论 content 显示 "[已删除]"，is_deleted = true
- 列表分页：{ list:[...], total, page, page_size, total_pages }

---

## 四、项目结构变化

- app/models/interaction.py        【新增】Like / Comment 模型
- app/models/__init__.py           【修改】导出 Like, Comment
- app/routes/interactions.py       【新增】7 个互动接口
- app/__init__.py                  【修改】注册 interactions 蓝图（url_prefix=/api/v1）
- migrations/versions/9de4bb700c38_...py  【新增】迁移文件
- tests/test_interactions.py       【新增】16 项接口测试
- work-logs/2026-07-31_interactions-module.md  【本文件】

---

## 五、接口测试结果

测试文件：tests/test_interactions.py，共 16 项全部通过。
测试场景：用户A创建并发布作品，用户B进行点赞 / 评论 / 回复等互动操作。

### 正常流程（全部通过）
| # | 测试 | 结果 |
|---|------|------|
| 1 | 点赞作品 | code=200, like_count +1 |
| 3 | 获取点赞列表 | 含点赞用户信息 |
| 4 | 发表一级评论 | code=200, 返回 comment_id |
| 5 | 获取评论列表 | 含 reply_count |
| 6 | 回复一级评论 | code=200, parent_id 正确 |
| 7 | 获取回复列表 | 按时间正序返回 |
| 8 | 删除自己的评论 | code=200，软删除生效 |
| 10 | 取消点赞 | like_count -1 |
| 11 | 删除评论后内容显示 | content="[已删除]" |

### 异常流程（全部通过）
| # | 场景 | HTTP | body.code | message |
|---|------|------|-----------|---------|
| 1b | 重复点赞 | 400 | 4003 | 已点赞过该作品 |
| 2 | 对未发布作品点赞 | 404 | 4001 | 作品不存在或未发布 |
| 9 | 未认证操作 | 401 | 401 | 未登录或Token过期 |
| 12 | 无权删除他人评论 | 403 | 4002 | 无权删除他人评论 |
| 13 | 空评论 | 400 | 4006 | 评论内容不能为空 |
| 14 | 评论内容超长 | 400 | 400 | 评论内容过长 |
| 15 | 父评论不存在 | 404 | 4005 | 父评论不存在 |
| 16 | 回复层级超限 | 400 | 4007 | 回复层级超限，只能回复一级评论 |

---

## 六、前端提醒

1. 点赞状态需前端自行缓存：接口不返回"当前用户是否已点赞"，前端登录后可维护本地状态或调点赞列表判断。
2. like_count 由接口实时返回：点赞 / 取消后用返回的 like_count 直接更新，无需重新拉详情。
3. 回复只能挂在一级评论下：调 /comments 时若传 parent_id，必须是某个一级评论的 id，不能传另一条回复的 id，否则返回 4007。
4. 评论列表只返回一级评论：要展示回复需单独调 /comments/<id>/replies，按时间正序排列。
5. 删除评论是软删除：删除后评论不会消失，content 变为 "[已删除]"，is_deleted=true。前端可据此展示样式（如灰色"该评论已删除"）。
6. 仅作者可删评论：作品作者也无权删除他人的评论（如需管理员/作者删除能力，后续再扩展）。
7. 作品必须是 published 才能互动：草稿 / 已删除作品点赞或评论返回 4001，与"作品不存在"同错误码（避免泄露作品存在性）。
8. 点赞 / 评论接口均需登录：未登录返回 401。
9. 分页参数：所有列表接口支持 page（默认1）和 page_size（默认20）。
