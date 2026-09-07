# -*- coding: utf-8 -*-
"""通知模块路由：官方/互动/待办通知"""
from flask import Blueprint, request
from app import db
from app.models import Notification, User, Conversation, ConversationRead, Work
from app.utils.helpers import login_required, success_response, error_response, get_pagination_params

bp = Blueprint('notifications', __name__)


# ========== 接口1：获取未读数字 ==========
@bp.route('/unread-counts', methods=['GET'])
@login_required
def get_unread_counts():
    """返回消息首页三个 Tab 的未读数字：官方/互动/待办"""
    user_id = request.user.id

    # 互动未读
    interaction_count = Notification.query.filter_by(
        user_id=user_id, type='interaction', is_read=False
    ).count()

    # 待办未读
    todo_count = Notification.query.filter_by(
        user_id=user_id, type='todo', is_read=False
    ).count()

    # 官方未读（与官方账号会话的未读数）
    official = User.query.filter_by(is_official=True).first()
    official_count = 0
    if official:
        u1, u2 = sorted([user_id, official.id])
        conv = Conversation.query.filter_by(user1_id=u1, user2_id=u2).first()
        if conv:
            cr = ConversationRead.query.filter_by(
                conversation_id=conv.id, user_id=user_id
            ).first()
            if cr:
                official_count = cr.unread_count

    return success_response(data={
        'official': official_count,
        'interaction': interaction_count,
        'todo': todo_count
    })


# ========== 接口2：互动消息列表 ==========
@bp.route('/interaction', methods=['GET'])
@login_required
def list_interaction():
    """互动消息列表（点赞/评论/关注），含时间/内容/操作账号/被操作对象"""
    user_id = request.user.id
    page, page_size = get_pagination_params()
    subtype = request.args.get('subtype')

    q = Notification.query.filter_by(user_id=user_id, type='interaction')
    if subtype:
        q = q.filter_by(subtype=subtype)
    q = q.order_by(Notification.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    # 批量查发送者
    sender_ids = list({n.sender_id for n in items if n.sender_id})
    senders = {u.id: u for u in User.query.filter(User.id.in_(sender_ids)).all()} if sender_ids else {}

    # 批量查被操作作品（related_type=work）
    work_ids = list({n.related_id for n in items if n.related_type == 'work'})
    works = {w.id: w for w in Work.query.filter(Work.id.in_(work_ids)).all()} if work_ids else {}

    list_data = []
    for n in items:
        sender = senders.get(n.sender_id) if n.sender_id else None
        # 被操作对象摘要
        related_work = None
        if n.related_type == 'work' and n.related_id in works:
            w = works[n.related_id]
            related_work = {
                'work_id': w.id,
                'title': w.title,
                'cover_url': w.cover_url,
                'files': (w.files or [])[:1]
            }
        list_data.append({
            'notification_id': n.id,
            'subtype': n.subtype,
            'title': n.title,
            'content': n.content,
            'sender': {
                'user_id': sender.id,
                'nickname': sender.nickname,
                'avatar': sender.avatar
            } if sender else None,
            'related_type': n.related_type,
            'related_id': n.related_id,
            'related_work': related_work,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        })

    return success_response(data={
        'list': list_data,
        'total': total,
        'page': page,
        'page_size': page_size
    })


# ========== 接口3：待办事项列表 ==========
@bp.route('/todo', methods=['GET'])
@login_required
def list_todo():
    """待办事项列表，含时间/内容"""
    user_id = request.user.id
    page, page_size = get_pagination_params()
    subtype = request.args.get('subtype')

    q = Notification.query.filter_by(user_id=user_id, type='todo')
    if subtype:
        q = q.filter_by(subtype=subtype)
    q = q.order_by(Notification.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    list_data = [{
        'notification_id': n.id,
        'subtype': n.subtype,
        'title': n.title,
        'content': n.content,
        'related_type': n.related_type,
        'related_id': n.related_id,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in items]

    return success_response(data={
        'list': list_data,
        'total': total,
        'page': page,
        'page_size': page_size
    })


# ========== 接口4：标记单条已读 ==========
@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """标记单条通知已读"""
    user_id = request.user.id
    n = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not n:
        return error_response(404, '通知不存在', http_code=404)
    n.is_read = True
    db.session.commit()
    return success_response(message='已标记为已读')


# ========== 接口5：批量已读 ==========
@bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """批量标记通知已读，type 可选 interaction/todo，不传全部"""
    user_id = request.user.id
    data = request.get_json() or {}
    n_type = data.get('type')

    q = Notification.query.filter_by(user_id=user_id, is_read=False)
    if n_type:
        q = q.filter_by(type=n_type)
    count = q.update({Notification.is_read: True}, synchronize_session=False)
    db.session.commit()
    return success_response(data={'updated_count': count}, message='批量已读成功')
