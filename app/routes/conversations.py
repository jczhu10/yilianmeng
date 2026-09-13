# -*- coding: utf-8 -*-
"""私聊会话路由：联系人列表/获取会话/消息记录/发消息/已读/官方会话"""
from flask import Blueprint, request
from app import db
from app.models import (Conversation, ConversationRead, Message, User, Follow, Project)
from app.utils.helpers import (login_required, success_response, error_response,
                               get_pagination_params)
from datetime import datetime

bp = Blueprint('conversations', __name__)

ALLOWED_MSG_TYPES = {'text', 'image', 'voice', 'file', 'project_invite'}


def _get_or_create_conversation(user1_id, user2_id):
    """获取或创建两个用户的会话（保证 user1_id < user2_id）"""
    u1, u2 = sorted([user1_id, user2_id])
    conv = Conversation.query.filter_by(user1_id=u1, user2_id=u2).first()
    if not conv:
        conv = Conversation(user1_id=u1, user2_id=u2)
        db.session.add(conv)
        db.session.flush()
        # 为双方创建未读记录
        db.session.add(ConversationRead(conversation_id=conv.id, user_id=u1, unread_count=0))
        db.session.add(ConversationRead(conversation_id=conv.id, user_id=u2, unread_count=0))
        db.session.commit()
    return conv


def _check_send_permission(sender_id, receiver_id, conversation_id):
    """检查发消息权限：返回 (can_send, error_code, error_msg)
    规则：
    - 接收方是官方账号 → 自由发
    - 互关 → 自由发
    - 单方面关注 → A 已发数 <= B 已发数 + 1
    - 陌生人 → 拒绝
    """
    receiver = User.query.get(receiver_id)
    if receiver and receiver.is_official:
        return True, None, None

    i_follow = Follow.query.filter_by(follower_id=sender_id, followed_id=receiver_id).first()
    follows_me = Follow.query.filter_by(follower_id=receiver_id, followed_id=sender_id).first()

    # 互关
    if i_follow and follows_me:
        return True, None, None

    # 陌生人（互不关注）
    if not i_follow and not follows_me:
        return False, 3001, '陌生人不能发消息，请先关注对方'

    # 单方面关注（任一方向）：sender 已发 <= receiver 已发 + 1
    sent_by_me = Message.query.filter_by(
        conversation_id=conversation_id, sender_id=sender_id
    ).count()
    sent_by_other = Message.query.filter_by(
        conversation_id=conversation_id, sender_id=receiver_id
    ).count()
    if sent_by_me >= sent_by_other + 1:
        return False, 3002, '单方面关注只能发一条，请等待对方回复或互关'
    return True, None, None


