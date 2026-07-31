import logging
from flask import Blueprint, request
from werkzeug.utils import secure_filename
from app import db
from app.models import Work, User, Skill
from app.utils.helpers import (
    login_required, success_response, error_response,
    get_pagination_params, format_pagination,
    save_file, allowed_file
)

bp = Blueprint('works', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    NOT_FOUND = 404
    WORK_NOT_FOUND = 3001
    NO_PERMISSION = 3002
    WORK_DELETED = 3003
    CHANNEL_INVALID = 3004
    FILES_LIMIT_EXCEEDED = 3005
    SKILL_TAG_INVALID = 3006

ALLOWED_CHANNELS = {'writing', 'visual', 'video', 'voice'}
ALLOWED_STATUSES = {'draft', 'published'}
MAX_FILES = 9
MAX_SKILL_TAGS = 5
MAX_TITLE_LEN = 200
MAX_DESC_LEN = 2000


def get_work_or_404(work_id, include_deleted=False):
    query = Work.query.filter_by(id=work_id)
    if not include_deleted:
        query = query.filter(Work.status != 'deleted')
    work = query.first()
    if not work:
        return None, error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在', http_code=404)
    return work, None


def validate_skill_tags(skill_tags):
    if not isinstance(skill_tags, list):
        return None, error_response(ErrorCode.PARAM_ERROR, 'skill_tags必须为数组', http_code=400)
    if len(skill_tags) > MAX_SKILL_TAGS:
        return None, error_response(ErrorCode.SKILL_TAG_INVALID, '技能标签最多5个', http_code=400)
    skill_tags = list(dict.fromkeys(skill_tags))
    if not skill_tags:
        return [], None
    valid_skills = Skill.query.filter(Skill.id.in_(skill_tags)).all()
    if len(valid_skills) != len(skill_tags):
        return None, error_response(ErrorCode.SKILL_TAG_INVALID, '存在无效的技能标签ID', http_code=400)
    return skill_tags, None


# 1. 创建作品
@bp.route('/', methods=['POST'])
@login_required
def create_work():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    title = (data.get('title') or '').strip()
    if not title:
        return error_response(ErrorCode.PARAM_ERROR, '标题不能为空', http_code=400)
    if len(title) > MAX_TITLE_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)

    description = data.get('description') or ''
    if len(description) > MAX_DESC_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '描述过长', http_code=400)

    channel = data.get('channel', 'writing')
    if channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    files = data.get('files') or []
    if not isinstance(files, list):
        return error_response(ErrorCode.PARAM_ERROR, 'files必须为数组', http_code=400)
    if len(files) > MAX_FILES:
        return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, '文件数量超限', http_code=400)

    cover_url = data.get('cover_url') or ''
    is_collaborative = bool(data.get('is_collaborative', False))
    collaborators = data.get('collaborators') or []
    if not isinstance(collaborators, list):
        return error_response(ErrorCode.PARAM_ERROR, 'collaborators必须为数组', http_code=400)

    skill_tags = data.get('skill_tags') or []
    valid_tags, err = validate_skill_tags(skill_tags)
    if err:
        return err

    status = data.get('status', 'draft')
    if status not in ALLOWED_STATUSES:
        return error_response(ErrorCode.PARAM_ERROR, '状态不合法', http_code=400)

    work = Work(
        user_id=request.user.id,
        title=title,
        description=description,
        channel=channel,
        cover_url=cover_url,
        is_collaborative=is_collaborative,
        status=status
    )
    work.set_files(files)
    work.set_collaborators(collaborators)
    work.set_skill_tags(valid_tags)

    db.session.add(work)
    db.session.commit()
    logger.info(f'作品创建: work_id={work.id}, user_id={request.user.id}, status={status}')

    return success_response(data=work.to_dict(), message='作品创建成功')


