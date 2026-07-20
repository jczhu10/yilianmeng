# 艺联萌后端开发工作日志 - 数据库搭建

## 日期
2026-07-20

## 阶段目标
完成数据库模型设计、迁移配置和表结构创建

---

## 1. 数据库连接配置

### 1.1 .env 文件配置
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=!13451789272Zz
DB_NAME=yilianmeng
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=jwt-secret-key
JWT_EXPIRES_IN=7
```

### 1.2 连接验证
```bash
python -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='!13451789272Zz', port=3306); print('MySQL连接成功! 版本:', conn.get_server_info()); conn.close()"
```
**结果**：MySQL 8.0.46 连接成功

### 1.3 创建数据库
```sql
CREATE DATABASE IF NOT EXISTS yilianmeng DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 2. 虚拟环境配置

### 2.1 创建虚拟环境
```bash
cd C:\Users\z1595\Desktop\yilianmeng-main
python -m venv venv
```

### 2.2 激活并安装依赖
```bash
.\venv\Scripts\activate
pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-CORS python-dotenv PyJWT pymysql
```

### 2.3 安装版本
| 依赖 | 版本 |
|------|------|
| Flask | 3.1.3 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Migrate | 4.1.0 |
| Flask-CORS | 6.0.5 |
| python-dotenv | 1.2.2 |
| PyJWT | 2.13.0 |
| pymysql | 1.2.0 |

---

## 3. 数据库模型设计

### 3.1 用户模型 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| phone | VARCHAR(20) | 手机号，唯一 |
| nickname | VARCHAR(50) | 昵称 |
| avatar | VARCHAR(255) | 头像URL |
| bio | VARCHAR(500) | 个人简介 |
| level | INT | 用户等级（默认1） |
| exp | INT | 当前经验值（默认0） |
| is_new_user | BOOLEAN | 是否新用户 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.2 创作者档案模型 (profiles)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户ID，外键 |
| identity_type | VARCHAR(20) | 身份类型：professional / amateur |
| skills | TEXT | 技能标签列表（JSON） |
| style_tags | TEXT | 创作风格标签列表（JSON） |
| work_history | TEXT | 工作资历描述 |
| education | TEXT | 教育/证书信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.3 作品模型 (works)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 发布者ID |
| title | VARCHAR(200) | 作品标题 |
| description | TEXT | 作品描述 |
| channel | VARCHAR(50) | 频道分类 |
| files | TEXT | 文件URL列表（JSON） |
| cover_url | VARCHAR(255) | 封面图URL |
| is_collaborative | BOOLEAN | 是否协作作品 |
| collaborators | TEXT | 协作成员ID列表（JSON） |
| view_count | INT | 浏览次数 |
| like_count | INT | 点赞次数 |
| created_at | DATETIME | 创建时间 |

### 3.4 项目模型 (projects)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 发起人ID |
| title | VARCHAR(200) | 项目标题 |
| description | TEXT | 项目描述 |
| required_skills | TEXT | 所需技能标签（JSON） |
| mode | VARCHAR(20) | 模式：paid / free |
| budget | INT | 预算金额 |
| deadline | DATETIME | 截止日期 |
| status | VARCHAR(20) | 状态：recruiting / in_progress / completed / cancelled |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.5 项目申请模型 (project_applications)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| project_id | INT | 项目ID |
| user_id | INT | 申请人ID |
| message | TEXT | 申请留言 |
| status | VARCHAR(20) | 状态：pending / approved / rejected |
| created_at | DATETIME | 创建时间 |

### 3.6 评分模型 (ratings)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| project_id | INT | 项目ID |
| from_user_id | INT | 评分人ID |
| to_user_id | INT | 被评分人ID |
| score | INT | 评分（1-5） |
| comment | TEXT | 评价内容 |
| created_at | DATETIME | 创建时间 |

