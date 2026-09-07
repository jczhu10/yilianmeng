# 登录+个人系统数据库设计（确认版 V2.1）

> 变更记录：2026-08-06 方案C确认，style_tags 改为字典表+关联表模式
> 生成时间：2026-08-06

---

## 一、决策确认（不变的部分）

| # | 不确定点 | 决策结果 |
|---|----------|----------|
| 2 | 自定义技能是否需要分类 | **方案B**：复用 4 大分类（文字/视觉/影像/配音） |
| 3 | 自定义技能是否公开 | **方案B**：公开，所有用户可见可用 |
| 4 | 技能数量上限 | 保留 5 个，不改 |
| 5 | 工作经历图片存储 | 独立子表 work_experience_images |
| 6 | 工作经历图片数量上限 | 最多 5 张 |
| 7 | 教育学段是否细分 | 不细分：小学 / 中学 / 大学 |
| 8 | 教育经历数量上限 | 最多 10 条 |
| 9 | 教育经历是否加证书图片 | 默认不加 |
| 10 | 能力证明字段 | text 介绍 + 文件子表存地址 |
| 11 | 能力证明文件存储 | 独立子表 ability_proof_files |

**新增确认项**：
| # | 项 | 结果 |
|---|----|------|
| 12 | style_tags 存储方案 | **方案C**：字典表 style_tags + 关联表 profile_style_tags（和技能设计完全一致） |

---

## 二、表总览（12 张表，新增 2 张：style_tags + profile_style_tags）

| # | 表名 | 动作 | 关联关系 |
|---|------|------|----------|
| 1 | users | ✅保留不变 | — |
| 2 | profiles | 🔧改造（5字段，**删除 style_tags**） | 1:1 → users |
| 3 | **style_tags** | 🆕新建 | 风格字典表，预置20条 |
| 4 | **profile_style_tags** | 🆕新建 | N:M 关联 profiles↔style_tags（上限5） |
| 5 | skill_categories | ✅保留（4条预置） | 1:N → skills |
| 6 | skills | 🔧改造（加 creator_id） | N:1 → skill_categories；N:1 → users(creator) |
| 7 | profile_skills | ✅保留 | N:M 关联 profiles↔skills（上限5） |
| 8 | work_experiences | 🆕新建 | N:1 → users |
| 9 | work_experience_images | 🆕新建 | N:1 → work_experiences（上限5） |
| 10 | education_experiences | 🆕新建 | N:1 → users（上限10） |
| 11 | ability_proofs | 🆕新建 | N:1 → users |
| 12 | ability_proof_files | 🆕新建 | N:1 → ability_proofs（上限10） |

---

## 三、各表详细字段

### 1. users（✅保留不变）

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

### 2. profiles（🔧改造 → 5 字段，**删除 style_tags JSON字段**）

原表删除字段：identity_type / work_history / education / **style_tags**（style_tags 改走关联表）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 档案ID |
| user_id | INT | FK→users.id, UNIQUE, NOT NULL | — | 对应用户（一对一） |
| identity | VARCHAR(30) | NOT NULL | '艺术爱好者' | 三选一：学生 / 艺术爱好者 / 艺术相关工作者 |
| created_at | DATETIME | | utcnow | 创建时间 |
| updated_at | DATETIME | | onupdate utcnow | 更新时间 |

#### identity 枚举（固定 3 个）
- 学生
- 艺术爱好者
- 艺术相关工作者

---

### 3. style_tags（🆕新建：风格词汇字典表，预置 20 条）

和 skill_categories（技能分类字典）同一层级概念。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 风格词ID |
| name | VARCHAR(30) | UNIQUE, NOT NULL | — | 风格词汇名称（唯一） |
| description | VARCHAR(200) | | '' | 词汇描述/释义 |
| sort_order | INT | | 0 | 排序，越小越前 |
| is_active | BOOLEAN | | TRUE | 是否启用（FALSE=后台临时下架） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**预置 20 条数据（初始化脚本 seed_style_tags.py 插入）**：

