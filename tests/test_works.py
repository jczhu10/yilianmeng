# -*- coding: utf-8 -*-
"""作品模块测试  用法: python tests/test_works.py"""
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
    print('作品模块测试 (works)')
    print('=' * 60)
    token = login()
    auth = {**HEADERS, 'Authorization': f'Bearer {token}'}

    r = requests.post(f'{BASE_URL}/works/', json={'title': '测试草稿作品', 'description': '描述', 'channel': 'writing', 'skill_tags': [1, 2], 'status': 'draft'}, headers=auth)
    body = test('1. 创建草稿', r)
    work_id = body.get('data', {}).get('work_id')
    if not work_id:
        print('!!! 创建失败，终止'); return

    r = requests.put(f'{BASE_URL}/works/{work_id}', json={'title': '修改后标题'}, headers=auth)
    test('2. 编辑作品', r)

    r = requests.post(f'{BASE_URL}/works/{work_id}/publish', headers=auth)
    test('3. 发布作品', r)

    r = requests.post(f'{BASE_URL}/works/{work_id}/publish', headers=auth)
    test('3b. 重复发布(已发布)', r)

    r = requests.get(f'{BASE_URL}/works/{work_id}', headers=auth)
    test('4. 获取详情', r)

    r = requests.get(f'{BASE_URL}/works/mine', headers=auth)
    test('5. 我的作品列表', r)

    r = requests.get(f'{BASE_URL}/works/mine?status=published', headers=auth)
    test('5b. 按状态筛选', r)

    r = requests.delete(f'{BASE_URL}/works/{work_id}', headers=auth)
    test('6. 删除作品', r)

    r = requests.delete(f'{BASE_URL}/works/{work_id}', headers=auth)
    test('6b. 重复删除(3003)', r, expect_code=3003, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/{work_id}', headers=auth)
    test('6c. 访问已删除(3001)', r, expect_code=3001, expect_http=404)

    r = requests.post(f'{BASE_URL}/works/', json={'title': 'test', 'channel': 'music'}, headers=auth)
    test('7. 无效渠道(3004)', r, expect_code=3004, expect_http=400)

    r = requests.post(f'{BASE_URL}/works/', json={'title': '', 'channel': 'writing'}, headers=auth)
    test('7b. 空标题(400)', r, expect_code=400, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/mine')
    test('8. 未认证(401)', r, expect_code=401, expect_http=401)

    print('=' * 60)
    print(f'作品模块完成: 通过 {passed} 项, 失败 {failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
