# 艺联萌

> 创作者协作对接平台 —— 让有单个技能的人，找到互补的团队。

## 项目简介

艺联萌是一个面向内容创作者的协作平台，解决「有单个技能，缺协作团队」的行业痛点。平台支持创作者发布作品、发起协作项目、互相评分、建立个人品牌，同时打通创作者与企业的供需对接通道。

## 技术栈

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| **后端框架** | Python / Flask | 3.0.3 |
| **数据库** | MySQL | 8.0+ |
| **ORM** | Flask-SQLAlchemy | 3.1.x |
| **数据库迁移** | Flask-Migrate | 4.1.x |
| **数据库驱动** | PyMySQL | 1.1.1 |
| **跨域处理** | Flask-CORS | 4.0.1 |
| **身份认证** | JWT (PyJWT) | 2.x |
| **环境管理** | python-dotenv | 1.0.1 |
| **前端** | 待定（跨平台框架 / 原生） | - |
| **部署** | 云服务器 + 对象存储 | - |

## 核心功能

- 创作者档案：技能标签体系 + 身份标识（专业/非专业）+ 能力证明
- 作品发布：独立发布 / 协作发布，支持视频、漫画、短剧等多品类
- 创作广场：作品流、关注流、搜索、按技能筛选
- 协作项目：发起/申请/审批/退出/踢人/结束/互评，支持付费/免费模式
- 评分与等级：项目合伙人互评 -> 用户等级升级（最高 7 级）
- 消息系统：私信会话、群聊、文件消息、未读计数、官方会话
- 通知系统：官方通知、互动通知、待办通知三类聚合
- 关注关系：单向关注、互相关注、粉丝/关注列表、计数冗余
- 内容频道：短视频 / 长视频 / 漫画 / 短剧 / 影视 / 动漫动画
- 个人主页：聚合主页、他人作品/项目列表、点赞作品、浏览记录

## 团队分工

| 角色 | 职责 |
|------|------|
| **产品** (苑+冯) | 需求文档、功能规划、竞品调研 |
| **设计** (罗+冯) | UI设计、交互规范、视觉风格 |
| **后端** | 数据库设计、接口开发、服务器部署 |
| **前端** | APP页面开发、接口联调、打包适配 |
| **物联网** | 多设备测试、弱网缓存方案、同步方案 |

## 项目状态

**后端 MVP 全量交付** · 11 个模块 96 个接口全部开发完成 · 等待前端联调对接。

### 开发进度

| 阶段 | 状态 | 完成内容 |
|------|------|----------|
| 需求分析 | 完成 | 产品思维导图分析、API 接口规范文档 |
| 技术架构设计 | 完成 | 目录结构设计、数据库模型设计 |
| 数据库搭建 | 完成 | 37 张业务表（含索引/外键/唯一键） |
| 认证模块 | 完成 | 7 接口：验证码、注册、登录、重置密码、Token刷新、用户信息、登出 |
| 创作者档案模块 | 完成 | 23 接口：档案读写、技能增改查、风格标签、工作经历、教育经历、能力证明、文件上传 |
| 作品模块 | 完成 | 12 接口：创建/编辑/发布/删除/详情/我的列表/Feed/关注流/搜索/按技能/转推/上传 |
| 互动模块 | 完成 | 7 接口：点赞/取消/列表、评论/回复/删除/回复列表 |
| 协作项目模块 | 完成 | 16 接口：发起/列表/详情/编辑/申请/审批/关闭/我的项目 + 申请列表/退出/踢人/结束/互评/查看互评 |
| 私信会话模块 | 完成 | 6 接口：会话列表/建立会话/消息收发/标记已读/官方会话 |
| 群聊模块 | 完成 | 8 接口：群列表/消息/发送/已读/成员/建群/邀请/退群 |
| 消息附件上传 | 完成 | 1 接口：私信文件消息上传 |
| 通知模块 | 完成 | 5 接口：未读计数/互动通知/待办通知/标记已读/全部已读 |
| 关注模块 | 完成 | 6 接口：关注/取关/状态/我的关注/我的粉丝/统计 |
| 钱包/活动/供需 | 完成 | 数据库表与模型已就绪，接口按 UI 需求补齐 |
| 前端开发 | 待开始 | APP页面开发、接口联调 |

### 测试覆盖

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| `tests/test_all_modules.py` | 29 | 作品/互动/项目核心流程联合回归 |
| `tests/test_messages.py` | 26 | 私信/群聊/通知/关注完整链路 |
| `tests/test_project_members_ratings.py` | 31 | 项目成员管理 + 互评（含异常分支） |
| `tests/test_auth*.py` / `test_profile*.py` / `test_works.py` / `test_feed.py` 等 | — | 各模块专项测试 |