| id | name | description | sort_order |
|----|------|-------------|------------|
| 1 | 写实风 | 真实还原事物样貌 | 1 |
| 2 | 国潮风 | 中国传统文化+潮流元素 | 2 |
| 3 | 二次元 | 日系动漫/漫画风格 | 3 |
| 4 | 极简风 | 简洁干净，留白为主 | 4 |
| 5 | 赛博朋克 | 霓虹科技感、未来主义 | 5 |
| 6 | 水墨风 | 中国传统水墨画风格 | 6 |
| 7 | 油画风 | 西方油画质感、厚重笔触 | 7 |
| 8 | 插画风 | 手绘插画、扁平卡通 | 8 |
| 9 | 科幻风 | 太空、机甲、未来科技 | 9 |
| 10 | 复古风 | 年代感、怀旧色调 | 10 |
| 11 | 治愈系 | 温暖柔和、心灵治愈 | 11 |
| 12 | 暗黑系 | 冷色调、哥特、神秘 | 12 |
| 13 | 萌系 | Q版、可爱、低龄向 | 13 |
| 14 | 森系 | 自然清新、植物元素 | 14 |
| 15 | 蒸汽波 | 复古未来、粉紫霓虹 | 15 |
| 16 | 扁平风 | 几何色块、无渐变阴影 | 16 |
| 17 | 3D立体 | 三维建模渲染风格 | 17 |
| 18 | 像素风 | 8-bit 复古像素画 | 18 |
| 19 | 哥特风 | 华丽黑暗、宗教建筑元素 | 19 |
| 20 | 低多边形 | Low Poly 几何多边形 | 20 |

---

### 4. profile_style_tags（🆕新建：档案-风格关联表 N:M）

和 profile_skills（技能关联表）设计完全一致。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | — |
| profile_id | INT | FK→profiles.id, NOT NULL | 档案ID |
| style_tag_id | INT | FK→style_tags.id, NOT NULL | 风格词ID |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(profile_id, style_tag_id)` → 同一档案不能重复选同一风格

**业务约束（应用层）**：单 profile_id 关联 style_tag_id 数量 ≤ 5（最多选 5 个风格词汇）

---

### 5. skill_categories（✅保留，4 条预置不变）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 分类ID |
| name | VARCHAR(50) | UNIQUE, NOT NULL | — | 分类名 |
| code | VARCHAR(20) | UNIQUE, NOT NULL | — | 分类编码 |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |

**预置 4 条**：
- id=1：文字创作 / writing
- id=2：视觉创作 / visual
- id=3：影像类 / video
- id=4：配音 / voice

---

### 6. skills（🔧改造：加 creator_id 支持自定义）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 技能ID |
| name | VARCHAR(50) | NOT NULL | — | 技能名称 |
| category_id | INT | FK→skill_categories.id, NOT NULL | — | 所属分类（4选1，自定义技能也必填） |
| creator_id | INT | FK→users.id | 0 | 创建者：0=平台预置，非0=用户ID（公开可用） |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |

**索引**：
- `(creator_id, name)` 联合索引 — 防同用户创建同名技能
- `(category_id)` — 按分类筛选

---

### 7. profile_skills（✅保留不变）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| profile_id | INT | FK→profiles.id, NOT NULL | 档案ID |
| skill_id | INT | FK→skills.id, NOT NULL | 技能ID |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(profile_id, skill_id)`
**业务约束**：单 profile 关联 skill 数 ≤ 5

---

### 8. work_experiences（🆕新建：工作经历）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 工作经历ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户 |
| company_name | VARCHAR(100) | NOT NULL | — | 公司名称（必填） |
| position | VARCHAR(80) | NOT NULL | — | 职位名称（必填） |
| start_date | DATE | NOT NULL | — | 入职时间（必填） |
| end_date | DATE | | NULL | 离职时间（空=至今） |
| is_current | BOOLEAN | | FALSE | 是否当前在职 |
| description | TEXT | | '' | 工作描述（选填） |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

