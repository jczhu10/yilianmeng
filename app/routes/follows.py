# -*- coding: utf-8 -*-
"""关注关系路由：关注/取消关注/关注状态/关注列表/粉丝列表"""
from flask import Blueprint, request
from app import db
from app.models import Follow, User, Notification
from app.utils.helpers import login_required, success_response, error_response, get_pagination_params

bp = Blueprint('follows', __name__)


# ========== 接口6：关注某人 ==========
@bp.route('/users/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    """关注某人"""
    my_id = request.user.id
    if my_id == user_id:
        return error_response(3005, '不能关注自己')
    target = User.query.get(user_id)
    if not target:
        return error_response(404, '用户不存在', http_code=404)

    existing = Follow.query.filter_by(follower_id=my_id, followed_id=user_id).first()
    if existing:
        return error_response(3006, '已关注该用户')

    follow = Follow(follower_id=my_id, followed_id=user_id)
    db.session.add(follow)

    # 给被关注者发一条互动通知
    n = Notification(
        user_id=user_id,
        type='interaction',
        subtype='follow',
        title='新关注',
        content=f'{request.user.nickname} 关注了你',
        sender_id=my_id,
        related_type='user',
        related_id=my_id
    )
    db.session.add(n)
    db.session.commit()

    # 判断是否互关
    is_mutual = Follow.query.filter_by(follower_id=user_id, followed_id=my_id).first() is not None
    return success_response(data={'is_following': True, 'is_mutual': is_mutual},
                            message='关注成功')


# ========== 接口7：取消关注 ==========
@bp.route('/users/<int:user_id>/follow', methods=['DELETE'])
@login_required
def unfollow_user(user_id):
    """取消关注"""
    my_id = request.user.id
    follow = Follow.query.filter_by(follower_id=my_id, followed_id=user_id).first()
    if not follow:
        return error_response(404, '未关注该用户', http_code=404)
    db.session.delete(follow)
    db.session.commit()
    return success_response(data={'is_following': False}, message='取消关注成功')


# ========== 接口8：关注状态 ==========
@bp.route('/users/<int:user_id>/follow/status', methods=['GET'])
@login_required
def follow_status(user_id):
    """获取关注状态：我是否关注他/他是否关注我/是否互关"""
    my_id = request.user.id
    is_following = Follow.query.filter_by(follower_id=my_id, followed_id=user_id).first() is not None
    is_followed_by = Follow.query.filter_by(follower_id=user_id, followed_id=my_id).first() is not None
    return success_response(data={
        'is_following': is_following,
        'is_followed_by': is_followed_by,
        'is_mutual': is_following and is_followed_by
    })


# ========== 接口9：我的关注列表 ==========
@bp.route('/following', methods=['GET'])
@login_required
def my_following():
    """我关注了谁"""
    my_id = request.user.id
    page, page_size = get_pagination_params()

    q = Follow.query.filter_by(follower_id=my_id).order_by(Follow.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    target_ids = [f.followed_id for f in items]
    users = {u.id: u for u in User.query.filter(User.id.in_(target_ids)).all()} if target_ids else {}

    list_data = []
    for f in items:
        u = users.get(f.followed_id)
        if not u:
            continue
        is_mutual = Follow.query.filter_by(follower_id=f.followed_id, followed_id=my_id).first() is not None
        list_data.append({
            'user_id': u.id,
            'nickname': u.nickname,
            'avatar': u.avatar,
            'bio': u.bio,
            'is_mutual': is_mutual,
            'followed_at': f.created_at.isoformat() if f.created_at else None
        })

    return success_response(data={'list': list_data, 'total': total, 'page': page, 'page_size': page_size})


# ========== 接口10：我的粉丝列表 ==========
@bp.route('/followers', methods=['GET'])
@login_required
def my_followers():
    """谁关注了我"""
    my_id = request.user.id
    page, page_size = get_pagination_params()

    q = Follow.query.filter_by(followed_id=my_id).order_by(Follow.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    target_ids = [f.follower_id for f in items]
    users = {u.id: u for u in User.query.filter(User.id.in_(target_ids)).all()} if target_ids else {}

    list_data = []
    for f in items:
        u = users.get(f.follower_id)
        if not u:
            continue
        is_mutual = Follow.query.filter_by(follower_id=my_id, followed_id=f.follower_id).first() is not None
        list_data.append({
            'user_id': u.id,
            'nickname': u.nickname,
            'avatar': u.avatar,
            'bio': u.bio,
            'is_mutual': is_mutual,
            'followed_at': f.created_at.isoformat() if f.created_at else None
        })

    return success_response(data={'list': list_data, 'total': total, 'page': page, 'page_size': page_size})


# ========== 接口11：关注/粉丝数 ==========
@bp.route('/users/<int:user_id>/follow/stats', methods=['GET'])
def follow_stats(user_id):
    """获取关注数/粉丝数（无需登录）"""
    following_count = Follow.query.filter_by(follower_id=user_id).count()
    followers_count = Follow.query.filter_by(followed_id=user_id).count()
    return success_response(data={
        'following_count': following_count,
        'followers_count': followers_count
    })