# 2. 编辑作品
@bp.route('/<int:work_id>', methods=['PUT'])
@login_required
def update_work(work_id):
    work, err = get_work_or_404(work_id)
    if err:
        return err

    if work.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作他人作品', http_code=403)

    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    if 'title' in data:
        title = (data['title'] or '').strip()
        if not title:
            return error_response(ErrorCode.PARAM_ERROR, '标题不能为空', http_code=400)
        if len(title) > MAX_TITLE_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)
        work.title = title

    if 'description' in data:
        description = data['description'] or ''
        if len(description) > MAX_DESC_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '描述过长', http_code=400)
        work.description = description

    if 'channel' in data:
        channel = data['channel']
        if channel not in ALLOWED_CHANNELS:
            return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)
        work.channel = channel

    if 'files' in data:
        files = data['files'] or []
        if not isinstance(files, list):
            return error_response(ErrorCode.PARAM_ERROR, 'files必须为数组', http_code=400)
        if len(files) > MAX_FILES:
            return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, '文件数量超限', http_code=400)
        work.set_files(files)

    if 'cover_url' in data:
        work.cover_url = data['cover_url'] or ''

    if 'is_collaborative' in data:
        work.is_collaborative = bool(data['is_collaborative'])

    if 'collaborators' in data:
        collaborators = data['collaborators'] or []
        if not isinstance(collaborators, list):
            return error_response(ErrorCode.PARAM_ERROR, 'collaborators必须为数组', http_code=400)
        work.set_collaborators(collaborators)

    if 'skill_tags' in data:
        valid_tags, err = validate_skill_tags(data['skill_tags'] or [])
        if err:
            return err
        work.set_skill_tags(valid_tags)

    db.session.commit()
    logger.info(f'作品编辑: work_id={work.id}, user_id={request.user.id}')

    return success_response(data=work.to_dict(), message='作品更新成功')


# 3. 发布作品（草稿 -> 已发布）
@bp.route('/<int:work_id>/publish', methods=['POST'])
@login_required
def publish_work(work_id):
    work, err = get_work_or_404(work_id)
    if err:
        return err

    if work.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作他人作品', http_code=403)

    if work.status == 'published':
        return success_response(data=work.to_dict(), message='作品已是发布状态')

    work.status = 'published'
    db.session.commit()
    logger.info(f'作品发布: work_id={work.id}, user_id={request.user.id}')

    return success_response(data=work.to_dict(), message='作品发布成功')


# 4. 删除作品（软删除）
@bp.route('/<int:work_id>', methods=['DELETE'])
@login_required
def delete_work(work_id):
    work, err = get_work_or_404(work_id, include_deleted=True)
    if err:
        return err

    if work.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作他人作品', http_code=403)

    if work.status == 'deleted':
        return error_response(ErrorCode.WORK_DELETED, '作品已删除', http_code=400)

    work.status = 'deleted'
    db.session.commit()
    logger.info(f'作品删除: work_id={work.id}, user_id={request.user.id}')

    return success_response(message='作品已删除')


# 5. 获取作品详情
@bp.route('/<int:work_id>', methods=['GET'])
@login_required
def get_work_detail(work_id):
    work, err = get_work_or_404(work_id)
    if err:
        return err

    # 草稿仅作者可见
    if work.status == 'draft' and work.user_id != request.user.id:
        return error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在', http_code=404)

    author = User.query.get(work.user_id)
    # 浏览数+1（仅published作品计数）
    if work.status == 'published':
        work.view_count = (work.view_count or 0) + 1
        db.session.commit()

    return success_response(data=work.to_dict(with_author=True, author=author))


# 6. 获取我的作品列表
@bp.route('/mine', methods=['GET'])
@login_required
def get_my_works():
    page, page_size = get_pagination_params()
    status = request.args.get('status')

    query = Work.query.filter_by(user_id=request.user.id)

    if status:
        if status not in ALLOWED_STATUSES and status != 'deleted':
            return error_response(ErrorCode.PARAM_ERROR, '状态参数不合法', http_code=400)
        query = query.filter_by(status=status)
    else:
        query = query.filter(Work.status != 'deleted')

    query = query.order_by(Work.created_at.desc())
    result = format_pagination(query, page, page_size)
    result['list'] = [w.to_dict() for w in result['list']]
    return success_response(data=result)


# 7. 文件上传（图片/视频）
@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return error_response(ErrorCode.PARAM_ERROR, '未提供文件', http_code=400)

    file = request.files['file']
    if not file.filename:
        return error_response(ErrorCode.PARAM_ERROR, '文件名为空', http_code=400)

    if not allowed_file(file.filename):
        return error_response(ErrorCode.PARAM_ERROR, '不支持的文件类型', http_code=400)

    try:
        url = save_file(file, folder='works')
        logger.info(f'文件上传: user_id={request.user.id}, url={url}')
        return success_response(data={'url': url}, message='上传成功')
    except Exception as e:
        logger.error(f'文件上传失败: {e}')
        return error_response(ErrorCode.PARAM_ERROR, '文件上传失败', http_code=500)


