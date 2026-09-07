# 登录+个人系统数据库设计方案（V2）

> 本文档只梳理数据库思路，不修改代码。
> 生成时间：2026-08-04

## 一、总体变更概览

| # | 表名 | 动作 | 与现有表的关系 |
|---|------|------|----------------|
| 1 | users | ✅保留不变 | 原表不动 |
| 2 | profiles | 🔧大幅改造 | 原表**删除3个字段**，保留6个核心字段 |
| 3 | skill_categories | ⚠️待定（见不确定点2） | 原表是否保留取决于分类设计 |
| 4 | skills | 🔧改造 | 原表新增 creator_id 支持用户自定义 |
| 5 | profile_skills | ✅保留（微调） | 关联表基本不变，可能改外键指向 |
| 6 | work_experiences | 🆕新建 | 工作经历（多对一） |
| 7 | work_experience_images | 🆕新建 / 或内嵌字段 | 工作经历图片证明 |
| 8 | education_experiences | 🆕新建 | 教育经历（多对一） |
| 9 | ability_proofs | 🆕新建 | 其他能力证明（多对一） |
| 10 | ability_proof_files | 🆕新建 / 或内嵌字段 | 能力证明文件（最多10个） |

**从 profiles 删除的字段**：identity_type（改名重定义）、work_history（拆表）、education（拆表）

---

## 二、具体表设计

### 1. users（✅保留不变）

认证表，字段完全沿用现有设计，不做任何改动。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 用户ID |
| phone | VARCHAR(20) UNIQUE | 手机号（登录凭证） |
| nickname | VARCHAR(50) | 昵称 |
| avatar | VARCHAR(255) | 头像URL |
| bio | VARCHAR(500) | 个人简介 |
| level | INT | 等级 |
| exp | INT | 经验值 |
| is_new_user | BOOLEAN | 是否新用户 |
| created_at | DATETIME | 注册时间 |
| updated_at | DATETIME | 更新时间 |

---

### 2. profiles（🔧大幅改造 → 6字段）

**删除字段**：identity_type / work_history / education
**保留并重命名**：identity_type → identity（三选一，非原来的 amateur/professional）
**保留**：style_tags（但改为内置词汇选择模式）

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 档案ID |
| user_id | INT | FK→users.id, UNIQUE, NOT NULL | — | 对应用户（一对一） |
| style_tags | TEXT | | '[]' | 内置风格词汇选择，JSON数组，最多5个 |
| identity | VARCHAR(30) | NOT NULL | '艺术爱好者' | 三选一：学生 / 艺术爱好者 / 艺术相关工作者 |
| created_at | DATETIME | | utcnow | 创建时间 |
| updated_at | DATETIME | | onupdate utcnow | 更新时间 |

**style_tags 内置风格词汇表**（❓不确定点1：请提供具体词汇清单，下面是草稿占位）：
> 例如：写实风 / 国潮风 / 二次元 / 极简风 / 赛博朋克 / 水墨风 / 油画风 / 插画风 / 科幻风 / 复古风 / 治愈系 / 暗黑系 / 萌系 / 森系 / 蒸汽波……
> ❓需要你明确具体有哪些词汇，以及后续是否支持后台增删改

**identity 枚举值**（固定3个，不可自定义）：
```
学生
艺术爱好者
艺术相关工作者
```

---

### 3. skills（🔧改造：支持平台预置 + 用户自定义）

原 `skills` 表只存平台预置技能，现在加 creator_id 区分来源。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 技能ID |
| name | VARCHAR(50) | NOT NULL | — | 技能名称 |
| category_id | INT | FK→skill_categories.id | NULL | 所属分类（平台预置必填，用户自定义是否必填见不确定点2） |
| creator_id | INT | FK→users.id | 0 | 创建者：0=平台预置，非0=用户自定义的用户ID |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |

**新增索引**：`(creator_id, name)` — 防止同一用户重复创建相同名字的自定义技能