# ========== 接口12：联系人列表 ==========
@bp.route('/', methods=['GET'])
@login_required
def list_conversations():
    """最近联系人列表（排除官方账号，官方走 /conversations/official）"""
    my_id = request.user.id
    page, page_size = get_pagination_params()

    q = Conversation.query.filter(
        db.or_(Conversation.user1_id == my_id, Conversation.user2_id == my_id)
    ).order_by(Conversation.last_message_at.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    # 批量查对方用户
    contact_ids = []
    for c in items:
        other_id = c.user2_id if c.user1_id == my_id else c.user1_id
        contact_ids.append(other_id)
    users = {u.id: u for u in User.query.filter(User.id.in_(contact_ids)).all()} if contact_ids else {}

    # 批量查未读
    conv_ids = [c.id for c in items]
    reads = {}
    if conv_ids:
        for cr in ConversationRead.query.filter(
            ConversationRead.conversation_id.in_(conv_ids),
            ConversationRead.user_id == my_id
        ).all():
            reads[cr.conversation_id] = cr

    list_data = []
    for c in items:
        other_id = c.user2_id if c.user1_id == my_id else c.user1_id
        u = users.get(other_id)
        if not u or u.is_official:
            continue  # 排除官方账号
        cr = reads.get(c.id)
        list_data.append({
            'conversation_id': c.id,
            'contact': {
                'user_id': u.id,
                'nickname': u.nickname,
                'avatar': u.avatar,
                'is_official': False
            },
            'last_message': c.last_message_content or '',
            'last_message_at': c.last_message_at.isoformat() if c.last_message_at else None,
            'unread_count': cr.unread_count if cr else 0
        })

    return success_response(data={'list': list_data, 'total': len(list_data),
                                  'page': page, 'page_size': page_size})


# ========== 接口13：获取/创建与某用户的会话 ==========
@bp.route('/with/<int:user_id>', methods=['POST'])
@login_required
def get_or_create_with_user(user_id):
    """点击联系人/用户主页发消息时调用，拿 conversation_id"""
    my_id = request.user.id
    if my_id == user_id:
        return error_response(3003, '不能和自己对话')
    target = User.query.get(user_id)
    if not target:
        return error_response(404, '用户不存在', http_code=404)
    conv = _get_or_create_conversation(my_id, user_id)
    return success_response(data={'conversation_id': conv.id})


# ========== 接口14：私聊消息记录 ==========
@bp.route('/<int:conversation_id>/messages', methods=['GET'])
@login_required
def list_messages(conversation_id):
    """私聊消息记录（分页，按时间倒序）"""
    my_id = request.user.id
    conv = Conversation.query.get(conversation_id)
    if not conv or (conv.user1_id != my_id and conv.user2_id != my_id):
        return error_response(3003, '会话不存在或无权访问', http_code=404)

    page, page_size = get_pagination_params()
    q = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    sender_ids = list({m.sender_id for m in items})
    senders = {u.id: u for u in User.query.filter(User.id.in_(sender_ids)).all()} if sender_ids else {}

    list_data = [{
        'message_id': m.id,
        'sender_id': m.sender_id,
        'sender': {
            'user_id': senders[m.sender_id].id,
            'nickname': senders[m.sender_id].nickname,
            'avatar': senders[m.sender_id].avatar
        } if m.sender_id in senders else None,
        'msg_type': m.msg_type,
        'content': m.content,
        'file_name': m.file_name,
        'file_size': m.file_size,
        'voice_duration': m.voice_duration,
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in items]

    return success_response(data={'list': list_data, 'total': total,
                                 'page': page, 'page_size': page_size})


# ========== 接口15：发送私聊消息 ==========
@bp.route('/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送私聊消息，含关注关系校验"""
    my_id = request.user.id
    conv = Conversation.query.get(conversation_id)
    if not conv or (conv.user1_id != my_id and conv.user2_id != my_id):
        return error_response(3003, '会话不存在或无权访问', http_code=404)

    data = request.get_json() or {}
    msg_type = data.get('msg_type')
    content = data.get('content')
    if not msg_type or not content:
        return error_response(400, 'msg_type 和 content 不能为空')
    if msg_type not in ALLOWED_MSG_TYPES:
        return error_response(3007, f'msg_type 暂不支持：{msg_type}')

    # 校验必填附加字段
    if msg_type == 'file' and not data.get('file_name'):
        return error_response(400, 'file 类型必须传 file_name')
    if msg_type == 'voice' and data.get('voice_duration') is None:
        return error_response(400, 'voice 类型必须传 voice_duration')
    if msg_type == 'project_invite':
        pid = data.get('project_id')
        if not pid:
            return error_response(400, 'project_invite 必须传 project_id')
        proj = Project.query.get(pid)
        if not proj:
            return error_response(5001, '项目不存在', http_code=404)

    # 关注关系校验
    receiver_id = conv.user2_id if conv.user1_id == my_id else conv.user1_id
    can_send, err_code, err_msg = _check_send_permission(my_id, receiver_id, conversation_id)
    if not can_send:
        return error_response(err_code, err_msg)

    if msg_type == 'project_invite':
        content = str(data.get('project_id'))
    msg = Message(
        conversation_type='private',
        conversation_id=conversation_id,
        sender_id=my_id,
        msg_type=msg_type,
        content=content,
        file_name=data.get('file_name'),
        file_size=data.get('file_size'),
        voice_duration=data.get('voice_duration')
    )
    db.session.add(msg)
    db.session.flush()

    # 更新会话冗余字段
    preview = content if msg_type == 'text' else ('[项目邀请]' if msg_type == 'project_invite' else f'[{msg_type}]')
    conv.last_message_content = preview
    conv.last_message_at = msg.created_at

    # 对方未读 +1
    cr = ConversationRead.query.filter_by(conversation_id=conversation_id, user_id=receiver_id).first()
    if not cr:
        cr = ConversationRead(conversation_id=conversation_id, user_id=receiver_id, unread_count=0)
        db.session.add(cr)
    cr.unread_count = (cr.unread_count or 0) + 1

    db.session.commit()

    ret = {
        'message_id': msg.id,
        'msg_type': msg.msg_type,
        'content': msg.content,
        'created_at': msg.created_at.isoformat() if msg.created_at else None
    }
    if msg_type == 'project_invite':
        proj = Project.query.get(data.get('project_id'))
        ret['project'] = {
            'project_id': proj.id,
            'title': proj.title,
            'cover_url': proj.cover_url,
            'status': proj.status
        } if proj else None
    return success_response(data=ret, message='发送成功')


# ========== 接口16：标记会话已读 ==========
@bp.route('/<int:conversation_id>/read', methods=['POST'])
@login_required
def mark_conversation_read(conversation_id):
    """标记会话已读，清零未读数"""
    my_id = request.user.id
    conv = Conversation.query.get(conversation_id)
    if not conv or (conv.user1_id != my_id and conv.user2_id != my_id):
        return error_response(3003, '会话不存在或无权访问', http_code=404)

    cr = ConversationRead.query.filter_by(conversation_id=conversation_id, user_id=my_id).first()
    if not cr:
        cr = ConversationRead(conversation_id=conversation_id, user_id=my_id, unread_count=0)
        db.session.add(cr)
    cr.unread_count = 0
    # 更新最后读到的消息ID
    last_msg = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc()).first()
    if last_msg:
        cr.last_read_message_id = last_msg.id
    db.session.commit()
    return success_response(data={'unread_count': 0}, message='已读')


# ========== 接口23：获取官方会话 ==========
@bp.route('/official', methods=['GET'])
@login_required
def get_official_conversation():
    """获取与官方账号的会话，点官方消息 Tab 时调用"""
    my_id = request.user.id
    official = User.query.filter_by(is_official=True).first()
    if not official:
        return error_response(404, '官方账号不存在', http_code=404)

    conv = _get_or_create_conversation(my_id, official.id)
    cr = ConversationRead.query.filter_by(conversation_id=conv.id, user_id=my_id).first()
    unread = cr.unread_count if cr else 0

    return success_response(data={
        'conversation_id': conv.id,
        'official': {
            'user_id': official.id,
            'nickname': official.nickname,
            'avatar': official.avatar
        },
        'unread_count': unread,
        'last_message': conv.last_message_content or '',
        'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None
    })
