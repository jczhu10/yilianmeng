# 协作项目模块开发日志

**日期**：2026-07-31
**模块**：协作项目（projects）
**接口数**：9
**测试用例**：25（全部通过）

---

## 一、需求背景

补齐"创作者协作"核心场景，让创作者可以发起协作项目、招募成员、审批申请，实现从内容消费（作品）到内容生产协作的闭环。

## 二、数据库变更

### 复用既有表（无新建）
- `projects`：协作项目表
- `project_applications`：项目申请表

### 微调字段（1 个迁移）
| 表 | 新增字段 | 类型 | 说明 |
|----|----------|------|------|
| project_applications | processed_at | DateTime | 审批时间 |

迁移文件：`migrations/versions/3aeb772d0893_add_processed_at_to_project_applications.py`

### 状态枚举明确化
- **Project.status**：`recruiting` / `ongoing` / `completed` / `closed`
- **Project.mode**：`free` / `paid`
- **ProjectApplication.status**：`pending` / `approved` / `rejected`

## 三、接口实现

### 新增文件
- `app/routes/projects.py`：9 个接口，5001-5007 错误码

### 接口清单

| # | 方法 | 路径 | 功能 | 鉴权 |
|---|------|------|------|------|
| 1 | POST | /projects/ | 发起协作项目 | 是 |
| 2 | GET | /projects/ | 项目列表（分页+状态/mode/skill_id筛选） | 是 |
| 3 | GET | /projects/<id> | 项目详情（权限分层返回） | 是 |
| 4 | PUT | /projects/<id> | 编辑项目（仅发起人，仅 recruiting） | 是 |
| 5 | POST | /projects/<id>/apply | 申请加入 | 是 |
| 6 | POST | /projects/<id>/applications/<app_id>/approve | 通过申请（仅发起人） | 是 |
| 7 | POST | /projects/<id>/applications/<app_id>/reject | 拒绝申请（仅发起人） | 是 |
| 8 | POST | /projects/<id>/close | 关闭项目（仅发起人） | 是 |
| 9 | GET | /projects/mine | 我的项目（role=created/joined/all） | 是 |

### 错误码（5xxx 区间）
| 业务码 | 含义 | HTTP |
|--------|------|------|
| 5001 | 项目不存在 | 404 |
| 5002 | 无权操作（非发起人） | 403 |
| 5003 | 项目状态不允许此操作 | 400 |
| 5004 | 不能申请自己的项目 | 400 |
| 5005 | 已申请过该项目 | 400 |
| 5006 | 申请不存在 | 404 |
| 5007 | 申请已处理 | 400 |

### 核心业务规则
1. **状态流转**：recruiting（默认）→ ongoing（首个申请通过自动转）→ completed/closed
2. **可编辑性**：仅 recruiting 状态可编辑
3. **申请规则**：不能申请自己项目(5004)、不能重复申请(5005)、仅 recruiting 可申请
4. **审批规则**：仅发起人可审批(5002)、项目转 ongoing 后不能再审批(5003)、已处理申请不可再操作(5007)
5. **数据可见性**：发起人见 applications 列表，非发起人 + ongoing/completed 见 members 列表

### 字段输出设计
项目对象额外字段：creator / is_creator / member_count / my_application / applications / members
申请对象额外字段：applicant / processed_at

## 四、蓝图注册

`app/__init__.py` 新增：
```python
from app.routes.projects import bp as projects_bp
app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')
```

## 五、测试结果

测试文件：`tests/test_projects.py`，**25 项全部通过**。

### 测试覆盖
**正常流程（14 项）**：发起→列表→详情→编辑→申请→通过→转ongoing→我的项目→关闭
**异常流程（11 项）**：无效技能/空标题/无效状态/重复申请/申请自己项目/申请已处理/非发起人审批/编辑ongoing项目/非发起人关闭/关闭后申请/项目不存在/未认证

### 测试中遇到的问题
1. **登录函数**：改为先调 `/auth/send-code` 获取 dev_code 再登录
2. **字段名**：`ProjectApplication.to_dict()` 返回 `id` 不是 `application_id`，已修正
3. **测试7业务顺序**：代码先校验项目状态再校验申请状态，改用独立项目验证 5007

## 六、技术要点

1. **JSON 查询**：按技能筛选用 MySQL `JSON_CONTAINS`
2. **批量查询避免 N+1**：申请列表/成员列表先收集 user_id 再批量查 User
3. **通用审批函数**：`_process_application()` 抽取 approve/reject 共同逻辑
4. **subquery 查询**：`/mine?role=joined` 用子查询获取已通过申请关联的项目
5. **权限分层**：发起人/申请人/普通用户三种视角返回不同字段

## 七、前端对接提醒

1. 列表/详情返回字段丰富，无需二次查询发起人和申请状态
2. `my_application` 判断"我是否已申请"及状态，控制按钮显示
3. `is_creator` 判断是否显示"编辑/审批/关闭"按钮
4. 编辑项目仅 recruiting 状态可用，前端需根据 status 控制 UI
5. 通过申请后项目自动转 ongoing，前端列表需及时刷新
6. `deadline` 用 ISO 8601 格式

## 八、项目整体进度

| 模块 | 接口数 | 测试用例 | 状态 |
|------|--------|----------|------|
| 认证 auth | 5 | 10 | ✅ |
| 档案 profile | 7 | 11 | ✅ |
| 作品 works | 7 | 13 | ✅ |
| 互动 interactions | 7 | 16 | ✅ |
| 推流 feed | 3 | 19 | ✅ |
| **协作 projects** | **9** | **25** | **✅ 新增** |
| **合计** | **38** | **94** | **全部通过** |
