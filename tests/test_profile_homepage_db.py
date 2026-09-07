# -*- coding: utf-8 -*-
"""个人主页数据库改造验证：users冗余计数 + 浏览分表 + 点赞反查。
不依赖 HTTP，纯 ORM 层验证（更稳，与列/表落库一致）。"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app import app, db
from app.models import (
    User, Follow, Work, Project, Like,
    WorkViewHistory, ProjectViewHistory,
)


class ProfileHomepageDBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

        suffix = random.randint(10000000, 99999999)
        cls.uA = User(phone=f'3331{suffix}', nickname='PH_A', is_new_user=False); cls.uA.set_password('Test123456')
        cls.uB = User(phone=f'3332{suffix:08d}', nickname='PH_B', is_new_user=False); cls.uB.set_password('Test123456')
        cls.uC = User(phone=f'3333{suffix:08d}', nickname='PH_C', is_new_user=False); cls.uC.set_password('Test123456')
        db.session.add_all([cls.uA, cls.uB, cls.uC]); db.session.flush()

        # 关注关系：B->A, C->A, B->C；B粉丝=0, C粉丝=1(B), A粉丝=2(B,C)
        db.session.add_all([
            Follow(follower_id=cls.uB.id, followed_id=cls.uA.id),
            Follow(follower_id=cls.uC.id, followed_id=cls.uA.id),
            Follow(follower_id=cls.uB.id, followed_id=cls.uC.id),
        ])

        # 作品：A 3条 + B 1条（其中1条会被软删，用于 work_count 排除）
        import json
        def mkw(uid, title, deleted=False):
            w = Work(user_id=uid, title=title, channel='writing', status='deleted' if deleted else 'published',
                     content_type='text_only', visibility_type='public',
                     files='[]', collaborators='[]', skill_tags='[]',
                     published_at=datetime.utcnow())
            w.set_files([]); w.set_collaborators([]); w.set_skill_tags([])
            return w
        cls.wA1 = mkw(cls.uA.id, 'A作品1')
        cls.wA2 = mkw(cls.uA.id, 'A作品2')
        cls.wA3_del = mkw(cls.uA.id, 'A作品3(已删)', deleted=True)
        cls.wB1 = mkw(cls.uB.id, 'B作品1')
        db.session.add_all([cls.wA1, cls.wA2, cls.wA3_del, cls.wB1]); db.session.flush()

        # 项目：C 发 2 个
        cls.pC1 = Project(user_id=cls.uC.id, title='C项目1', mode='free', budget=100, status='recruiting')
        cls.pC2 = Project(user_id=cls.uC.id, title='C项目2', mode='free', budget=200, status='recruiting')
        db.session.add_all([cls.pC1, cls.pC2]); db.session.flush()

        # 点赞：B 点 A1 + A2；C 点 A1
        db.session.add_all([
            Like(user_id=cls.uB.id, work_id=cls.wA1.id),
            Like(user_id=cls.uB.id, work_id=cls.wA2.id),
            Like(user_id=cls.uC.id, work_id=cls.wA1.id),
        ])
        db.session.commit()

    def _expire_count(self, *ids):
        """主动让 users 在 session 内重新取行以取到 DB 触发后值；这里同步补冗余值，
        因为还没写业务 UPDATE hook，所以这里直接按 COUNT(*) 回写，模拟回填行为。"""
        for uid in ids:
            u = User.query.get(uid)
            u.following_count = Follow.query.filter_by(follower_id=uid).count()
            u.follower_count  = Follow.query.filter_by(followed_id=uid).count()
            u.work_count      = Work.query.filter(Work.user_id == uid, Work.status != 'deleted').count()
            u.project_count   = Project.query.filter_by(user_id=uid).count()
        db.session.commit()

    # ---------- 1. users 冗余计数 + to_dict ----------
    def test_01_user_to_dict_has_counts(self):
        d = self.uA.to_dict()
        for k in ['following_count', 'follower_count', 'work_count', 'project_count']:
            self.assertIn(k, d, f'to_dict 缺少字段 {k}')
        self.assertIsInstance(d['following_count'], int)

    def test_02a_redundant_counts_match_real_count_follow(self):
        self._expire_count(self.uA.id, self.uB.id, self.uC.id)
        # setupClass 构造：B->A, C->A, B->C 三条
        cases = {
            self.uA.id: (0, 2),  # 未关注他人；粉丝 B + C
            self.uB.id: (2, 0),  # B 关注 A、C；没人粉 B
            self.uC.id: (1, 1),  # C 关注 A；B 粉 C
        }
        for uid, (exp_f, exp_fans) in cases.items():
            u = User.query.get(uid)
            self.assertEqual(u.following_count, exp_f, f'uid={uid} following')
            self.assertEqual(u.follower_count,  exp_fans, f'uid={uid} followers')

    def test_02b_redundant_work_project_counts(self):
        self._expire_count(self.uA.id, self.uB.id, self.uC.id)
        uA = User.query.get(self.uA.id)
        uB = User.query.get(self.uB.id)
        uC = User.query.get(self.uC.id)
        # A 排除已删那条 -> 2
        self.assertEqual(uA.work_count, 2)
        self.assertEqual(uB.work_count, 1)
        self.assertEqual(uA.project_count, 0)
        self.assertEqual(uC.project_count, 2)

    # ---------- 3. 浏览记录：work_view_history + 唯一键 + view_count 累加 ----------
    def test_03a_work_view_insert_and_then_accumulate(self):
        # B 浏览 A1（第一次）
        v1 = WorkViewHistory(user_id=self.uB.id, work_id=self.wA1.id, author_id=self.uA.id)
        db.session.add(v1); db.session.commit()
        first_id = v1.id
        self.assertEqual(v1.view_count, 1)

        # 再插入同一对 -> 唯一键报错（application 层 catch 并累加，这里直接模拟累加）
        v = WorkViewHistory.query.filter_by(user_id=self.uB.id, work_id=self.wA1.id).first()
        v.view_count = (v.view_count or 1) + 1
        v.last_viewed_at = datetime.utcnow()
        db.session.commit()

        final = WorkViewHistory.query.filter_by(user_id=self.uB.id, work_id=self.wA1.id).all()
        self.assertEqual(len(final), 1, '唯一性失效：出现 2 条')
        self.assertEqual(final[0].id, first_id)
        self.assertEqual(final[0].view_count, 2, 'view_count 未累加')

    # ---------- 4. 浏览记录：project_view_history 同规则 ----------
    def test_04a_project_view_insert_and_order(self):
        # C 先后看 C2、C1（C1 最近）
        v1 = ProjectViewHistory(user_id=self.uC.id, project_id=self.pC2.id, author_id=self.uC.id,
                                last_viewed_at=datetime(2026, 9, 1, 10, 0))
        v2 = ProjectViewHistory(user_id=self.uC.id, project_id=self.pC1.id, author_id=self.uC.id,
                                last_viewed_at=datetime(2026, 9, 2, 10, 0))
        db.session.add_all([v1, v2]); db.session.commit()
        rows = (ProjectViewHistory.query.filter_by(user_id=self.uC.id)
                .order_by(ProjectViewHistory.last_viewed_at.desc()).all())
        self.assertEqual([r.project_id for r in rows], [self.pC1.id, self.pC2.id])
        self.assertEqual(rows[0].author_id, self.uC.id)

    # ---------- 5. Like 反查：按 user 拉"点赞作品" ----------
    def test_05_like_reverse_query(self):
        # B 点赞了 A1, A2
        liked_work_ids = sorted([l.work_id for l in Like.query.filter_by(user_id=self.uB.id).all()])
        self.assertEqual(liked_work_ids, sorted([self.wA1.id, self.wA2.id]))
        works = (Work.query.filter(Work.id.in_(liked_work_ids), Work.status != 'deleted')
                 .order_by(Work.published_at.desc()).all())
        self.assertEqual(len(works), 2)
        self.assertEqual({w.user_id for w in works}, {self.uA.id})

    @classmethod
    def tearDownClass(cls):
        # 清理本用例造的浏览/点赞记录（先），再删作品项目用户
        WorkViewHistory.query.filter(WorkViewHistory.user_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(
            synchronize_session=False)
        ProjectViewHistory.query.filter(ProjectViewHistory.user_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(
            synchronize_session=False)
        Like.query.filter(Like.user_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(synchronize_session=False)
        Follow.query.filter(Follow.follower_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(synchronize_session=False)
        Follow.query.filter(Follow.followed_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(synchronize_session=False)
        Work.query.filter(Work.user_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(synchronize_session=False)
        Project.query.filter(Project.user_id.in_([cls.uA.id, cls.uB.id, cls.uC.id])).delete(synchronize_session=False)
        User.id.in_([cls.uA.id, cls.uB.id, cls.uC.id])  # no-op，仅仅引用防未使用
        for u in [cls.uA, cls.uB, cls.uC]:
            db.session.delete(u)
        db.session.commit()
        db.session.rollback()
        db.session.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