> 累计 86+ 测试用例全部 PASS（截至 2026-09-07）。

## 项目结构

```
yilianmeng-main/
├── app/                          # Flask 应用核心目录
│   ├── __init__.py               # 应用初始化、蓝图注册、配置
│   ├── config.py                 # 配置文件
│   ├── models/                   # 数据库模型（23 个模型文件，37 张表）
│   │   ├── __init__.py
│   │   ├── user.py               # 用户模型（含计数冗余字段）
│   │   ├── profile.py            # 创作者档案模型
│   │   ├── skill.py              # 技能模型（分类/技能/用户技能）
│   │   ├── style_tags.py         # 风格标签
│   │   ├── work.py               # 作品模型
│   │   ├── interaction.py        # 点赞 + 评论
│   │   ├── project.py            # 项目 + 申请 + 所需技能
│   │   ├── rating.py             # 互评 + 评价标签字典
│   │   ├── message.py            # 消息模型
│   │   ├── conversation.py       # 私信会话 + 已读
│   │   ├── group.py              # 群聊 + 成员 + 已读
│   │   ├── notification.py       # 通知模型
│   │   ├── event.py              # 活动模型
│   │   ├── wallet.py             # 钱包 + 交易流水
│   │   ├── experience.py         # 工作/教育经历
│   │   ├── ability.py            # 能力证明
│   │   ├── follows.py            # 关注关系
│   │   ├── work_repost.py        # 作品转推
│   │   ├── work_visibility_rule.py  # 作品可见性规则
│   │   ├── work_top.py           # 作品置顶
│   │   ├── work_view_history.py    # 作品浏览历史
│   │   └── project_view_history.py # 项目浏览历史
│   ├── routes/                   # API 路由（11 个模块，96 个接口）
│   │   ├── __init__.py
│   │   ├── auth.py               # 认证（7）
│   │   ├── profile.py            # 档案 + 主页（26）
│   │   ├── works.py              # 作品 + 广场（14）
│   │   ├── interactions.py       # 互动（7）
│   │   ├── projects.py           # 协作项目（16）
│   │   ├── conversations.py      # 私信会话（6）
│   │   ├── groups.py             # 群聊（8）
│   │   ├── messages_upload.py    # 消息附件（1）
│   │   ├── notifications.py      # 通知（5）
│   │   └── follows.py            # 关注（6）
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── helpers.py            # Token/响应/分页/文件上传/装饰器
├── migrations/                   # 数据库迁移文件
│   └── versions/                 # 迁移版本记录
├── tests/                        # 接口测试脚本（86+ 用例）
├── uploads/                      # 文件上传目录（自动创建）
├── work-logs/                    # 开发工作日志（含全量接口+DB 清单）
├── venv/                         # Python 虚拟环境
├── app.py                        # 应用入口
├── seed_skills.py                # 技能数据初始化脚本
├── API.md                        # 接口文档（96 个，最新）
├── DATABASE.md                   # 数据库文档（37 张表，最新）
├── requirements.txt              # 依赖清单
├── .env                          # 环境变量
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略配置
└── README.md                     # 项目说明
```

## 数据库表结构（37 张表）

| 模块 | 表 | 说明 |
|------|----|------|
| 用户 | `users` | 用户表（含 following_count / follower_count / work_count / project_count 冗余字段） |
| 用户 | `wallets` | 钱包表 |
| 用户 | `transactions` | 交易流水表 |
| 档案 | `profiles` | 创作者档案 |
| 档案 | `profile_skills` | 用户技能关联 |
| 档案 | `profile_style_tags` | 用户风格标签 |
| 档案 | `work_experiences` | 工作经历 |
| 档案 | `work_experience_images` | 工作经历图片 |
| 档案 | `education_experiences` | 教育经历 |
| 档案 | `ability_proofs` | 能力证明 |
| 档案 | `ability_proof_files` | 能力证明文件 |
| 字典 | `skill_categories` | 技能分类 |
| 字典 | `skills` | 技能 |
| 字典 | `style_tags` | 风格标签 |
| 字典 | `rating_tags` | 评价标签字典 |
| 作品 | `works` | 作品表（25 字段） |
| 作品 | `work_view_history` | 作品浏览历史 |
| 作品 | `work_reposts` | 转推关系 |
| 作品 | `work_top` | 置顶 |
| 作品 | `work_visibility_rules` | 可见性规则 |
| 互动 | `likes` | 点赞 |
| 互动 | `comments` | 评论 + 回复 |
| 项目 | `projects` | 项目表（16 字段，含 topic/required_level/required_project_count/contact_visible） |
| 项目 | `project_applications` | 项目申请（status 扩展 pending/approved/rejected/left/removed） |
| 项目 | `project_required_skills` | 项目所需技能 |
| 项目 | `project_view_history` | 项目浏览历史 |
| 项目 | `ratings` | 项目互评（唯一约束 project_id+from_user_id+to_user_id） |
| 消息 | `conversations` | 私信会话（user1_id < user2_id 唯一） |
| 消息 | `conversation_reads` | 会话已读状态 |
| 消息 | `messages` | 消息记录（支持文本/文件/语音） |
| 消息 | `groups` | 群聊 |
| 消息 | `group_members` | 群成员 |
| 消息 | `group_reads` | 群已读状态 |
| 通知 | `notifications` | 通知（official/interaction/todo 三类聚合） |
| 活动 | `events` | 活动 |
| 活动 | `event_participants` | 活动参与者 |
| 关注 | `follows` | 关注关系（唯一约束 follower_id+followed_id） |

