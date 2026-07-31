# -*- coding: utf-8 -*-
"""互动模块测试  用法: python tests/test_interactions.py
覆盖：点赞/取消点赞/点赞列表、评论/回复/删除评论/回复列表、权限与异常场景
"""
import requests
import sys

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
    print(f'[{status}] {name} | HTTP={http_code}(exp {expect_http}) code={body_code}(exp {expect_code}) | {body.get("message", "")}')
    return body


def login(phone):
    r = requests.post(f'{BASE_URL}/auth/send-code', json={'phone': phone}, headers=HEADERS)
    code = r.json()['data']['dev_code']
    r = requests.post(f'{BASE_URL}/auth/login', json={'phone': phone, 'code': code}, headers=HEADERS)
    return r.json()['data']['token']


def main():
    global passed, failed
    print('=' * 60)
    print('互动模块测试 (interactions)')
    print('=' * 60)

    # 登录用户A（作者）并创建已发布作品
    token_a = login('13800138000')
    auth_a = {**HEADERS, 'Authorization': f'Bearer {token_a}'}
    r = requests.post(f'{BASE_URL}/works/', json={
        'title': '互动测试作品', 'description': '用于互动测试', 'channel': 'writing', 'status': 'published'
    }, headers=auth_a)
    work_id = r.json()['data']['work_id']
    print(f'-- 准备: 用户A创建已发布作品 work_id={work_id}')

    # 登录用户B（互动者）
    token_b = login('13800138002')
    auth_b = {**HEADERS, 'Authorization': f'Bearer {token_b}'}

    # ===== 点赞 =====
    r = requests.post(f'{BASE_URL}/works/{work_id}/like', headers=auth_b)
    test('1. 点赞', r)

    r = requests.post(f'{BASE_URL}/works/{work_id}/like', headers=auth_b)
    test('1b. 重复点赞(4003)', r, expect_code=4003, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/{work_id}/likes', headers=auth_b)
    test('2. 点赞列表', r)

    r = requests.delete(f'{BASE_URL}/works/{work_id}/like', headers=auth_b)
    test('3. 取消点赞', r)

    r = requests.delete(f'{BASE_URL}/works/{work_id}/like', headers=auth_b)
    test('3b. 未点赞时取消(4004)', r, expect_code=4004, expect_http=400)

    # 重新点赞用于后续评论测试
    requests.post(f'{BASE_URL}/works/{work_id}/like', headers=auth_b)

    # ===== 评论 =====
    r = requests.post(f'{BASE_URL}/works/{work_id}/comments', json={'content': '很好的作品'}, headers=auth_b)
    body = test('4. 发表评论', r)
    comment_id = body.get('data', {}).get('comment_id')

    r = requests.post(f'{BASE_URL}/works/{work_id}/comments', json={'content': ''}, headers=auth_b)
    test('4b. 空评论(4006)', r, expect_code=4006, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/{work_id}/comments', headers=auth_b)
    test('5. 评论列表', r)

    # ===== 回复 =====
    r = requests.post(f'{BASE_URL}/works/{work_id}/comments', json={'content': '谢谢支持', 'parent_id': comment_id}, headers=auth_a)
    body = test('6. 发表回复', r)
    reply_id = body.get('data', {}).get('comment_id')

    # 二级回复超限：用户B对回复再回复（parent_id 指向回复），预期4007
    r = requests.post(f'{BASE_URL}/works/{work_id}/comments', json={'content': '回复的回复', 'parent_id': reply_id}, headers=auth_b)
    test('6b. 回复层级超限(4007)', r, expect_code=4007, expect_http=400)

    r = requests.get(f'{BASE_URL}/comments/{comment_id}/replies', headers=auth_b)
    test('7. 回复列表', r)

    # ===== 删除评论 =====
    # 用户B删自己的评论
    r = requests.delete(f'{BASE_URL}/comments/{comment_id}', headers=auth_b)
    test('8. 删除自己的评论', r)

    # 用户B删用户A的回复（无权），预期4002
    r = requests.delete(f'{BASE_URL}/comments/{reply_id}', headers=auth_b)
    test('8b. 删除他人评论(4002)', r, expect_code=4002, expect_http=403)

    # ===== 异常场景 =====
    r = requests.get(f'{BASE_URL}/works/{work_id}/comments')
    test('9. 未认证(401)', r, expect_code=401, expect_http=401)

    r = requests.post(f'{BASE_URL}/works/999999/like', headers=auth_b)
    test('9b. 作品不存在(4001)', r, expect_code=4001, expect_http=404)

    r = requests.delete(f'{BASE_URL}/comments/999999', headers=auth_b)
    test('9c. 评论不存在(404)', r, expect_code=4005, expect_http=404)

    print('=' * 60)
    print(f'互动模块完成: 通过 {passed} 项, 失败 {failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
