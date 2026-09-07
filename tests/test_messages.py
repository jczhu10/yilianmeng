# -*- coding: utf-8 -*-
"""消息模块接口测试：通知/关注/私聊/群聊"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import User, Follow, Notification, Conversation, ConversationRead, Message, Group, GroupMember
from app.utils.helpers import create_token
import unittest


class MessageModuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        cls.user_a = User(phone=f'139{random.randint(10000000,99999999)}',
                          nickname='测试A', is_new_user=False)
        cls.user_a.set_password('Test123456')
        cls.user_b = User(phone=f'138{random.randint(10000000,99999999):08d}',
                          nickname='测试B', is_new_user=False)
        cls.user_b.set_password('Test123456')
        db.session.add_all([cls.user_a, cls.user_b])
        db.session.commit()
        cls.token_a = create_token(cls.user_a.id)
        cls.token_b = create_token(cls.user_b.id)

    @classmethod
    def tearDownClass(cls):
        try:
            for u in [cls.user_a, cls.user_b]:
                Follow.query.filter((Follow.follower_id==u.id)|(Follow.followed_id==u.id)).delete()
                Notification.query.filter_by(user_id=u.id).delete()
                # 先查出会话ID，按顺序删除 messages → reads → conversations
                convs = Conversation.query.filter(
                    (Conversation.user1_id==u.id)|(Conversation.user2_id==u.id)
                ).all()
                conv_ids = [cv.id for cv in convs]
                if conv_ids:
                    Message.query.filter(Message.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
                    ConversationRead.query.filter(ConversationRead.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
                    Conversation.query.filter(Conversation.id.in_(conv_ids)).delete(synchronize_session=False)
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

    def test_01_get_unread_counts(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/notifications/unread-counts', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertIn('official', data['data'])
            self.assertIn('interaction', data['data'])
            self.assertIn('todo', data['data'])
            print('[OK] 1 未读数字:', data['data'])

    def test_02_follow_user(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/users/{self.user_b.id}/follow', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertTrue(data['data']['is_following'])
            print('[OK] 2 A关注B:', data['data'])

    def test_03_follow_status(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/users/{self.user_b.id}/follow/status', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertTrue(data['data']['is_following'])
            self.assertFalse(data['data']['is_mutual'])
            print('[OK] 3 关注状态:', data['data'])

    def test_04_follow_stats(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/users/{self.user_a.id}/follow/stats')
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['following_count'], 1)
            print('[OK] 4 关注数:', data['data'])

    def test_05_list_following(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/following', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 5 关注列表:', data['data']['total'])

    def test_06_list_followers(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/followers', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 6 粉丝列表:', data['data']['total'])

    def test_07_get_conversation_with_b(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/with/{self.user_b.id}', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.conv_id = data['data']['conversation_id']
            print('[OK] 7 会话ID:', self.conv_id)

    def test_08_send_message_single_follow(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/{self.conv_id}/messages',
                       headers=self.headers(self.token_a),
                       json={'msg_type': 'text', 'content': '你好B'})
            self.assertEqual(r.status_code, 200)
            print('[OK] 8 单关注发1条成功')

    def test_09_send_message_blocked(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/{self.conv_id}/messages',
                       headers=self.headers(self.token_a),
                       json={'msg_type': 'text', 'content': '再发一条'})
            data = r.get_json()
            self.assertEqual(data['code'], 3002)
            print('[OK] 9 单关注第2条被拒:', data['message'])

    def test_10_b_reply_then_a_can_send(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/{self.conv_id}/messages',
                       headers=self.headers(self.token_b),
                       json={'msg_type': 'text', 'content': '你好A'})
            self.assertEqual(r.status_code, 200)
            r = c.post(f'/api/v1/conversations/{self.conv_id}/messages',
                       headers=self.headers(self.token_a),
                       json={'msg_type': 'text', 'content': '收到'})
            self.assertEqual(r.status_code, 200)
            print('[OK] 10 B回复后A可再发')

    def test_11_list_messages(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/conversations/{self.conv_id}/messages', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 3)
            print('[OK] 11 消息记录:', data['data']['total'])

    def test_12_list_conversations(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/conversations/', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print('[OK] 12 联系人列表:', data['data']['total'])

    def test_13_mark_conversation_read(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/{self.conv_id}/read', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(data['data']['unread_count'], 0)
            print('[OK] 13 标记已读:', data['data'])

    def test_14_official_conversation(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/conversations/official', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertIn('conversation_id', data['data'])
            print('[OK] 14 官方会话:', data['data'].get('official', {}).get('nickname'))

    def test_15_list_interaction(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/notifications/interaction', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 15 互动消息:', data['data']['total'])

    def test_16_mark_all_read(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/notifications/read-all',
                       headers=self.headers(self.token_b), json={'type': 'interaction'})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print('[OK] 16 批量已读:', data['data'])

    def test_17_create_group(self):
        with self.app.test_client() as c:
            r = c.post('/api/v1/groups/', headers=self.headers(self.token_a),
                       json={'name': '测试群', 'member_ids': [self.user_b.id]})
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.__class__.group_id = data['data']['group_id']
            print('[OK] 17 建群:', self.group_id)

    def test_18_list_groups(self):
        with self.app.test_client() as c:
            r = c.get('/api/v1/groups/', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 18 群列表:', data['data']['total'])

    def test_19_send_group_message(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/groups/{self.group_id}/messages',
                       headers=self.headers(self.token_a),
                       json={'msg_type': 'text', 'content': '群里大家好'})
            self.assertEqual(r.status_code, 200)
            print('[OK] 19 群发消息')

    def test_20_list_group_messages(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/groups/{self.group_id}/messages', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 1)
            print('[OK] 20 群消息:', data['data']['total'])

    def test_21_list_group_members(self):
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/groups/{self.group_id}/members', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(data['data']['total'], 2)
            print('[OK] 21 群成员:', data['data']['total'])

    def test_22_mark_group_read(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/groups/{self.group_id}/read', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print('[OK] 22 群已读:', data['data'])

    def test_23_mutual_follow_free_send(self):
        with self.app.test_client() as c:
            c.post(f'/api/v1/users/{self.user_a.id}/follow', headers=self.headers(self.token_b))
        with self.app.test_client() as c:
            for i in range(3):
                r = c.post(f'/api/v1/conversations/{self.conv_id}/messages',
                           headers=self.headers(self.token_a),
                           json={'msg_type': 'text', 'content': f'互关{i}'})
                self.assertEqual(r.status_code, 200)
        print('[OK] 23 互关后自由发3条')

    def test_24_stranger_blocked(self):
        user_c = User(phone=f'137{random.randint(10000000,99999999)}',
                      nickname='测试C', is_new_user=False)
        user_c.set_password('Test123456')
        db.session.add(user_c)
        db.session.commit()
        token_c = create_token(user_c.id)
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/conversations/with/{self.user_b.id}', headers=self.headers(token_c))
            conv_id = r.get_json()['data']['conversation_id']
            r = c.post(f'/api/v1/conversations/{conv_id}/messages',
                       headers=self.headers(token_c),
                       json={'msg_type': 'text', 'content': '陌生消息'})
            data = r.get_json()
            self.assertEqual(data['code'], 3001)
            print('[OK] 24 陌生人被拒:', data['message'])
        Follow.query.filter((Follow.follower_id==user_c.id)|(Follow.followed_id==user_c.id)).delete()
        convs_c = Conversation.query.filter(
            (Conversation.user1_id==user_c.id)|(Conversation.user2_id==user_c.id)
        ).all()
        conv_ids_c = [cv.id for cv in convs_c]
        if conv_ids_c:
            Message.query.filter(Message.conversation_id.in_(conv_ids_c)).delete(synchronize_session=False)
            ConversationRead.query.filter(ConversationRead.conversation_id.in_(conv_ids_c)).delete(synchronize_session=False)
            Conversation.query.filter(Conversation.id.in_(conv_ids_c)).delete(synchronize_session=False)
        db.session.delete(user_c)
        db.session.commit()

    def test_25_leave_group(self):
        with self.app.test_client() as c:
            r = c.post(f'/api/v1/groups/{self.group_id}/leave', headers=self.headers(self.token_b))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print('[OK] 25 B退群:', data['message'])

    def test_26_unfollow(self):
        with self.app.test_client() as c:
            r = c.delete(f'/api/v1/users/{self.user_b.id}/follow', headers=self.headers(self.token_a))
            data = r.get_json()
            self.assertEqual(r.status_code, 200)
            print('[OK] 26 取消关注:', data['message'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
