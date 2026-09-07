# 登录 + 个人档案系统 接口清单 V2（最终定稿）

> 决策：认证模式改为"手机号+密码"；忘记密码=重置密码；密码哈希存 users；教育/能力证明分开；经历类做完整CRUD；经历编辑用部分更新；文件先上传拿URL再随主记录提交。
> 生成时间：2026-08-19
> 共 30 个接口

---

## 通用约定

- Base URL：`http://localhost:5000`
- 所有接口前缀：`/api/v1`
- 统一响应：`{"code": 200, "message": "...", "data": {...}}`（code=200 成功）
- 登录鉴权：需登录的接口请求头带 `Authorization: Bearer <token>`
- token 有效期 7 天，过期前调 `/auth/refresh` 刷新

---

## 一、认证模块 `/api/v1/auth`（7 个）

### 1. POST /auth/send-code — 发送验证码
- 登录：否
- 请求：`{"phone":"13800138000", "scene":"register"}`  // scene: register/reset，必填
- 限流：同手机号 60 秒 1 次，验证码 5 分钟有效
- 返回：`{"code":200, "message":"验证码已发送", "data":{"dev_code":"123456"}}`（生产不返回 dev_code）

### 2. POST /auth/register — 注册
- 登录：否
- 请求：`{"phone":"...", "code":"123456", "password":"abc12345", "nickname":"可选"}`
- 密码规则：8-20 位含字母+数字
- 逻辑：校验验证码 → 检查手机号未注册 → 密码哈希存 users.password_hash → 自动建空 profile(identity=艺术爱好者) → 发 token
- 返回：`{"code":200, "data":{"token":"...", "user":{...}, "is_new_user":true}}`

### 3. POST /auth/login — 登录
- 登录：否
- 请求：`{"phone":"...", "password":"..."}`
- 逻辑：查 users → 校验密码哈希 → 发 token
- 错误：手机号或密码错误（统一提示，防撞库）
- 返回：`{"code":200, "data":{"token":"...", "user":{...}, "is_new_user":false}}`

### 4. POST /auth/reset-password — 重置密码
- 登录：否
- 请求：`{"phone":"...", "code":"123456", "new_password":"新密码"}`
- 逻辑：校验验证码(scene=reset) → 更新 password_hash
- 返回：`{"code":200, "message":"密码重置成功"}`

### 5. POST /auth/refresh — 刷新 token
- 登录：是
- 请求：无
- 返回：`{"code":200, "data":{"token":"新token"}}`

### 6. GET /auth/me — 获取当前用户信息
- 登录：是
- 返回：`{"code":200, "data":{users全字段}}`

### 7. POST /auth/logout — 退出登录
- 登录：是
- 逻辑：后端记录日志，前端删 token
- 返回：`{"code":200, "message":"已退出登录"}`

---

## 二、档案基础 `/api/v1/profile`（3 个）

### 8. GET /profile/me — 获取我的完整档案
- 登录：是
- 逻辑：无档案自动创建(identity=艺术爱好者)，返回含所有关联数据
- 返回：`{"code":200, "data":{profile基础 + style_tags + skills + work_experiences + education_experiences + ability_proofs}}`

### 9. PUT /profile/me — 更新档案基础信息
- 登录：是
- 请求：`{"identity":"学生"}`  // 可选：学生/艺术爱好者/艺术相关工作者
- 返回：同接口 8（不含关联数据，仅基础）

### 10. GET /profile/<user_id> — 查看他人档案
- 登录：是
- 返回：他人完整档案（含关联数据）；他人无档案 404

---

## 三、技能 `/api/v1/profile`（4 个）

### 11. PUT /profile/skills — 更新我的技能
- 登录：是
- 请求：`{"skill_ids":[1,2,5]}`  // 上限5，覆盖式
- 返回：`{"code":200, "data":{"skills":[...]}}`

### 12. GET /profile/skills/mine — 我的技能
- 登录：是
- 返回：`{"code":200, "data":{"skills":[...]}}`

### 13. GET /profile/skills/categories — 技能分类字典
- 登录：否
- 返回：4 分类 + 各分类下技能项

### 14. GET /profile/skills — 技能扁平列表
- 登录：否
- Query：`category_id` 可选
- 返回：`{"code":200, "data":{"skills":[...]}}`

---

## 四、风格词汇 `/api/v1/profile`（3 个）

### 15. GET /profile/style-tags — 风格词汇字典
- 登录：否
- 返回：20 个预置风格词

### 16. PUT /profile/style-tags — 更新我的风格词汇
- 登录：是
- 请求：`{"style_tag_ids":[1,2,5]}`  // 上限5，覆盖式
- 返回：`{"code":200, "data":{"style_tags":[...]}}`

### 17. GET /profile/style-tags/mine — 我的风格词汇
- 登录：是
- 返回：`{"code":200, "data":{"style_tags":[...]}}`

