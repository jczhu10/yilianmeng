# 项目相关数据库设计（最终定稿）

> 决策：所有"可加可不加"的字段全部加上；projects.required_skills 拆为独立表维护人数。
> 生成时间：2026-08-06
> 范围：作品、互动、协作项目、评分、消息通知、用户私信、钱包交易（7 大模块）

---

## 一、决策确认清单

| # | 项 | 决策 |
|---|----|------|
| 1 | works.comment_count（冗余评论数） | ✅加 |
| 2 | works.project_id（关联协作项目） | ✅加 |
| 3 | comments.reply_to_user_id（回复@目标用户） | ✅加 |
| 4 | projects.max_members + cover_url | ✅加 |
| 5 | projects.required_skills 拆表 | ✅拆为 project_required_skills（带所需人数+已招人数） |
| 6 | ratings.tags + is_anonymous | ✅加 |
| 7 | wallets.frozen_balance | ✅加 |
| 8 | notifications 拆 related_type + extra_data | ✅加 |
| 9 | conversations 冗余 user1_unread/user2_unread + last_message_content | ✅加 |
| 10 | transactions 加 direction/balance_after/status | ✅加 |

---

## 二、表总览（13 张表）

| # | 表名 | 状态 | 所属模块 |
|---|------|------|----------|
| 1 | works | 🔧改造（加 comment_count、project_id） | 作品 |
| 2 | likes | ✅不变 | 互动 |
| 3 | comments | 🔧改造（加 reply_to_user_id） | 互动 |
| 4 | projects | 🔧改造（加 max_members、cover_url，删 required_skills） | 协作 |
| 5 | project_required_skills | 🆕新建（替代 required_skills，带人数） | 协作 |
| 6 | project_applications | ✅不变 | 协作 |
| 7 | ratings | 🔧改造（加 tags、is_anonymous，加联合唯一索引） | 评分 |
| 8 | notifications | 🆕新建 | 通知 |
| 9 | conversations | 🆕新建 | 私信 |
| 10 | messages | 🔧改造（会话模型） | 私信 |
| 11 | wallets | 🔧改造（加 frozen_balance） | 钱包 |
| 12 | transactions | 🔧改造（加 direction/balance_after/status） | 钱包 |
| 13 | rating_tags | 🆕新建（评价标签字典，可选） | 评分 |

---

## 三、各表详细字段

### 1. works — 作品表（🔧改造）

**新增字段**：comment_count、project_id

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 作品ID |
| user_id | INT | FK→users.id, NOT NULL | — | 作者ID |
| title | VARCHAR(200) | NOT NULL | — | 标题 |
| description | TEXT | | '' | 描述 |
| channel | VARCHAR(50) | | 'writing' | writing/visual/video/voice |
| files | TEXT | | '[]' | 文件URL数组（JSON，上限9） |
| cover_url | VARCHAR(255) | | '' | 封面URL |
| is_collaborative | BOOLEAN | | FALSE | 是否协作作品 |
| project_id | INT | FK→projects.id | NULL | **新增**：关联的协作项目ID |
| collaborators | TEXT | | '[]' | 协作者ID数组（JSON） |
| skill_tags | TEXT | | '[]' | 技能标签ID数组（JSON，上限5） |
| status | VARCHAR(20) | | 'draft' | draft/published/deleted（软删除） |
| view_count | INT | | 0 | 浏览数 |
| like_count | INT | | 0 | 点赞数（冗余） |
| comment_count | INT | | 0 | **新增**：评论数（冗余） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**索引**：user_id, status, channel, project_id

---

