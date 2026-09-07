# -*- coding: utf-8 -*-
"""群聊路由：群列表/消息记录/发消息/已读/成员/建群/邀请/退出"""
from flask import Blueprint, request
from app import db
from app.models import (Group, GroupMember, GroupRead, Message, User)
from app.utils.helpers import (login_required, success_response, error_response,
                               get_pagination_params)

bp = Blueprint('groups', __name__)

ALLOWED_MSG_TYPES = {'text', 'image', 'voice', 'file'}


def _check_member(group_id, user_id):
    """检查是否群成员"""
    return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()


# ========== 接口17：群聊列表 ==========
@bp.route('/', methods=['GET'])
@login_required
def list_groups():
    """我加入的群聊列表"""
    my_id = request.user.id
    page, page_size = get_pagination_params()

    q = Group.query.join(GroupMember, GroupMember.group_id == Group.id).filter(
        GroupMember.user_id == my_id
    ).order_by(Group.last_message_at.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    group_ids = [g.id for g in items]
    reads = {}
    if group_ids:
        for gr in GroupRead.query.filter(
            GroupRead.group_id.in_(group_ids),
            GroupRead.user_id == my_id
        ).all():
            reads[gr.group_id] = gr

    list_data = [{
        'group_id': g.id,
        'name': g.name,
        'avatar': g.avatar,
        'last_message': g.last_message_content or '',
        'last_message_at': g.last_message_at.isoformat() if g.last_message_at else None,
        'unread_count': reads[g.id].unread_count if g.id in reads else 0,
        'member_count': g.member_count or 0
    } for g in items]

    return success_response(data={'list': list_data, 'total': len(list_data),
                                  'page': page, 'page_size': page_size})


# ========== 接口18：群聊消息记录 ==========
@bp.route('/<int:group_id>/messages', methods=['GET'])
@login_required
def list_group_messages(group_id):
    """群聊消息记录（分页）"""
    my_id = request.user.id
    if not _check_member(group_id, my_id):
        return error_response(3004, '群不存在或非群成员', http_code=404)

    page, page_size = get_pagination_params()
    q = Message.query.filter_by(group_id=group_id).order_by(Message.created_at.desc())
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


# ========== 接口19：发送群聊消息 ==========
@bp.route('/<int:group_id>/messages', methods=['POST'])
@login_required
def send_group_message(group_id):
    """发送群聊消息"""
    my_id = request.user.id
    if not _check_member(group_id, my_id):
        return error_response(3004, '群不存在或非群成员', http_code=404)

    data = request.get_json() or {}
    msg_type = data.get('msg_type')
    content = data.get('content')
    if not msg_type or not content:
        return error_response(400, 'msg_type 和 content 不能为空')
    if msg_type not in ALLOWED_MSG_TYPES:
        return error_response(3007, f'msg_type 暂不支持：{msg_type}')
    if msg_type == 'file' and not data.get('file_name'):
        return error_response(400, 'file 类型必须传 file_name')
    if msg_type == 'voice' and data.get('voice_duration') is None:
        return error_response(400, 'voice 类型必须传 voice_duration')

    msg = Message(
        conversation_type='group',
        group_id=group_id,
        sender_id=my_id,
        msg_type=msg_type,
        content=content,
        file_name=data.get('file_name'),
        file_size=data.get('file_size'),
        voice_duration=data.get('voice_duration')
    )
    db.session.add(msg)
    db.session.flush()

    # 更新群冗余字段
    preview = content if msg_type == 'text' else f'[{msg_type}]'
    grp = Group.query.get(group_id)
    grp.last_message_content = preview
    grp.last_message_at = msg.created_at

    # 其他成员未读 +1
    members = GroupMember.query.filter(GroupMember.group_id == group_id, GroupMember.user_id != my_id).all()
    for m in members:
        gr = GroupRead.query.filter_by(group_id=group_id, user_id=m.user_id).first()
        if not gr:
            gr = GroupRead(group_id=group_id, user_id=m.user_id, unread_count=0)
            db.session.add(gr)
        gr.unread_count = (gr.unread_count or 0) + 1

    db.session.commit()

    return success_response(data={
        'message_id': msg.id,
        'msg_type': msg.msg_type,
        'content': msg.content,
        'created_at': msg.created_at.isoformat() if msg.created_at else None
    }, message='发送成功')


# ========== 接口20：标记群聊已读 ==========
@bp.route('/<int:group_id>/read', methods=['POST'])
@login_required
def mark_group_read(group_id):
    """标记群聊已读，清零未读数"""
    my_id = request.user.id
    if not _check_member(group_id, my_id):
        return error_response(3004, '群不存在或非群成员', http_code=404)

    gr = GroupRead.query.filter_by(group_id=group_id, user_id=my_id).first()
    if not gr:
        gr = GroupRead(group_id=group_id, user_id=my_id, unread_count=0)
        db.session.add(gr)
    gr.unread_count = 0
    last_msg = Message.query.filter_by(group_id=group_id).order_by(Message.created_at.desc()).first()
    if last_msg:
        gr.last_read_message_id = last_msg.id
    db.session.commit()
    return success_response(data={'unread_count': 0}, message='已读')


# ========== 接口21：群成员列表 ==========
@bp.route('/<int:group_id>/members', methods=['GET'])
@login_required
def list_group_members(group_id):
    """群成员列表"""
    my_id = request.user.id
    if not _check_member(group_id, my_id):
        return error_response(3004, '群不存在或非群成员', http_code=404)

    members = GroupMember.query.filter_by(group_id=group_id).order_by(
        GroupMember.joined_at.asc()
    ).all()
    user_ids = [m.user_id for m in members]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    list_data = [{
        'user_id': u.id,
        'nickname': u.nickname,
        'avatar': u.avatar,
        'role': m.role,
        'joined_at': m.joined_at.isoformat() if m.joined_at else None,
        'group_nickname': m.nickname
    } for m in members for u in [users.get(m.user_id)] if u]

    return success_response(data={'list': list_data, 'total': len(list_data)})


# ========== 接口24：创建群聊 ==========
@bp.route('/', methods=['POST'])
@login_required
def create_group():
    """创建群聊（自由建群）"""
    my_id = request.user.id
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return error_response(400, '群名称不能为空')
    member_ids = data.get('member_ids', [])

    grp = Group(name=name, avatar=data.get('avatar', ''), owner_id=my_id, member_count=1 + len(member_ids))
    db.session.add(grp)
    db.session.flush()

    # 创建人 owner
    db.session.add(GroupMember(group_id=grp.id, user_id=my_id, role='owner'))
    # 批量加成员
    for uid in member_ids:
        if uid == my_id:
            continue
        if User.query.get(uid):
            db.session.add(GroupMember(group_id=grp.id, user_id=uid, role='member'))

    grp.member_count = GroupMember.query.filter_by(group_id=grp.id).count()
    db.session.commit()

    return success_response(data={'group_id': grp.id}, message='群创建成功')


# ========== 接口25：邀请加入群聊 ==========
@bp.route('/<int:group_id>/invite', methods=['POST'])
@login_required
def invite_members(group_id):
    """邀请加入群聊（仅群主/管理员）"""
    my_id = request.user.id
    me = _check_member(group_id, my_id)
    if not me or me.role not in ('owner', 'admin'):
        return error_response(403, '无权邀请，仅群主或管理员可操作', http_code=403)

    data = request.get_json() or {}
    user_ids = data.get('user_ids', [])
    if not user_ids:
        return error_response(400, 'user_ids 不能为空')

    added = []
    for uid in user_ids:
        if uid == my_id:
            continue
        if not User.query.get(uid):
            continue
        if _check_member(group_id, uid):
            continue
        db.session.add(GroupMember(group_id=group_id, user_id=uid, role='member'))
        added.append(uid)

    grp = Group.query.get(group_id)
    grp.member_count = GroupMember.query.filter_by(group_id=group_id).count()
    db.session.commit()

    return success_response(data={'added': added, 'added_count': len(added)},
                            message=f'成功邀请 {len(added)} 人')


# ========== 接口26：退出群聊 ==========
@bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """退出群聊（群主不能直接退）"""
    my_id = request.user.id
    me = _check_member(group_id, my_id)
    if not me:
        return error_response(3004, '群不存在或非群成员', http_code=404)

    if me.role == 'owner':
        return error_response(3008, '群主不能直接退出，请先转让或解散群')

    db.session.delete(me)
    grp = Group.query.get(group_id)
    grp.member_count = (grp.member_count or 1) - 1
    # 清理未读记录
    gr = GroupRead.query.filter_by(group_id=group_id, user_id=my_id).first()
    if gr:
        db.session.delete(gr)
    db.session.commit()
    return success_response(message='已退出群聊')
