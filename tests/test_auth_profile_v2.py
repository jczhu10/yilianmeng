"""V2 接口测试：认证 + 个人档案系统（30个接口核心流程）"""
import sys, json, time
sys.path.insert(0, r'C:\Users\z1595\Desktop\yilianmeng-main')

from app import app, db
from app.models import User, Profile

client = app.test_client()
PASS = 0
FAIL = 0

def check(name, resp, expect_code=200):
    global PASS, FAIL
    data = resp.get_json() or {}
    if expect_code == 200:
        ok = resp.status_code == 200 and data.get('code') == 200
    else:
        ok = data.get('code') == expect_code
    if ok:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} | http={resp.status_code} code={data.get("code")} msg={data.get("message")}')
    return data

def header(token):
    return {'Authorization': f'Bearer {token}'} if token else {}

# 唯一手机号
PHONE = f'138{int(time.time()) % 100000000:08d}'
PASSWORD = 'test1234'

print(f'\n========== 测试手机号: {PHONE} ==========\n')

# ===== 认证模块 =====
print('--- 认证模块 ---')

# 1. 发送验证码（注册场景）
r = client.post('/api/v1/auth/send-code', json={'phone': PHONE, 'scene': 'register'})
d = check('1. 发送验证码(注册)', r)
code = d.get('data', {}).get('dev_code', '')

# 1b. 场景参数不合法
r = client.post('/api/v1/auth/send-code', json={'phone': PHONE, 'scene': 'xxx'})
check('1b. 场景不合法(应失败)', r, 1008)

# 2. 注册
r = client.post('/api/v1/auth/register', json={'phone': PHONE, 'code': code, 'password': PASSWORD, 'nickname': '测试用户'})
d = check('2. 注册', r)
token = d.get('data', {}).get('token', '')
user_id = d.get('data', {}).get('user', {}).get('user_id')

# 2b. 重复注册
r = client.post('/api/v1/auth/send-code', json={'phone': PHONE, 'scene': 'register'})
check('2b. 已注册手机号发码(应失败)', r, 1005)

# 2c. 密码格式错误
r = client.post('/api/v1/auth/register', json={'phone': f'139{int(time.time())%100000000:08d}', 'code': '000000', 'password': '123'})
check('2c. 密码格式错误(应失败)', r, 1007)

# 3. 登录
r = client.post('/api/v1/auth/login', json={'phone': PHONE, 'password': PASSWORD})
d = check('3. 登录', r)
token = d.get('data', {}).get('token', '')

# 3b. 错误密码
r = client.post('/api/v1/auth/login', json={'phone': PHONE, 'password': 'wrong000'})
check('3b. 错误密码(应失败)', r, 1006)

# 4. 重置密码
r = client.post('/api/v1/auth/send-code', json={'phone': PHONE, 'scene': 'reset'})
d = check('4. 发送验证码(重置)', r)
reset_code = d.get('data', {}).get('dev_code', '')
NEW_PASSWORD = 'newpass99'
r = client.post('/api/v1/auth/reset-password', json={'phone': PHONE, 'code': reset_code, 'new_password': NEW_PASSWORD})
check('4b. 重置密码', r)

# 4c. 用新密码登录
r = client.post('/api/v1/auth/login', json={'phone': PHONE, 'password': NEW_PASSWORD})
d = check('4c. 新密码登录', r)
token = d.get('data', {}).get('token', '')

# 5. 刷新token
r = client.post('/api/v1/auth/refresh', headers=header(token))
check('5. 刷新token', r)

# 6. 获取当前用户
r = client.get('/api/v1/auth/me', headers=header(token))
check('6. 获取当前用户', r)

# 7. 退出
r = client.post('/api/v1/auth/logout', headers=header(token))
check('7. 退出登录', r)


# ===== 档案基础 =====
print('\n--- 档案基础 ---')

# 8. 获取我的完整档案
r = client.get('/api/v1/profile/me', headers=header(token))
d = check('8. 获取我的档案', r)

# 9. 更新身份
r = client.put('/api/v1/profile/me', json={'identity': '学生'}, headers=header(token))
check('9. 更新身份', r)

# 9b. 非法身份
r = client.put('/api/v1/profile/me', json={'identity': '程序员'}, headers=header(token))
check('9b. 非法身份(应失败)', r, 2001)

# 10. 看他人档案（用自己user_id测试）
r = client.get(f'/api/v1/profile/{user_id}', headers=header(token))
check('10. 查看档案', r)


# ===== 技能 =====
print('\n--- 技能 ---')

# 11. 更新技能
r = client.put('/api/v1/profile/skills', json={'skill_ids': [1, 2]}, headers=header(token))
check('11. 更新技能', r)

# 11b. 超过5个
r = client.put('/api/v1/profile/skills', json={'skill_ids': [1,2,3,4,5,6]}, headers=header(token))
check('11b. 技能超限(应失败)', r, 2004)

