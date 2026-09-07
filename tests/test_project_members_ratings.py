# -*- coding: utf-8 -*-
"""协作项目模块新增功能测试：成员管理 + 互评 + 新字段
使用进程内 unittest 模式（与 test_messages.py 一致），不依赖外部服务器。
"""
import sys, os, random, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import (User, Profile, Project, ProjectApplication,
                        Rating, RatingTag, Notification)
from app.utils.helpers import create_token


class ProjectMembersRatingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        # 创建 3 个测试用户
        cls.user_a = User(phone=f'139{random.randint(10000000,99999999)}',
                          nickname='测试A', is_new_user=False)
        cls.user_a.set_password('Test123456')
        cls.user_b = User(phone=f'138{random.randint(10000000,99999999):08d}',
                          nickname='测试B', is_new_user=False)
        cls.user_b.set_password('Test123456')
        cls.user_c = User(phone=f'137{random.randint(10000000,99999999):08d}',
                          nickname='测试C', is_new_user=False)
        cls.user_c.set_password('Test123456')
        db.session.add_all([cls.user_a, cls.user_b, cls.user_c])
        db.session.commit()
        for u in [cls.user_a, cls.user_b, cls.user_c]:
            db.session.add(Profile(user_id=u.id, identity='艺术爱好者'))
        db.session.commit()
        cls.token_a = create_token(cls.user_a.id)
        cls.token_b = create_token(cls.user_b.id)
        cls.token_c = create_token(cls.user_c.id)
        cls.project_ids = []
        cls.rating_ids = []

    @classmethod
    def tearDownClass(cls):
        try:
            # 清理项目相关数据
            for pid in cls.project_ids:
                Rating.query.filter_by(project_id=pid).delete()
                ProjectApplication.query.filter_by(project_id=pid).delete()
                Project.query.filter_by(id=pid).delete()
            # 清理通知
            for u in [cls.user_a, cls.user_b, cls.user_c]:
                Notification.query.filter_by(user_id=u.id).delete()
            db.session.commit()
            # 清理 rating_tags 之外的评价记录
            Rating.query.filter(
                (Rating.from_user_id.in_([cls.user_a.id, cls.user_b.id, cls.user_c.id])) |
                (Rating.to_user_id.in_([cls.user_a.id, cls.user_b.id, cls.user_c.id]))
            ).delete(synchronize_session=False)
            db.session.commit()
            # 先删 profiles（外键约束）
            from app.models import Profile
            for u in [cls.user_a, cls.user_b, cls.user_c]:
                Profile.query.filter_by(user_id=u.id).delete()
            db.session.commit()
            db.session.delete(cls.user_a)
            db.session.delete(cls.user_b)
            db.session.delete(cls.user_c)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f'teardown error: {e}')
        cls.ctx.pop()

    def headers(self, token=None):
        h = {'Content-Type': 'application/json'}
        if token:
            h['Authorization'] = f'Bearer {token}'
        return h

    def _create_project(self, token, payload=None):
        """辅助：创建项目并记录 id"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', json=payload or {'title': '测试项目', 'mode': 'free'},
                       headers=self.headers(token))
            return r

    def _approve_and_go_ongoing(self, creator_token, project_id, applicant_token, applicant_id):
        """辅助：applicant 申请 → creator approve → 项目转 ongoing"""
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{project_id}/apply',
                       json={'message': 'join'}, headers=self.headers(applicant_token))
            app_id = r.get_json()['data']['id']
            c.post(f'/api/v1/projects/{project_id}/applications/{app_id}/approve',
                   headers=self.headers(creator_token))
            return app_id

    # ====== 新字段测试 ======
    def test_01_create_with_new_fields(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', json={
                'title': '新字段项目',
                'description': '测试新字段',
                'mode': 'free',
                'topic': '元宇宙剧本杀',
                'required_level': 3,
                'required_project_count': 2,
                'contact_visible': False,
                'max_members': 5,
                'cover_url': 'https://cdn.example.com/cover.png'
            }, headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['topic'], '元宇宙剧本杀')
            self.assertEqual(data['data']['required_level'], 3)
            self.assertEqual(data['data']['required_project_count'], 2)
            self.assertFalse(data['data']['contact_visible'])
            self.assertEqual(data['data']['max_members'], 5)
            self.assertEqual(data['data']['cover_url'], 'https://cdn.example.com/cover.png')
            self.project_ids.append(data['data']['project_id'])
            print(f'[OK] 01 发起项目带新字段: project_id={data["data"]["project_id"]}')

    def test_02_create_invalid_topic(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', json={
                'title': 'topic过长', 'topic': 'x' * 200
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 400)
            print('[OK] 02 topic过长(400)')

    def test_03_create_invalid_max_members(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', json={
                'title': 'mm', 'max_members': 0
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            print('[OK] 03 max_members<1(400)')

    def test_04_create_invalid_required_level(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/projects/', json={
                'title': 'lvl', 'required_level': 999
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            print('[OK] 04 required_level>100(400)')

    def test_05_update_new_fields(self):
        r = self._create_project(self.token_a, {'title': '编辑测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            r = c.put(f'/api/v1/projects/{pid}', json={
                'topic': '更新后的主题',
                'contact_visible': True,
                'max_members': 8
            }, headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['topic'], '更新后的主题')
            self.assertTrue(data['data']['contact_visible'])
            self.assertEqual(data['data']['max_members'], 8)
            print('[OK] 05 编辑新字段')

    # ====== 我的申请列表 ======
    def test_06_my_applications_empty(self):
        # C 还没有任何申请
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/my-applications', headers=self.headers(self.token_c))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['total'], 0)
            print('[OK] 06 我的申请列表(初始空)')

    def test_07_my_applications_with_data(self):
        r = self._create_project(self.token_a, {'title': '申请列表测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            c.post(f'/api/v1/projects/{pid}/apply', json={'message': '我想加入'},
                   headers=self.headers(self.token_c))
            r = c.get('/api/v1/projects/my-applications', headers=self.headers(self.token_c))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            self.assertIsNotNone(data['data']['list'][0].get('project'))
            print('[OK] 07 我的申请列表(有数据)')

    def test_08_my_applications_filter_by_status(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/my-applications?status=pending',
                      headers=self.headers(self.token_c))
            self.assertEqual(r.status_code, 200)
            print('[OK] 08 我的申请-按status过滤')

    def test_09_my_applications_invalid_status(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/projects/my-applications?status=invalid',
                      headers=self.headers(self.token_c))
            self.assertEqual(r.status_code, 400)
            print('[OK] 09 我的申请-无效status(400)')

    # ====== 退出项目 ======
    def test_10_leave_recruiting_state(self):
        r = self._create_project(self.token_a, {'title': '退出测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/apply', json={'message': 'join'},
                       headers=self.headers(self.token_b))
            # recruiting 状态 + B 未 approved 不能退出
            r = c.post(f'/api/v1/projects/{pid}/leave', headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 400)
            print('[OK] 10 recruiting不可退出(400)')

    def test_11_leave_as_creator(self):
        r = self._create_project(self.token_a, {'title': '退出测试2', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/leave', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            print('[OK] 11 发起人不可退出(400)')

    def test_12_leave_success(self):
        r = self._create_project(self.token_a, {'title': '退出成功测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            # B 退出
            r = c.post(f'/api/v1/projects/{pid}/leave', headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 200)
            # 验证状态
            r = c.get('/api/v1/projects/my-applications?status=left',
                      headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 12 B退出项目成功')

    def test_13_leave_non_member(self):
        r = self._create_project(self.token_a, {'title': '非成员退出', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/leave', headers=self.headers(self.token_c))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5008)
            print('[OK] 13 非成员退出(5008)')

    # ====== 踢人 ======
    def test_14_remove_non_creator(self):
        r = self._create_project(self.token_a, {'title': '踢人测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/members/{self.user_b.id}/remove',
                       headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.get_json()['code'], 5002)
            print('[OK] 14 非发起人踢人(5002)')

    def test_15_remove_self(self):
        r = self._create_project(self.token_a, {'title': '踢自己测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/members/{self.user_a.id}/remove',
                       headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            print('[OK] 15 踢自己(400)')

    def test_16_remove_non_member(self):
        r = self._create_project(self.token_a, {'title': '踢非成员', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/members/{self.user_c.id}/remove',
                       headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5008)
            print('[OK] 16 踢非成员(5008)')

    def test_17_remove_success(self):
        r = self._create_project(self.token_a, {'title': '踢人成功测试', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/members/{self.user_b.id}/remove',
                       headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            # 验证状态
            r = c.get('/api/v1/projects/my-applications?status=removed',
                      headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 17 踢人成功')

    # ====== 结束项目 ======
    def test_18_finish_non_creator(self):
        r = self._create_project(self.token_a, {'title': '结束项目', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/finish', headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.get_json()['code'], 5002)
            print('[OK] 18 非发起人结束(5002)')

    def test_19_finish_success(self):
        r = self._create_project(self.token_a, {'title': '结束成功', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/finish', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            # 重复结束
            r = c.post(f'/api/v1/projects/{pid}/finish', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 200)
            print('[OK] 19 结束项目成功(含重复结束)')

    def test_20_finish_recruiting(self):
        r = self._create_project(self.token_a, {'title': 'rec结束', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/finish', headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5003)
            print('[OK] 20 recruiting不可结束(5003)')

    # ====== 互评 ======
    def _setup_completed_project_with_b(self):
        r = self._create_project(self.token_a, {'title': '互评项目', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        self._approve_and_go_ongoing(self.token_a, pid, self.token_b, self.user_b.id)
        with self.app.test_client() as c:
            c.post(f'/api/v1/projects/{pid}/finish', headers=self.headers(self.token_a))
        return pid

    def test_21_rating_unfinished_project(self):
        r = self._create_project(self.token_a, {'title': '未完成互评', 'mode': 'free'})
        pid = r.get_json()['data']['project_id']
        self.project_ids.append(pid)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 5
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5011)
            print('[OK] 21 项目未完成不可互评(5011)')

    def test_22_rating_non_member(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_a.id, 'score': 5
            }, headers=self.headers(self.token_c))
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.get_json()['code'], 5008)
            print('[OK] 22 非成员互评(5008)')

    def test_23_rating_self(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_a.id, 'score': 5
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5009)
            print('[OK] 23 评价自己(5009)')

    def test_24_rating_invalid_score(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 0
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5012)
            print('[OK] 24 无效分数(5012)')

    def test_25_rating_to_non_member(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_c.id, 'score': 5
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5008)
            print('[OK] 25 评价非成员(5008)')

    def test_26_rating_success(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id,
                'score': 5,
                'comment': '表现优秀',
                'is_anonymous': False
            }, headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['score'], 5)
            self.assertEqual(data['data']['from_user_id'], self.user_a.id)
            self.rating_ids.append(data['data']['rating_id'])
            print('[OK] 26 提交互评成功')

    def test_27_rating_duplicate(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 5
            }, headers=self.headers(self.token_a))
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 4
            }, headers=self.headers(self.token_a))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json()['code'], 5010)
            print('[OK] 27 重复评价(5010)')

    def test_28_rating_anonymous(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_a.id,
                'score': 4,
                'comment': '匿名评价',
                'is_anonymous': True
            }, headers=self.headers(self.token_b))
            self.assertEqual(r.status_code, 200)
            self.rating_ids.append(r.get_json()['data']['rating_id'])
            print('[OK] 28 匿名互评成功')

    # ====== 查看互评 ======
    def test_29_list_ratings_as_member(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 5
            }, headers=self.headers(self.token_a))
            r = c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_a.id, 'score': 4, 'is_anonymous': True
            }, headers=self.headers(self.token_b))
            self.rating_ids.append(r.get_json()['data']['rating_id'])
            r = c.get(f'/api/v1/projects/{pid}/ratings', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 2)
            # 匿名评价 from_user_id 应为 null
            anon = next((x for x in data['data']['list'] if x.get('is_anonymous')), None)
            self.assertIsNotNone(anon)
            self.assertIsNone(anon['from_user_id'])
            self.assertIsNone(anon['from_user'])
            print('[OK] 29 查看互评列表(含匿名)')

    def test_30_list_ratings_non_member(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/projects/{pid}/ratings', headers=self.headers(self.token_c))
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.get_json()['code'], 5008)
            print('[OK] 30 非成员查看互评(5008)')

    def test_31_list_ratings_pagination(self):
        pid = self._setup_completed_project_with_b()
        with self.app.test_client() as c:
            c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_b.id, 'score': 5
            }, headers=self.headers(self.token_a))
            c.post(f'/api/v1/projects/{pid}/ratings', json={
                'to_user_id': self.user_a.id, 'score': 4
            }, headers=self.headers(self.token_b))
            r = c.get(f'/api/v1/projects/{pid}/ratings?page=1&page_size=1',
                      headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(data['data']['list']), 1)
            print('[OK] 31 互评分页')


if __name__ == '__main__':
    unittest.main(verbosity=2)