---

### 9. work_experience_images（🆕新建：工作经历图片证明）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 图片ID |
| work_experience_id | INT | FK→work_experiences.id, NOT NULL | — | 所属工作经历 |
| image_url | VARCHAR(255) | NOT NULL | — | 图片地址 |
| caption | VARCHAR(200) | | '' | 图片说明（选填） |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |

**业务约束**：单 work_experience_id 关联图片 ≤ 5 张

---

### 10. education_experiences（🆕新建：教育经历）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 教育经历ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户 |
| school_level | VARCHAR(20) | NOT NULL | — | 学段：小学 / 中学 / 大学（不细分） |
| school_name | VARCHAR(100) | NOT NULL | — | 学校名称 |
| start_year | YEAR | NOT NULL | — | 入学年份，如 2020 |
| end_year | YEAR | | NULL | 毕业年份（空=在读） |
| degree | VARCHAR(20) | | NULL | 学历层级：本科 / 硕士 / 博士（仅大学填） |
| major | VARCHAR(80) | | NULL | 专业名称（仅大学填） |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**业务约束**：
- 单 user_id 教育经历 ≤ 10 条
- school_level=小学/中学 时 degree/major 应为 NULL
- school_level=大学 时 degree 建议必填，值 ∈ {本科, 硕士, 博士}

---

### 11. ability_proofs（🆕新建：能力证明）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 能力证明ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户 |
| title | VARCHAR(200) | NOT NULL | — | 标题（简明介绍这项证明是什么） |
| description | TEXT | | '' | text 详细介绍 |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

---

### 12. ability_proof_files（🆕新建：能力证明文件）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 文件ID |
| ability_proof_id | INT | FK→ability_proofs.id, NOT NULL | — | 所属能力证明 |
| file_url | VARCHAR(255) | NOT NULL | — | 文件地址 |
| file_name | VARCHAR(200) | | '' | 文件名/证书名 |
| file_type | VARCHAR(20) | | 'image' | image / pdf / doc / video 等 |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |

**业务约束**：单 ability_proof_id 关联文件 ≤ 10 个

---

## 四、表关系图（更新版）

```
                 ┌──────────────┐               ┌────────────────────┐
                 │  style_tags   │               │  skill_categories   │
                 │(20条预置字典) │               │ (4条预置分类)       │
                 └──┬───────────┘               └─────────┬───────────┘
                    │ 1:N                                    │ 1:N
                    ▼                                        ▼
users ──1:1── profiles              profile_style_tags       skills (加 creator_id→users)
  │           │                    (上限5个/档案)            0=平台 / 非0=用户(公开)
  │           └──1:N── profile_skills ──N:1──►
  │                  (上限5个/档案)
  │
  ├──1:N── work_experiences ──1:N── work_experience_images（上限5张/经历）
  │
  ├──1:N── education_experiences（上限10条/人）
  │
  └──1:N── ability_proofs ──1:N── ability_proof_files（上限10个/证明）
```

> 观察：**风格**和**技能**是两套完全对称的设计：
> - style_tags ↔ skills（字典表，支持自定义与否不同）
> - profile_style_tags ↔ profile_skills（关联表，5个上限）

---

## 五、索引汇总（新增 2 表索引）

| 表 | 索引 | 类型 | 目的 |
|----|------|------|------|
| users | phone | UNIQUE | 登录 |
| profiles | user_id | UNIQUE | 一对一 |
| **style_tags** | name | UNIQUE | 风格词不重复 |
| **profile_style_tags** | (profile_id, style_tag_id) | UNIQUE | 防重复选风格 |
| skills | (creator_id, name) | 普通 | 防同用户同名技能 |
| skills | category_id | 普通 | 按分类筛选 |
| profile_skills | (profile_id, skill_id) | UNIQUE | 防重复选技能 |
| work_experiences | user_id | 普通 | 查用户工作经历 |
| work_experience_images | work_experience_id | 普通 | 查经历图片 |
| education_experiences | user_id | 普通 | 查用户教育经历 |
| ability_proofs | user_id | 普通 | 查用户能力证明 |
| ability_proof_files | ability_proof_id | 普通 | 查证明文件 |