### 2. likes — 点赞表（✅不变）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| user_id | INT | FK→users.id, NOT NULL | 点赞人 |
| work_id | INT | FK→works.id, NOT NULL | 作品 |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(user_id, work_id)`

---

### 3. comments — 评论表（🔧改造）

**新增字段**：reply_to_user_id

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| user_id | INT | FK→users.id, NOT NULL | — | 评论人 |
| work_id | INT | FK→works.id, NOT NULL | — | 所属作品 |
| parent_id | INT | FK→comments.id | NULL | 父评论ID：NULL=一级，非NULL=回复 |
| reply_to_user_id | INT | FK→users.id | NULL | **新增**：回复@的目标用户ID |
| content | VARCHAR(2000) | NOT NULL | — | 评论内容 |
| is_deleted | BOOLEAN | | FALSE | 软删除 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

> reply_to_user_id 作用：二级回复中精准通知被回复者；parent_id 指向一级评论，reply_to_user_id 指向被@的那个人。

---

### 4. projects — 协作项目表（🔧改造）

**新增字段**：max_members、cover_url
**删除字段**：required_skills（拆到 project_required_skills 表）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | 项目ID |
| user_id | INT | FK→users.id, NOT NULL | — | 发起人 |
| title | VARCHAR(200) | NOT NULL | — | 项目标题 |
| description | TEXT | | '' | 项目描述 |
| mode | VARCHAR(20) | | 'free' | free 无偿 / paid 有偿 |
| budget | INT | | 0 | 预算（分，paid 模式用） |
| deadline | DATETIME | | NULL | 截止时间 |
| max_members | INT | | 10 | **新增**：招募总人数上限 |
| cover_url | VARCHAR(255) | | '' | **新增**：项目封面 |
| status | VARCHAR(20) | | 'recruiting' | recruiting/ongoing/completed/closed |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**状态流转**：
```
recruiting（招募中）
    ↓（首个申请通过 / 达到 max_members 自动触发）
 ongoing（进行中）
    ↓（发起人手动结束）
 completed（已完成）→ 解锁评分
    ↓（发起人关闭 / 逾期自动）
 closed（已关闭）
