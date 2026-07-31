import logging
from flask import Blueprint, request
from app import db
from app.models import Work, User, Like, Comment
from app.utils.helpers import (
    login_required, success_response, error_response,
    get_pagination_params, format_pagination
)

bp = Blueprint('interactions', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    WORK_NOT_FOUND = 4001
    NO_PERMISSION = 4002
    ALREADY_LIKED = 4003
    NOT_LIKED = 4004
    COMMENT_NOT_FOUND = 4005
    COMMENT_EMPTY = 4006
    REPLY_LEVEL_EXCEEDED = 4007

MAX_COMMENT_LEN = 2000


def get_published_work_or_404(work_id):
    """获取已发布作品，草稿/删除/不存在均返回 4001"""
    work = Work.query.filter_by(id=work_id).filter(Work.status == 'published').first()
    if not work:
        return None, error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在或未发布', http_code=404)
    return work, None


# 1. 点赞作品
@bp.route('/works/<int:work_id>/like', methods=['POST'])
@login_required
def like_work(work_id):
    work, err = get_published_work_or_404(work_id)
    if err:
        return err

    existing = Like.query.filter_by(user_id=request.user.id, work_id=work_id).first()
    if existing:
        return error_response(ErrorCode.ALREADY_LIKED, '已点赞过该作品', http_code=400)

    like = Like(user_id=request.user.id, work_id=work_id)
    db.session.add(like)
    work.like_count = (work.like_count or 0) + 1
    db.session.commit()
    logger.info(f'点赞: user_id={request.user.id}, work_id={work_id}')

    return success_response(data={'like_count': work.like_count}, message='点赞成功')


# 2. 取消点赞
@bp.route('/works/<int:work_id>/like', methods=['DELETE'])
@login_required
def unlike_work(work_id):
    work, err = get_published_work_or_404(work_id)
    if err:
        return err

    like = Like.query.filter_by(user_id=request.user.id, work_id=work_id).first()
    if not like:
        return error_response(ErrorCode.NOT_LIKED, '未点赞过该作品', http_code=400)

    db.session.delete(like)
    work.like_count = max((work.like_count or 0) - 1, 0)
    db.session.commit()
    logger.info(f'取消点赞: user_id={request.user.id}, work_id={work_id}')

    return success_response(data={'like_count': work.like_count}, message='已取消点赞')


# 3. 获取作品点赞用户列表
@bp.route('/works/<int:work_id>/likes', methods=['GET'])
@login_required
def get_work_likes(work_id):
    work, err = get_published_work_or_404(work_id)
    if err:
        return err

    page, page_size = get_pagination_params()
    query = Like.query.filter_by(work_id=work_id).order_by(Like.created_at.desc())
    result = format_pagination(query, page, page_size)

    # 批量查用户，避免 N+1
    user_ids = [l.user_id for l in result['list']]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    result['list'] = [l.to_dict(user=users.get(l.user_id)) for l in result['list']]
    return success_response(data=result)


# 4. 发表评论（或回复）
@bp.route('/works/<int:work_id>/comments', methods=['POST'])
@login_required
def create_comment(work_id):
    work, err = get_published_work_or_404(work_id)
    if err:
        return err

    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    content = (data.get('content') or '').strip()
    if not content:
        return error_response(ErrorCode.COMMENT_EMPTY, '评论内容不能为空', http_code=400)
    if len(content) > MAX_COMMENT_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '评论内容过长', http_code=400)

    parent_id = data.get('parent_id')
    if parent_id is not None:
        parent = Comment.query.get(parent_id)
        if not parent or parent.work_id != work_id:
            return error_response(ErrorCode.COMMENT_NOT_FOUND, '父评论不存在', http_code=404)
        # 二级回复限制：parent_id 必须指向一级评论
        if parent.parent_id is not None:
            return error_response(ErrorCode.REPLY_LEVEL_EXCEEDED, '回复层级超限，只能回复一级评论', http_code=400)

    comment = Comment(
        user_id=request.user.id,
        work_id=work_id,
        parent_id=parent_id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    logger.info(f'评论: comment_id={comment.id}, user_id={request.user.id}, work_id={work_id}, parent_id={parent_id}')

    return success_response(data=comment.to_dict(user=request.user), message='评论成功')


# 5. 获取作品评论列表（一级评论，含回复数）
@bp.route('/works/<int:work_id>/comments', methods=['GET'])
@login_required
def get_work_comments(work_id):
    work, err = get_published_work_or_404(work_id)
    if err:
        return err

    page, page_size = get_pagination_params()
    # 仅返回一级评论（parent_id IS NULL），按时间倒序
    query = Comment.query.filter_by(work_id=work_id, parent_id=None).order_by(Comment.created_at.desc())
    result = format_pagination(query, page, page_size)

    # 批量查用户 + 回复数
    comment_ids = [c.id for c in result['list']]
    user_ids = [c.user_id for c in result['list']]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    reply_counts = {}
    if comment_ids:
        from sqlalchemy import func
        rows = db.session.query(Comment.parent_id, func.count(Comment.id)).filter(
            Comment.parent_id.in_(comment_ids)
        ).group_by(Comment.parent_id).all()
        reply_counts = {pid: cnt for pid, cnt in rows}

    result['list'] = [c.to_dict(user=users.get(c.user_id), reply_count=reply_counts.get(c.id, 0)) for c in result['list']]
    return success_response(data=result)


# 6. 删除评论（软删除，仅作者）
@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return error_response(ErrorCode.COMMENT_NOT_FOUND, '评论不存在', http_code=404)

    if comment.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权删除他人评论', http_code=403)

    if comment.is_deleted:
        return success_response(message='评论已删除')

    comment.is_deleted = True
    db.session.commit()
    logger.info(f'评论删除: comment_id={comment_id}, user_id={request.user.id}')

    return success_response(message='评论已删除')


# 7. 获取评论的回复列表
@bp.route('/comments/<int:comment_id>/replies', methods=['GET'])
@login_required
def get_comment_replies(comment_id):
    parent = Comment.query.get(comment_id)
    if not parent:
        return error_response(ErrorCode.COMMENT_NOT_FOUND, '评论不存在', http_code=404)

    page, page_size = get_pagination_params()
    query = Comment.query.filter_by(parent_id=comment_id).order_by(Comment.created_at.asc())
    result = format_pagination(query, page, page_size)

    user_ids = [c.user_id for c in result['list']]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    result['list'] = [c.to_dict(user=users.get(c.user_id)) for c in result['list']]
    return success_response(data=result)
