# 作品发布模块开发日志

**日期**: 2026-07-31
**模块**: 作品发布（Works）
**状态**: 已完成开发与接口测试

---

## 一、实现的具体功能

### 1. 数据库变更（works 表新增 3 列）
| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | VARCHAR(20) | draft | 状态：draft/published/deleted |
| skill_tags | TEXT | [] | 技能标签ID数组（JSON） |
| updated_at | DATETIME | now() | 更新时间 |

> 不新增表，只改 works 表结构。files/collaborators/skill_tags 暂用 JSON 存储（MVP够用），后续按需拆关联表。

### 2. 接口（7 个，前缀 /api/v1/works）
| # | 方法 | 路径 | 功能 | 鉴权 |
|---|------|------|------|------|
| 1 | POST | / | 创建作品（支持草稿/直接发布） | 是 |
| 2 | PUT | /<work_id> | 编辑作品（仅作者） | 是 |
| 3 | POST | /<work_id>/publish | 发布作品（草稿->已发布） | 是 |
| 4 | DELETE | /<work_id> | 删除作品（软删除） | 是 |
| 5 | GET | /<work_id> | 作品详情（含作者信息，浏览数+1） | 是 |
| 6 | GET | /mine | 我的作品列表（可按status筛选，分页） | 是 |
| 7 | POST | /upload | 文件上传（图片/视频） | 是 |

### 3. 业务约束
- title：1-200 字符
- description：最多 2000 字符
- channel：writing / visual / video / voice（与技能分类 code 对齐）
- files：最多 9 个
- skill_tags：最多 5 个，必须为有效技能ID
- status：draft / published（创建时），deleted（软删除）
- 草稿仅作者可见
- 浏览数仅对 published 作品计数

### 4. 业务错误码
| 业务码 | 含义 | HTTP |
|--------|------|------|
| 400 | 参数错误 | 400 |
| 401 | 未认证 | 401 |
| 404 | 资源不存在 | 404 |
| 3001 | 作品不存在 | 404 |
| 3002 | 无权操作他人作品 | 403 |
| 3003 | 作品已删除 | 400 |
| 3004 | 渠道不合法 | 400 |
| 3005 | 文件数量超限 | 400 |
| 3006 | 技能标签无效 | 400 |

---

## 二、实现方式

### 1. Work 模型调整
新增 status/skill_tags/updated_at 字段，to_dict 支持 with_author 参数返回作者信息。

### 2. 软删除设计
- 删除作品时不真删，设 status=deleted
- 查询时默认过滤 status != deleted
- 删除接口用 include_deleted=True 查询（避免重复删除报错）
- 我的作品列表默认不返回已删除，可通过 ?status=deleted 查看

### 3. 草稿可见性
草稿仅作者可见，非作者访问草稿返回404（避免泄露作品存在性）。

### 4. 文件上传
复用 helpers.py 的 save_file 和 allowed_file，存到 uploads/works/ 目录。
支持类型：jpg/jpeg/png/gif/webp/mp4/mov。

### 5. 数据库迁移
- 迁移文件：migrations/versions/1391ae1b978d_add_work_status_skill_tags_updated_at.py
- 命令：flask db migrate + flask db upgrade

---

## 三、与前端的对接

### 1. 典型对接流程
1. 上传文件（可选）：POST /api/v1/works/upload (multipart/form-data) -> { url }
2. 创建作品（存草稿）：POST /api/v1/works/ body含 title/channel/files/skill_tags/status=draft
3. 编辑草稿（可多次）：PUT /api/v1/works/<work_id> 只传需要改的字段
4. 发布作品：POST /api/v1/works/<work_id>/publish
5. 查看详情：GET /api/v1/works/<work_id>
6. 我的作品列表：GET /api/v1/works/mine?page=1&page_size=20&status=published

### 2. 响应格式（统一）
成功：{ code: 200, message: "...", data: {...} }
失败：{ code: 3004, message: "渠道不合法", data: null }

### 3. 关键数据结构
作品对象含：work_id, user_id, title, description, channel, files[], cover_url,
is_collaborative, collaborators[], skill_tags[], status, view_count, like_count,
created_at, updated_at。详情接口额外返回 author 对象。

列表分页：{ list:[...], total, page, page_size, total_pages }

---

## 四、项目结构变化

- app/models/work.py            【修改】加 status/skill_tags/updated_at
- app/routes/works.py           【新增】7 个作品接口
- app/__init__.py               【修改】注册 works 蓝图
- migrations/versions/1391ae1b978d_...py  【新增】迁移文件
- work-logs/2026-07-31_works-module.md    【本文件】

---

## 五、接口测试结果

### 正常流程（9 项，全部通过）
| # | 测试 | 结果 |
|---|------|------|
| 1 | 创建草稿作品 | code=200, work_id=1, status=draft |
| 2 | 编辑作品 | title 更新成功 |
| 3 | 发布作品 | status=published |
| 4 | 获取详情 | views=1, 含author信息 |
| 5 | 我的作品列表 | total=1 |
| 5b | 按status筛选 | published -> total=1 |
| 6 | 直接发布作品 | work_id=2, status=published |
| 7 | 删除作品 | code=200, 作品已删除 |
| 7b | 删除后列表 | total=1（已删除不出现） |

### 异常流程（9 项，全部通过）
| # | 场景 | HTTP | body.code | message |
|---|------|------|-----------|---------|
| 8 | 未认证创建 | 401 | 401 | 未登录或Token过期 |
| 9 | 无效channel | 400 | 3004 | 渠道不合法 |
| 10 | 文件超限(10个) | 400 | 3005 | 文件数量超限 |
| 11 | 无效skill_tag | 400 | 3006 | 存在无效的技能标签ID |
| 12 | 标题为空 | 400 | 400 | 标题不能为空 |
| 13 | 作品不存在 | 404 | 3001 | 作品不存在 |
| 14 | 操作已删除作品 | 404 | 3001 | 作品不存在 |
| 15 | 重复删除 | 400 | 3003 | 作品已删除 |
| 16 | 无效状态参数 | 400 | 400 | 状态参数不合法 |

---

## 六、前端提醒

1. 文件上传是独立接口：先调 /upload 拿到 URL，再把 URL 放到 files 数组里调创建/编辑接口。
2. 草稿和发布分开：创建时 status 可传 draft 或 published。草稿可多次编辑，最终通过 /publish 接口发布。
3. 编辑是部分更新：PUT 接口只传需要改的字段，不传的字段保持不变。
4. channel 枚举：只接受 writing/visual/video/voice，和技能分类的 code 对齐。
5. skill_tags 是技能ID数组：不是技能名，是 skills 表的 id。前端可从 /api/v1/profile/skills 获取技能列表。
6. 删除是软删除：作品不会真删，status 变为 deleted。我的列表默认不返回已删除作品。
7. 草稿仅作者可见：非作者访问草稿作品详情会返回 404（不是 403，避免泄露作品存在性）。
8. 浏览数自动+1：每次访问已发布作品详情，view_count 自动 +1。草稿不计浏览数。
9. 文件类型限制：图片 jpg/jpeg/png/gif/webp，视频 mp4/mov。文件大小限制 500MB。