```

---

### 5. project_required_skills — 项目所需技能表（🆕新建）

替代 projects.required_skills JSON 字段，每个技能独立一行，附带所需人数。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | — |
| project_id | INT | FK→projects.id, NOT NULL | — | 所属项目 |
| skill_id | INT | FK→skills.id, NOT NULL | — | 所需技能 |
| required_count | INT | NOT NULL | 1 | 所需人数（该技能要招几人） |
| filled_count | INT | | 0 | 已招到人数（冗余，便于查询进度） |
| created_at | DATETIME | | utcnow | — |

**联合唯一索引**：`(project_id, skill_id)` — 同一项目同一技能只一行

**业务规则**：
- 申请时校验：申请人技能必须命中 project_required_skills 中某项
- 审批通过时：对应技能 filled_count += 1
- 当所有技能 filled_count >= required_count，或总成员达 max_members，项目可自动转 ongoing

---

### 6. project_applications — 项目申请表（✅不变）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | 申请ID |
| project_id | INT | FK→projects.id, NOT NULL | — | 目标项目 |
| user_id | INT | FK→users.id, NOT NULL | — | 申请人 |
| message | TEXT | | '' | 申请理由 |
| status | VARCHAR(20) | | 'pending' | pending/approved/rejected |
| created_at | DATETIME | | utcnow | — |
| processed_at | DATETIME | | NULL | 审批时间 |

---

### 7. ratings — 评分表（🔧改造）

**新增字段**：tags、is_anonymous
**新增约束**：联合唯一索引

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| project_id | INT | FK→projects.id, NOT NULL | — | 项目 |
| from_user_id | INT | FK→users.id, NOT NULL | — | 评分人 |
| to_user_id | INT | FK→users.id, NOT NULL | — | 被评分人 |
| score | TINYINT | NOT NULL | — | 分数 1-5 |
| comment | VARCHAR(500) | | '' | 文字评价 |
| tags | TEXT | | '[]' | **新增**：评价标签ID数组（JSON，见 rating_tags 字典） |
| is_anonymous | BOOLEAN | | FALSE | **新增**：是否匿名评价 |
| created_at | DATETIME | | utcnow | — |

**联合唯一索引**：`(project_id, from_user_id, to_user_id)` — 一项目一对人只能评一次

**前置条件**：projects.status = completed
**有效期**：项目 completed 后 30 天内可评（应用层校验）

---

### 8. rating_tags — 评价标签字典表（🆕新建，可选）

预置一组评价标签（类似 style_tags 字典），用户评分时可多选。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| name | VARCHAR(30) | UNIQUE, NOT NULL | — | 标签名 |
| category | VARCHAR(20) | | 'positive' | positive 正向 / negative 负向 / neutral 中性 |
| sort_order | INT | | 0 | 排序 |
| is_active | BOOLEAN | | TRUE | 是否启用 |
| created_at | DATETIME | | utcnow | — |

**预置标签示例**（seed 脚本插入）：
- 正向：准时交付、沟通顺畅、专业度高、创意十足、态度认真、配合默契、作品质量高
- 负向：交付延期、沟通困难、专业性不足、态度敷衍

---

### 9. notifications — 系统通知表（🆕新建）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 通知ID |
| user_id | INT | FK→users.id, NOT NULL | — | 接收用户 |
| type | VARCHAR(30) | NOT NULL | — | 通知类型（见下方矩阵） |
| title | VARCHAR(100) | | '' | 通知标题（短） |
| content | VARCHAR(500) | NOT NULL | — | 通知文案（长） |
| related_type | VARCHAR(20) | | '' | 关联对象类型：work/comment/project/application/rating/transaction/user |
| related_id | INT | | 0 | 关联对象ID |
| sender_id | INT | FK→users.id | 0 | 触发者（0=系统） |
| extra_data | TEXT | | '{}' | 扩展数据 JSON（跳转路径/头像/缩略图等） |
| is_read | BOOLEAN | | FALSE | 是否已读 |
| created_at | DATETIME | | utcnow | — |

**索引**：
- `(user_id, is_read, created_at)` — 查未读数 + 列表（复合）
- `(user_id, created_at)` — 列表倒序

**type 通知类型矩阵**：

| type | 触发场景 | related_type | sender_id | 文案示例 |
|------|----------|-------------|-----------|----------|
| like | 点赞我的作品 | work | 点赞人 | "xxx 赞了你的作品《xxx》" |
| comment | 评论我的作品 | work | 评论人 | "xxx 评论了你的作品《xxx》" |
| reply | 回复我的评论 | comment | 回复人 | "xxx 回复了你的评论" |
| mention | 评论@了我 | comment | 评论人 | "xxx 在评论中提到了你" |
| apply | 申请我的项目 | project | 申请人 | "xxx 申请加入《xxx》" |
| approved | 申请被通过 | project | 发起人 | "你已加入《xxx》项目" |
| rejected | 申请被拒绝 | project | 发起人 | "你申请的《xxx》未通过" |
| member_join | 新成员加入项目 | project | 新成员 | "xxx 加入了你的项目" |
| project_completed | 参与项目已完成 | project | 0 | "《xxx》已完成，可以评分啦" |
| rating_received | 收到新评分 | rating | 评分人 | "xxx 给你打了 5 分" |
| system_announce | 系统公告 | — | 0 | "欢迎来到艺联萌" |
| recharge_success | 充值成功 | transaction | 0 | "充值成功 +50元" |
| withdraw_approved | 提现到账 | transaction | 0 | "提现 100元 已到账" |
| reward | 创作奖励 | transaction | 0 | "你获得创作激励 10元" |
| transfer_in | 收到转账 | transaction | 转账人 | "xxx 转给你 50元" |

> 联动写入：在点赞/评论/申请/审批/评分/充值/转账等接口里事务性 INSERT。

---

### 10. conversations — 私信会话表（🆕新建）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 会话ID |
| user1_id | INT | FK→users.id, NOT NULL | — | 参与方A（ID较小的） |
| user2_id | INT | FK→users.id, NOT NULL | — | 参与方B（ID较大的） |
| last_message_id | INT | FK→messages.id | NULL | 最后一条消息ID |
| last_message_content | VARCHAR(200) | | '' | 最后消息预览（冗余） |
| last_message_at | DATETIME | | NULL | 最后消息时间（排序用） |
| user1_unread | INT | | 0 | user1 的未读数 |
| user2_unread | INT | | 0 | user2 的未读数 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**联合唯一索引**：`(user1_id, user2_id)` — 两人之间唯一会话
**存入约定**：`user1_id = min(a,b)`，`user2_id = max(a,b)`

---

### 11. messages — 私信表（🔧改造为会话模型）

**删除字段**：from_user_id、to_user_id、type、related_id
**新增字段**：conversation_id、sender_id

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| conversation_id | INT | FK→conversations.id, NOT NULL | — | 所属会话 |
| sender_id | INT | FK→users.id, NOT NULL | — | 发送人 |
| content | TEXT | NOT NULL | — | 消息内容 |
| is_read | BOOLEAN | | FALSE | 是否已读 |
| created_at | DATETIME | | utcnow | — |

**索引**：`(conversation_id, created_at)`

---

### 12. wallets — 钱包表（🔧改造）

**新增字段**：frozen_balance

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| user_id | INT | FK→users.id, UNIQUE, NOT NULL | — | 一人一钱包 |
| balance | INT | | 0 | 可用余额（分） |
| frozen_balance | INT | | 0 | **新增**：冻结金额（提现中/保证金） |
| total_earned | INT | | 0 | 累计收入（分） |
| total_withdrawn | INT | | 0 | 累计提现（分） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

> 首次 GET /wallet 自动创建（get_or_create）

---

### 13. transactions — 交易流水表（🔧改造）

**新增字段**：direction、balance_after、related_type、related_id、status

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| user_id | INT | FK→users.id, NOT NULL | — | 所属用户 |
| type | VARCHAR(20) | NOT NULL | — | 流水类型（见下方枚举） |
| direction | VARCHAR(10) | | 'in' | **新增**：in 收入 / out 支出 |
| amount | INT | NOT NULL | — | 金额（分，正数） |
| balance_after | INT | | 0 | **新增**：交易后余额快照（对账用） |
| related_type | VARCHAR(20) | | '' | **新增**：project/rating/order/withdraw/system |
| related_id | INT | | 0 | **新增**：关联对象ID |
| status | VARCHAR(20) | | 'success' | **新增**：pending/success/failed/cancelled |
| description | VARCHAR(200) | | '' | 描述 |
| created_at | DATETIME | | utcnow | — |

**type 枚举 + direction 对应**：

| type | 含义 | direction | balance | frozen | total_earned | total_withdrawn |
|------|------|-----------|---------|--------|--------------|-----------------|
| admin_recharge | 后台充值 | in | + | — | + | — |
| reward | 创作激励 | in | + | — | + | — |
| transfer_in | 转账收入 | in | + | — | + | — |
| project_income | 项目报酬收入 | in | + | — | + | — |
| withdraw | 提现申请 | out | - | + | — | + |
| transfer_out | 转账支出 | out | - | — | — | — |
| service_fee | 手续费 | out | - | — | — | — |
| project_pay | 项目付费支出 | out | - | — | — | — |
| freeze | 冻结 | out(冻结) | balance 不变，frozen + | + | — | — |
| unfreeze | 解冻 | in(解冻) | frozen - | - | — | — |

**索引**：`(user_id, created_at)`、`(related_type, related_id)`

---

## 四、表关系总图

```
users ──1:1── wallets ──1:N── transactions
  │
  ├──1:N── projects ──1:N── project_required_skills ──N:1── skills
  │        │    │
  │        │    └──1:N── project_applications ──N:1── users（申请人）
  │        │
  │        └── status=completed → ratings ──N:1── users（评/被评）
  │                                  └── tags → rating_tags 字典
  │
  ├──1:N── works ──1:N── likes ──N:1── users → like 通知
  │        │     │
  │        │     └──1:N── comments ──N:1── users → comment/reply/mention 通知
  │        │                     └── reply_to_user_id → users
  │        │
  │        └── project_id ──N:1── projects
  │
  ├──1:N── notifications（user_id 接收人，sender_id 触发人）
  │
  └──1:N── conversations（as user1 或 user2）
                └──1:N── messages ──N:1── users（sender_id）
