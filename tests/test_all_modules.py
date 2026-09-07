# -*- coding: utf-8 -*-
"""统一测试：作品/互动/项目模块（使用 Flask test client，无需启动服务器）"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import User, Work, Like, Comment, Project, ProjectApplication
from app.utils.helpers import create_token
import unittest


class WorksInteractionsProjectsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        # 创建两个测试用户
        phone_a = f'139{random.randint(10000000,99999999)}'
        phone_b = f'138{random.randint(10000000,99999999):08d}'
        cls.user_a = User(phone=phone_a, nickname='作者A', is_new_user=False)
        cls.user_a.set_password('Test123456')
        cls.user_b = User(phone=phone_b, nickname='用户B', is_new_user=False)
        cls.user_b.set_password('Test123456')
        db.session.add_all([cls.user_a, cls.user_b])
        db.session.commit()
        cls.token_a = create_token(cls.user_a.id)
        cls.token_b = create_token(cls.user_b.id)

    @classmethod
    def tearDownClass(cls):
        try:
            # 清理顺序：likes → comments → works → projects → users
            for u in [cls.user_a, cls.user_b]:
                Like.query.filter((Like.user_id==u.id)).delete(synchronize_session=False)
                Comment.query.filter(Comment.user_id==u.id).delete(synchronize_session=False)
                Work.query.filter_by(user_id=u.id).delete(synchronize_session=False)
                ProjectApplication.query.filter_by(user_id=u.id).delete(synchronize_session=False)
                Project.query.filter_by(user_id=u.id).delete(synchronize_session=False)
            db.session.delete(cls.user_a)
            db.session.delete(cls.user_b)
            db.session.commit()
        except Exception:
            db.session.rollback()
        cls.ctx.pop()

    def headers(self, token=None):
        h = {'Content-Type': 'application/json'}
        if token:
            h['Authorization'] = f'Bearer {token}'
        return h

    # ==================== 作品模块 ====================
    def test_01_create_work_draft(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.token_a),
                       json={'title': '测试草稿', 'description': '描述', 'channel': 'writing',
                             'skill_tags': [1, 2], 'status': 'draft'})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.work_id = data['data']['work_id']
            print(f'[OK] 1 创建草稿 work_id={self.work_id}')

    def test_02_update_work(self):
        with self.app.test_client() as c:
            r = c.put(f'/api/v1/works/{self.work_id}', headers=self.headers(self.token_a),
                      json={'title': '修改标题'})
            self.assertEqual(r.status_code, 200)
            print('[OK] 2 编辑作品')

    def test_03_publish_work(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/publish', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 3 发布作品')

    def test_04_get_work_detail(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{self.work_id}', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 4 作品详情')

    def test_05_get_my_works(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/mine', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 5 我的作品 total={data["data"]["total"]}')

    def test_06_get_feed(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/feed', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print(f'[OK] 6 推流 total={data["data"]["total"]}')

    def test_07_search_works(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/search?q=修改', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 7 搜索作品')

    def test_08_get_works_by_skill(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/by-skill?skill_id=1', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 8 按技能筛选')

    def test_09_delete_work(self):
        with self.app.test_client() as c:
            # 先创建一个草稿再删
            r = c.post('/api/v1/works/', headers=self.headers(self.token_a),
                       json={'title': '待删草稿', 'channel': 'visual', 'status': 'draft'})
            wid = r.get_json()['data']['work_id']
            r = c.delete(f'/api/v1/works/{wid}', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 9 删除作品')

    # ==================== 互动模块 ====================
    def test_10_like_work(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/like', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['like_count'], 1)
            print(f'[OK] 10 点赞 like_count={data["data"]["like_count"]}')

    def test_11_already_liked(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/like', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(data['code'], 4003)
            print('[OK] 11 重复点赞被拒')

    def test_12_get_likes(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{self.work_id}/likes', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 12 点赞列表 total={data["data"]["total"]}')

    def test_13_create_comment(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.token_b),
                       json={'content': '好作品！'})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.comment_id = data['data']['comment_id']
            print(f'[OK] 13 评论 comment_id={self.comment_id}')

    def test_14_create_reply(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.token_a),
                       json={'content': '谢谢', 'parent_id': self.comment_id})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.reply_id = data['data']['comment_id']
            print('[OK] 14 回复评论')

    def test_15_get_comments(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 15 评论列表 total={data["data"]["total"]}')

    def test_16_get_replies(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/comments/{self.comment_id}/replies', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 16 回复列表 total={data["data"]["total"]}')

    def test_17_reply_level_exceeded(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.token_b),
                       json={'content': '三级回复', 'parent_id': self.reply_id})
            data = r.get_json()
            self.assertEqual(data['code'], 4007)
            print('[OK] 17 三级回复被拒')

    def test_18_delete_comment(self):
        with self.app.test_client() as c:
            r = c.delete(f'/api/v1/comments/{self.comment_id}', headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 200)
            print('[OK] 18 删除评论')

    def test_19_unlike_work(self):
        with self.app.test_client() as c:
            r = c.delete(f'/api/v1/works/{self.work_id}/like', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print(f'[OK] 19 取消点赞 like_count={data["data"]["like_count"]}')

    # ==================== 项目模块 ====================
    def test_20_create_project(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', headers=self.headers(self.token_a),
                       json={'title': '测试项目', 'description': '描述', 'required_skills': [1],
                             'mode': 'free', 'deadline': '2026-12-31T00:00:00'})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.project_id = data['data']['project_id']
            print(f'[OK] 20 创建项目 project_id={self.project_id}')

    def test_21_list_projects(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 21 项目列表 total={data["data"]["total"]}')

    def test_22_get_project_detail(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/projects/{self.project_id}', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 22 项目详情')

    def test_23_update_project(self):
        with self.app.test_client() as c:
            r = c.put(f'/api/v1/projects/{self.project_id}', headers=self.headers(self.token_a),
                      json={'title': '修改项目标题'})
            self.assertEqual(r.status_code, 200)
            print('[OK] 23 编辑项目')

    def test_24_apply_project(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{self.project_id}/apply', headers=self.headers(self.token_b),
                       json={'message': '我想加入'})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.app_id = data['data']['id']
            print(f'[OK] 24 申请加入 app_id={self.app_id}')

    def test_25_apply_again_rejected(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{self.project_id}/apply', headers=self.headers(self.token_b),
                       json={'message': '再申请一次'})
            data = r.get_json()
            self.assertEqual(data['code'], 5005)
            print('[OK] 25 重复申请被拒')

    def test_26_approve_application(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{self.project_id}/applications/{self.app_id}/approve',
                       headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['status'], 'approved')
            print('[OK] 26 通过申请')

    def test_27_my_projects(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/mine', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 27 我的项目 total={data["data"]["total"]}')

    def test_28_my_joined_projects(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/mine?role=joined', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print(f'[OK] 28 我参与的项目 total={data["data"]["total"]}')

    def test_29_close_project(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{self.project_id}/close', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 29 关闭项目')


if __name__ == '__main__':
    unittest.main(verbosity=2)
