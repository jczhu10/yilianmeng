# -*- coding: utf-8 -*-
"""协作项目模块测试"""
import requests
import sys

BASE_URL = 'http://127.0.0.1:8080'
HEADERS = {'Content-Type': 'application/json'}

passed = 0
failed = 0


def login(phone):
    # 先发送验证码，开发环境返回 dev_code
    r = requests.post(f'{BASE_URL}/api/v1/auth/send-code', json={'phone': phone}, headers=HEADERS)
    code = r.json().get('data', {}).get('dev_code', '123456')
    r = requests.post(f'{BASE_URL}/api/v1/auth/login', json={'phone': phone, 'code': code}, headers=HEADERS)
    return r.json()['data']['token']


def test(name, r, expect_code=200, expect_http=200):
    global passed, failed
    http_ok = (r.status_code == expect_http)
    try:
        body = r.json()
    except Exception:
        body = {}
    code_ok = (body.get('code') == expect_code)
    if http_ok and code_ok:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        print(f'  [FAIL] {name}  expect http={expect_http} code={expect_code}, got http={r.status_code} code={body.get("code")} msg={body.get("message")}')
    return body


def main():
    token_a = login('13800138000')
    auth_a = {**HEADERS, 'Authorization': f'Bearer {token_a}'}
    token_b = login('13800138002')
    auth_b = {**HEADERS, 'Authorization': f'Bearer {token_b}'}

    print('=== 协作项目模块测试 ===')

    # 1. 发起项目
    r = requests.post(f'{BASE_URL}/api/v1/projects/', json={
        'title': '测试协作项目',
        'description': '用于测试',
        'required_skills': [1, 2],
        'mode': 'free'
    }, headers=auth_a)
    body = test('1. 发起项目', r)
    project_id = body.get('data', {}).get('project_id')

    # 1b. 无效技能ID
    r = requests.post(f'{BASE_URL}/api/v1/projects/', json={'title': '无效技能', 'required_skills': [9999]}, headers=auth_a)
    test('1b. 无效技能ID(400)', r, expect_code=400, expect_http=400)

    # 1c. 标题为空
    r = requests.post(f'{BASE_URL}/api/v1/projects/', json={'title': ''}, headers=auth_a)
    test('1c. 标题为空(400)', r, expect_code=400, expect_http=400)

    # 2. 项目列表
    r = requests.get(f'{BASE_URL}/api/v1/projects/', headers=auth_a)
    body = test('2. 项目列表', r)
    assert body['data']['total'] >= 1

    # 2b. 按状态筛选
    r = requests.get(f'{BASE_URL}/api/v1/projects/?status=recruiting', headers=auth_a)
    test('2b. 按状态筛选', r)

    # 2c. 无效状态
    r = requests.get(f'{BASE_URL}/api/v1/projects/?status=invalid', headers=auth_a)
    test('2c. 无效状态(400)', r, expect_code=400, expect_http=400)

    # 3. 项目详情(发起人)
    r = requests.get(f'{BASE_URL}/api/v1/projects/{project_id}', headers=auth_a)
    body = test('3. 项目详情(发起人)', r)
    assert body['data']['is_creator'] is True
    assert body['data']['applications'] is not None

    # 4. 编辑项目
    r = requests.put(f'{BASE_URL}/api/v1/projects/{project_id}', json={'title': '编辑后的项目'}, headers=auth_a)
    body = test('4. 编辑项目', r)
    assert body['data']['title'] == '编辑后的项目'

    # 5. 用户B申请加入
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/apply', json={'message': '我想加入'}, headers=auth_b)
    body = test('5. 申请加入', r)
    app_id = body.get('data', {}).get('id')

    # 5b. 重复申请
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/apply', json={'message': '再次申请'}, headers=auth_b)
    test('5b. 重复申请(5005)', r, expect_code=5005, expect_http=400)

    # 5c. 申请自己项目
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/apply', json={'message': '自己加入'}, headers=auth_a)
    test('5c. 申请自己项目(5004)', r, expect_code=5004, expect_http=400)

    # 5d. 项目详情(申请人)
    r = requests.get(f'{BASE_URL}/api/v1/projects/{project_id}', headers=auth_b)
    body = test('5d. 项目详情(申请人)', r)
    assert body['data']['my_application'] is not None

    # 6. 通过申请
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/applications/{app_id}/approve', headers=auth_a)
    body = test('6. 通过申请', r)
    assert body['data']['status'] == 'approved'

    # 6b. 验证转ongoing
    r = requests.get(f'{BASE_URL}/api/v1/projects/{project_id}', headers=auth_a)
    body = test('6b. 验证转ongoing', r)
    assert body['data']['status'] == 'ongoing', f"状态应为 ongoing，实际 {body['data']['status']}"

    # 7. 申请已处理(5007) - 用独立项目验证：先拒绝一个申请，再尝试对它 approve
    r = requests.post(f'{BASE_URL}/api/v1/projects/', json={'title': '5007测试项目', 'mode': 'free'}, headers=auth_a)
    p2_id = r.json()['data']['project_id']
    r = requests.post(f'{BASE_URL}/api/v1/projects/{p2_id}/apply', json={'message': 'test'}, headers=auth_b)
    app2_id = r.json()['data']['id']
    # 先拒绝
    requests.post(f'{BASE_URL}/api/v1/projects/{p2_id}/applications/{app2_id}/reject', headers=auth_a)
    # 再尝试 approve -> 应返回 5007（项目仍在 recruiting，但申请已 rejected）
    r = requests.post(f'{BASE_URL}/api/v1/projects/{p2_id}/applications/{app2_id}/approve', headers=auth_a)
    test('7. 申请已处理(5007)', r, expect_code=5007, expect_http=400)

    # 7b. 非发起人审批
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/applications/{app_id}/approve', headers=auth_b)
    test('7b. 非发起人审批(5002)', r, expect_code=5002, expect_http=403)

    # 8. 编辑ongoing项目
    r = requests.put(f'{BASE_URL}/api/v1/projects/{project_id}', json={'title': '尝试改'}, headers=auth_a)
    test('8. 编辑ongoing项目(5003)', r, expect_code=5003, expect_http=400)

    # 9. 我发起的项目
    r = requests.get(f'{BASE_URL}/api/v1/projects/mine?role=created', headers=auth_a)
    body = test('9. 我发起的项目', r)
    assert body['data']['total'] >= 1

    # 9b. 我参与的项目
    r = requests.get(f'{BASE_URL}/api/v1/projects/mine?role=joined', headers=auth_b)
    body = test('9b. 我参与的项目', r)
    assert body['data']['total'] >= 1

    # 10. 关闭项目
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/close', headers=auth_a)
    test('10. 关闭项目', r)

    # 10b. 验证已关闭
    r = requests.get(f'{BASE_URL}/api/v1/projects/{project_id}', headers=auth_a)
    body = test('10b. 验证已关闭', r)
    assert body['data']['status'] == 'closed'

    # 10c. 非发起人关闭
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/close', headers=auth_b)
    test('10c. 非发起人关闭(5002)', r, expect_code=5002, expect_http=403)

    # 11. 关闭后申请
    r = requests.post(f'{BASE_URL}/api/v1/projects/{project_id}/apply', headers=auth_b)
    test('11. 关闭后申请(5003)', r, expect_code=5003, expect_http=400)

    # 12. 项目不存在
    r = requests.get(f'{BASE_URL}/api/v1/projects/999999', headers=auth_a)
    test('12. 项目不存在(5001)', r, expect_code=5001, expect_http=404)

    # 13. 未认证
    r = requests.post(f'{BASE_URL}/api/v1/projects/', json={'title': 'test'}, headers=HEADERS)
    test('13. 未认证(401)', r, expect_code=401, expect_http=401)

    print(f'\n=== 测试结果: {passed} 通过 / {failed} 失败 ===')
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
