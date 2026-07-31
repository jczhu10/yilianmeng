# 创作者档案模块开发日志

**日期**: 2026-07-31
**模块**: 创作者档案（Profile）
**状态**: 已完成开发与接口测试

---

## 一、实现的具体功能

### 1. 数据库新增（3 张表）
- `skill_categories`：技能分类表（文字创作 / 视觉创作 / 影像类 / 配音）
- `skills`：技能项表（每个分类下的具体技能，共 21 个）
- `profile_skills`：用户档案-技能关联表（多对多，不存熟练度）

### 2. 数据库变更
- `profiles` 表移除 `skills` JSON 字段（原用于存储技能数组）
- 改为通过 `profile_skills` 关联表管理技能，支持按技能筛选用户

### 3. 技能初始化数据（4 分类 / 21 技能）
| 分类 | code | 子技能 |
|------|------|--------|
| 文字创作 | writing | 小说创作、剧本创作、文案策划、诗词散文、新闻稿 |
| 视觉创作 | visual | 平面设计、插画、UI设计、漫画、摄影、原画 |
| 影像类 | video | 视频剪辑、视频拍摄、动画制作、后期特效、调色 |
| 配音 | voice | 中文配音、英文配音、日语配音、方言配音、唱歌配音 |

### 4. 接口（7 个，前缀 `/api/v1/profile`）
| # | 方法 | 路径 | 功能 | 鉴权 |
|---|------|------|------|------|
| 1 | GET | `/me` | 获取我的档案（含技能列表） | 是 |
| 2 | PUT | `/me` | 更新档案基础信息（身份类型/风格标签/工作经历/教育背景） | 是 |
| 3 | PUT | `/skills` | 覆盖式更新我的技能（传 skill_ids 数组） | 是 |
| 4 | GET | `/skills/mine` | 获取我的技能列表 | 是 |
| 5 | GET | `/skills/categories` | 获取所有技能分类（含子技能，用于前端选择器） | 否 |
| 6 | GET | `/skills` | 获取所有技能（扁平列表，可按 category_id 筛选） | 否 |
| 7 | GET | `/<user_id>` | 查看他人档案（含技能） | 是 |

### 5. 业务约束
- 身份类型：仅允许 `amateur`（业余）/ `professional`（专业）
- 风格标签：最多 10 个
- 技能选择：最多 20 个，自动去重
- 技能更新：覆盖式（传入新列表完全替换旧列表）

---

## 二、实现方式

### 1. 模型设计（关联表代替 JSON）
```python
# app/models/skill.py
class SkillCategory(db.Model):    # 技能分类
    id, name, code, sort_order, created_at
    skills = relationship('Skill', backref='category', cascade='all, delete-orphan')

class Skill(db.Model):            # 技能项
    id, category_id, name, sort_order, created_at

class ProfileSkill(db.Model):     # 档案-技能关联（多对多）
    id, profile_id, skill_id, created_at
    __table_args__ = (UniqueConstraint('profile_id', 'skill_id'),)  # 防重复
```

### 2. Profile 模型调整
- 移除 `skills = db.Column(db.Text, default='[]')` 字段
- 移除 `set_skills()` 方法
- 新增 `profile_skills` 关系：`db.relationship('ProfileSkill', backref='profile', cascade='all, delete-orphan')`
- `to_dict(with_skills=False)` 支持按需加载技能

### 3. 覆盖式技能更新逻辑
```python
# 先删除旧关联，再批量插入新关联
ProfileSkill.query.filter_by(profile_id=profile.id).delete()
for skill_id in skill_ids:
    db.session.add(ProfileSkill(profile_id=profile.id, skill_id=skill_id))
```
优点：实现简单，无需 diff 计算；保证最终状态与传入列表一致。

### 4. 业务错误码体系（延续 auth 模块风格）
| 错误码 | 含义 | HTTP |
|--------|------|------|
| 400 | 参数错误 | 400 |
| 401 | 未认证 | 401 |
| 404 | 资源不存在 | 404 |
| 2001 | 身份类型不合法 | 400 |
| 2002 | 无效的技能ID | 404 |
| 2004 | 超过技能上限 | 400 |
> 采用「HTTP 状态码 + Body 业务码」分离方案，与 auth 模块一致。

### 5. 数据库迁移
- 迁移文件：`migrations/versions/d64710a5542f_add_skill_tables_and_remove_profile_.py`
- 命令：`flask db migrate` + `flask db upgrade`
- 检测到：新增 3 张表、删除 profiles.skills 列、更新列注释

### 6. 技能数据初始化
- 脚本：`seed_skills.py`（幂等执行，重复运行会跳过）
- 命令：`python seed_skills.py`

---

## 三、与前端的对接

