# -*- coding: utf-8 -*-
"""项目+消息增强功能专项测试
1. 项目卡片 member_avatars（已招募队友头像）
2. 项目详情队长 skills + joined_project_count
3. 私聊 project_invite 消息
4. 群聊 rating_request 消息
"""
import sys, os, random, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import (
    User, Project, ProjectApplication, Profile, ProfileSkill,
    Skill, SkillCategory, Group, GroupMember, Follow,
    Conversation, ConversationRead, Message, GroupRead
)
from app.utils.helpers import create_token


def _rand_phone():
    return f'199{random.randint(10000000, 99999999)}'


class ProjectMessageEnhancementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def setUp(self):
        db.session.remove()  # 确保每个测试用干净的 session
        self.created_user_ids = []
        self.created_project_ids = []
        self.created_group_ids = []
        self.created_conv_ids = []

    def tearDown(self):
        with self.app.app_context():
            try:
                db.session.rollback()
                if self.created_conv_ids:
                    Message.query.filter(Message.conversation_id.in_(self.created_conv_ids)).delete(synchronize_session=False)
                    ConversationRead.query.filter(ConversationRead.conversation_id.in_(self.created_conv_ids)).delete(synchronize_session=False)
                    Conversation.query.filter(Conversation.id.in_(self.created_conv_ids)).delete(synchronize_session=False)
                if self.created_group_ids:
                    GroupMember.query.filter(GroupMember.group_id.in_(self.created_group_ids)).delete(synchronize_session=False)
                    GroupRead.query.filter(GroupRead.group_id.in_(self.created_group_ids)).delete(synchronize_session=False)
                    Group.query.filter(Group.id.in_(self.created_group_ids)).delete(synchronize_session=False)
                if self.created_project_ids:
                    ProjectApplication.query.filter(ProjectApplication.project_id.in_(self.created_project_ids)).delete(synchronize_session=False)
                    Project.query.filter(Project.id.in_(self.created_project_ids)).delete(synchronize_session=False)
                if self.created_user_ids:
                    uid = self.created_user_ids
                    Follow.query.filter(Follow.follower_id.in_(uid) | Follow.followed_id.in_(uid)).delete(synchronize_session=False)
                    profs = Profile.query.filter(Profile.user_id.in_(uid)).all()
                    prof_ids = [p.id for p in profs]
                    if prof_ids:
                        ProfileSkill.query.filter(ProfileSkill.profile_id.in_(prof_ids)).delete(synchronize_session=False)
                    Profile.query.filter(Profile.user_id.in_(uid)).delete(synchronize_session=False)
                    User.query.filter(User.id.in_(uid)).delete(synchronize_session=False)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f'[tearDown 清理异常] {e}')
            finally:
                db.session.remove()

    def _headers(self, token):
        return {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

    # ---------- 测试1：项目卡片 member_avatars ----------
    def test_01_member_avatars(self):
        with self.app.app_context():
            u1 = User(phone=_rand_phone(), nickname='creator', avatar='a.png')
            u2 = User(phone=_rand_phone(), nickname='member', avatar='b.png')
            db.session.add_all([u1, u2])
            db.session.flush()
            p = Project(user_id=u1.id, title='avatar test', description='d')
            db.session.add(p)
            db.session.flush()
            db.session.add(ProjectApplication(project_id=p.id, user_id=u2.id, status='approved'))
            db.session.commit()
            uid1, pid, uid2 = u1.id, p.id, u2.id
            self.created_user_ids = [u1.id, u2.id]
            self.created_project_ids = [p.id]

        token = create_token(uid1)
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/projects/{pid}', headers=self._headers(token))
            self.assertEqual(r.status_code, 200, r.get_json())
            d = r.get_json()['data']
            self.assertIn('member_avatars', d)
            self.assertEqual(len(d['member_avatars']), 2)
            self.assertEqual(d['member_avatars'][0]['user_id'], uid1)
            self.assertEqual(d['member_avatars'][1]['user_id'], uid2)
            print('[PASS] test_01 member_avatars: 2 个成员头像正确返回')

    # ---------- 测试2：队长 skills + joined_project_count ----------
    def test_02_creator_skills_and_joined_count(self):
        with self.app.app_context():
            u1 = User(phone=_rand_phone(), nickname='creator', avatar='a.png')
            u2 = User(phone=_rand_phone(), nickname='other', avatar='b.png')
            db.session.add_all([u1, u2])
            db.session.flush()
            # 使用已有技能（避免 Skill.creator_id FK 约束问题）
            skill = Skill.query.first()
            if not skill:
                cat = SkillCategory(name='design', code=f'design_{random.randint(1000,9999)}')
                db.session.add(cat)
                db.session.flush()
                skill = Skill(category_id=cat.id, name='UI', creator_id=u1.id)
                db.session.add(skill)
                db.session.flush()
            profile = Profile(user_id=u1.id)
            db.session.add(profile)
            db.session.flush()
            db.session.add(ProfileSkill(profile_id=profile.id, skill_id=skill.id))
            p_other = Project(user_id=u2.id, title='other project', description='d')
            db.session.add(p_other)
            db.session.flush()
            db.session.add(ProjectApplication(project_id=p_other.id, user_id=u1.id, status='approved'))
            p1 = Project(user_id=u1.id, title='mine', description='d')
            db.session.add(p1)
            db.session.commit()
            uid1, pid = u1.id, p1.id
            self.created_user_ids = [u1.id, u2.id]
            self.created_project_ids = [p_other.id, p1.id]
            self._skill_name = skill.name

        token = create_token(uid1)
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/projects/{pid}', headers=self._headers(token))
            self.assertEqual(r.status_code, 200, r.get_json())
            cr = r.get_json()['data']['creator']
            self.assertIn('skills', cr)
            self.assertTrue(len(cr['skills']) >= 1)
            self.assertIn('joined_project_count', cr)
            self.assertEqual(cr['joined_project_count'], 1)
            print('[PASS] test_02 creator skills + joined_project_count 正确')

    # ---------- 测试3：私聊 project_invite ----------
    def test_03_private_project_invite(self):
        with self.app.app_context():
            u1 = User(phone=_rand_phone(), nickname='A', avatar='a.png')
            u2 = User(phone=_rand_phone(), nickname='B', avatar='b.png')
            db.session.add_all([u1, u2])
            db.session.flush()
            db.session.add_all([
                Follow(follower_id=u1.id, followed_id=u2.id),
                Follow(follower_id=u2.id, followed_id=u1.id),
            ])
            p = Project(user_id=u1.id, title='invite project', description='d')
            db.session.add(p)
            db.session.commit()
            uid1, uid2, pid = u1.id, u2.id, p.id
            self.created_user_ids = [u1.id, u2.id]
            self.created_project_ids = [p.id]

        token = create_token(uid1)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/with/{uid2}', headers=self._headers(token))
            self.assertEqual(r.status_code, 200, r.get_json())
            cid = r.get_json()['data']['conversation_id']
            self.created_conv_ids = [cid]
            r = c.post(f'/api/v1/conversations/{cid}/messages',
                       headers=self._headers(token),
                       json={'msg_type': 'project_invite', 'project_id': pid, 'content': 'x'})
            self.assertEqual(r.status_code, 200, r.get_json())
            d = r.get_json()['data']
            self.assertEqual(d['msg_type'], 'project_invite')
            self.assertIn('project', d)
            self.assertEqual(d['project']['project_id'], pid)
            print('[PASS] test_03 私聊 project_invite 消息发送成功')

    # ---------- 测试4：群聊 rating_request ----------
    def test_04_group_rating_request(self):
        with self.app.app_context():
            u1 = User(phone=_rand_phone(), nickname='A', avatar='a.png')
            u2 = User(phone=_rand_phone(), nickname='B', avatar='b.png')
            db.session.add_all([u1, u2])
            db.session.flush()
            g = Group(name='test group', owner_id=u1.id)
            db.session.add(g)
            db.session.flush()
            db.session.add_all([
                GroupMember(group_id=g.id, user_id=u1.id, role='owner'),
                GroupMember(group_id=g.id, user_id=u2.id),
            ])
            p = Project(user_id=u1.id, title='rate project', description='d', status='completed')
            db.session.add(p)
            db.session.commit()
            uid1, gid, pid = u1.id, g.id, p.id
            self.created_user_ids = [u1.id, u2.id]
            self.created_group_ids = [g.id]
            self.created_project_ids = [p.id]

        token = create_token(uid1)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/groups/{gid}/messages',
                       headers=self._headers(token),
                       json={'msg_type': 'rating_request', 'project_id': pid, 'content': 'x'})
            self.assertEqual(r.status_code, 200, r.get_json())
            d = r.get_json()['data']
            self.assertEqual(d['msg_type'], 'rating_request')
            self.assertIn('project', d)
            self.assertEqual(d['project']['project_id'], pid)
            print('[PASS] test_04 群聊 rating_request 消息发送成功')


if __name__ == '__main__':
    unittest.main(verbosity=2)
