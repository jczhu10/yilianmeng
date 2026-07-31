# -*- coding: utf-8 -*-
"""档案模块测试  用法: python tests/test_profile.py"""
import requests, sys
BASE_URL = 'http://localhost:8080/api/v1'
HEADERS = {'Content-Type': 'application/json'}
passed = 0
failed = 0

def test(name, response, expect_code=200, expect_http=200):
    global passed, failed
    http_code = response.status_code
    try:
        body = response.json()
    except Exception:
        body = {}
    body_code = body.get('code')
    ok = (http_code == expect_http) and (body_code == expect_code)
    if ok: passed += 1
    else: failed += 1
    status = 'PASS' if ok else 'FAIL'
    print(f'[{status}] {name} | HTTP={http_code}(exp {expect_http}) code={body_code}(exp {expect_code}) | {body.get("message", "")}')
    return body

def login():
    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '13800138000'}, headers=HEADERS)
    code = r.json()['data']['dev_code']
    r = requests.post(f'{BASE_URL}/auth/login', json={'phone': '13800138000', 'code': code}, headers=HEADERS)
    return r.json()['data']['token']

def main():
    global passed, failed
    print('=' * 60)
    print('档案模块测试 (profile)')
    print('=' * 60)
    token = login()
    auth = {**HEADERS, 'Authorization': f'Bearer {token}'}

    r = requests.get(f'{BASE_URL}/profile/me', headers=auth)
    test('1. 获取我的档案', r)

    r = requests.put(f'{BASE_URL}/profile/me', json={'identity_type': 'professional', 'style_tags': ['搞笑','治愈'], 'work_history': '测试工作经历', 'education': '测试大学'}, headers=auth)
    test('2. 更新档案', r)

    r = requests.put(f'{BASE_URL}/profile/me', json={'identity_type': 'invalid_type'}, headers=auth)
    test('2b. 无效身份类型(2001)', r, expect_code=2001, expect_http=400)

    r = requests.get(f'{BASE_URL}/profile/skills/categories')
    body = test('3. 获取技能分类', r)
    cat_id = 1
    if body.get('data', {}).get('categories'):
        cat_id = body['data']['categories'][0]['id']

    r = requests.get(f'{BASE_URL}/profile/skills?category_id={cat_id}')
    test('4. 按分类获取技能', r)

    r = requests.put(f'{BASE_URL}/profile/skills', json={'skill_ids': [1, 2, 5]}, headers=auth)
    test('5. 更新技能', r)

    r = requests.put(f'{BASE_URL}/profile/skills', json={'skill_ids': [99999]}, headers=auth)
    test('5b. 无效技能ID(2002)', r, expect_code=2002, expect_http=404)

    r = requests.get(f'{BASE_URL}/profile/skills/mine', headers=auth)
    test('6. 获取我的技能', r)

    r = requests.get(f'{BASE_URL}/auth/me', headers=auth)
    my_uid = r.json()['data']['user_id']
    r = requests.get(f'{BASE_URL}/profile/{my_uid}', headers=auth)
    test('7. 查看档案(by user_id)', r)

    r = requests.get(f'{BASE_URL}/profile/99999', headers=auth)
    test('7b. 不存在的用户(404)', r, expect_code=404, expect_http=404)

    r = requests.get(f'{BASE_URL}/profile/me')
    test('8. 未认证(401)', r, expect_code=401, expect_http=401)

    print('=' * 60)
    print(f'档案模块完成: 通过 {passed} 项, 失败 {failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