---

## 五、工作经历 `/api/v1/profile`（4 个）

### 18. GET /profile/work-experiences — 我的工作经历列表
- 登录：是
- 返回：`{"code":200, "data":{"work_experiences":[{...含images}]}}`

### 19. POST /profile/work-experiences — 新增工作经历
- 登录：是
- 请求：
```json
{
  "company_name": "A公司",
  "position": "设计师",
  "start_date": "2020-01-01",
  "end_date": "2022-01-01",
  "is_current": false,
  "description": "负责UI设计",
  "sort_order": 0,
  "images": [{"image_url":"https://...", "caption":"作品集"}]
}
```
- images 上限 5 张
- 返回：新建的完整记录

### 20. PUT /profile/work-experiences/<id> — 编辑工作经历（部分更新）
- 登录：是
- 请求：只传要改的字段；images 传则整体覆盖该经历的图片
- 校验：仅作者可改
- 返回：更新后的完整记录

### 21. DELETE /profile/work-experiences/<id> — 删除工作经历
- 登录：是
- 校验：仅作者可删（级联删图片）
- 返回：`{"code":200, "message":"删除成功"}`

---

## 六、教育经历 `/api/v1/profile`（4 个）

### 22. GET /profile/education-experiences — 列表
- 登录：是
- 返回：`{"code":200, "data":{"education_experiences":[...]}}`

### 23. POST /profile/education-experiences — 新增
- 登录：是
- 请求：
```json
{
  "school_level": "大学",
  "school_name": "中央美院",
  "start_year": 2018,
  "end_year": 2022,
  "degree": "本科",
  "major": "视觉传达",
  "sort_order": 0
}
```
- school_level：小学/中学/大学；degree/major 仅大学填

### 24. PUT /profile/education-experiences/<id> — 编辑（部分更新）
- 登录：是，仅作者

### 25. DELETE /profile/education-experiences/<id> — 删除
- 登录：是，仅作者

---

## 七、能力证明 `/api/v1/profile`（4 个）

### 26. GET /profile/ability-proofs — 列表
- 登录：是
- 返回：`{"code":200, "data":{"ability_proofs":[{...含files}]}}`

### 27. POST /profile/ability-proofs — 新增
- 登录：是
- 请求：
```json
{
  "title": "Adobe认证设计师",
  "description": "2021年获得",
  "sort_order": 0,
  "files": [{"file_url":"https://...", "file_name":"证书.pdf", "file_type":"pdf"}]
}
```
- files 上限 10 个；file_type：image/pdf/doc/video

### 28. PUT /profile/ability-proofs/<id> — 编辑（部分更新）
- 登录：是，仅作者；files 传则整体覆盖

### 29. DELETE /profile/ability-proofs/<id> — 删除
- 登录：是，仅作者（级联删文件）

---

## 八、文件上传 `/api/v1/profile`（1 个）

### 30. POST /profile/upload — 档案文件上传
- 登录：是
- 请求：multipart/form-data，字段 `file`
- 存储：uploads/profile 目录
- 返回：`{"code":200, "data":{"url":"https://...", "file_name":"xxx.pdf", "file_type":"pdf"}}`

---

## 错误码规划

### 认证模块
| code | 含义 |
|------|------|
| 400 | 参数错误 |
| 401 | 未登录或token过期 |
| 429 | 验证码发送过于频繁 |
| 1001 | 手机号格式不正确 |
| 1002 | 验证码错误 |
| 1003 | 验证码已过期 |
| 1004 | 请先发送验证码 |
| 1005 | 手机号已注册 |
| 1006 | 手机号或密码错误 |
| 1007 | 密码格式不正确（8-20位含字母+数字） |
| 1008 | 场景参数不合法 |

### 档案模块
| code | 含义 |
|------|------|
| 400 | 参数错误 |
| 404 | 档案/资源不存在 |
| 2001 | 身份类型不合法 |
| 2002 | 技能ID无效 |
| 2004 | 技能数量超限（上限5） |
| 2005 | 风格词汇数量超限（上限5） |
| 2006 | 风格词汇ID无效 |
| 2010 | 资源不存在或无权操作 |
| 2011 | 学段类型不合法 |
| 2012 | 文件数量超限 |

---

## 数据库改动

### users 表新增字段
- `password_hash` VARCHAR(255) — 密码哈希（werkzeug 生成）
- `nickname` 注册时可选传入

### profiles 表
- 注册时自动建空记录（identity=艺术爱好者）

---

## 接口总数

| 模块 | 接口数 |
|------|--------|
| 认证 | 7 |
| 档案基础 | 3 |
| 技能 | 4 |
| 风格词汇 | 3 |
| 工作经历 | 4 |
| 教育经历 | 4 |
| 能力证明 | 4 |
| 文件上传 | 1 |
| **合计** | **30** |
