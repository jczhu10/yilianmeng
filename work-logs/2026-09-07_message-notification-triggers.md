# 工作日志 · 消息页面通知触发补齐 · 2026-09-07

> **任务**：解决消息页面"互动消息"和"待办事项"列表为空的问题——点赞、评论、项目申请三个动作此前不会往 `notifications` 表写数据。

## 一、问题根因

消息页面的"未读数接口"（`GET /notifications/unread-counts`）和"列表接口"（`/interaction`、`/todo`）都已实现，但**只有"关注"动作会创建 Notification 记录**，点赞、评论、项目申请三个动作**没有通知写入逻辑**，导致：
- 互动消息 Tab 永远只有"关注"类通知
- 待办事项 Tab 永远为空

## 二、数据库改动

**零改动。** `notifications` 表现有字段完全覆盖需求：

| 字段 | 本次用途 |
|------|---------|
| `user_id` | 接收者（作品作者 / 项目发起人 / 被回复者） |
| `type` | `interaction`（点赞/评论） / `todo`（项目申请） |
| `subtype` | `like` / `comment` / `apply` |
| `sender_id` | 操作账号 |
| `related_type` | `work` / `project` |
| `related_id` | 被操作对象 ID |
| `title` / `content` | 通知文案 |
| `is_read` / `created_at` | 已读状态 + 时间 |

## 三、接口改动（3 个文件，4 处逻辑）

### 1. `app/routes/interactions.py` — 点赞触发通知

`like_work()`：点赞成功后，若点赞者 ≠ 作品作者，写入一条 `type=interaction, subtype=like` 通知。

### 2. `app/routes/interactions.py` — 评论/回复触发通知

`create_comment()`：
- **一级评论**（`parent_id=None`）→ 通知作品作者（评论者 ≠ 作者时）
- **二级回复**（`parent_id` 非空）→ 通知被回复者，且被回复者 ≠ 作者时才发（避免作者重复收到两条）

### 3. `app/routes/projects.py` — 项目申请触发待办通知

`apply_project()`：申请提交后，给项目发起人写入一条 `type=todo, subtype=apply` 通知。

### 4. `app/routes/notifications.py` — 互动列表增强（可选优化）

`list_interaction()`：批量查询 `related_type=work` 的作品，在每条通知里附加 `related_work` 摘要（work_id / title / cover_url / files[0]），前端无需再单独请求作品详情。

## 四、边界处理

| 场景 | 处理 |
|------|------|
| 自己点赞/评论自己的作品 | 不发通知 |
| 回复自己的评论 | 不发通知 |
| 回复他人评论但被回复者是作者 | 只发作者的评论通知，不重复发回复通知 |
| 申请自己发起的项目 | 已被 `CANNOT_APPLY_OWN` 拦截，不会触发 |
| 重复点赞 | 点赞接口已防重（`ALREADY_LIKED`），不会重复写通知 |

## 五、测试覆盖（tests/test_notification_triggers.py · 7/7 OK）

| # | 用例 | 验证点 |
|---|------|--------|
| 01 | 点赞触发通知 | B 赞 A 的作品 → A 收到 like 通知，互动未读数 = 1 |
| 02 | 自己点赞不通知 | A 赞自己作品 → 无通知记录 |
| 03 | 评论触发通知 | B 评论 A 的作品 → A 收到 comment 通知，未读数 = 2 |
| 04 | 回复触发通知 | C 回复 B 的评论 → B 收到回复通知 |
| 05 | 项目申请触发待办 | B 申请 A 的项目 → A 收到 apply 待办，todo 未读数 = 1 |
| 06 | 互动列表含作品摘要 | 列表项带 `related_work`（work_id/title）+ sender 信息 |
| 07 | 标记已读清零 | 批量已读后互动未读数 = 0 |

**回归测试**：`test_notification_triggers + test_plaza + test_interactions + test_projects + test_messages` → **Ran 54 tests · OK**

## 六、前端对接提醒

1. **消息首页三个 Tab 未读数**：`GET /api/v1/notifications/unread-counts` 返回 `{ official, interaction, todo }`，直接绑定红点即可。
2. **互动消息列表**：`GET /api/v1/notifications/interaction?subtype=like|comment`，每条含 `sender`（操作账号头像昵称）、`related_work`（被操作作品摘要）、`created_at`，可直接渲染"XX 赞了你的作品"。
3. **待办事项列表**：`GET /api/v1/notifications/todo?subtype=apply`，每条含 `content`（申请文案）、`related_id`（项目 ID），点击可跳项目详情。
4. **已读操作**：单条 `POST /notifications/<id>/read`，批量 `POST /notifications/read-all { type: 'interaction'|'todo' }`。
5. 后续若需"项目审批通过/拒绝"也通知申请者，可在 `approve_application` / `reject_application` 里同样加 Notification 写入，本次未做（需求未明确）。
