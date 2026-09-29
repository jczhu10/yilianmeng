# -*- coding: utf-8 -*-
"""用户搜索路由"""
import logging
from flask import Blueprint, request
from app.models import User
from app.utils.helpers import (
    login_required, success_response, error_response,
    get_pagination_params, format_pagination
)

bp = Blueprint('users', __name__)
logger = logging.getLogger(__name__)


# 1. 用户搜索（按昵称模糊匹配）
@bp.route('/search', methods=['GET'])
@login_required
def search_users():
    q = (request.args.get('q') or '').strip()
    if not q:
        return error_response(400, '搜索关键词不能为空', http_code=400)
    page, page_size = get_pagination_params()
    query = User.query.filter(User.nickname.ilike(f'%{q}%'))
    result = format_pagination(query, page, page_size)
    result['list'] = [u.to_dict() for u in result['list']]
    return success_response(data=result)
