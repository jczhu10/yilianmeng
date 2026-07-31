import requests
import json

BASE_URL = 'http://localhost:8080/api/v1'

def test(name, response):
    print(f'\n=== {name} ===')
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

# ============ 1. 发送验证码 ============
r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '13800000000'})
test('1. 发送验证码', r)
dev_code = r.json()['data']['dev_code']
print(f'\n>>> 获取到验证码: {dev_code}')

# ============ 2. 登录 ============
r = requests.post(f'{BASE_URL}/auth/login', json={'phone': '13800000000', 'code': dev_code})
test('2. 登录', r)
token = r.json()['data']['token']
print(f'\n>>> 获取到Token: {token[:30]}...')

# ============ 3. 获取用户信息 ============
r = requests.get(f'{BASE_URL}/auth/me', headers={'Authorization': f'Bearer {token}'})
test('3. 获取用户信息', r)

# ============ 4. 刷新Token ============
r = requests.post(f'{BASE_URL}/auth/refresh', headers={'Authorization': f'Bearer {token}'})
test('4. 刷新Token', r)
new_token = r.json()['data']['token']
print(f'\n>>> 新Token: {new_token[:30]}...')

# ============ 5. 登出 ============
r = requests.post(f'{BASE_URL}/auth/logout', headers={'Authorization': f'Bearer {token}'})
test('5. 登出', r)

# ============ 6. 测试未认证访问 ============
r = requests.get(f'{BASE_URL}/auth/me')
test('6. 未认证访问（预期401）', r)

# ============ 7. 测试错误码 ============
r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '12345'})
test('7. 手机号格式错误（预期1001）', r)

r = requests.post(f'{BASE_URL}/auth/login', json={'phone': '13800000000', 'code': '000000'})
test('8. 未发送验证码直接登录（预期1004）', r)

print('\n\n=== 所有测试完成 ===')