### 1. 鉴权
所有标记「是」的接口需要在请求头携带：
```
Authorization: Bearer <token>
```
token 通过 `/api/v1/auth/login` 获取。

### 2. 典型对接流程
```
1. 进入档案编辑页
   → GET /api/v1/profile/me              （回显当前档案+技能）
   → GET /api/v1/profile/skills/categories （渲染技能多级选择器）

2. 保存基础信息
   → PUT /api/v1/profile/me
   body: { identity_type, style_tags[], work_history, education }

3. 保存技能
   → PUT /api/v1/profile/skills
   body: { skill_ids: [1, 6, 12, ...] }

4. 查看他人主页
   → GET /api/v1/profile/<user_id>
```

### 3. 响应格式（统一）
```json
// 成功
{ "code": 200, "message": "success", "data": {...} }

// 失败
{ "code": 2001, "message": "身份类型不合法", "data": null }
```

### 4. 关键数据结构
**档案对象**（GET/PUT /me 返回）
```json
{
  "id": 1, "user_id": 4,
  "identity_type": "professional",
  "style_tags": ["古风", "治愈"],
  "work_history": "...",
  "education": "...",
  "skills": [ {"id":1,"category_id":1,"name":"小说创作"}, ... ],
  "created_at": "...", "updated_at": "..."
}
```

**技能分类树**（GET /skills/categories 返回，用于选择器）
```json
{
  "categories": [
    { "id":1, "name":"文字创作", "code":"writing", "sort_order":0,
      "skills": [ {"id":1,"name":"小说创作"}, ... ] }
  ]
}
```

---

## 四、项目结构变化

```
yilianmeng-main/
├── app/
│   ├── models/
│   │   ├── skill.py          【新增】SkillCategory / Skill / ProfileSkill
│   │   ├── profile.py        【修改】移除 skills JSON 字段，改用关联表
│   │   └── __init__.py       【修改】导出新模型
│   ├── routes/
│   │   └── profile.py        【新增】7 个档案/技能接口
│   └── __init__.py           【修改】注册 profile 蓝图
├── migrations/versions/
│   └── d64710a5542f_...py    【新增】迁移文件
├── seed_skills.py            【新增】技能数据初始化脚本
└── work-logs/
    └── 2026-07-31_profile-module.md  【本文件】
```

---

## 五、接口测试结果

### 正常流程（11 项，全部通过）
| # | 测试 | 结果 |
|---|------|------|
| 1 | 发送验证码 | code=200 |
| 2 | 登录（新用户自动注册） | code=200, is_new_user=True |
| 3 | GET /me（首次，默认档案） | identity=amateur, skills=0 |
| 4 | PUT /me（更新档案） | identity=professional |
| 5 | GET /skills/categories | 4 分类，21 技能 |
| 6 | GET /skills | total=21 |
| 6b | GET /skills?category_id=1 | count=5（筛选正常） |
| 7 | PUT /skills（选3个跨分类） | selected=3 |
| 8 | GET /skills/mine | count=3 |
| 9 | GET /me（含技能） | skills_count=3 |
| 10 | GET /profile/4（他人档案） | skills=3 |
| 11 | 覆盖式更新（3→2） | count=2（覆盖正常） |

### 异常流程（6 项，全部通过）
| # | 场景 | HTTP | body.code | message |
|---|------|------|-----------|---------|
| 12 | 未认证访问 | 401 | 401 | 未登录或Token过期 |
| 13 | 无效token | 401 | 401 | 未登录或Token过期 |
| 14 | 无效skill_id | 404 | 2002 | 存在无效的技能ID |
| 15 | 无效身份类型 | 400 | 2001 | 身份类型不合法 |
| 16 | 不存在用户档案 | 404 | 404 | 该用户尚未创建档案 |
| 17 | 超过技能上限 | 400 | 2004 | 最多选择 20 个技能 |

---

## 六、前端提醒

1. **技能选择器数据源**：用 `GET /skills/categories` 一次性拉取分类树（含子技能），无需多次请求。
2. **技能保存是覆盖式**：每次 `PUT /skills` 传入完整 skill_ids 数组，后端会用新列表完全替换旧列表。前端不需要做增量 diff。
3. **身份类型枚举**：只接受 `amateur` / `professional` 两个值，其他值会返回业务码 2001。
4. **技能上限**：单用户最多 20 个技能，前端选择器建议做前端校验提前拦截，后端也会兜底返回 2004。
5. **档案懒创建**：用户首次访问 `GET /me` 时若没有档案会自动创建默认档案，前端无需先调创建接口。
6. **查看他人档案**：`GET /<user_id>` 需要登录，若对方尚未创建档案返回 404（业务码 404）。
7. **风格标签**：以字符串数组形式存储，最多 10 个，前端可做自由输入或预设标签选择。