---

## 六、业务约束汇总

| 规则 | 限制值 |
|------|--------|
| profile_style_tags 数 / profile | ≤ 5 |
| profiles.identity | 学生 / 艺术爱好者 / 艺术相关工作者 |
| profile_skills 数 / profile | ≤ 5 |
| work_experience_images / 经历 | ≤ 5 张 |
| education_experiences 数 / user | ≤ 10 条 |
| education.degree | 本科 / 硕士 / 博士（仅大学） |
| ability_proof_files / 证明 | ≤ 10 个 |
| skills.category_id 必填 | 4 分类之一 |
| skills.name + creator_id 唯一 | 同用户不能创建同名技能 |
| style_tags.name 全局唯一 | 风格词不重复 |

---

## 七、数据迁移提示（开发阶段）

| 迁移项 | 策略 |
|--------|------|
| profiles **删除** style_tags 列 | 旧 style_tags JSON 数据：如非空，映射到 style_tags.id → 插入 profile_style_tags 关联表；不在20词白名单内的提示用户重选 |
| profiles **删除** identity_type 列 | 新增 identity 列：amateur→艺术爱好者，professional→艺术相关工作者（或二次确认） |
| profiles **删除** work_history 列 | 数据丢弃或备份列，用户手动补录 |
| profiles **删除** education 列 | 同上 |
| style_tags 表初始化 | seed_style_tags.py 脚本插入 20 条预置数据（类似 seed_skills.py） |
| profile_style_tags 新建表 | （空表，由用户后续录入或迁移时自动映射） |
| skills 新增 creator_id 列 | 现有 21 条预置技能 creator_id=0 |

---

## 八、对应接口规划（开发参考，约 27 个接口）

### 风格词汇（新增 2 个接口）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/style-tags | 获取全部风格词汇列表（字典，返回id+name+desc） |
| GET | /profile/style-tags/mine | 我选的风格词汇（关联表查，上限5个） |
| PUT | /profile/style-tags | 更新我的风格词汇（传数组 style_tag_ids，校验≤5，替换关联表） |

### 档案基础

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/me | 我的档案基础（identity） |
| PUT | /profile/me | 更新 identity（三选一） |

### 技能标签

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/skills/mine | 我的技能（≤5） |
| PUT | /profile/skills | 更新我的技能 |
| GET | /profile/skills | 技能列表（平台+用户自定义，可按分类筛选） |
| POST | /profile/skills/create | 用户创建自定义技能（公开，4分类必填） |

### 工作经历（5+2=7）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/me/work | 工作经历列表 |
| POST | /profile/me/work | 新增 |
| PUT | /profile/me/work/<id> | 编辑 |
| DELETE | /profile/me/work/<id> | 删除（级联删图片） |
| POST | /profile/me/work/<id>/images | 上传图片（≤5张校验） |
| DELETE | /profile/me/work/images/<id> | 删除单张图 |

### 教育经历（4）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/me/education | 教育经历列表（≤10） |
| POST | /profile/me/education | 新增 |
| PUT | /profile/me/education/<id> | 编辑 |
| DELETE | /profile/me/education/<id> | 删除 |

### 能力证明（4+2=6）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/me/proofs | 能力证明列表 |
| POST | /profile/me/proofs | 新增 |
| PUT | /profile/me/proofs/<id> | 编辑 |
| DELETE | /profile/me/proofs/<id> | 删除（级联删文件） |
| POST | /profile/me/proofs/<id>/files | 上传文件（≤10个校验） |
| DELETE | /profile/me/proofs/files/<id> | 删除单个文件 |

### 查他人档案（1）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /profile/<user_id> | 他人档案全量（基础+风格+技能+工作+教育+能力证明） |

合计约 **3 + 2 + 4 + 7 + 4 + 6 + 1 = 27 个接口**。