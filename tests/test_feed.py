# -*- coding: utf-8 -*-
"""推流/搜索/按技能筛选 测试  用法: python tests/test_feed.py"""
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
    print('推流模块测试 (feed / search / by-skill)')
    print('=' * 60)

    token_a = login('13800138000')
    auth_a = {**HEADERS, 'Authorization': f'Bearer {token_a}'}
    # 作品1: writing + skill_tags
    requests.post(f'{BASE_URL}/works/', json={
        'title': 'Python入门教程', 'description': '适合零基础学习的Python教程',
        'channel': 'writing', 'skill_tags': [1], 'status': 'published'
    }, headers=auth_a)
    # 作品2: visual
    requests.post(f'{BASE_URL}/works/', json={
        'title': '水彩画技法分享', 'description': '水彩画基础到进阶', 'channel': 'visual', 'status': 'published'
    }, headers=auth_a)
    # 作品3: writing 关键词命中
    requests.post(f'{BASE_URL}/works/', json={
        'title': '散文集', 'description': 'Python风格的散文创作', 'channel': 'writing', 'status': 'published'
    }, headers=auth_a)

    token_b = login('13800138002')
    auth_b = {**HEADERS, 'Authorization': f'Bearer {token_b}'}

    # ===== feed 推流 =====
    r = requests.get(f'{BASE_URL}/works/feed', headers=auth_b)
    body = test('1. feed默认(latest)', r)
    feed_list = body.get('data', {}).get('list', [])
    print(f'   feed 返回 {len(feed_list)} 条')

    r = requests.get(f'{BASE_URL}/works/feed?sort=hot', headers=auth_b)
    test('2. feed热门排序(hot)', r)

    r = requests.get(f'{BASE_URL}/works/feed?channel=writing', headers=auth_b)
    body = test('3. feed按channel筛选', r)
    items = body.get('data', {}).get('list', [])
    all_writing = all(it.get('channel') == 'writing' for it in items) if items else True
    print(f'   channel=writing 返回 {len(items)} 条, 全部writing: {all_writing}')
    if not all_writing:
        failed += 1
        print('[FAIL] 3b. channel筛选结果含非writing作品')
    else:
        passed += 1
        print('[PASS] 3b. channel筛选结果均为writing作品')

    r = requests.get(f'{BASE_URL}/works/feed?exclude_self=false', headers=auth_a)
    test('4. feed包含自己作品(exclude_self=false)', r)

    r = requests.get(f'{BASE_URL}/works/feed?sort=invalid', headers=auth_b)
    test('5. 无效sort参数(400)', r, expect_code=400, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/feed?channel=music', headers=auth_b)
    test('6. 无效channel(3004)', r, expect_code=3004, expect_http=400)

    # ===== search 搜索 =====
    r = requests.get(f'{BASE_URL}/works/search?q=Python', headers=auth_b)
    body = test('7. 搜索Python(命中标题/描述)', r)
    print(f'   搜索Python返回 {len(body.get("data", {}).get("list", []))} 条')

    r = requests.get(f'{BASE_URL}/works/search?q=水彩', headers=auth_b)
    test('8. 搜索水彩(命中)', r)

    r = requests.get(f'{BASE_URL}/works/search?q=Python&channel=writing', headers=auth_b)
    test('9. 搜索+channel叠加', r)

    r = requests.get(f'{BASE_URL}/works/search?q=', headers=auth_b)
    test('10. 空关键词(400)', r, expect_code=400, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/search?q=Python&channel=music', headers=auth_b)
    test('11. 搜索+无效channel(3004)', r, expect_code=3004, expect_http=400)

    # ===== by-skill 按技能筛选 =====
    r = requests.get(f'{BASE_URL}/works/by-skill?skill_id=1', headers=auth_b)
    body = test('12. 按技能1筛选', r)
    print(f'   skill_id=1 返回 {len(body.get("data", {}).get("list", []))} 条')

    r = requests.get(f'{BASE_URL}/works/by-skill', headers=auth_b)
    test('13. 缺skill_id(400)', r, expect_code=400, expect_http=400)

    r = requests.get(f'{BASE_URL}/works/by-skill?skill_id=1&sort=hot', headers=auth_b)
    test('14. 按技能+热门排序', r)

    r = requests.get(f'{BASE_URL}/works/by-skill?skill_id=1&sort=invalid', headers=auth_b)
    test('15. 按技能+无效sort(400)', r, expect_code=400, expect_http=400)

    # ===== 鉴权 =====
    r = requests.get(f'{BASE_URL}/works/feed')
    test('16. 未认证(401)', r, expect_code=401, expect_http=401)

    # ===== is_liked 字段校验 =====
    if feed_list:
        wid = feed_list[0].get('work_id')
        requests.post(f'{BASE_URL}/works/{wid}/like', headers=auth_b)
        r = requests.get(f'{BASE_URL}/works/feed?exclude_self=false', headers=auth_b)
        body = test('17. feed含is_liked字段', r)
        items = body.get('data', {}).get('list', [])
        liked_item = next((it for it in items if it.get('work_id') == wid), None)
        if liked_item and liked_item.get('is_liked') is True:
            passed += 1
            print('[PASS] 18. is_liked字段正确(true)')
        else:
            failed += 1
            print(f'[FAIL] 18. is_liked字段不正确: {liked_item}')

    print('=' * 60)
    print(f'推流模块完成: 通过 {passed} 项, 失败 {failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
