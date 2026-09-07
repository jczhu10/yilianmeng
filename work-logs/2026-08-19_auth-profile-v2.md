# 认证 + 个人档案系统 V2 工作日志

**日期**：2026-08-19
**模块**：认证模块 + 个人档案系统
**版本**：V2（密码认证模式）
**状态**：✅ 完成并测试通过

---

## 一、本次改动背景

将认证模式从"手机号+验证码自动登录"改为"手机号+密码"标准认证体系，并重写个人档案系统接口以适配第一批数据库改造（V2 拆表结构）。

---

## 二、实现逻辑

### 2.1 认证模式变更

| 项 | 旧版 | V2 |
|----|------|-----|
| 登录方式 | 手机号+验证码 | 手机号+密码 |
| 注册 | 自动注册 | 手动注册（设密码） |
| 忘记密码 | 无 | 重置密码流程 |
| 验证码用途 | 登录凭证 | 注册校验 + 重置密码校验 |
| 密码存储 | 无 | users.password_hash（werkzeug 哈希） |

### 2.2 密码安全

- 密码规则：8-20 位含字母+数字（正则 `^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$`）
- 存储：werkzeug `generate_password_hash` 哈希，**绝不存明文**
- 校验：`check_password_hash`
- 登录失败统一提示"手机号或密码错误"（防撞库）
- 忘记密码 = 重置密码（不返回密码）

### 2.3 验证码场景区分

验证码存储结构升级为 `{phone: {code, expire, sent, scene}}`，`scene` 必填：
- `register`：注册场景，校验手机号未注册
- `reset`：重置密码场景，校验手机号已注册

### 2.4 档案系统 V2

注册时自动建空 profile（identity=艺术爱好者），用户进入个人主页无需触发创建。

经历类（工作/教育/能力证明）采用完整 CRUD：
- 新增：POST
- 编辑：PUT（部分更新，只传要改的字段）
- 删除：DELETE（级联删子项图片/文件）
- 列表：GET

文件上传采用混合方案：先调 `/profile/upload` 拿 URL，再随主记录提交 URL 数组。

---

## 三、项目结构变更

### 3.1 新增文件
- `docs/API_AUTH_PROFILE_V2_FINAL.md` — 接口清单文档（30个接口）
- `tests/test_auth_profile_v2.py` — V2 接口测试（39个测试点）
- `migrations/versions/60523706c09c_add_password_hash_to_users.py` — users 加 password_hash 迁移

### 3.2 修改文件
- `app/models/user.py` — 加 password_hash 字段 + set_password/check_password 方法 + to_dict 补 exp/updated_at
- `app/routes/auth.py` — 完全重写（7个接口：发码/注册/登录/重置密码/刷新/me/logout）
- `app/routes/profile.py` — 完全重写（23个接口：档案基础/技能/风格词汇/工作经历CRUD/教育经历CRUD/能力证明CRUD/文件上传）

### 3.3 数据库变更
- users 表新增 `password_hash` VARCHAR(255) 字段

---

## 四、接口清单（30个）

### 认证模块 `/api/v1/auth`（7个）
1. POST /auth/send-code — 发送验证码（scene=register/reset）
2. POST /auth/register — 注册（phone+code+password+nickname?）
3. POST /auth/login — 登录（phone+password）
4. POST /auth/reset-password — 重置密码（phone+code+new_password）
5. POST /auth/refresh — 刷新token
6. GET /auth/me — 获取当前用户
7. POST /auth/logout — 退出登录

### 档案基础 `/api/v1/profile`（3个）
8. GET /profile/me — 获取我的完整档案
9. PUT /profile/me — 更新档案基础信息（identity）
10. GET /profile/<user_id> — 查看他人档案

### 技能（4个）
11. PUT /profile/skills — 更新我的技能（上限5）
12. GET /profile/skills/mine — 我的技能
13. GET /profile/skills/categories — 技能分类字典
14. GET /profile/skills — 技能列表

### 风格词汇（3个）
15. GET /profile/style-tags — 风格词汇字典
16. PUT /profile/style-tags — 更新我的风格词汇（上限5）
17. GET /profile/style-tags/mine — 我的风格词汇

### 工作经历 CRUD（4个）
18-21. GET/POST/PUT/DELETE /profile/work-experiences

### 教育经历 CRUD（4个）
22-25. GET/POST/PUT/DELETE /profile/education-experiences

### 能力证明 CRUD（4个）
26-29. GET/POST/PUT/DELETE /profile/ability-proofs

### 文件上传（1个）
30. POST /profile/upload — 档案文件上传

---

## 五、错误码规划

### 认证模块
| code | 含义 |
|------|------|
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
| 2001 | 身份类型不合法 |
| 2002 | 技能ID无效 |
| 2004 | 技能数量超限（上限5） |
| 2005 | 风格词汇数量超限（上限5） |
| 2006 | 风格词汇ID无效 |
| 2010 | 资源不存在或无权操作 |
| 2011 | 学段类型不合法 |
| 2012 | 文件数量超限 |

---

## 六、测试结果

**39 个测试点全部通过，0 失败**

| 模块 | 测试点 | 结果 |
|------|--------|------|
| 认证（含异常场景） | 13 | ✅ |
| 档案基础 | 4 | ✅ |
| 技能 | 5 | ✅ |
| 风格词汇 | 4 | ✅ |
| 工作经历 CRUD | 4 | ✅ |
| 教育经历 CRUD | 4 | ✅ |
| 能力证明 CRUD | 4 | ✅ |
| 鉴权 | 1 | ✅ |

覆盖场景：
- 正常流程：注册→登录→重置密码→档案增删改查
- 异常场景：场景不合法、重复注册、密码格式错误、错误密码、非法身份、技能/风格超限、无token访问

---

## 七、注意事项

1. **旧测试文件失效**：`tests/test_auth.py` 和 `tests/test_profile.py` 使用旧的验证码登录模式，现已失效，建议用 `test_auth_profile_v2.py` 替代。
2. **旧用户无密码**：users 表中原有 5 个用户没有 password_hash，无法用密码登录。如需保留，需手动设密码或引导重置。
3. **验证码内存存储**：开发阶段验证码存内存，服务重启失效。生产环境需接短信服务。
4. **退出登录**：当前后端未做 token 黑名单，前端删 token 即可（token 7天后自动过期）。

---

## 八、前端对接提醒

1. **登录接口变了**：从 `{phone, code}` 改为 `{phone, password}`，前端登录页需改成密码输入框。
2. **新增注册页**：`POST /auth/register`，需手机号+验证码+密码+可选昵称。
3. **新增忘记密码页**：`POST /auth/reset-password`，需手机号+验证码+新密码。
4. **发验证码要带 scene**：`POST /auth/send-code` 必须传 `scene=register` 或 `scene=reset`。
5. **Token 存取**：登录/注册返回 token，前端存 localStorage，每次请求带 `Authorization: Bearer <token>`。
6. **个人主页数据**：`GET /profile/me` 一次返回档案+技能+风格词汇+工作经历+教育经历+能力证明全部数据。
7. **经历类操作**：工作/教育/能力证明都是独立 CRUD，前端对应增删改查界面。
8. **文件上传**：先调 `/profile/upload` 拿 URL，再随主记录提交。