### 3.7 消息模型 (messages)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| from_user_id | INT | 发送者ID（系统消息为0） |
| to_user_id | INT | 接收者ID |
| type | VARCHAR(20) | 类型：private / system / group |
| content | TEXT | 消息内容 |
| is_read | BOOLEAN | 是否已读 |
| related_id | INT | 关联ID |
| created_at | DATETIME | 创建时间 |

### 3.8 活动模型 (events)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| title | VARCHAR(200) | 活动标题 |
| description | TEXT | 活动描述 |
| cover_url | VARCHAR(255) | 封面图URL |
| deadline | DATETIME | 截止日期 |
| reward | INT | 奖励艺联币 |
| status | VARCHAR(20) | 状态：ongoing / ended |
| participant_count | INT | 参与人数 |
| created_at | DATETIME | 创建时间 |

### 3.9 活动参与者模型 (event_participants)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| event_id | INT | 活动ID |
| user_id | INT | 用户ID |
| work_id | INT | 作品ID |
| rank | INT | 排名 |
| score | INT | 得分 |
| created_at | DATETIME | 创建时间 |

### 3.10 钱包模型 (wallets)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户ID |
| balance | INT | 当前余额 |
| total_earned | INT | 总收入 |
| total_withdrawn | INT | 总提现 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.11 交易记录模型 (transactions)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户ID |
| type | VARCHAR(20) | 类型：earn / spend / withdraw |
| amount | INT | 金额 |
| description | VARCHAR(200) | 描述 |
| created_at | DATETIME | 创建时间 |

---

## 4. 迁移命令执行记录

### 4.1 初始化迁移
```bash
flask db init
```
**结果**：成功创建 `migrations/` 目录

### 4.2 生成迁移脚本
```bash
flask db migrate -m "init database"
```
**检测到的表**：
- events
- users
- messages
- profiles
- projects
- transactions
- wallets
- works
- event_participants
- project_applications
- ratings

### 4.3 执行迁移
```bash
flask db upgrade
```
**结果**：所有表创建成功

---

## 5. 验证结果

### 5.1 已创建的表
```
1. alembic_version      (迁移版本控制)
2. users                (用户表)
3. profiles             (创作者档案表)
4. works                (作品表)
5. projects             (项目表)
6. project_applications (项目申请表)
7. ratings              (评分表)
8. messages             (消息表)
9. events               (活动表)
10. event_participants  (活动参与者表)
11. wallets             (钱包表)
12. transactions        (交易记录表)
```

### 5.2 数据库信息
| 项目 | 信息 |
|------|------|
| 数据库名 | yilianmeng |
| 主机 | localhost |
| 端口 | 3306 |
| 字符集 | utf8mb4 |
| MySQL版本 | 8.0.46 |

---

## 6. 目录结构

```
yilianmeng-main/
├── app/
│   ├── __init__.py       # Flask应用初始化、数据库配置
│   ├── config.py         # 配置文件
│   ├── models/           # 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── work.py
│   │   ├── project.py
│   │   ├── rating.py
│   │   ├── message.py
│   │   ├── event.py
│   │   └── wallet.py
│   └── utils/
│       └── helpers.py    # 工具函数
├── migrations/           # 数据库迁移文件
│   ├── versions/
│   │   └── ed94894c6747_init_database.py
│   ├── alembic.ini
│   ├── env.py
│   └── README
├── venv/                 # 虚拟环境
├── work-logs/            # 工作日志
├── .env                  # 环境变量
└── .env.example          # 环境变量示例
```

---

## 总结

本阶段完成了数据库的搭建工作：

1. **MySQL连接验证**：确认服务运行正常，密码正确
2. **虚拟环境配置**：创建并激活虚拟环境，安装所有依赖
3. **模型设计**：创建了11个核心数据库模型，涵盖用户、作品、项目、评分、消息、活动、钱包等模块
4. **迁移执行**：通过 Flask-Migrate 成功创建了所有表结构
5. **验证通过**：确认12张表已成功创建

**下一步计划**：实现 API 路由接口（用户认证、创作者档案、作品发布、创作广场模块）
