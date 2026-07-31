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
- 创作广场：项目协作邀请、付费/免费模式、技能匹配
- 评分与等级：项目合伙人互评 -> 用户等级升级（最高7级）
- 内容频道：短视频 / 长视频 / 漫画 / 短剧 / 影视 / 动漫动画
- 供需对接：找工作、找项目、招人、发简历
- 主题活动：定期创作挑战 + 艺联币激励（可提现）

## 团队分工

| 角色 | 职责 |
|------|------|
| **产品** (苑+冯) | 需求文档、功能规划、竞品调研 |
| **设计** (罗+冯) | UI设计、交互规范、视觉风格 |
| **后端** | 数据库设计、接口开发、服务器部署 |
| **前端** | APP页面开发、接口联调、打包适配 |
| **物联网** | 多设备测试、弱网缓存方案、同步方案 |

## 项目状态

开发中 · 预计第一轮 Demo 完成时间：2026年8月1日

### 开发进度

| 阶段 | 状态 | 完成内容 |
|------|------|----------|
| 需求分析 | 完成 | 产品思维导图分析、API接口规范文档 |
| 技术架构设计 | 完成 | 目录结构设计、数据库模型设计 |
| 数据库搭建 | 完成 | 11个核心模型、15张表结构创建 |
| 用户认证模块 | 完成 | 5个接口：验证码、登录/注册、Token刷新、用户信息、登出 |
| 创作者档案模块 | 完成 | 7个接口：档案读写、技能增改查、技能分类、查看他人档案 |
| 作品发布模块 | 完成 | 7个接口：创建/编辑/发布/删除/详情/我的列表/文件上传 |
| 创作广场模块 | 待开始 | 作品流、项目招募、申请参与 |
| 互动模块 | 待开始 | 点赞、评论、回复 |
| 其他模块 | 待开始 | 评分、消息、供需、活动、钱包 |
| 前端开发 | 待开始 | APP页面开发、接口联调 |

### 第1个月目标（~8.1）：需求定型 + 视觉风格确立

| 小组 | 任务 | 状态 |
|------|------|------|
| 产品 | 竞品调研表 + 完整 PRD + 用户定位 + 盈利模式 | 进行中 |
| 设计 | 视觉风格定稿 + 所有页面线框图 + 高保真 UI 初稿 | 进行中 |
| 后端 | 数据结构设计 + 数据库搭建 + 接口清单规划 + 工程环境搭建 | 完成 |
| 前端 | APP 基础工程 + 安卓/iOS 适配 + 空白页面框架 | 待开始 |
| 物联网 | 理解业务逻辑 + 准备测试设备 + 弱网/同步方案调研 | 待开始 |

## 项目结构

```
yilianmeng-main/
├── app/                          # Flask 应用核心目录
│   ├── __init__.py               # 应用初始化、蓝图注册、配置
│   ├── config.py                 # 配置文件
│   ├── models/                   # 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py               # 用户模型
│   │   ├── profile.py            # 创作者档案模型
│   │   ├── skill.py              # 技能模型（分类/技能/用户技能关联）
│   │   ├── work.py               # 作品模型
│   │   ├── project.py            # 项目模型
│   │   ├── rating.py             # 评分模型
│   │   ├── message.py            # 消息模型
│   │   ├── event.py              # 活动模型
│   │   └── wallet.py             # 钱包模型
│   ├── routes/                   # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py               # 用户认证接口（已完成，5个）
│   │   ├── profile.py            # 创作者档案接口（已完成，7个）
│   │   └── works.py              # 作品发布接口（已完成，7个）
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── helpers.py            # 通用辅助函数（Token/响应/分页/文件上传）
├── migrations/                   # 数据库迁移文件
│   └── versions/                 # 迁移版本记录（3个迁移版本）
├── tests/                        # 接口测试脚本
│   ├── test_auth.py              # 认证模块测试
│   ├── test_profile.py           # 档案模块测试
│   └── test_works.py             # 作品模块测试
├── uploads/                      # 文件上传目录（自动创建）
├── work-logs/                    # 开发工作日志（7份）
├── venv/                         # Python 虚拟环境
├── app.py                        # 应用入口
├── seed_skills.py                # 技能数据初始化脚本
├── requirements.txt              # 依赖清单
├── API_DOCS.md                   # 接口文档（19个接口）
├── .env                          # 环境变量
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略配置
├── README.md                     # 项目说明
└── docs/                         # 项目文档
    └── api-spec.md               # API 接口规范文档
```

## 数据库表结构

