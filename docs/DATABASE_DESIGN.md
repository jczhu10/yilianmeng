<!-- ============================================================ -->
<!-- ⚠️  本文档已过时 (DEPRECATED) -->
<!-- 最后更新: 2026-09-13 -->
<!-- 请参阅最新文档：DATABASE.md -->
<!-- 本文件保留仅供历史参考，内容与当前代码可能不一致 -->
<!-- ============================================================ -->

# 艺联萌数据库设计文档

> 本文档记录全部数据库表结构设计，包括已实现表和计划新增/改造表。
> 最后更新：2026-08-01

## 目录

- [一、表总览](#一表总览)
- [二、认证模块](#二认证模块)
- [三、档案模块](#三档案模块)
- [四、作品模块](#四作品模块)
- [五、互动模块](#五互动模块)
- [六、协作项目模块](#六协作项目模块)
- [七、消息通知模块（🆕新建）](#七消息通知模块新建)
- [八、用户私信模块（🆕新建+🔧改造）](#八用户私信模块新建改造)
- [九、评分互评模块](#九评分互评模块)
- [十、钱包交易模块](#十钱包交易模块)
- [十一、表关系图](#十一表关系图)
- [十二、状态枚举与约定](#十二状态枚举与约定)

---

## 一、表总览

共 **18 张表**：14 张已建 + 2 张新建 + 2 张改造（messages 改造 + project_applications 微调）

| # | 表名 | 状态 | 所属模块 | 模型文件 |
|---|------|------|----------|----------|
| 1 | users | ✅已建不变 | 认证 | app/models/user.py |
| 2 | profiles | ✅已建不变 | 档案 | app/models/profile.py |
| 3 | skill_categories | ✅已建不变 | 档案 | app/models/skill.py |
| 4 | skills | ✅已建不变 | 档案 | app/models/skill.py |
| 5 | profile_skills | ✅已建不变 | 档案 | app/models/skill.py |
| 6 | works | ✅已建不变 | 作品 | app/models/work.py |
| 7 | likes | ✅已建不变 | 互动 | app/models/interaction.py |
| 8 | comments | ✅已建不变 | 互动 | app/models/interaction.py |
| 9 | projects | ✅已建不变（补 completed 流转） | 协作 | app/models/project.py |
| 10 | project_applications | ✅已建不变 | 协作 | app/models/project.py |
| 11 | **notifications** | 🆕新建 | 消息通知 | app/models/notification.py |
| 12 | **conversations** | 🆕新建 | 私信 | app/models/conversation.py |
| 13 | messages | 🔧改造（改会话模型） | 私信 | app/models/message.py |
| 14 | ratings | ✅已建不变 | 评分 | app/models/rating.py |
| 15 | wallets | ✅已建不变 | 钱包 | app/models/wallet.py |
| 16 | transactions | ✅已建不变 | 钱包 | app/models/wallet.py |
| 17 | events | ⏸待定（暂不开发） | 活动 | app/models/event.py |
| 18 | event_participants | ⏸待定（暂不开发） | 活动 | app/models/event.py |

---

## 二、认证模块

### 1. users — 用户表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 用户ID |
| phone | VARCHAR(20) | UNIQUE, NOT NULL | — | 手机号（登录凭证） |
| nickname | VARCHAR(50) | | '用户' | 昵称 |
| avatar | VARCHAR(255) | | '' | 头像URL |
| bio | VARCHAR(500) | | '' | 个人简介 |
| level | INT | | 1 | 等级 |
| exp | INT | | 0 | 经验值 |
| is_new_user | BOOLEAN | | TRUE | 是否新用户 |
| created_at | DATETIME | | utcnow | 注册时间 |
| updated_at | DATETIME | | onupdate utcnow | 更新时间 |

---

## 三、档案模块

### 2. profiles — 创作者档案表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 档案ID |
| user_id | INT | FK→users.id, UNIQUE, NOT NULL | — | 对应用户（一对一） |
| identity_type | VARCHAR(20) | | 'amateur' | amateur业余 / professional专业 |
| style_tags | TEXT | | '[]' | 风格标签（JSON数组） |
| work_history | TEXT | | '' | 工作经历 |
| education | TEXT | | '' | 教育背景 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

### 3. skill_categories — 技能分类表（字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 分类名 |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 编码：writing/visual/video/voice |
| sort_order | INT | 默认 0 | 排序，越小越前 |
| created_at | DATETIME | | utcnow |

**预置数据**：文字创作(writing) / 视觉创作(visual) / 影像类(video) / 配音(voice)

### 4. skills — 技能表（字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| category_id | INT | FK→skill_categories.id, NOT NULL | 所属分类 |
| name | VARCHAR(50) | NOT NULL | 技能名 |
| sort_order | INT | 默认 0 | 排序 |
| created_at | DATETIME | | utcnow |

**预置 21 条数据**（详见 seed_skills.py）

### 5. profile_skills — 档案-技能关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| profile_id | INT | FK→profiles.id, NOT NULL | 档案ID |
| skill_id | INT | FK→skills.id, NOT NULL | 技能ID |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(profile_id, skill_id)` → 防止重复选同一技能

---

## 四、作品模块

### 6. works — 作品表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | 作品ID |
| user_id | INT | FK→users.id, NOT NULL | — | 作者ID |
| title | VARCHAR(200) | NOT NULL | — | 标题 |
| description | TEXT | | '' | 描述 |
| channel | VARCHAR(50) | | 'short_video' | writing/visual/video/voice |
| files | TEXT | | '[]' | 文件URL数组（JSON） |
| cover_url | VARCHAR(255) | | '' | 封面URL |
| is_collaborative | BOOLEAN | | FALSE | 是否协作作品 |
| collaborators | TEXT | | '[]' | 协作者ID数组（JSON） |
| skill_tags | TEXT | | '[]' | 技能标签ID数组（JSON） |
| status | VARCHAR(20) | | 'draft' | draft/published/deleted（软删除） |
| view_count | INT | | 0 | 浏览数 |
| like_count | INT | | 0 | 点赞数（冗余计数） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

---

## 五、互动模块

### 7. likes — 点赞记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| user_id | INT | FK→users.id, NOT NULL | 点赞人 |
| work_id | INT | FK→works.id, NOT NULL | 被点赞作品 |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(user_id, work_id)` → 防止重复点赞

### 8. comments — 评论表（支持二级回复 + 软删除）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | 评论ID |
| user_id | INT | FK→users.id, NOT NULL | — | 评论人 |
| work_id | INT | FK→works.id, NOT NULL | — | 所属作品 |
| parent_id | INT | FK→comments.id | NULL | 根评论ID：NULL=一级，非NULL=回复 |
| content | VARCHAR(2000) | NOT NULL | — | 评论内容 |
| is_deleted | BOOLEAN | | FALSE | 软删除（显示"[已删除]"） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

---

## 六、协作项目模块

### 9. projects — 协作项目表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | 项目ID |
| user_id | INT | FK→users.id, NOT NULL | — | 发起人 |
| title | VARCHAR(200) | NOT NULL | — | 项目标题 |
| description | TEXT | | '' | 项目描述 |
| required_skills | TEXT | | '[]' | 所需技能ID数组（JSON） |
| mode | VARCHAR(20) | | 'free' | free无偿 / paid有偿 |
| budget | INT | | 0 | 预算（分） |
| deadline | DATETIME | | NULL | 截止时间 |
| status | VARCHAR(20) | | 'recruiting' | recruiting/ongoing/completed/closed |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**状态流转**：
```
recruiting → ongoing（首个申请通过自动转）→ completed（发起人手动结束）→ closed（可选）
```

### 10. project_applications — 项目申请表

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

## 七、消息通知模块（🆕新建）

### 11. notifications — 系统通知表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 通知ID |
| user_id | INT | FK→users.id, NOT NULL | — | 接收通知的用户 |
| type | VARCHAR(20) | NOT NULL | — | 通知类型 |
| content | VARCHAR(500) | NOT NULL | — | 通知文案 |
| related_id | INT | | 0 | 关联业务ID |
| sender_id | INT | FK→users.id | 0 | 触发者（0=系统） |
| is_read | BOOLEAN | | FALSE | 是否已读 |
| created_at | DATETIME | | utcnow | — |

**索引**：
- `(user_id, is_read)` — 快速查未读数
- `(user_id, created_at)` — 通知列表排序

**通知类型与文案规则**：

| type | 触发场景 | 文案示例 | related_id | sender_id |
|------|----------|----------|------------|-----------|
| like | 有人点赞我的作品 | "xxx 赞了你的作品《标题》" | work_id | 点赞人ID |
| comment | 有人评论我的作品 | "xxx 评论了你的作品《标题》" | work_id | 评论人ID |
| reply | 有人回复我的评论 | "xxx 回复了你的评论" | comment_id | 回复人ID |
| apply | 有人申请我的协作项目 | "xxx 申请加入你的项目《标题》" | project_id | 申请人ID |
| approved | 我的申请被通过 | "你已加入项目《标题》" | project_id | 项目发起人ID |
| rejected | 我的申请被拒绝 | "你的项目申请未通过" | project_id | 项目发起人ID |
| system | 系统公告 | "欢迎来到艺联萌" | 0 | 0 |

---

## 八、用户私信模块（🆕新建+🔧改造）

### 12. conversations — 私信会话表（🆕新建）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 会话ID |
| user1_id | INT | FK→users.id, NOT NULL | — | 参与方A（ID较小的） |
| user2_id | INT | FK→users.id, NOT NULL | — | 参与方B（ID较大的） |
| last_message_id | INT | FK→messages.id | NULL | 最后一条消息（冗余加速） |
| last_message_at | DATETIME | | NULL | 最后消息时间（排序用） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**联合唯一索引**：`(user1_id, user2_id)` → 两用户间只有一个会话
**存入约定**：`user1_id = min(a,b)`，`user2_id = max(a,b)`，避免重复建会话

### 13. messages — 私信表（🔧改造为会话模型）

**改造前字段**：id, from_user_id, to_user_id, type, content, is_read, related_id, created_at

**改造后字段**：

| 字段 | 类型 | 约束 | 默认值 | 说明 | 变更 |
|------|------|------|--------|------|------|
| id | INT | PK | — | 消息ID | 保留 |
| conversation_id | INT | FK→conversations.id, NOT NULL | — | 所属会话 | 🆕新增 |
| sender_id | INT | FK→users.id, NOT NULL | — | 发送人 | 🆕新增（替代 from_user_id） |
| content | TEXT | NOT NULL | — | 消息内容 | 保留 |
| is_read | BOOLEAN | | FALSE | 是否已读 | 保留 |
| created_at | DATETIME | | utcnow | — | 保留 |

**删除字段**：from_user_id、to_user_id、type、related_id（会话模型下不需要）

> 注：messages 表目前无接口、无数据，改造等于重新定义，无迁移负担。

---

## 九、评分互评模块

### 14. ratings — 评分表（已建，直接用）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| project_id | INT | FK→projects.id, NOT NULL | 哪个项目产生的评分 |
| from_user_id | INT | FK→users.id, NOT NULL | 评分人 |
| to_user_id | INT | FK→users.id, NOT NULL | 被评分人 |
| score | INT | NOT NULL | 分数（1-5） |
| comment | TEXT | 默认 '' | 评价内容 |
| created_at | DATETIME | | utcnow |

**建议索引**：`(project_id, from_user_id, to_user_id)` 联合唯一 → 一项目一对人只能评一次

**业务规则**：
- 前置条件：项目 status=completed
- 评分范围：1-5 分
- 评分人校验：必须是项目发起人或已通过申请的成员
- 被评人校验：必须是同一项目的其他成员

---

## 十、钱包交易模块

### 15. wallets — 钱包表（已建，直接用）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| user_id | INT | FK→users.id, UNIQUE, NOT NULL | — | 一人一钱包 |
| balance | INT | | 0 | 余额（分） |
| total_earned | INT | | 0 | 累计收入 |
| total_withdrawn | INT | | 0 | 累计提现 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**规则**：首次访问自动创建（get_or_create）

### 16. transactions — 交易流水表（已建，直接用）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK | — | — |
| user_id | INT | FK→users.id, NOT NULL | — | 所属用户 |
| type | VARCHAR(20) | NOT NULL | — | 流水类型 |
| amount | INT | NOT NULL | — | 金额（分） |
| description | VARCHAR(200) | | '' | 交易描述 |
| created_at | DATETIME | | utcnow | — |

**流水 type 约定**：

| type | 含义 | balance 影响 | total_earned 影响 | total_withdrawn 影响 |
|------|------|--------------|-------------------|---------------------|
| recharge | 充值 | + | + | — |
| reward | 奖励 | + | + | — |
| withdraw | 提现 | - | — | + |
| transfer_in | 转入（收到转账） | + | + | — |
| transfer_out | 转出（发出转账） | - | — | — |

---

## 十一、表关系图

```
users ──1:1── profiles ──1:N── profile_skills ──N:1── skills ──N:1── skill_categories
  │
  ├──1:N── works ──1:N── likes ──N:1── users
  │              └──1:N── comments ──1:N── comments（parent_id 自关联）
  │
  ├──1:N── projects（我发起的）
  │              └──1:N── project_applications ──N:1── users（申请人）
  │              └──1:N── ratings ──N:1── users（from_user/to_user）
  │
  ├──1:N── notifications（user_id 接收者）
  │              └──N:1── users（sender_id 触发者）
  │
  ├──1:N── conversations（user1_id）
  ├──1:N── conversations（user2_id）
  │              └──1:N── messages ──N:1── users（sender_id）
  │
  ├──1:1── wallets ──1:N── transactions
  │
  └──1:N── event_participants ──N:1── events（待定）
```

---

## 十二、状态枚举与约定

### 1. works.status（作品状态）
| 值 | 含义 | 说明 |
|----|------|------|
| draft | 草稿 | 仅作者可见 |
| published | 已发布 | 公开可见 |
| deleted | 已删除 | 软删除，不物理删 |

### 2. projects.status（协作项目状态）
| 值 | 含义 | 说明 |
|----|------|------|
| recruiting | 招募中 | 可申请、可编辑 |
| ongoing | 进行中 | 首个申请通过后自动转 |
| completed | 已完成 | 发起人手动结束，解锁评分 |
| closed | 已关闭 | 不再接受操作 |

### 3. project_applications.status（申请状态）
| 值 | 含义 |
|----|------|
| pending | 待处理 |
| approved | 已通过 |
| rejected | 已拒绝 |

### 4. works.channel（作品渠道，对齐技能分类）
| 值 | 含义 |
|----|------|
| writing | 文字创作 |
| visual | 视觉创作 |
| video | 影像类 |
| voice | 配音 |

### 5. profiles.identity_type（身份类型）
| 值 | 含义 |
|----|------|
| amateur | 业余创作者 |
| professional | 专业创作者 |

### 6. projects.mode（项目模式）
| 值 | 含义 |
|----|------|
| free | 无偿协作 |
| paid | 有偿协作 |

### 7. notifications.type（通知类型）
| 值 | 含义 |
|----|------|
| like | 点赞 |
| comment | 评论 |
| reply | 回复 |
| apply | 协作申请 |
| approved | 申请通过 |
| rejected | 申请拒绝 |
| system | 系统公告 |

### 8. transactions.type（交易流水类型）
| 值 | 含义 |
|----|------|
| recharge | 充值 |
| reward | 奖励 |
| withdraw | 提现 |
| transfer_in | 转入 |
| transfer_out | 转出 |

### 9. 金额单位约定
- 所有金额字段（balance / amount / budget / reward）均以**分**为单位存储
- 前端展示时除以 100 转换为元
- 避免浮点数误差，全部用整数

### 10. 时间约定
- 所有 `created_at` / `updated_at` 默认 `datetime.utcnow`（UTC 时间）
- 接口返回时用 `isoformat()` 序列化
- 前端按需转换为本地时区显示