# 12. 我的技能
r = client.get('/api/v1/profile/skills/mine', headers=header(token))
check('12. 我的技能', r)

# 13. 技能分类字典
r = client.get('/api/v1/profile/skills/categories')
check('13. 技能分类字典', r)

# 14. 技能列表
r = client.get('/api/v1/profile/skills')
check('14. 技能列表', r)


# ===== 风格词汇 =====
print('\n--- 风格词汇 ---')

# 15. 风格词汇字典
r = client.get('/api/v1/profile/style-tags')
check('15. 风格词汇字典', r)

# 16. 更新风格词汇
r = client.put('/api/v1/profile/style-tags', json={'style_tag_ids': [1, 2]}, headers=header(token))
check('16. 更新风格词汇', r)

# 16b. 超过5个
r = client.put('/api/v1/profile/style-tags', json={'style_tag_ids': [1,2,3,4,5,6]}, headers=header(token))
check('16b. 风格词汇超限(应失败)', r, 2005)

# 17. 我的风格词汇
r = client.get('/api/v1/profile/style-tags/mine', headers=header(token))
check('17. 我的风格词汇', r)


# ===== 工作经历 =====
print('\n--- 工作经历 ---')

# 19. 新增
r = client.post('/api/v1/profile/work-experiences', json={
    'company_name': '测试公司', 'position': '设计师', 'start_date': '2020-01-01',
    'end_date': '2022-01-01', 'description': '做UI',
    'images': [{'image_url': 'http://x.com/1.jpg', 'caption': '作品'}]
}, headers=header(token))
d = check('19. 新增工作经历', r)
work_id = d.get('data', {}).get('id')

# 18. 列表
r = client.get('/api/v1/profile/work-experiences', headers=header(token))
check('18. 工作经历列表', r)

# 20. 编辑（部分更新）
r = client.put(f'/api/v1/profile/work-experiences/{work_id}', json={'position': '高级设计师'}, headers=header(token))
check('20. 编辑工作经历', r)

# 21. 删除
r = client.delete(f'/api/v1/profile/work-experiences/{work_id}', headers=header(token))
check('21. 删除工作经历', r)


# ===== 教育经历 =====
print('\n--- 教育经历 ---')

# 23. 新增
r = client.post('/api/v1/profile/education-experiences', json={
    'school_level': '大学', 'school_name': '测试大学', 'start_year': 2018, 'end_year': 2022,
    'degree': '本科', 'major': '视觉传达'
}, headers=header(token))
d = check('23. 新增教育经历', r)
edu_id = d.get('data', {}).get('id')

# 22. 列表
r = client.get('/api/v1/profile/education-experiences', headers=header(token))
check('22. 教育经历列表', r)

# 24. 编辑
r = client.put(f'/api/v1/profile/education-experiences/{edu_id}', json={'major': '工业设计'}, headers=header(token))
check('24. 编辑教育经历', r)

# 25. 删除
r = client.delete(f'/api/v1/profile/education-experiences/{edu_id}', headers=header(token))
check('25. 删除教育经历', r)


# ===== 能力证明 =====
print('\n--- 能力证明 ---')

# 27. 新增
r = client.post('/api/v1/profile/ability-proofs', json={
    'title': 'Adobe认证', 'description': '2021年获得',
    'files': [{'file_url': 'http://x.com/cert.pdf', 'file_name': '证书.pdf', 'file_type': 'pdf'}]
}, headers=header(token))
d = check('27. 新增能力证明', r)
proof_id = d.get('data', {}).get('id')

# 26. 列表
r = client.get('/api/v1/profile/ability-proofs', headers=header(token))
check('26. 能力证明列表', r)

# 28. 编辑
r = client.put(f'/api/v1/profile/ability-proofs/{proof_id}', json={'title': 'Adobe认证设计师'}, headers=header(token))
check('28. 编辑能力证明', r)

# 29. 删除
r = client.delete(f'/api/v1/profile/ability-proofs/{proof_id}', headers=header(token))
check('29. 删除能力证明', r)


# ===== 无token访问应失败 =====
print('\n--- 鉴权 ---')
r = client.get('/api/v1/profile/me')
check('无token访问(应401)', r, 401)


# ===== 清理测试数据 =====
print('\n--- 清理 ---')
with app.app_context():
    u = User.query.filter_by(phone=PHONE).first()
    if u:
        # 先删 profile 及其关联，再删 user
        p = Profile.query.filter_by(user_id=u.id).first()
        if p:
            db.session.delete(p)
            db.session.commit()
        db.session.delete(u)
        db.session.commit()
        print(f'  [OK] 已清理测试用户 {PHONE}')

print(f'\n========== 测试结果: {PASS} 通过 / {FAIL} 失败 ==========')