| 表名 | 说明 | 状态 |
|------|------|------|
| `users` | 用户表 | 已创建 |
| `profiles` | 创作者档案表 | 已创建 |
| `skill_categories` | 技能分类表 | 已创建 |
| `skills` | 技能表 | 已创建 |
| `profile_skills` | 用户技能关联表 | 已创建 |
| `works` | 作品表 | 已创建 |
| `projects` | 项目表 | 已创建（接口未开发） |
| `project_applications` | 项目申请表 | 已创建（接口未开发） |
| `ratings` | 评分表 | 已创建（接口未开发） |
| `messages` | 消息表 | 已创建（接口未开发） |
| `events` | 活动表 | 已创建（接口未开发） |
| `event_participants` | 活动参与者表 | 已创建（接口未开发） |
| `wallets` | 钱包表 | 已创建（接口未开发） |
| `transactions` | 交易记录表 | 已创建（接口未开发） |

## API 接口规范

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:8080/api/v1` |
| 请求体格式 | `Content-Type: application/json` |
| 文件上传 | `Content-Type: multipart/form-data` |
| 认证方式 | JWT Bearer Token（请求头 `Authorization: Bearer <token>`） |

### 响应格式

```json
{ "code": 200, "message": "success", "data": { ... } }
```

> HTTP状态码与业务码分离：HTTP状态码遵循HTTP语义(200/400/401/403/404/429/500)，Body中的code为业务码(200=成功,1xxx=认证类,2xxx=档案类,3xxx=作品类)。详细文档见 [API_DOCS.md](API_DOCS.md)。

### 已实现接口（19个）

| 模块 | 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|------|
| 认证 | POST | `/auth/send-code` | 发送验证码 | 否 |
| 认证 | POST | `/auth/login` | 登录/注册 | 否 |
| 认证 | POST | `/auth/refresh` | 刷新Token | 是 |
| 认证 | GET | `/auth/me` | 获取用户信息 | 是 |
| 认证 | POST | `/auth/logout` | 登出 | 是 |
| 档案 | GET | `/profile/me` | 获取我的档案 | 是 |
| 档案 | PUT | `/profile/me` | 更新我的档案 | 是 |
| 档案 | PUT | `/profile/skills` | 更新我的技能 | 是 |
| 档案 | GET | `/profile/skills/mine` | 获取我的技能 | 是 |
| 档案 | GET | `/profile/skills/categories` | 获取技能分类 | 否 |
| 档案 | GET | `/profile/skills` | 获取技能列表 | 否 |
| 档案 | GET | `/profile/<user_id>` | 查看他人档案 | 是 |
| 作品 | POST | `/works/` | 创建作品 | 是 |
| 作品 | PUT | `/works/<work_id>` | 编辑作品 | 是 |
| 作品 | POST | `/works/<work_id>/publish` | 发布作品 | 是 |
| 作品 | DELETE | `/works/<work_id>` | 删除作品 | 是 |
| 作品 | GET | `/works/<work_id>` | 作品详情 | 是 |
| 作品 | GET | `/works/mine` | 我的作品列表 | 是 |
| 作品 | POST | `/works/upload` | 文件上传 | 是 |

### 待实现接口

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 创作广场 | `/square` / `/works/feed` | 作品流/推荐流、项目招募/申请参与 |
| 互动 | `/likes` / `/comments` | 点赞、评论、回复 |
| 评分与等级 | `/ratings` / `/level` | 互评/等级查询 |
| 消息 | `/messages` | 私信/系统通知 |
| 供需对接 | `/market` | 招聘/求职/项目发布 |
| 主题活动 | `/events` | 活动列表/参与/排行榜 |
| 艺联币 | `/wallet` | 钱包/交易/提现 |

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

### 2. 运行分模块测试

测试脚本位于 `tests/` 目录，按模块划分：

```bash
# 测试认证模块（5个接口 + 异常场景）
python tests/test_auth.py

# 测试档案模块（7个接口 + 异常场景）
python tests/test_profile.py

# 测试作品模块（7个接口 + 异常场景）
python tests/test_works.py
```

> 详细接口说明、请求参数、返回示例见 [API_DOCS.md](API_DOCS.md)。

### 3. 验证清单

| 检验项 | 预期结果 |
|--------|----------|
| 服务启动 | http://localhost:8080 可访问 |
| 发送验证码 | 返回 `dev_code` 字段 |
| 登录新用户 | 返回 `is_new_user: true` 和 Token |
| 登录老用户 | 返回 `is_new_user: false` 和 Token |
| 获取用户信息 | 返回用户信息，手机号脱敏 |
| Token刷新 | 返回新的 Token |
| 登出 | 返回成功 |
| 未认证访问 | 返回 401 错误 |
| 档案读写 | 档案可更新，技能可覆盖式更新 |
| 技能分类查询 | 返回4分类21技能 |
| 作品创建/发布 | 草稿可发布，浏览数+1 |
| 作品软删除 | 删除后列表不显示 |
| 草稿不可见 | 非作者访问草稿返回404 |

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

### API 规范

- 统一响应格式：`{ code, message, data }`
- HTTP状态码与业务码分离（HTTP遵循语义，Body.code为业务码）
- 分页接口返回 `list`, `total`, `page`, `page_size`, `total_pages`
- 软删除用 status 字段标记，不真正删除数据

## 联系方式

如有问题，请联系团队成员或提交 Issue。
