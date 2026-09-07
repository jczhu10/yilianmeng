# -*- coding: utf-8 -*-
"""个人主页接口测试：聚合主页、他人作品/项目、点赞作品、浏览记录"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import (User, Follow, Work, Project, WorkViewHistory,
                        ProjectViewHistory, Profile, ProfileSkill, Skill)
from app.utils.helpers import create_token


class ProfileHomepageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

        suffix = random.randint(10000000, 99999999)
        cls.userA = User(phone=f'5511{suffix}', nickname='主页A', is_new_user=False); cls.userA.set_password('Test123456')
        cls.userB = User(phone=f'5522{suffix:08d}', nickname='主页B', is_new_user=False); cls.userB.set_password('Test123456')
        cls.userC = User(phone=f'5533{suffix:08d}', nickname='主页C', is_new_user=False); cls.userC.set_password('Test123456')
        db.session.add_all([cls.userA, cls.userB, cls.userC])
        db.session.commit()

        cls.tokenA = create_token(cls.userA.id)
        cls.tokenB = create_token(cls.userB.id)
        cls.tokenC = create_token(cls.userC.id)

        # B 关注 A，A 也关注 B（互关）
        db.session.add(Follow(follower_id=cls.userB.id, followed_id=cls.userA.id))
        db.session.add(Follow(follower_id=cls.userA.id, followed_id=cls.userB.id))
        # C 关注 A（单向）
        db.session.add(Follow(follower_id=cls.userC.id, followed_id=cls.userA.id))
        db.session.commit()

        # A 发布一条公开作品
        with cls.app.test_client() as c:
            r = c.post('/api/v1/works/', headers={'Authorization': f'Bearer {cls.tokenA}', 'Content-Type': 'application/json'}, json={
                'content_type': 'text_only', 'channel': 'writing',
                'text_content': '主页测试作品', 'visibility_type': 'public', 'status': 'published',
            })
            cls.work_id = r.get_json()['data']['work_id']

        # A 发布一个项目
        with cls.app.test_client() as c:
            r = c.post('/api/v1/projects/', headers={'Authorization': f'Bearer {cls.tokenA}', 'Content-Type': 'application/json'}, json={
                'title': '主页测试项目', 'description': '测试主页',
                'mode': 'free', 'budget': 0, 'required_skills': [],
            })
            cls.project_id = r.get_json()['data']['project_id']

    def headers(self, token):
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # ---- 1. 主页聚合接口：他人视角 ----
    def test_01_homepage_other_view(self):
        with self.app.test_client() as c:
            # B 查看 A 的主页
            r = c.get(f'/api/v1/profile/homepage/{self.userA.id}', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)
            d = r.get_json()['data']
            self.assertIn('user', d)
            self.assertEqual(d['user']['user_id'], self.userA.id)
            self.assertEqual(d['user']['nickname'], '主页A')
            # 他人查看手机号脱敏
            self.assertIn('****', d['user']['phone'])
            # 计数存在
            self.assertIn('follower_count', d['user'])
            self.assertIn('work_count', d['user'])
            # 关注关系：B 关注了 A，A 也关注了 B -> 互关
            self.assertTrue(d['is_following'])
            self.assertTrue(d['is_followed_by'])
            self.assertTrue(d['is_mutual'])
            self.assertFalse(d['is_self'])

    # ---- 2. 主页聚合接口：自己视角（完整手机号） ----
    def test_02_homepage_self_view(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/profile/homepage/{self.userA.id}', headers=self.headers(self.tokenA))
            d = r.get_json()['data']
            self.assertTrue(d['is_self'])
            # 自己看自己：完整手机号
            self.assertNotIn('****', d['user']['phone'])
            self.assertEqual(d['user']['phone'], self.userA.phone)

    # ---- 3. 单向关注视角 ----
    def test_03_homepage_one_way_follow(self):
        with self.app.test_client() as c:
            # C 查看 A：C 关注了 A，但 A 没关注 C
            r = c.get(f'/api/v1/profile/homepage/{self.userA.id}', headers=self.headers(self.tokenC))
            d = r.get_json()['data']
            self.assertTrue(d['is_following'])
            self.assertFalse(d['is_followed_by'])
            self.assertFalse(d['is_mutual'])

    # ---- 4. 他人作品列表 ----
    def test_04_user_works_list(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/user/{self.userA.id}', headers=self.headers(self.tokenB))
            d = r.get_json()['data']
            self.assertGreaterEqual(d['total'], 1)
            # A 的公开作品应在列表中
            work_ids = [w['work_id'] for w in d['list']]
            self.assertIn(self.work_id, work_ids)

    # ---- 5. 点赞作品列表 ----
    def test_05_liked_works_list(self):
        with self.app.test_client() as c:
            # B 点赞 A 的作品
            r = c.post(f'/api/v1/works/{self.work_id}/like', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)

            # 查询 B 点赞过的作品
            r = c.get(f'/api/v1/works/user/{self.userB.id}/liked', headers=self.headers(self.tokenA))
            d = r.get_json()['data']
            self.assertGreaterEqual(d['total'], 1)
            liked_ids = [w['work_id'] for w in d['list']]
            self.assertIn(self.work_id, liked_ids)

    # ---- 6. 作品浏览记录写入 + 查询 ----
    def test_06_work_view_history(self):
        with self.app.test_client() as c:
            # B 浏览 A 的作品（写浏览记录）
            r = c.get(f'/api/v1/works/{self.work_id}', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)

            # B 再浏览一次（应累加 view_count，不新增行）
            r = c.get(f'/api/v1/works/{self.work_id}', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)

            # 验证数据库
            h = WorkViewHistory.query.filter_by(user_id=self.userB.id, work_id=self.work_id).first()
            self.assertIsNotNone(h)
            self.assertEqual(h.view_count, 2)

            # B 的浏览记录接口能看到
            r = c.get('/api/v1/profile/views/works', headers=self.headers(self.tokenB))
            d = r.get_json()['data']
            self.assertGreaterEqual(d['total'], 1)
            wids = [x['work_id'] for x in d['list']]
            self.assertIn(self.work_id, wids)
            # 含作品标题和作者信息
            item = next(x for x in d['list'] if x['work_id'] == self.work_id)
            self.assertEqual(item['author']['user_id'], self.userA.id)

    # ---- 7. 项目浏览记录写入 + 查询 ----
    def test_07_project_view_history(self):
        with self.app.test_client() as c:
            # B 浏览 A 的项目
            r = c.get(f'/api/v1/projects/{self.project_id}', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)

            h = ProjectViewHistory.query.filter_by(user_id=self.userB.id, project_id=self.project_id).first()
            self.assertIsNotNone(h)

            # B 的项目浏览记录接口
            r = c.get('/api/v1/profile/views/projects', headers=self.headers(self.tokenB))
            d = r.get_json()['data']
            pids = [x['project_id'] for x in d['list']]
            self.assertIn(self.project_id, pids)
            item = next(x for x in d['list'] if x['project_id'] == self.project_id)
            self.assertEqual(item['author']['user_id'], self.userA.id)

    # ---- 8. 他人项目列表 ----
    def test_08_user_projects_list(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/projects/user/{self.userA.id}', headers=self.headers(self.tokenB))
            d = r.get_json()['data']
            self.assertGreaterEqual(d['total'], 1)
            pids = [p['project_id'] for p in d['list']]
            self.assertIn(self.project_id, pids)

    # ---- 9. 自己浏览自己作品不写记录 ----
    def test_09_self_view_no_history(self):
        before = WorkViewHistory.query.filter_by(user_id=self.userA.id, work_id=self.work_id).count()
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{self.work_id}', headers=self.headers(self.tokenA))
            self.assertEqual(r.status_code, 200)
        after = WorkViewHistory.query.filter_by(user_id=self.userA.id, work_id=self.work_id).count()
        self.assertEqual(before, after, '自己浏览自己作品不应写浏览记录')

    @classmethod
    def tearDownClass(cls):
        from app.models import Notification
        Notification.query.filter(Notification.user_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        Notification.query.filter(Notification.sender_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        WorkViewHistory.query.filter(WorkViewHistory.user_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        ProjectViewHistory.query.filter(ProjectViewHistory.user_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        from app.models import Like, Comment, ProjectApplication, ProjectRequiredSkill
        Comment.query.filter_by(work_id=cls.work_id).delete(synchronize_session=False)
        Like.query.filter_by(work_id=cls.work_id).delete(synchronize_session=False)
        ProjectApplication.query.filter_by(project_id=cls.project_id).delete(synchronize_session=False)
        ProjectRequiredSkill.query.filter_by(project_id=cls.project_id).delete(synchronize_session=False)
        Work.query.filter_by(id=cls.work_id).delete(synchronize_session=False)
        Project.query.filter_by(id=cls.project_id).delete(synchronize_session=False)
        Follow.query.filter(Follow.follower_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        Follow.query.filter(Follow.followed_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        for u in [cls.userA, cls.userB, cls.userC]:
            db.session.delete(u)
        db.session.commit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
