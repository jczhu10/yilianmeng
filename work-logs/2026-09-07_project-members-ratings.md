# 工作日志 · 项目模块成员管理与互评 · 2026-09-07

> **任务**：补全项目页缺失功能——申请过期标记、成员退出/踢人、项目结束、项目互评，并扩展项目卡片/详情新字段。
> **方案**：全部按方案 A 执行——退出/踢人复用 `project_applications.status`（新增 `left` / `removed` 取值）；申请过期通过 `deadline` 动态计算（`ProjectApplication.to_dict(with_expired=True)`），不新增字段。

## 一、数据库改动

### 1. `projects` 表新增 4 列（迁移脚本已执行）

| 列名 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `topic` | VARCHAR(100) | `''` | 项目主题 |
| `required_level` | INT | `1` | 要求账号最低等级 |
| `required_project_count` | INT | `0` | 要求参与项目次数下限 |
| `contact_visible` | TINYINT(1) | `1` | 队长是否公开联系方式 |

> `max_members` / `cover_url` 为前序任务已添加的列，本次沿用。

### 2. `project_applications.status` 取值扩展（无 DDL 改动）

| 原有值 | 新增值 | 含义 |
|--------|--------|------|
| `pending` / `approved` / `rejected` | — | 申请流转 |
| — | `left` | 成员主动退出 |
| — | `removed` | 被队长踢出 |

> 不新增字段，仅扩展 `status` 取值集合；`APP_STATUSES` 同步扩展为 `{'pending','approved','rejected','left','removed'}`。

### 3. 申请过期判断

不新增 `is_expired` 列，通过 `deadline` 动态计算：
```python
ProjectApplication.to_dict(with_expired=True)
# pending + project.deadline < now() → 返回 status='expired', is_expired=True
```

## 二、模型改动（2 个文件）

### 1. `app/models/project.py`

- **`Project`** 新增 4 列定义（topic / required_level / required_project_count / contact_visible），`to_dict()` 同步返回。
- **`ProjectApplication.to_dict(with_expired=False)`** 新增 `with_expired` 参数：
  - `with_expired=False`（默认）：原行为，返回真实 status
  - `with_expired=True`：动态判断 pending 申请是否已过期，过期则返回 `status='expired'` + `is_expired=true`

### 2. `app/models/rating.py`（前序任务已建，本次直接引用）

- `Rating` 表：`(project_id, from_user_id, to_user_id)` 唯一约束，保证同一项目内 A→B 只能评价一次。
- `RatingTag` 字典表：评价标签（positive/negative/neutral）。

## 三、路由改动（`app/routes/projects.py`）

### 1. 全局改动

| 项 | 改动 |
|----|------|
| import | 新增 `import json` + `Rating, RatingTag` |
| ErrorCode | 新增 5008 NOT_A_MEMBER / 5009 CANNOT_RATE_SELF / 5010 ALREADY_RATED / 5011 PROJECT_NOT_COMPLETED / 5012 INVALID_RATING_SCORE / 5013 INVALID_RATING_TAGS |
| 常量 | 新增 `MAX_TOPIC_LEN=100` / `MAX_COVER_URL_LEN=255` / `MAX_MEMBERS_MIN=1` / `MAX_MEMBERS_MAX=999` / `MIN_LEVEL=1` / `MAX_LEVEL=100` / `RATING_SCORE_MIN=1` / `RATING_SCORE_MAX=5` |
| `APP_STATUSES` | 扩展为 `{'pending','approved','rejected','left','removed'}` |
| `APP_QUERY_STATUSES` | 同上，用于我的申请列表过滤 |

### 2. 改造 2 个既有接口

| Method | Path | 改动 |
|--------|------|------|
| POST | `/api/v1/projects/` | 新增接收 `topic` / `cover_url` / `max_members` / `required_level` / `required_project_count` / `contact_visible`，带范围校验 |
| PUT | `/api/v1/projects/<project_id>` | 支持以上 6 个字段按需更新（`if 'xxx' in data`） |

