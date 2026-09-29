# -*- coding: utf-8 -*-
"""艺联盟 测试种子数据（前端联调用）

功能：
  - 创建 2 个互关测试账号（含 token）
  - 创建 1 个群组（含 2 名成员）
  - 创建 3 条已发布作品（覆盖 writing/visual/video 三种 channel）
  - 创建 1 个招募中项目（含 1 条 pending 申请）
  - 创建若干互动/待办通知
  - 自动建技能分类+技能+风格标签+评价标签字典

用法：
  cd <项目根>
  python scripts/seed_test_data.py

注意：脚本会先清理这些手机号对应的旧数据再写入，可重复执行。
"""
import os
import sys
import random
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import (
    User, Profile, SkillCategory, Skill, StyleTag, RatingTag,
    Work, WorkRepost, WorkVisibilityRule, Follow,
    Project, ProjectApplication, ProjectRequiredSkill,
    Conversation, ConversationRead, Group, GroupMember, GroupRead,
    Notification, Like, Comment,
)
from app.utils.helpers import create_token

# 固定测试账号（便于前端记忆）
PHONE_A = '15500000001'
PHONE_B = '15500000002'
PASSWORD = 'Pass1234'


def clean_old():
    """清理旧测试数据"""
    users = User.query.filter(User.phone.in_([PHONE_A, PHONE_B])).all()
    uids = [u.id for u in users]
    if not uids:
        return
    # 通知
    Notification.query.filter(Notification.user_id.in_(uids)).delete(synchronize_session=False)
    # 点赞
    Like.query.filter(Like.user_id.in_(uids)).delete(synchronize_session=False)
    # 评论
    Comment.query.filter(Comment.user_id.in_(uids)).delete(synchronize_session=False)
    # 作品可见性规则
    wids = [w.id for w in Work.query.filter(Work.user_id.in_(uids)).all()]
    if wids:
        WorkVisibilityRule.query.filter(WorkVisibilityRule.work_id.in_(wids)).delete(synchronize_session=False)
        WorkRepost.query.filter(WorkRepost.work_id.in_(wids)).delete(synchronize_session=False)
    # 作品
    Work.query.filter(Work.user_id.in_(uids)).delete(synchronize_session=False)
    # 项目申请
    ProjectApplication.query.filter(ProjectApplication.user_id.in_(uids)).delete(synchronize_session=False)
    ProjectApplication.query.filter(ProjectApplication.project_id.in_(
        [p.id for p in Project.query.filter(Project.user_id.in_(uids)).all()]
    )).delete(synchronize_session=False)
    ProjectRequiredSkill.query.filter(ProjectRequiredSkill.project_id.in_(
        [p.id for p in Project.query.filter(Project.user_id.in_(uids)).all()]
    )).delete(synchronize_session=False)
    # 项目
    Project.query.filter(Project.user_id.in_(uids)).delete(synchronize_session=False)
    # 关注
    Follow.query.filter(db.or_(Follow.follower_id.in_(uids), Follow.followed_id.in_(uids))).delete(synchronize_session=False)
    # 会话已读
    conv_ids = [c.id for c in Conversation.query.filter(
        db.or_(Conversation.user1_id.in_(uids), Conversation.user2_id.in_(uids))
    ).all()]
    if conv_ids:
        ConversationRead.query.filter(ConversationRead.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
    # 会话
    Conversation.query.filter(db.or_(Conversation.user1_id.in_(uids), Conversation.user2_id.in_(uids))).delete(synchronize_session=False)
    # 群成员已读
    gids = [g.id for g in Group.query.filter(Group.owner_id.in_(uids)).all()]
    if gids:
        GroupRead.query.filter(GroupRead.group_id.in_(gids)).delete(synchronize_session=False)
        GroupMember.query.filter(GroupMember.group_id.in_(gids)).delete(synchronize_session=False)
    # 群
    Group.query.filter(Group.owner_id.in_(uids)).delete(synchronize_session=False)
    # 档案
    Profile.query.filter(Profile.user_id.in_(uids)).delete(synchronize_session=False)
    # 用户
    User.query.filter(User.id.in_(uids)).delete(synchronize_session=False)
    db.session.commit()
    print(f'已清理 {len(uids)} 个旧测试用户及其关联数据')


def ensure_dicts():
    """确保字典数据存在"""
    # 技能分类
    cats = SkillCategory.query.all()
    if not cats:
        c1 = SkillCategory(name='写作', code='writing', sort_order=1)
        c2 = SkillCategory(name='视觉', code='visual', sort_order=2)
        c3 = SkillCategory(name='影视', code='video', sort_order=3)
        c4 = SkillCategory(name='声音', code='voice', sort_order=4)
        db.session.add_all([c1, c2, c3, c4])
        db.session.flush()
        cats = [c1, c2, c3, c4]
    # 技能
    if Skill.query.count() == 0:
        skills = []
        for c in cats:
            for i in range(1, 3):
                skills.append(Skill(category_id=c.id, name=f'{c.name}技能{i}', sort_order=i))
        db.session.add_all(skills)
        db.session.flush()
    # 风格标签
    if StyleTag.query.count() == 0:
        for i, name in enumerate(['文艺', '极简', '复古', '前卫', '抒情']):
            db.session.add(StyleTag(name=name, sort_order=i, is_active=True))
    # 评价标签
    if RatingTag.query.count() == 0:
        for name, t in [('沟通顺畅', 'positive'), ('交付及时', 'positive'),
                         ('态度敷衍', 'negative'), ('能力不足', 'negative'),
                         ('中规中矩', 'neutral')]:
            db.session.add(RatingTag(name=name, category=t, is_active=True, sort_order=0))
    db.session.commit()
    print('字典数据就绪')


def make_user(phone, nickname, identity, bio, avatar=''):
    u = User(phone=phone, nickname=nickname, avatar=avatar, bio=bio, is_new_user=False)
    u.set_password(PASSWORD)
    db.session.add(u)
    db.session.flush()
    p = Profile(user_id=u.id, identity=identity)
    db.session.add(p)
    db.session.flush()
    return u


def main():
    with app.app_context():
        db.create_all()
        clean_old()
        ensure_dicts()

        # ---- 用户 ----
        userA = make_user(PHONE_A, '艺小A', '学生', '美术学院大三，主修视觉传达', avatar='https://cdn.example.com/a.png')
        userB = make_user(PHONE_B, '艺小B', '艺术相关工作者', '独立插画师，3 年商稿经验', avatar='https://cdn.example.com/b.png')
        db.session.flush()

        # 互关
        db.session.add(Follow(follower_id=userA.id, followed_id=userB.id))
        db.session.add(Follow(follower_id=userB.id, followed_id=userA.id))
        userA.following_count = 1; userA.follower_count = 1
        userB.following_count = 1; userB.follower_count = 1
        db.session.flush()

        # ---- 作品 3 条（不同 channel）----
        w1 = Work(user_id=userA.id, title='《晨光》散文随笔', description='记录清晨第一缕光的感受',
                  channel='writing', content_type='original', status='published',
                  visibility_type='public', image_layout='flip', cover_url='',
                  files='[]', collaborators='[]', skill_tags='[]',
                  published_at=datetime.datetime.utcnow())
        w2 = Work(user_id=userB.id, title='《城市切片》插画', description='城市光影系列第 3 张',
                  channel='visual', content_type='original', status='published',
                  visibility_type='public', image_layout='grid', cover_url='https://cdn.example.com/w2.png',
                  files='["https://cdn.example.com/w2_1.png","https://cdn.example.com/w2_2.png"]',
                  collaborators='[]', skill_tags='[]',
                  published_at=datetime.datetime.utcnow())
        w3 = Work(user_id=userA.id, title='《一段日常》Vlog', description='周末 vlog',
                  channel='video', content_type='original', status='published',
                  visibility_type='followers', image_layout='flip', cover_url='https://cdn.example.com/w3.png',
                  files='["https://cdn.example.com/w3.mp4"]',
                  collaborators='[]', skill_tags='[]',
                  published_at=datetime.datetime.utcnow())
        db.session.add_all([w1, w2, w3])
        db.session.flush()
        userA.work_count = 2
        userB.work_count = 1

        # 给 w2 一条点赞 + 评论（来自 A）
        db.session.add(Like(user_id=userA.id, work_id=w2.id))
        w2.like_count = 1
        db.session.add(Comment(user_id=userA.id, work_id=w2.id, content='画风太赞了！', is_deleted=False))
        w2.comment_count = 1

        # 通知 B：有人点赞
        db.session.add(Notification(
            user_id=userB.id, type='interaction', subtype='like',
            title='收到一条点赞', content='艺小A 赞了你的作品《城市切片》插画',
            sender_id=userA.id, related_type='work', related_id=w2.id, is_read=False
        ))
        # 通知 B：有人评论
        db.session.add(Notification(
            user_id=userB.id, type='interaction', subtype='comment',
            title='收到一条评论', content='艺小A 评论了你的作品：画风太赞了！',
            sender_id=userA.id, related_type='work', related_id=w2.id, is_read=False
        ))

        # ---- 群组 ----
        g = Group(name='艺联萌联调群', owner_id=userA.id,
                  avatar='https://cdn.example.com/g.png')
        db.session.add(g)
        db.session.flush()
        db.session.add(GroupMember(group_id=g.id, user_id=userA.id, role='owner', nickname='艺小A(队长)'))
        db.session.add(GroupMember(group_id=g.id, user_id=userB.id, role='member', nickname='艺小B'))
        g.member_count = 2
        db.session.flush()

        # ---- 项目（招募中）+ 申请 ----
        proj = Project(
            user_id=userA.id, title='校园文创周边设计招募', description='招 2 名插画师做校园文创',
            mode='paid', budget=2000, deadline=datetime.datetime(2026, 12, 31, 23, 59, 59),
            max_members=3, cover_url='https://cdn.example.com/p.png', topic='设计',
            required_level=1, required_project_count=0, contact_visible=True,
            status='recruiting'
        )
        db.session.add(proj)
        db.session.flush()
        userA.project_count = 1

        # 项目所需技能
        skills = Skill.query.limit(2).all()
        for i, s in enumerate(skills):
            db.session.add(ProjectRequiredSkill(
                project_id=proj.id, skill_id=s.id, required_count=1, filled_count=0
            ))

        # B 发起 1 条 pending 申请
        app_obj = ProjectApplication(
            project_id=proj.id, user_id=userB.id, status='pending',
            message='我有 3 年插画经验，可以试试'
        )
        db.session.add(app_obj)

        # 待办通知给 A：有人申请你的项目
        db.session.add(Notification(
            user_id=userA.id, type='todo', subtype='apply',
            title='收到一条项目申请', content='艺小B 申请加入你的项目《校园文创周边设计招募》',
            sender_id=userB.id, related_type='project', related_id=proj.id, is_read=False
        ))

        db.session.commit()

        tokenA = create_token(userA.id)
        tokenB = create_token(userB.id)

        print('=' * 60)
        print('种子数据写入成功！')
        print('=' * 60)
        print(f'测试账号 A:  手机号={PHONE_A}  密码={PASSWORD}')
        print(f'  user_id={userA.id}  token={tokenA}')
        print(f'测试账号 B:  手机号={PHONE_B}  密码={PASSWORD}')
        print(f'  user_id={userB.id}  token={tokenB}')
        print('-' * 60)
        print(f'群组: id={g.id}  name={g.name}')
        print(f'作品: w1(id={w1.id},writing)  w2(id={w2.id},visual)  w3(id={w3.id},video)')
        print(f'项目: id={proj.id}  status=recruiting  budget={proj.budget}')
        print(f'申请: id={app_obj.id}  status=pending  applicant=B')
        print('=' * 60)
        print('后端启动: python app.py  (默认 0.0.0.0:8080, debug=True)')
        print('send-code 接口会返回 dev_code，前端无需真实短信即可注册/登录任意号')
        print('=' * 60)


if __name__ == '__main__':
    main()
