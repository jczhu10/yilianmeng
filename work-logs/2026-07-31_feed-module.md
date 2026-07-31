# 作品推荐推流模块开发日志

**日期**: 2026-07-31
**模块**: 作品推荐推流（Feed / Search / BySkill）
**状态**: 已完成开发与接口测试

---

## 一、实现的具体功能

### 1. 新增 3 个接口（归入 works 蓝图，前缀 /api/v1/works）
| # | 方法 | 路径 | 功能 | 鉴权 |
|---|------|------|------|------|
| 8 | GET | /works/feed | 首页推荐推流（排序+筛选） | 是 |
| 9 | GET | /works/search | 搜索作品（关键词+channel） | 是 |
| 10 | GET | /works/by-skill | 按技能标签筛选作品 | 是 |

### 2. feed 推流接口参数
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| sort | string | latest | 排序：latest(最新)/hot(热门) |
| channel | string | - | 筛选：writing/visual/video/voice |
| exclude_self | bool | true | 是否排除自己的作品 |
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数（上限100） |

### 3. 排序策略
- **latest（最新）**：按 created_at 倒序
- **hot（热门）**：热度分 = like_count * 2 + view_count，按热度倒序，相同分按时间倒序

### 4. search 搜索接口参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 关键词（匹配 title/description，最长100） |
| channel | string | 否 | 渠道筛选 |
| page / page_size | int | 否 | 分页 |

### 5. by-skill 按技能筛选参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skill_id | int | 是 | 技能ID（skills 表 id） |
| sort | string | 否 | latest/hot，默认 latest |
| page / page_size | int | 否 | 分页 |

### 6. 业务约束
- 三个接口只返回 status=published 的作品
- feed 默认排除当前用户自己的作品（exclude_self=false 可包含）
- search 关键词不能为空，最长 100 字符
- by-skill 的 skill_id 必填，用 MySQL JSON_CONTAINS 查询 skill_tags 数组
- 错误码沿用 works 模块 3xxx 区间（3004 渠道不合法 / 400 参数错误）

### 7. 返回数据增强
列表项除作品字段外，额外返回：
- author：作者用户信息（批量查询避免 N+1）
- is_liked：当前登录用户是否已点赞该作品（便于前端直接渲染点赞状态）

---

## 二、实现方式

### 1. 复用 works 蓝图
推流接口归入 works 蓝图（无需新建蓝图/迁移），复用 ErrorCode、ALLOWED_CHANNELS、分页工具等。

### 2. 热度排序
用 SQLAlchemy 算术表达式 Work.like_count * 2 + Work.view_count 直接在 SQL 层排序，避免全表扫描到内存。like_count 为 works 表冗余字段（互动模块维护）。

### 3. 技能标签查询
skill_tags 字段是 JSON 数组字符串，用 MySQL 原生函数 JSON_CONTAINS(skill_tags, CAST(:sid AS JSON)) 查询，通过 SQLAlchemy text() 绑定参数防注入。

### 4. N+1 查询优化
- 批量查作者：收集 user_id 集合，一次 User.query.filter(id.in_([...])) 取回，按 id 索引
- is_liked 判断：逐条查 Like 表（MVP 阶段可接受，后续可优化为批量查询）

### 5. 参数校验
- sort 不在 ALLOWED_SORT 返回 400
- channel 不在 ALLOWED_CHANNELS 返回 3004
- search 关键词为空返回 400
- by-skill 缺 skill_id 返回 400

---

## 三、与前端的对接

### 1. 典型对接流程
1. 首页推荐流：GET /api/v1/works/feed?sort=latest&page=1&page_size=20
2. 切换热门：GET /api/v1/works/feed?sort=hot
3. 切换分类：GET /api/v1/works/feed?channel=visual
4. 搜索作品：GET /api/v1/works/search?q=Python&page=1
5. 按技能浏览：GET /api/v1/works/by-skill?skill_id=1&sort=hot
6. 我的作品主页包含自己：GET /api/v1/works/feed?exclude_self=false

### 2. 响应格式（统一分页）
{ code: 200, message: "success", data: { list:[...], total, page, page_size, total_pages } }

### 3. 关键数据结构
列表项作品对象含：work_id, user_id, title, description, channel, files[], cover_url,
is_collaborative, collaborators[], skill_tags[], status, view_count, like_count,
created_at, updated_at, author, is_liked

---

## 四、项目结构变化

- app/routes/works.py            【修改】追加 3 个推流接口 + build_work_list_item 辅助函数
- tests/test_feed.py             【新增】19 项接口测试
- work-logs/2026-07-31_feed-module.md  【本文件】

> 无新增表/无迁移文件/无新增蓝图。复用 works 蓝图和既有数据结构。

---

## 五、接口测试结果

测试文件：tests/test_feed.py，共 19 项全部通过。
测试场景：用户A创建3个不同channel/技能标签的已发布作品，用户B进行浏览/搜索/筛选。

### 正常流程（全部通过）
| # | 测试 | 结果 |
|---|------|------|
| 1 | feed默认(latest) | 返回6条已发布作品 |
| 2 | feed热门排序(hot) | code=200 |
| 3 | feed按channel筛选 | channel=writing返回4条 |
| 3b | channel筛选校验 | 全部为writing作品 |
| 4 | feed含自己作品(exclude_self=false) | code=200 |
| 7 | 搜索Python(命中标题/描述) | 返回2条 |
| 8 | 搜索水彩(命中) | code=200 |
| 9 | 搜索+channel叠加 | code=200 |
| 12 | 按技能1筛选 | 返回1条 |
| 14 | 按技能+热门排序 | code=200 |
| 17 | feed含is_liked字段 | code=200 |
| 18 | is_liked字段正确(true) | 点赞后is_liked=true |

### 异常流程（全部通过）
| # | 场景 | HTTP | body.code | message |
|---|------|------|-----------|---------|
| 5 | 无效sort参数 | 400 | 400 | 排序参数不合法 |
| 6 | 无效channel | 400 | 3004 | 渠道不合法 |
| 10 | 空关键词 | 400 | 400 | 搜索关键词不能为空 |
| 11 | 搜索+无效channel | 400 | 3004 | 渠道不合法 |
| 13 | 缺skill_id | 400 | 400 | skill_id 不能为空 |
| 15 | 按技能+无效sort | 400 | 400 | 排序参数不合法 |
| 16 | 未认证 | 401 | 401 | 未登录或Token过期 |

---

## 六、前端提醒

1. feed 默认排除自己作品：首页推荐流默认 exclude_self=true，看不到自己的作品。个人主页想看自己的作品请用 /works/mine 或传 exclude_self=false。
2. is_liked 字段已内置：feed/search/by-skill 列表项已带 is_liked 字段，前端无需再单独查询点赞状态。
3. author 字段已内置：列表项已带作者信息（user_id/nickname/avatar等），无需二次拉取用户信息。
4. 热门排序公式：热度分 = 点赞数*2 + 浏览数。点赞权重更高。后续可按需调整权重或加入时间衰减。
5. 搜索是模糊匹配：匹配 title 和 description，用 LIKE %keyword%。中文搜索依赖 MySQL 字符集（建议 utf8mb4）。
6. by-skill 用 skill_id：传的是 skills 表的 id，不是技能名。前端可从 /api/v1/profile/skills 获取技能列表。
7. 分页上限：page_size 最大 100，默认 20。
8. 草稿和已删除不进推流：三个接口只返回 published 作品，草稿/已删除作品对其他用户不可见。
9. MVP 阶段无个性化推荐：当前是规则排序（时间/热度），未做基于用户画像的个性化推荐，后续可扩展。