> 完整字段/索引/外键明细见 [API.md](API.md) / [DATABASE.md](DATABASE.md)（全量最新）。

## API 接口规范

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:8080/api/v1` |
| 请求体格式 | `Content-Type: application/json` |
| 文件上传 | `Content-Type: multipart/form-data` |
| 认证方式 | JWT Bearer Token（请求头 `Authorization: Bearer <token>`） |
| 分页参数 | `?page=1&page_size=20` |
| 分页返回 | `{ total, page, page_size, total_pages, list }` |

### 响应格式

```json
{ "code": 200, "message": "success", "data": { ... } }
```

> HTTP 状态码与业务码分离：HTTP 遵循语义（200/400/401/403/404/429/500），Body.code 为业务码（200=成功，1xxx=认证，3xxx=作品，5xxx=项目）。

### 已实现接口（96 个，按模块分组）

| 模块 | 接口数 | 路径前缀 | 主要功能 |
|------|--------|----------|----------|
| 认证 | 7 | `/auth` | 验证码/注册/登录/重置密码/Token刷新/用户信息/登出 |
| 档案 + 主页 | 23 | `/profile` | 档案读写/技能/风格标签/工作经历/教育经历/能力证明/文件上传 + 个人主页聚合 |
| 作品 + 广场 | 12 | `/works` | 创建/编辑/发布/删除/详情/我的/Feed/关注流/搜索/按技能/转推/上传 |
| 互动 | 7 | `/works/<id>/like` `/comments` | 点赞/取消/列表、评论/回复/删除/回复列表 |
| 协作项目 | 16 | `/projects` | 发起/列表/详情/编辑/申请/审批/关闭 + 我的申请/退出/踢人/结束/互评/查看互评 |
| 私信会话 | 6 | `/conversations` | 会话列表/建立会话/消息收发/标记已读/官方会话 |
| 群聊 | 8 | `/groups` | 群列表/消息/发送/已读/成员/建群/邀请/退群 |
| 消息附件 | 1 | `/messages/upload` | 私信文件消息上传 |
| 通知 | 5 | `/notifications` | 未读计数/互动通知/待办通知/标记已读/全部已读 |
| 关注 | 6 | `/users/<id>/follow` `/following` `/followers` | 关注/取关/状态/我的关注/我的粉丝/统计 |

> 完整接口清单（含路径/方法/函数定位/文件）见 [API.md](API.md) / [DATABASE.md](DATABASE.md)（全量最新）。

### 错误码一览

| 范围 | 模块 | 示例 |
|------|------|------|
| 200 | 成功 | — |
| 1xxx | 认证 | 1001 手机号格式 / 1005 已注册 / 1008 场景参数 |
| 3xxx | 作品 | 3001 不存在 / 3003 草稿不可见 |
| 5xxx | 项目 | 5001 不存在 / 5002 无权限 / 5008 非成员 / 5009 不可自评 / 5010 已评 / 5011 项目未完成 |

## 本地运行

### 环境要求

- Python 3.10+
- MySQL 8.0+
- Git

### 安装步骤

```bash
# 1. 克隆项目
git clone <仓库地址>
cd yilianmeng-main

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填写真实的数据库密码和密钥

# 5. 创建数据库（MySQL 命令行）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yilianmeng DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. 数据库迁移（首次运行）
flask db init        # 初始化迁移目录（仅首次）
flask db migrate -m "init database"  # 生成迁移脚本
flask db upgrade     # 执行迁移，创建表结构

# 7. 初始化技能数据（首次运行）
python seed_skills.py

# 8. 启动后端服务
python app.py
# 服务启动后访问 http://localhost:8080
```

### 配置文件说明

`.env` 文件配置项：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=yilianmeng

# Flask 配置
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=随机字符串

# JWT 配置
JWT_SECRET_KEY=随机字符串
JWT_EXPIRES_IN=7
```

