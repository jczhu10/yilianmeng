# -*- coding: utf-8 -*-
"""活动模块路由"""
import logging
from flask import Blueprint, request
from app import db
from app.models import Event, EventParticipant, Work, User
from app.utils.helpers import (
    login_required, success_response, error_response,
    get_pagination_params, format_pagination
)

bp = Blueprint('events', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    NOT_FOUND = 404
    EVENT_NOT_FOUND = 6001
    WORK_NOT_FOUND = 6002
    ALREADY_JOINED = 6003
    DEADLINE_PASSED = 6004


# 1. 活动列表
@bp.route('/', methods=['GET'])
@login_required
def list_events():
    page, page_size = get_pagination_params()
    status = request.args.get('status', 'ongoing')
    query = Event.query
    if status:
        query = query.filter(Event.status == status)
    query = query.order_by(Event.created_at.desc())
    result = format_pagination(query, page, page_size)
    result['list'] = [e.to_dict() for e in result['list']]
    return success_response(data=result)


# 2. 活动详情
@bp.route('/<int:event_id>', methods=['GET'])
@login_required
def get_event_detail(event_id):
    event = Event.query.get(event_id)
    if not event:
        return error_response(ErrorCode.EVENT_NOT_FOUND, '活动不存在', http_code=404)
    data = event.to_dict()
    # 当前用户是否已参与
    joined = EventParticipant.query.filter_by(
        event_id=event_id, user_id=request.user.id
    ).first()
    data['is_joined'] = joined is not None
    return success_response(data=data)


# 3. 参与活动（提交作品）
@bp.route('/<int:event_id>/join', methods=['POST'])
@login_required
def join_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return error_response(ErrorCode.EVENT_NOT_FOUND, '活动不存在', http_code=404)
    if event.status != 'ongoing':
        return error_response(ErrorCode.DEADLINE_PASSED, '活动已结束', http_code=400)

    data = request.get_json()
    if not data or not data.get('work_id'):
        return error_response(ErrorCode.PARAM_ERROR, 'work_id 不能为空', http_code=400)

    work_id = data['work_id']
    work = Work.query.filter_by(id=work_id, user_id=request.user.id, status='published').first()
    if not work:
        return error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在或不属于你', http_code=404)

    existing = EventParticipant.query.filter_by(
        event_id=event_id, user_id=request.user.id
    ).first()
    if existing:
        return error_response(ErrorCode.ALREADY_JOINED, '已参与该活动', http_code=400)

    participant = EventParticipant(
        event_id=event_id,
        user_id=request.user.id,
        work_id=work_id,
    )
    db.session.add(participant)
    event.participant_count = (event.participant_count or 0) + 1
    db.session.commit()
    logger.info(f'参与活动: event_id={event_id}, user_id={request.user.id}, work_id={work_id}')
    return success_response(data=participant.to_dict(), message='参与成功')