```

---

## 五、索引汇总

| 表 | 索引 | 类型 | 目的 |
|----|------|------|------|
| works | (user_id, status) | 普通 | 查作者作品 |
| works | (status, channel) | 普通 | 推流按渠道筛选 |
| works | project_id | 普通 | 查项目关联作品 |
| likes | (user_id, work_id) | UNIQUE | 防重复点赞 |
| comments | (work_id, created_at) | 普通 | 作品评论列表 |
| comments | parent_id | 普通 | 查回复 |
| projects | (user_id, status) | 普通 | 我的项目 |
| projects | status | 普通 | 列表筛选 |
| project_required_skills | (project_id, skill_id) | UNIQUE | 防重复 |
| project_applications | (project_id, status) | 普通 | 项目申请列表 |
| project_applications | (user_id, project_id) | 普通 | 防重复申请 |
| ratings | (project_id, from_user_id, to_user_id) | UNIQUE | 防重复评分 |
| ratings | to_user_id | 普通 | 查某人收到的评分 |
| notifications | (user_id, is_read, created_at) | 普通 | 未读数+列表 |
| conversations | (user1_id, user2_id) | UNIQUE | 会话去重 |
| messages | (conversation_id, created_at) | 普通 | 会话消息列表 |
| wallets | user_id | UNIQUE | 一人一钱包 |
| transactions | (user_id, created_at) | 普通 | 流水列表 |
| transactions | (related_type, related_id) | 普通 | 关联查询 |

---

## 六、业务约束汇总

| 规则 | 限制值 |
|------|--------|
| works.files 数量 | ≤ 9 |
| works.skill_tags 数量 | ≤ 5 |
| comments 回复层级 | ≤ 2（parent_id 只能指向一级评论） |
| projects.max_members | ≥ 1 |
| project_required_skills.required_count | ≥ 1 |
| project_applications 同人同项目 | 仅 1 条（pending/approved） |
| ratings.score | 1-5 |
| ratings 有效期 | completed 后 30 天 |
| ratings 同项目一对人 | 仅 1 条 |
| notifications 单条 | 一次操作写一条 |
| conversations 两人 | 仅 1 个会话 |
| wallets 首次访问 | get_or_create |
| transactions 金额 | 以分为单位，正整数 |

---

## 七、通知类型与联动写入点

| 模块 | 接口 | 写入通知 type |
|------|------|---------------|
| 互动 | POST /works/<id>/like | like |
| 互动 | POST /works/<id>/comments（评论作品） | comment |
| 互动 | POST /works/<id>/comments（回复评论，带 parent_id） | reply |
| 互动 | POST /works/<id>/comments（带 reply_to_user_id） | mention |
| 协作 | POST /projects/<id>/apply | apply |
| 协作 | POST /projects/<id>/applications/<id>/approve | approved（给申请人）+ member_join（给其他成员） |
| 协作 | POST /projects/<id>/applications/<id>/reject | rejected |
| 协作 | POST /projects/<id>/complete | project_completed（给所有成员） |
| 评分 | POST /ratings/ | rating_received |
| 钱包 | POST /wallet/recharge | recharge_success |
| 钱包 | POST /wallet/withdraw（到账） | withdraw_approved |
| 钱包 | POST /wallet/transfer | transfer_in（给对方） |
| 系统 | 管理后台/定时任务 | reward / system_announce |

---

## 八、对应接口规划（参考，约 40+ 个）

### 作品（含推流，10 个）
- POST /works/ 创建
- PUT /works/<id> 编辑
- POST /works/<id>/publish 发布
- DELETE /works/<id> 删除
- GET /works/<id> 详情
- GET /works/mine 我的作品
- POST /works/upload 上传
- GET /works/feed 推流
- GET /works/search 搜索
- GET /works/by-skill 按技能筛选

### 互动（7 个）
- POST /works/<id>/like 点赞
- DELETE /works/<id>/like 取消
- GET /works/<id>/likes 点赞列表
- POST /works/<id>/comments 评论
- GET /works/<id>/comments 评论列表
- DELETE /comments/<id> 删除
- GET /comments/<id>/replies 回复列表

### 协作（10 个）
- POST /projects/ 发起（含 required_skills 数组带 count）
- GET /projects/ 列表
- GET /projects/<id> 详情
- PUT /projects/<id> 编辑
- POST /projects/<id>/apply 申请
- POST /projects/<id>/applications/<app_id>/approve 通过
- POST /projects/<id>/applications/<app_id>/reject 拒绝
- POST /projects/<id>/complete 完成
- POST /projects/<id>/close 关闭
- GET /projects/mine 我的项目

### 评分（5 个）
- POST /ratings/ 提交评分
- GET /ratings/<user_id> 某人收到的评分
- GET /ratings/mine-given 我发出的
- GET /ratings/mine-received 我收到的
- GET /ratings/project/<project_id> 项目评分
- GET /ratings/tags 评价标签字典

### 通知（5 个）
- GET /notifications/ 列表
- GET /notifications/unread-count 未读数
- POST /notifications/<id>/read 标记已读
- POST /notifications/read-all 全部已读
- DELETE /notifications/<id> 删除

### 私信（6 个）
- GET /messages/conversations 会话列表
- POST /messages/conversations 创建/获取会话
- GET /messages/conversations/<id> 会话消息
- POST /messages/conversations/<id> 发送消息
- POST /messages/conversations/<id>/read 标记已读
- DELETE /messages/conversations/<id> 删除会话

### 钱包（6 个）
- GET /wallet/ 钱包余额
- GET /wallet/transactions 流水
- POST /wallet/recharge 充值
- POST /wallet/withdraw 提现
- POST /wallet/transfer 转账
- GET /wallet/transactions/<id> 流水详情