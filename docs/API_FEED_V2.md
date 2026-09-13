<!-- ============================================================ -->
<!-- ⚠️  本文档已过时 (DEPRECATED) -->
<!-- 最后更新: 2026-09-13 -->
<!-- 请参阅最新文档：API.md -->
<!-- 本文件保留仅供历史参考，内容与当前代码可能不一致 -->
<!-- ============================================================ -->

# 广场推流机制 V2（阶段1）接口设计

> 决策：阶段1（多Tab + 时间衰减热度 + 作者去重 + 关注流）；新建 follows 表；同作者连续最多2条。
> 生成时间：2026-08-19

---

## 一、推流机制设计

### 1.1 三种 Tab 模式

| Tab | 说明 | 排序规则 |
|-----|------|---------|
| latest | 最新发布 | 按发布时间倒序 |
| hot | 热门 | 按热度分倒序（带时间衰减） |
| following | 关注流 | 只看关注的人的作品，按时间倒序 |

### 1.2 热度公式（带时间衰减）

```
热度分 = like_count * 2 + view_count * 1 + comment_count * 3 - 距发布天数 * 5
```

- 点赞权重 2，评论权重 3（互动深度更高），浏览权重 1
- 时间衰减：每天扣 5 分，让老作品热度下降，给新作品曝光机会
- 热度分相同按发布时间倒序

### 1.3 作者去重

- 同一作者的作品，连续出现最多 2 条
- 实现方式：当前页内重排，避免刷屏

### 1.4 筛选

- channel：writing/visual/video/voice，可选
- following 流不支持 channel 筛选（关注的人本来就少）

---

## 二、接口清单

### 改造接口

#### 1. GET /works/feed — 广场推流（改造）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tab | string | 否 | latest(默认)/hot/following |
| channel | string | 否 | writing/visual/video/voice |
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页数量，默认10 |

- latest/hot：排除自己作品（默认）
- following：只看关注的人的作品，含自己作品

### 新增接口：关注关系 `/api/v1/social`（5个）

#### 2. POST /social/follow — 关注用户
- 请求：`{"followed_id": 2}`
- 不能关注自己
- 重复关注返回成功（幂等）
- 返回：`{"code":200, "data":{"is_following": true}}`

#### 3. DELETE /social/follow/<followed_id> — 取消关注
- 返回：`{"code":200, "data":{"is_following": false}}`

#### 4. GET /social/follow/<followed_id> — 查询关注状态
- 返回：`{"code":200, "data":{"is_following": true, "followed_at": "..."}}`

#### 5. GET /social/followings — 我关注的人列表
- Query：page/per_page
- 返回：关注的人的用户信息列表

#### 6. GET /social/followers — 关注我的人列表
- Query：page/per_page
- 返回：粉丝的用户信息列表

---

## 三、数据库改动

### 新建表：follows — 关注关系

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | — |
| follower_id | INT FK→users.id | 关注者 |
| followed_id | INT FK→users.id | 被关注者 |
| created_at | DATETIME | — |
| 联合唯一 | (follower_id, followed_id) | 防重复关注 |

---

## 四、错误码

| code | 含义 |
|------|------|
| 400 | 参数错误 |
| 3001 | 作品不存在 |
| 3004 | 渠道不合法 |
| 3007 | tab参数不合法 |
| 4001 | 不能关注自己 |
| 4002 | 目标用户不存在 |
