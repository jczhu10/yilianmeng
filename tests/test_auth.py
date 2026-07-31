# -*- coding: utf-8 -*-
"""认证模块测试  用法: python tests/test_auth.py"""
import requests, json, sys
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
    if ok:
        passed += 1
    else:
        failed += 1
    status = 'PASS' if ok else 'FAIL'
    print(f'[{status}] {name} | HTTP={http_code}(expect {expect_http}) code={body_code}(expect {expect_code}) | {body.get("message", "")}')
    return body

def main():
    global passed, failed
    print('=' * 60)
    print('认证模块测试 (auth)')
    print('=' * 60)

    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '13800138000'}, headers=HEADERS)
    body = test('1. 发送验证码', r)
    dev_code = body.get('data', {}).get('dev_code')
    if not dev_code:
        print('!!! 无法获取验证码，终止'); return

    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '13800138000'}, headers=HEADERS)
    test('1b. 重复发送(429)', r, expect_code=429, expect_http=429)

    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '123'}, headers=HEADERS)
    test('1c. 手机号格式错误(1001)', r, expect_code=1001, expect_http=400)

    r = requests.post(f'{BASE_URL}/auth/login', json={'phone': '13800138000', 'code': dev_code}, headers=HEADERS)
    body = test('2. 登录', r)
    token = body.get('data', {}).get('token')
    if not token:
        print('!!! 登录失败，终止'); return
    auth_headers = {**HEADERS, 'Authorization': f'Bearer {token}'}

    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': '13800138001'}, headers=HEADERS)
    r = requests.post(f'{BASE_URL}/auth/login', json={'phone': '13800138001', 'code': '000000'}, headers=HEADERS)
    test('2b. 验证码错误(1002)', r, expect_code=1002, expect_http=400)

    r = requests.get(f'{BASE_URL}/auth/me', headers=auth_headers)
    test('3. 获取用户信息', r)

    r = requests.post(f'{BASE_URL}/auth/refresh', headers=auth_headers)
    test('4. 刷新Token', r)

    r = requests.post(f'{BASE_URL}/auth/logout', headers=auth_headers)
    test('5. 登出', r)

    r = requests.get(f'{BASE_URL}/auth/me')
    test('6. 未认证访问(401)', r, expect_code=401, expect_http=401)

    bad_headers = {**HEADERS, 'Authorization': 'Bearer invalid.token.here'}
    r = requests.get(f'{BASE_URL}/auth/me', headers=bad_headers)
    test('7. 无效Token(401)', r, expect_code=401, expect_http=401)

    print('=' * 60)
    print(f'认证模块完成: 通过 {passed} 项, 失败 {failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