# ===== 推流 / 搜索 / 按技能筛选 =====
ALLOWED_SORT = {'latest', 'hot'}


def build_work_list_item(work, author=None, current_user_id=None):
    """构造推流/搜索列表的作品项，附加作者信息和当前用户是否已点赞"""
    item = work.to_dict()
    if author is None:
        author = User.query.get(work.user_id)
    item['author'] = author.to_dict() if author else None
    if current_user_id is not None:
        from app.models import Like
        item['is_liked'] = Like.query.filter_by(user_id=current_user_id, work_id=work.id).first() is not None
    else:
        item['is_liked'] = False
    return item


# 8. 首页推荐推流
@bp.route('/feed', methods=['GET'])
@login_required
def get_feed():
    """首页推荐推流。
    排序:
      - latest: 按发布时间倒序(默认)
      - hot: 按热度分(like_count*2 + view_count)倒序, 热度分相同按时间倒序
    筛选:
      - channel: writing/visual/video/voice, 可选
      - exclude_self: 默认 true 排除当前用户自己的作品, 传 false 可包含
    """
    page, page_size = get_pagination_params()
    sort = request.args.get('sort', 'latest')
    if sort not in ALLOWED_SORT:
        return error_response(ErrorCode.PARAM_ERROR, '排序参数不合法', http_code=400)

    channel = request.args.get('channel')
    if channel and channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    exclude_self = request.args.get('exclude_self', 'true').lower() != 'false'

    query = Work.query.filter(Work.status == 'published')
    if exclude_self:
        query = query.filter(Work.user_id != request.user.id)
    if channel:
        query = query.filter(Work.channel == channel)

    if sort == 'hot':
        hot_score = (Work.like_count * 2 + Work.view_count)
        query = query.order_by(hot_score.desc(), Work.created_at.desc())
    else:
        query = query.order_by(Work.created_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)


# 9. 搜索作品
@bp.route('/search', methods=['GET'])
@login_required
def search_works():
    """按标题/描述关键词搜索已发布作品, 可叠加 channel 筛选, 按时间倒序。"""
    keyword = (request.args.get('q') or '').strip()
    if not keyword:
        return error_response(ErrorCode.PARAM_ERROR, '搜索关键词不能为空', http_code=400)
    if len(keyword) > 100:
        return error_response(ErrorCode.PARAM_ERROR, '关键词过长', http_code=400)

    channel = request.args.get('channel')
    if channel and channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    page, page_size = get_pagination_params()
    like_pattern = f'%{keyword}%'
    query = Work.query.filter(
        Work.status == 'published',
        db.or_(Work.title.like(like_pattern), Work.description.like(like_pattern))
    )
    if channel:
        query = query.filter(Work.channel == channel)
    query = query.order_by(Work.created_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)


# 10. 按技能标签筛选作品
@bp.route('/by-skill', methods=['GET'])
@login_required
def get_works_by_skill():
    """按技能标签筛选已发布作品。
    参数:
      - skill_id: 必填, 技能ID
      - sort: latest/hot, 默认 latest
    """
    skill_id = request.args.get('skill_id', type=int)
    if not skill_id:
        return error_response(ErrorCode.PARAM_ERROR, 'skill_id 不能为空', http_code=400)

    sort = request.args.get('sort', 'latest')
    if sort not in ALLOWED_SORT:
        return error_response(ErrorCode.PARAM_ERROR, '排序参数不合法', http_code=400)

    page, page_size = get_pagination_params()
    from sqlalchemy import text
    query = Work.query.filter(
        Work.status == 'published',
        text("JSON_CONTAINS(skill_tags, CAST(:sid AS JSON))").bindparams(sid=skill_id)
    )
    if sort == 'hot':
        hot_score = (Work.like_count * 2 + Work.view_count)
        query = query.order_by(hot_score.desc(), Work.created_at.desc())
    else:
        query = query.order_by(Work.created_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)