## 接口测试

### 1. 启动服务

```bash
cd C:\Users\z1595\Desktop\yilianmeng-main
.\venv\Scripts\activate
python app.py
```

服务启动后访问：http://localhost:8080

### 2. 运行测试

测试脚本位于 `tests/` 目录，使用 unittest 模式（无需启动服务器，进程内执行）：

```bash
# 联合回归测试（作品/互动/项目核心流程）
python -m unittest tests.test_all_modules -v

# 消息模块完整链路
python -m unittest tests.test_messages -v

# 项目成员管理 + 互评（31 项，含异常分支）
python -m unittest tests.test_project_members_ratings -v
```

### 3. 验证清单

| 检验项 | 预期结果 |
|--------|----------|
| 服务启动 | http://localhost:8080 可访问 |
| 发送验证码 | 返回 `dev_code` 字段（开发环境） |
| 登录新用户 | 返回 `is_new_user: true` 和 Token |
| 登录老用户 | 返回 `is_new_user: false` 和 Token |
| 获取用户信息 | 返回用户信息，手机号脱敏（他人查看）/ 完整（自己） |
| Token 刷新 | 返回新的 Token |
| 登出 | 返回成功 |
| 未认证访问 | 返回 401 错误 |
| 档案读写 | 档案可更新，技能可覆盖式更新 |
| 技能分类查询 | 返回 4 分类 21 技能 |
| 作品创建/发布 | 草稿可发布，浏览数 +1 |
| 作品软删除 | 删除后列表不显示 |
| 草稿不可见 | 非作者访问草稿返回 404 |
| 私信会话 | 单向关注可发 1 条，互关可自由发 |
| 群聊 | 建群/邀请/发消息/已读/退群全链路 |
| 项目协作 | 申请→审批→转 ongoing→结束→互评 |
| 项目退出/踢人 | status 标记 left/removed，发通知 |
| 项目互评 | 不可自评/重复评，匿名评价脱敏 |

## 开发日志

| 日期 | 文件 | 内容 |
|------|------|------|
| 2026-07-20 | `work-logs/2026-07-20_phase1.md` | 项目分析与技术架构设计 |
| 2026-07-20 | `work-logs/2026-07-20_database-setup.md` | 数据库模型设计与表结构创建 |
| 2026-07-20 | `work-logs/2026-07-20_auth-module.md` | 用户认证模块开发 |
| 2026-07-31 | `work-logs/2026-07-31_auth-optimization.md` | 认证模块优化 |
| 2026-07-31 | `work-logs/2026-07-31_auth-refinement.md` | 登录模块完善（返回信息/Token刷新/错误码） |
| 2026-07-31 | `work-logs/2026-07-31_profile-module.md` | 创作者档案模块开发 |
| 2026-07-31 | `work-logs/2026-07-31_works-module.md` | 作品发布模块开发 |
| 2026-09-07 | `work-logs/2026-09-07_full-api-and-db.md` | **全量接口 + 数据库清单（90 接口 / 37 表）** |
| 2026-09-07 | `work-logs/2026-09-07_message-notification-triggers.md` | 消息页通知触发补齐 |
| 2026-09-07 | `work-logs/2026-09-07_profile-homepage-apis.md` | 个人主页接口补齐（6 新增 + 2 改造） |
| 2026-09-07 | `work-logs/2026-09-07_project-members-ratings.md` | 项目成员管理 + 互评（6 新增 + 2 改造） |

## 开发规范

### 代码规范

- 使用 PEP 8 规范编写 Python 代码
- 变量命名使用蛇形命名法（snake_case）
- 函数命名使用蛇形命名法
- 类命名使用大驼峰命名法（PascalCase）

### 数据库规范

- 使用 Flask-Migrate 管理数据库迁移
- 所有字符串字段使用 utf8mb4 字符集
- 时间字段使用 DATETIME 类型，存储 UTC 时间
- 金额使用「分」为单位（整数），避免浮点误差
- 软删除用 status 字段标记，不真正删除数据
- 冗余计数字段（follower_count 等）随业务变更同步更新

### API 规范

- 统一响应格式：`{ code, message, data }`
- HTTP 状态码与业务码分离（HTTP 遵循语义，Body.code 为业务码）
- 分页接口返回 `list`, `total`, `page`, `page_size`, `total_pages`
- 软删除用 status 字段标记，不真正删除数据
- 错误码分段：1xxx 认证 / 3xxx 作品 / 5xxx 项目
- 列表接口支持批量预取，避免 N+1 查询

## 联系方式

如有问题，请联系团队成员或提交 Issue。