**关于 skill_categories（技能分类表）去留**：
> ❓**不确定点2**：用户自定义的技能是否需要分类？
> - **方案A**：分类机制仅对平台预置生效；用户自定义技能不分类（category_id=NULL）
>   - 优点：简单，用户不用选分类
>   - 缺点：自定义技能无法按分类筛选展示
> - **方案B**：用户自定义技能必须选分类，复用平台预置的4大分类（文字/视觉/影像/配音）
>   - 优点：分类统一，筛选方便
>   - 缺点：用户要多做一步选择；自定义技能可能跨分类
> - **方案C**：用户不仅能自定义技能，还能自定义分类（skill_categories 加 creator_id）
>   - 优点：最灵活
>   - 缺点：分类泛滥，筛选体验差
>
> ❓**不确定点3**：用户自定义的技能，其他用户是否可见并能选用？
> - **方案A（私有）**：仅创建者自己能用
>   - 优点：避免乱造词汇，质量可控
>   - 缺点：用户之间技能名称不统一，按技能匹配协作时效果打折
> - **方案B（公开）**：所有人都能用
>   - 优点：技能池自动丰富
>   - 缺点：可能出现大量重复/低质量/奇葩技能；需要审核机制
> - **方案C（混合·推荐）**：平台预置公开可见；用户自定义默认私有，可选"提交公开审核"
>   - 优点：兼顾质量和丰富度
>   - 缺点：需要审核流程（可先不做审核，先提交就公开）

---

### 4. profile_skills（✅保留，小幅微调）

档案-技能关联表（多对多）。表结构几乎不变，仅说明字段含义。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| profile_id | INT | FK→profiles.id, NOT NULL | 档案ID |
| skill_id | INT | FK→skills.id, NOT NULL | 技能ID |
| created_at | DATETIME | | utcnow |

**联合唯一索引**：`(profile_id, skill_id)` — 同一档案不能重复选同一技能

> ❓**不确定点4**：用户最多可选多少个技能？
> - 原 profile 模块限制最多5个，是否沿用此限制？
> - 或者放宽到 8 个 / 10 个 / 无限制？

---

### 5. work_experiences（🆕新建：工作经历表）

多对一：一个用户有多条工作经历。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 工作经历ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户（多对一） |
| company_name | VARCHAR(100) | NOT NULL | — | 公司名称（必填） |
| position | VARCHAR(80) | NOT NULL | — | 职位名称（必填） |
| start_date | DATE | NOT NULL | — | 入职时间（必填） |
| end_date | DATE | | NULL | 离职时间（空=至今） |
| is_current | BOOLEAN | | FALSE | 是否当前在职 |
| description | TEXT | | '' | 工作描述（选填） |
| sort_order | INT | | 0 | 排序（按时间倒序展示） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**关于图片证明的存储方案（二选一）**：

> ❓**不确定点5**：工作经历的图片证明怎么存？
> - **方案A（独立表·推荐）**：新建 work_experience_images 子表
>   - 优点：灵活，支持任意数量图片；查询经历列表时可按需懒加载
>   - 缺点：多一次 JOIN
> - **方案B（内嵌JSON）**：在 work_experiences 表加一个 images 字段（TEXT，存 JSON 数组）
>   - 优点：一次查出，不用 JOIN
>   - 缺点：反范式；图片多时字段体积大；无法对单张图片管理
>
> 推荐方案A。若选择方案A，子表结构如下：

**方案A：work_experience_images（🆕新建）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| work_experience_id | INT | FK→work_experiences.id, NOT NULL | 所属工作经历 |
| image_url | VARCHAR(255) | NOT NULL | 图片地址 |
| sort_order | INT | 默认 0 | 排序 |
| created_at | DATETIME | | utcnow |

> ❓**不确定点6**：工作经历的图片证明是否有数量上限？（如最多3张/5张/不限）

---

### 6. education_experiences（🆕新建：教育经历表）

多对一：一个用户有多条教育经历（小学/中学/大学各一条或多条）。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 教育经历ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户（多对一） |
| school_level | VARCHAR(20) | NOT NULL | — | 学段分类：小学 / 中学 / 大学 |
| school_name | VARCHAR(100) | NOT NULL | — | 学校名称（所有阶段必填） |
| start_year | YEAR | NOT NULL | — | 入学年份（如 2020） |
| end_year | YEAR | | NULL | 毕业年份（空=在读） |
| degree | VARCHAR(20) | | NULL | 学历层级：本科 / 硕士 / 博士（仅大学填） |
| major | VARCHAR(80) | | NULL | 专业名称（仅大学填） |
| sort_order | INT | | 0 | 排序（按时间倒序展示） |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

**字段条件生效规则**：
- school_level = "小学" 或 "中学"：degree 和 major 应为 NULL
- school_level = "大学"：degree 和 major 建议必填（至少 degree 必填）

> ❓**不确定点7**：中学是否要细分初中/高中？还是统一"中学"？
> - 方案A：统一中学（简单）
> - 方案B：小学 / 初中 / 高中 / 大学 / 硕士 / 博士 细分（但你给的字段有 degree 区分学历，硕士和博士其实是大学阶段后的学历层级，和 school_level 的"大学"重叠）

> ❓**不确定点8**：教育经历有没有数量上限？（理论上最多 小学1 + 中学1 + 本科1 + 硕士1 + 博士1 = 5条足够）

