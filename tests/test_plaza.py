# -*- coding: utf-8 -*-
"""广场模块测试（14接口，覆盖4类型作品/6种可见性/推荐推流/关注推流/点赞/评论/转发）"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import User, Follow
from app.utils.helpers import create_token


class PlazaModuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()

        # 准备 5 个用户：A(发布主) B(粉丝) C(互关) D(陌生人) E(官方暂未用)
        suffix = random.randint(10000000, 99999999)
        cls.userA = User(phone=f'1991{suffix}', nickname='广场A', is_new_user=False)
        cls.userA.set_password('Test123456')
        cls.userB = User(phone=f'1992{suffix:08d}', nickname='广场B', is_new_user=False)
        cls.userB.set_password('Test123456')
        cls.userC = User(phone=f'1993{suffix:08d}', nickname='广场C', is_new_user=False)
        cls.userC.set_password('Test123456')
        cls.userD = User(phone=f'1994{suffix:08d}', nickname='广场D', is_new_user=False)
        cls.userD.set_password('Test123456')
        db.session.add_all([cls.userA, cls.userB, cls.userC, cls.userD])
        db.session.commit()

        # 建立关系：
        # B 关注 A  (A粉丝)
        # C 关注 A + A 关注 C  (互关)
        # D 啥都不关注  (陌生人)
        db.session.add_all([
            Follow(follower_id=cls.userB.id, followed_id=cls.userA.id),
            Follow(follower_id=cls.userC.id, followed_id=cls.userA.id),
            Follow(follower_id=cls.userA.id, followed_id=cls.userC.id),
        ])
        db.session.commit()

        cls.tokenA = create_token(cls.userA.id)
        cls.tokenB = create_token(cls.userB.id)
        cls.tokenC = create_token(cls.userC.id)
        cls.tokenD = create_token(cls.userD.id)
        # 提前占位所有用到的 work_id，防止前序用例挂掉后后序 AttributeError
        cls.w_visual = cls.w_video = cls.w_text = cls.w_repost = None
        # 兼容：test_01d 可能失败，04a 推荐 feed 只断言非空非 None 的
        # （断言本身在测试函数里做的不依赖此变量，占位避免 AttributeError）

    def headers(self, token):
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # -------------------- 接口1：创建 4 种 content_type 作品 --------------------
    def test_01a_create_original_visual(self):
        """1. 原创图片+文字（朋友圈 grid 布局）"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'visual',
                'title': '我的九宫格',
                'description': '今天天气不错',
                'files': [f'/uploads/works/{i}.jpg' for i in range(9)],
                'image_layout': 'grid',
                'visibility_type': 'public',
                'location': '北京·故宫',
                'status': 'published',
            })
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            self.assertEqual(d['code'], 200)
            self.assertEqual(d['data']['content_type'], 'original')
            self.assertEqual(d['data']['image_layout'], 'grid')
            self.assertEqual(d['data']['visibility_type'], 'public')
            self.assertEqual(len(d['data']['files']), 9)
            self.assertIsNotNone(d['data']['published_at'])
            self.assertEqual(d['data']['location'], '北京·故宫')
            PlazaModuleTest.w_visual = d['data']['work_id']

    def test_01b_create_original_video(self):
        """2. 原创视频+文字（文字选填，不传 description）"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'video',
                'title': '一分钟vlog',
                'files': ['/uploads/works/vlog.mp4'],
                'cover_url': '/uploads/works/vlog.jpg',
                'visibility_type': 'public',
                'status': 'published',
            })
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            self.assertEqual(d['code'], 200)
            self.assertEqual(d['data']['channel'], 'video')
            self.assertEqual(d['data']['description'], '')
            PlazaModuleTest.w_video = d['data']['work_id']

    def test_01c_create_text_only(self):
        """3. 纯文字作品"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'text_only',
                'text_content': '今天吃了一碗牛肉面，真香！' * 10,
                'visibility_type': 'public',
                'location': '上海·静安寺',
                'status': 'published',
            })
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            self.assertEqual(d['code'], 200)
            self.assertEqual(d['data']['content_type'], 'text_only')
            self.assertIn('今天吃了一碗牛肉面', d['data']['text_content'])
            PlazaModuleTest.w_text = d['data']['work_id']

    def test_01d_create_repost_original_via_create(self):
        """4. 转发作品（直接走 POST /works content_type=repost）"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenB), json={
                'content_type': 'repost',
                'source_work_id': PlazaModuleTest.w_visual,
                'description': '哈哈，拍得好！',
                'visibility_type': 'public',
                'status': 'published',
            })
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            self.assertEqual(d['code'], 200)
            self.assertEqual(d['data']['content_type'], 'repost')
            PlazaModuleTest.w_repost = d['data']['work_id']

    def test_01e_text_only_repost_xor_invalid(self):
        """5. 转发 xor 校验：两个 source 都传 -> 报错"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenB), json={
                'content_type': 'repost',
                'source_work_id': PlazaModuleTest.w_visual,
                'source_project_id': 1,
                'visibility_type': 'public',
                'status': 'published',
            })
            self.assertEqual(r.status_code, 400, r.get_json())
            self.assertNotEqual(r.get_json()['code'], 200)

    # -------------------- 可见性 6 种权限测试 --------------------
    def test_02a_visibility_private(self):
        """A 创建 private 作品；B 详情404 + feed 不出现；A 自己能看见"""
        with self.app.test_client() as c:
            # 创建
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'writing',
                'title': '私人日记',
                'visibility_type': 'private',
                'status': 'published',
            })
            w_priv = r.get_json()['data']['work_id']
            # A 详情 OK
            r2 = c.get(f'/api/v1/works/{w_priv}', headers=self.headers(self.tokenA))
            self.assertEqual(r2.status_code, 200, r2.get_json())
            # B 详情 404
            r3 = c.get(f'/api/v1/works/{w_priv}', headers=self.headers(self.tokenB))
            self.assertEqual(r3.status_code, 404)
            # B feed 里没这条
            r4 = c.get('/api/v1/works/feed?per_page=200', headers=self.headers(self.tokenB))
            ids = [w['work_id'] for w in r4.get_json()['data']['list']]
            self.assertNotIn(w_priv, ids)

    def test_02b_visibility_followers(self):
        """A 建仅粉丝作品；B(粉丝)/C(粉丝)/D(陌生人) 分别可见/可见/404"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'writing',
                'title': '仅粉丝可见',
                'visibility_type': 'followers',
                'status': 'published',
            })
            w = r.get_json()['data']['work_id']
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).status_code, 200)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenC)).status_code, 200)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenD)).status_code, 404)

    def test_02c_visibility_mutual(self):
        """A 建仅互关；C 可见；B(仅单向关注) 404"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'writing',
                'title': '仅互关',
                'visibility_type': 'mutual',
                'status': 'published',
            })
            w = r.get_json()['data']['work_id']
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenC)).status_code, 200)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).status_code, 404)

    def test_02d_visibility_custom_allow(self):
        """白名单：只有 C 可见，B/D 404"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'writing',
                'title': '仅给C看',
                'visibility_type': 'custom_allow',
                'allow_users': [self.userC.id],
                'status': 'published',
            })
            d = r.get_json()
            w = d['data']['work_id']
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenC)).status_code, 200)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).status_code, 404)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenD)).status_code, 404)

    def test_02e_visibility_custom_deny(self):
        """黑名单：B 被禁，其他 C/D 都可见"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'original',
                'channel': 'writing',
                'title': '禁止B看',
                'visibility_type': 'custom_deny',
                'deny_users': [self.userB.id],
                'status': 'published',
            })
            w = r.get_json()['data']['work_id']
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).status_code, 404)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenC)).status_code, 200)
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenD)).status_code, 200)

    # -------------------- 作品详情 7 项显示字段检查 --------------------
    def test_03_detail_7_items(self):
        """详情页必须包含 7 项展示信息：本身/时间/作者/点赞数/评论数/地点 + 可点赞可评论"""
        with self.app.test_client() as c:
            r = c.get(f'/api/v1/works/{PlazaModuleTest.w_visual}', headers=self.headers(self.tokenA))
            d = r.get_json()['data']
            # 1.作品本身
            self.assertEqual(d['content_type'], 'original')
            self.assertEqual(len(d['files']), 9)
            self.assertEqual(d['image_layout'], 'grid')
            # 2.发布时间
            self.assertIsNotNone(d['published_at'])
            # 3.发布账号
            self.assertEqual(d['author']['user_id'], self.userA.id)
            # 4.点赞数  5.评论数
            self.assertIn('like_count', d)
            self.assertIn('comment_count', d)
            # 6.评论区：单独接口可拉
            rc = c.get(f'/api/v1/works/{PlazaModuleTest.w_visual}/comments?page=1&per_page=5',
                       headers=self.headers(self.tokenB))
            self.assertEqual(rc.status_code, 200)
            self.assertIn('list', rc.get_json()['data'])
            # 7.发送地点
            self.assertEqual(d['location'], '北京·故宫')

    # -------------------- 推流两套：推荐 + 关注 --------------------
    def test_04a_feed_recommend(self):
        """推荐 feed 返回含所有新字段 + 权限过滤（A的private作品不出现在B的feed里）"""
        with self.app.test_client() as c:
            # exclude_self=false：保留 B 自己刚才的转发帖，方便与前序测试数据对齐断言
            r = c.get('/api/v1/works/feed?sort=latest&per_page=200&exclude_self=false',
                      headers=self.headers(self.tokenB))
            d = r.get_json()
            self.assertEqual(r.status_code, 200)
            self.assertTrue(d['code'] == 200)
            # 可见项至少有 A 的三个 public（visual/video/text） + B 自己刚才转发的 1 条
            ids = [w['work_id'] for w in d['data']['list']]
            for expected in [PlazaModuleTest.w_visual, PlazaModuleTest.w_video,
                             PlazaModuleTest.w_text, PlazaModuleTest.w_repost]:
                self.assertIn(expected, ids, f'推荐 feed 缺作品#{expected}')
            # 每条都有 published_at / author / is_liked / location / content_type / like_count / comment_count / repost_count
            for it in d['data']['list']:
                for k in ['published_at', 'author', 'is_liked', 'content_type',
                          'like_count', 'comment_count', 'repost_count']:
                    self.assertIn(k, it, f'列表项缺字段 {k}')

    def test_04b_feed_following_only_authors_I_follow(self):
        """关注Tab：B只关注了A，所以作者集合只能是 A（B发过的转发帖自己没关注自己，不出）"""
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/feed/following?per_page=200', headers=self.headers(self.tokenB))
            d = r.get_json()
            self.assertEqual(r.status_code, 200)
            ids = [w['work_id'] for w in d['data']['list']]
            # 应该只看到 A 发布的作品（不是自己转发自己的就排除）
            authors = {w['author']['user_id'] for w in d['data']['list']}
            self.assertEqual(authors, {self.userA.id}, f'关注Tab作者集合应为{{{self.userA.id}}}，实际{authors}')
            # 确认 A 的 public/fans 作品都在里面
            for expected in [PlazaModuleTest.w_visual, PlazaModuleTest.w_video, PlazaModuleTest.w_text]:
                self.assertIn(expected, ids)
            # 排序：published_at 倒序
            ts = [w['published_at'] for w in d['data']['list']]
            self.assertEqual(ts, sorted(ts, reverse=True), '关注Tab应按published_at倒序')

    def test_04c_d_feed_no_auth_for_unknown(self):
        """没有关注任何人的 D，关注 Tab 应为 0 条"""
        with self.app.test_client() as c:
            r = c.get('/api/v1/works/feed/following', headers=self.headers(self.tokenD))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.get_json()['data']['total'], 0)

    # -------------------- 点赞 / 评论 / 转发 --------------------
    def test_05a_like_cancel(self):
        """点赞+取消点赞，like_count 变化正确"""
        with self.app.test_client() as c:
            w = PlazaModuleTest.w_visual
            before = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).get_json()['data']['like_count']
            r = c.post(f'/api/v1/works/{w}/like', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200, r.get_json())
            after_like = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).get_json()['data']['like_count']
            self.assertEqual(after_like, before + 1)
            r = c.delete(f'/api/v1/works/{w}/like', headers=self.headers(self.tokenB))
            self.assertEqual(r.status_code, 200)
            after_cancel = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).get_json()['data']['like_count']
            self.assertEqual(after_cancel, before)

    def test_05b_comment_and_list(self):
        """发表评论 + 拉评论列表"""
        with self.app.test_client() as c:
            w = PlazaModuleTest.w_video
            r = c.post(f'/api/v1/works/{w}/comments', headers=self.headers(self.tokenB),
                       json={'content': '拍的不错，加油！'})
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            # 列表拉出来至少有这条
            rl = c.get(f'/api/v1/works/{w}/comments', headers=self.headers(self.tokenC))
            self.assertEqual(rl.status_code, 200)
            self.assertGreaterEqual(rl.get_json()['data']['total'], 1)
            comments = [x['content'] for x in rl.get_json()['data']['list']]
            self.assertIn('拍的不错，加油！', comments)

    def test_05c_repost_endpoint(self):
        """快捷转发接口 /works/<id>/repost：能成功、原作品 repost_count+1、含 source 快照"""
        with self.app.test_client() as c:
            w = PlazaModuleTest.w_text
            before = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenA)).get_json()['data']['repost_count']
            r = c.post(f'/api/v1/works/{w}/repost', headers=self.headers(self.tokenC),
                       json={'description': '赞同', 'visibility_type': 'public', 'location': '广州'})
            d = r.get_json()
            self.assertEqual(r.status_code, 200, d)
            self.assertEqual(d['code'], 200)
            self.assertEqual(d['data']['content_type'], 'repost')
            self.assertEqual(d['data']['author']['user_id'], self.userC.id)
            self.assertIn('source', d['data'])
            self.assertEqual(d['data']['source']['type'], 'work')
            self.assertEqual(d['data']['source']['data']['work_id'], w)
            after = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenA)).get_json()['data']['repost_count']
            self.assertEqual(after, before + 1, '原作品 repost_count 未 +1')

    # -------------------- 管理：编辑/publish/删除/我的作品 --------------------
    def test_06a_draft_publish_flow(self):
        """草稿创建 → publish 时写入 published_at"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenB), json={
                'content_type': 'text_only',
                'text_content': '我是草稿内容',
                'visibility_type': 'public',
                'status': 'draft',
            })
            d = r.get_json()
            self.assertEqual(d['data']['status'], 'draft')
            self.assertIsNone(d['data']['published_at'])
            w = d['data']['work_id']
            # 发布
            pr = c.post(f'/api/v1/works/{w}/publish', headers=self.headers(self.tokenB))
            self.assertEqual(pr.status_code, 200)
            after = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).get_json()['data']
            self.assertEqual(after['status'], 'published')
            self.assertIsNotNone(after['published_at'])

    def test_06b_edit_update_fields(self):
        """编辑：更新 title + description + location"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenC), json={
                'content_type': 'text_only', 'text_content': '第一版', 'visibility_type': 'public',
                'status': 'published',
            })
            w = r.get_json()['data']['work_id']
            # 编辑
            pu = c.put(f'/api/v1/works/{w}', headers=self.headers(self.tokenC),
                       json={'title': '第二版标题', 'description': '补充说明', 'location': '深圳'})
            self.assertEqual(pu.status_code, 200, pu.get_json())
            after = c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenC)).get_json()['data']
            self.assertEqual(after['title'], '第二版标题')
            self.assertEqual(after['description'], '补充说明')
            self.assertEqual(after['location'], '深圳')
            self.assertEqual(after['text_content'], '第一版')  # 没改的字段保留

    def test_06c_delete_soft_and_invisible(self):
        """软删除作品后：自己在 /mine?status=deleted 可见；别人 feed/详情均 404"""
        with self.app.test_client() as c:
            r = c.post('/api/v1/works/', headers=self.headers(self.tokenC), json={
                'content_type': 'text_only', 'text_content': '即将删除', 'visibility_type': 'public',
                'status': 'published',
            })
            w = r.get_json()['data']['work_id']
            dl = c.delete(f'/api/v1/works/{w}', headers=self.headers(self.tokenC))
            self.assertEqual(dl.status_code, 200, dl.get_json())
            # 别人看 404
            self.assertEqual(c.get(f'/api/v1/works/{w}', headers=self.headers(self.tokenB)).status_code, 404)
            # 作者自己 status=deleted 能看见
            rmine = c.get('/api/v1/works/mine?status=deleted', headers=self.headers(self.tokenC))
            ids = [x['work_id'] for x in rmine.get_json()['data']['list']]
            self.assertIn(w, ids)

    # -------------------- 我的作品 --------------------
    def test_06d_mine_ordering(self):
        """mine 列表排序：published 作品按 published_at DESC 在前，草稿在后面"""
        with self.app.test_client() as c:
            # A 创建一个草稿
            draft = c.post('/api/v1/works/', headers=self.headers(self.tokenA), json={
                'content_type': 'text_only', 'text_content': '草稿哦', 'visibility_type': 'public',
                'status': 'draft',
            }).get_json()['data']['work_id']
            r = c.get('/api/v1/works/mine?page=1&per_page=50', headers=self.headers(self.tokenA))
            items = r.get_json()['data']['list']
            # 找 draft 和 之前发布的 作品的前后位置
            draft_idx = next((i for i, x in enumerate(items) if x['work_id'] == draft), None)
            pub_idx = next((i for i, x in enumerate(items) if x['work_id'] == PlazaModuleTest.w_visual), None)
            self.assertIsNotNone(draft_idx)
            self.assertIsNotNone(pub_idx)
            self.assertGreater(draft_idx, pub_idx, '草稿 published_at=NULL 应排在已发布作品之后')

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        db.session.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