> `build_project_item` 无需修改——通过 `project.to_dict()` 已自动返回全部新字段。

### 3. 新增 6 个接口

| # | Method | Path | 说明 | 权限 | 关键校验 |
|---|--------|------|------|------|----------|
| 10 | GET | `/api/v1/projects/my-applications` | 我的申请列表（含动态过期标记 + 项目摘要） | 登录 | 可选 `status` 过滤 |
| 11 | POST | `/api/v1/projects/<project_id>/leave` | 成员主动退出 | 非发起人 | 项目须 ongoing/completed；申请须 approved；标记 status='left' |
| 12 | POST | `/api/v1/projects/<project_id>/members/<user_id>/remove` | 队长踢人 | 仅发起人 | 项目须 ongoing/completed；目标须 approved 成员；标记 status='removed' |
| 13 | POST | `/api/v1/projects/<project_id>/finish` | 结束项目（ongoing→completed） | 仅发起人 | 仅 ongoing 可结束；重复结束返回成功 |
| 14 | POST | `/api/v1/projects/<project_id>/ratings` | 提交互评 | 项目成员 | 项目须 completed；不可评自己；score 1-5；标签须有效；不可重复 |
| 15 | GET | `/api/v1/projects/<project_id>/ratings` | 查看互评列表 | 项目成员 | 匿名评价 from_user_id/from_user 返回 null |

### 4. 内部辅助函数

| 函数 | 用途 |
|------|------|
| `_is_project_member(project, user_id)` | 判断是否项目成员（发起人或 approved 申请） |
| `_build_my_application_item(application, project)` | 我的申请列表项构造（附带项目摘要 + 动态过期） |

### 5. 通知触发

| 事件 | type | subtype | 接收人 |
|------|------|---------|--------|
| 成员退出 | system | leave | 项目发起人 |
| 成员被踢 | system | removed | 被踢者 |

> 互评提交不发通知（按需可后续补充）。

## 四、接口清单（项目模块全量，共 16 个）

| # | Method | Path | 状态 |
|---|--------|------|------|
| 1 | POST | `/api/v1/projects/` | 改造（接收新字段） |
| 2 | GET | `/api/v1/projects/` | 既有 |
| 3 | GET | `/api/v1/projects/<project_id>` | 既有 |
| 4 | PUT | `/api/v1/projects/<project_id>` | 改造（支持新字段） |
| 5 | POST | `/api/v1/projects/<project_id>/apply` | 既有 |
| 6 | POST | `/api/v1/projects/<project_id>/applications/<app_id>/approve` | 既有 |
| 7 | POST | `/api/v1/projects/<project_id>/applications/<app_id>/reject` | 既有 |
| 8 | POST | `/api/v1/projects/<project_id>/close` | 既有 |
| 9 | GET | `/api/v1/projects/user/<user_id>` | 既有 |
| 10 | GET | `/api/v1/projects/my-applications` | **新增** |
| 11 | POST | `/api/v1/projects/<project_id>/leave` | **新增** |
| 12 | POST | `/api/v1/projects/<project_id>/members/<user_id>/remove` | **新增** |
| 13 | POST | `/api/v1/projects/<project_id>/finish` | **新增** |
| 14 | POST | `/api/v1/projects/<project_id>/ratings` | **新增** |
| 15 | GET | `/api/v1/projects/<project_id>/ratings` | **新增** |
| 16 | GET | `/api/v1/projects/mine` | 既有 |

## 五、测试覆盖矩阵

### 专项测试 `tests/test_project_members_ratings.py`（31 项，全部 PASS）

