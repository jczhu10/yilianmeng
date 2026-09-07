# -*- coding: utf-8 -*-
"""消息通知触发测试：点赞/评论/项目申请 -> notifications 表 + 未读数"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import User, Follow, Work, Project, ProjectApplication, ProjectRequiredSkill, Notification, Comment, Like
from app.utils.helpers import create_token


class NotificationTriggerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

        suffix = random.randint(10000000, 99999999)
        cls.userA = User(phone=f'4411{suffix}', nickname='消息A', is_new_user=False); cls.userA.set_password('Test123456')
        cls.userB = User(phone=f'4422{suffix:08d}', nickname='消息B', is_new_user=False); cls.userB.set_password('Test123456')
        cls.userC = User(phone=f'4433{suffix:08d}', nickname='消息C', is_new_user=False); cls.userC.set_password('Test123456')
        db.session.add_all([cls.userA, cls.userB, cls.userC])
        db.session.commit()

        cls.tokenA = create_token(cls.userA.id)
        cls.tokenB = create_token(cls.userB.id)
        cls.tokenC = create_token(cls.userC.id)

        # A 发布一条作品
        with cls.app.test_client() as c:
            r = c.post('/api/v1/works/', headers={'Authorization': f'Bearer {cls.tokenA}', 'Content-Type': 'application/json'}, json={
                'content_type': 'text_only',
                'channel': 'writing',
                'text_content': '通知测试作品',
                'visibility_type': 'public',
                'status': 'published',
            })
            cls.work_id = r.get_json()['data']['work_id']

        # A 发布一个项目
        with cls.app.test_client() as c:
            r = c.post('/api/v1/projects/', headers={'Authorization': f'Bearer {cls.tokenA}', 'Content-Type': 'application/json'}, json={
                'title': '通知测试项目',
                'description': '测试项目申请通知',
                'mode': 'free',
                'budget': 0,
                'required_skills': [],
            })
            cls.project_id = r.get_json()['data']['project_id']

    def headers(self, token):
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # ---- 1. 点赞触发通知 ----
    def test_01_like_creates_notification(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/like', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200, r.get_json())

            n = Notification.query.filter_by(
                user_id=self.userA.id, type='interaction', subtype='like',
                sender_id=self.userB.id, related_type='work', related_id=self.work_id
            ).first()
            self.assertIsNotNone(n, '点赞未创建通知')
            self.assertFalse(n.is_read)

            r2 = c.get('/api/v1/notifications/unread-counts', headers=self.headers(self.tokenA))
            self.assertEqual(r2.get_json()['data']['interaction'], 1)

    # ---- 2. 自己点赞自己不通知 ----
    def test_02_self_like_no_notification(self):
        before = Notification.query.filter_by(
            user_id=self.userA.id, type='interaction', subtype='like',
            sender_id=self.userA.id
        ).count()
        self.assertEqual(before, 0, '自己点赞不应产生通知')

    # ---- 3. 评论触发通知 ----
    def test_03_comment_creates_notification(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.tokenB),
                       json={'content': '写得真好'})
            self.assertEqual(r.status_code, 200, r.get_json())

            n = Notification.query.filter_by(
                user_id=self.userA.id, type='interaction', subtype='comment',
                sender_id=self.userB.id, related_type='work', related_id=self.work_id
            ).first()
            self.assertIsNotNone(n, '评论未创建通知')

            r2 = c.get('/api/v1/notifications/unread-counts', headers=self.headers(self.tokenA))
            self.assertEqual(r2.get_json()['data']['interaction'], 2)

    # ---- 4. 回复评论触发通知给被回复者 ----
    def test_04_reply_creates_notification(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.tokenA))
            comments = r.get_json()['data']['list']
            b_comment = next((x for x in comments if x['user_id'] == self.userB.id), None)
            self.assertIsNotNone(b_comment)

            r = c.post(f'/api/v1/works/{self.work_id}/comments', headers=self.headers(self.tokenC),
                       json={'content': '我也觉得', 'parent_id': b_comment['comment_id']})
            self.assertEqual(r.status_code, 200, r.get_json())

            n = Notification.query.filter_by(
                user_id=self.userB.id, type='interaction', subtype='comment',
                sender_id=self.userC.id
            ).first()
            self.assertIsNotNone(n, '回复评论未给被回复者发通知')

    # ---- 5. 项目申请触发待办通知 ----
    def test_05_apply_project_creates_todo(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{self.project_id}/apply', headers=self.headers(self.tokenB),
                       json={'message': '我想加入'})
            self.assertEqual(r.status_code, 200, r.get_json())

            n = Notification.query.filter_by(
                user_id=self.userA.id, type='todo', subtype='apply',
                sender_id=self.userB.id, related_type='project', related_id=self.project_id
            ).first()
            self.assertIsNotNone(n, '项目申请未创建待办通知')

            r2 = c.get('/api/v1/notifications/unread-counts', headers=self.headers(self.tokenA))
            self.assertEqual(r2.get_json()['data']['todo'], 1)

    # ---- 6. 互动列表返回作品摘要 ----
    def test_06_interaction_list_has_work_summary(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/notifications/interaction', headers=self.headers(self.tokenA))
            d = r.get_json()['data']
            self.assertGreater(d['total'], 0)
            like_items = [x for x in d['list'] if x['subtype'] == 'like']
            self.assertGreater(len(like_items), 0)
            item = like_items[0]
            self.assertIn('related_work', item)
            self.assertIsNotNone(item['related_work'])
            self.assertEqual(item['related_work']['work_id'], self.work_id)
            self.assertIn('title', item['related_work'])
            self.assertIsNotNone(item['sender'])
            self.assertEqual(item['sender']['user_id'], self.userB.id)

    # ---- 7. 标记已读后未读数清零 ----
    def test_07_mark_read_clears_count(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/notifications/read-all', headers=self.headers(self.tokenA),
                       json={'type': 'interaction'})
            self.assertEqual(r.status_code, 200)

            r2 = c.get('/api/v1/notifications/unread-counts', headers=self.headers(self.tokenA))
            self.assertEqual(r2.get_json()['data']['interaction'], 0)

    @classmethod
    def tearDownClass(cls):
        Notification.query.filter(Notification.user_id.in_([cls.userA.id, cls.userB.id, cls.userC.id])).delete(synchronize_session=False)
        # 先删回复（parent_id 非空），再删一级评论，避免自引用 FK 冲突
        Comment.query.filter(Comment.work_id == cls.work_id, Comment.parent_id.isnot(None)).delete(synchronize_session=False)
        Comment.query.filter_by(work_id=cls.work_id).delete(synchronize_session=False)
        Like.query.filter_by(work_id=cls.work_id).delete(synchronize_session=False)
        ProjectApplication.query.filter_by(project_id=cls.project_id).delete(synchronize_session=False)
        ProjectRequiredSkill.query.filter_by(project_id=cls.project_id).delete(synchronize_session=False)
        Work.query.filter_by(id=cls.work_id).delete(synchronize_session=False)
        Project.query.filter_by(id=cls.project_id).delete(synchronize_session=False)
        for u in [cls.userA, cls.userB, cls.userC]:
            db.session.delete(u)
        db.session.commit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