> ❓**不确定点9**：教育经历要不要图片证明（毕业证/学位证）？你没提，所以默认不加。如果要加，类似工作经历的图片子表或内嵌字段。

---

### 7. ability_proofs（🆕新建：其他能力证明表）

多对一：一个用户有多条能力证明。

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | INT | PK, AUTO_INCREMENT | — | 能力证明ID |
| user_id | INT | FK→users.id, NOT NULL | — | 对应用户（多对一） |
| title | VARCHAR(200) | NOT NULL | — | 内容简介/标题（纯文字，你说"内容简介，纯文字"） |
| description | TEXT | | '' | 详细描述（选填，补充说明用；如果你只想要一个简介字段，可删） |
| sort_order | INT | | 0 | 排序 |
| created_at | DATETIME | | utcnow | — |
| updated_at | DATETIME | | onupdate utcnow | — |

> ❓**不确定点10**：你说的"内容简介"是只要一个文本字段就够？还是要 title + description？（我倾向加个 description 给用户补充详情空间）

---

### 8. ability_proof_files（🆕新建：能力证明文件表）

每条能力证明关联最多 10 个文件。

**关于文件存储（二选一）**：和工作经历图片相同的选择题。

> ❓**不确定点11**：能力证明的文件怎么存？
> - **方案A（独立表·推荐）**：新建 ability_proof_files 子表（如下）
> - **方案B（内嵌JSON）**：ability_proofs 加 files 字段（TEXT，JSON数组，最多10个）

**方案A：ability_proof_files（🆕新建）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK | — |
| ability_proof_id | INT | FK→ability_proofs.id, NOT NULL | 所属能力证明 |
| file_url | VARCHAR(255) | NOT NULL | 文件地址 |
| file_name | VARCHAR(200) | | '' | 文件名（证书名等，便于展示） |
| file_type | VARCHAR(20) | | 'image' | image / pdf / doc 等 |
| sort_order | INT | 默认 0 | 排序 |
| created_at | DATETIME | | utcnow |

**数量限制**：每条 ability_proof 关联的 files 数量 **最多 10 个**（你明确说了）。这个限制在应用层通过 COUNT 校验实现。

---

## 三、表关系图（V2）

```
users ──1:1── profiles
  │           │
  │           └──1:N── profile_skills ──N:1── skills ──N:1── skill_categories（待定）
  │                                                │
  │                                                └── creator_id → users（自定义技能的创建者）
  │
  ├──1:N── work_experiences ──1:N── work_experience_images（方案A时存在）
  │
  ├──1:N── education_experiences
  │
  └──1:N── ability_proofs ──1:N── ability_proof_files（方案A时存在）
```

---

## 四、不确定点汇总（请逐条回复）

| # | 不确定点 | 选项/建议 |
|---|----------|-----------|
| 1 | **style_tags 具体的内置风格词汇清单**是什么？ | （请你列出来） |
| 2 | 用户自定义技能是否需要分类？skill_categories 怎么处理？ | A=不分类 / B=复用平台4分类 / C=用户也能自定义分类 |
| 3 | 用户自定义技能其他用户是否可见可用？ | A=私有 / B=公开 / C=混合（建议C） |
| 4 | 用户可选技能数量上限？ | 原限制5个，或改8/10/无限制 |
| 5 | 工作经历图片证明用独立子表还是内嵌JSON？ | 建议A（独立表） |
| 6 | 工作经历图片数量上限？ | 建议3张或5张 |
| 7 | 教育经历 school_level 是否细分初中/高中？ | A=中学统一 / B=细分 |
| 8 | 教育经历数量上限？ | 建议5条（小+中+本+硕+博） |
| 9 | 教育经历是否需要图片（证书）？ | 默认不加，需要请说明 |
| 10 | 能力证明的"内容简介"只要一个文本还是 title+description？ | 建议加 description 字段 |
| 11 | 能力证明文件用独立子表还是内嵌JSON？ | 建议A（独立表） |

---

## 五、数据迁移影响提示（开发时需注意）

如果现有 profiles 表里已经有数据，开发时需要：
1. 把现有 identity_type（amateur/professional）**映射**到新 identity 三选一
   - 建议映射规则：amateur→艺术爱好者，professional→艺术相关工作者（或给用户二次确认）
2. 现有 style_tags 如果包含非内置词汇，需要**清洗或提示用户重新选**
3. 原 work_history（TEXT 大字段）和 education（TEXT）的内容**无法自动迁移**到新表（因为自由文本→结构化字段），只能作为旧数据保留或让用户重新填写