| # | 测试名 | 覆盖接口/场景 |
|---|--------|---------------|
| 01 | 发起项目带新字段 | create_project + 6 个新字段返回校验 |
| 02 | topic 过长(400) | create_project 校验 |
| 03 | max_members<1(400) | create_project 校验 |
| 04 | required_level>100(400) | create_project 校验 |
| 05 | 编辑新字段 | update_project + 新字段更新 |
| 06 | 我的申请列表(初始空) | my-applications |
| 07 | 我的申请列表(有数据) | my-applications + project 摘要 |
| 08 | 我的申请-按 status 过滤 | my-applications?status=pending |
| 09 | 我的申请-无效 status(400) | my-applications 校验 |
| 10 | recruiting 不可退出(400) | leave 状态校验 |
| 11 | 发起人不可退出(400) | leave 权限校验 |
| 12 | B 退出项目成功 | leave 成功路径 + status=left 验证 |
| 13 | 非成员退出(5008) | leave 成员校验 |
| 14 | 非发起人踢人(5002) | remove 权限校验 |
| 15 | 踢自己(400) | remove 自踢校验 |
| 16 | 踢非成员(5008) | remove 成员校验 |
| 17 | 踢人成功 | remove 成功路径 + status=removed 验证 |
| 18 | 非发起人结束(5002) | finish 权限校验 |
| 19 | 结束项目成功(含重复结束) | finish 成功路径 + 幂等 |
| 20 | recruiting 不可结束(5003) | finish 状态校验 |
| 21 | 项目未完成不可互评(5011) | create_rating 状态校验 |
| 22 | 非成员互评(5008) | create_rating 成员校验 |
| 23 | 评价自己(5009) | create_rating 自评校验 |
| 24 | 无效分数(5012) | create_rating score 校验 |
| 25 | 评价非成员(5008) | create_rating to_user 成员校验 |
| 26 | 提交互评成功 | create_rating 成功路径 |
| 27 | 重复评价(5010) | create_rating 唯一约束 |
| 28 | 匿名互评成功 | create_rating is_anonymous |
| 29 | 查看互评列表(含匿名) | list_ratings + 匿名脱敏 |
| 30 | 非成员查看互评(5008) | list_ratings 成员校验 |
| 31 | 互评分页 | list_ratings 分页 |

### 联合回归测试（全部 PASS）

| 测试文件 | 用例数 | 结果 |
|----------|--------|------|
| `tests/test_all_modules.py` | 29 | PASS（作品/互动/项目核心流程未受影响） |
| `tests/test_messages.py` | 26 | PASS（消息/通知/群聊未受影响） |

## 六、问题修复清单

| 问题 | 原因 | 修复 |
|------|------|------|
| `max_members=0` 被当作合法值 | `int(data.get('max_members') or 10)` 中 `0 or 10` 返回 10 | 改为 `int(data.get('max_members', 10))`，同理修复 `required_level` / `required_project_count` |
| 测试 teardown 外键报错 | `users` 删除前未清理 `profiles` | teardown 先 `Profile.query.filter_by(user_id=...).delete()` 再删用户 |

## 七、前端对接提醒

1. **项目卡片/详情新增字段**（无需升级即可使用）：
   - `topic`（项目主题，字符串）
   - `required_level`（要求最低等级，整数）
   - `required_project_count`（要求参与项目次数下限，整数）
   - `contact_visible`（队长是否公开联系方式，布尔）
   - `max_members`（招募总人数上限，整数，默认 10）
   - `cover_url`（项目封面 URL，字符串）

2. **申请状态扩展**：
   - `my_application.status` 现在可能是 `pending` / `approved` / `rejected` / `left` / `removed`
   - 在「我的申请」列表中，`to_dict(with_expired=True)` 还会返回 `is_expired` 标记 + 动态 `status='expired'`（仅 pending 且 deadline 已过）

3. **新接口路径**（见上表第 10-15 项），注意：
   - 退出/踢人仅在项目 `ongoing` 或 `completed` 状态可操作
   - 结束项目仅 `ongoing` → `completed`；`recruiting` 不可直接结束
   - 互评仅在项目 `completed` 后开放；同一对用户在同一项目内只能评价一次
   - 匿名评价在列表接口中 `from_user_id` / `from_user` 返回 `null`

4. **通知新增 subtype**：`leave`（成员退出）/ `removed`（被踢），type 均为 `system`。
