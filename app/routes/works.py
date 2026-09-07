import logging
from flask import Blueprint, request
from werkzeug.utils import secure_filename
from app import db
from app.models import Work, User, Skill, Follow, WorkVisibilityRule, WorkRepost, Project
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
    VISIBILITY_TYPE_INVALID = 3007
    CUSTOM_RULES_LIMIT = 3008
    REPOST_XOR = 3009

ALLOWED_CHANNELS = {'writing', 'visual', 'video', 'voice'}
ALLOWED_STATUSES = {'draft', 'published'}
ALLOWED_CONTENT_TYPES = {'original', 'repost', 'text_only'}
ALLOWED_IMAGE_LAYOUTS = {'flip', 'grid'}
ALLOWED_VISIBILITY = {'private', 'followers', 'mutual', 'public', 'custom_allow', 'custom_deny'}
MAX_FILES = 9
MAX_SKILL_TAGS = 5
MAX_TITLE_LEN = 200
MAX_DESC_LEN = 2000
MAX_TEXT_CONTENT_LEN = 5000
MAX_CUSTOM_RULES = 20


# ============================================================
# 公共工具：可见性过滤 Query（6 种 visibility_type）
# ============================================================
def visible_works_query(user_id):
    """返回只包含 user_id 能看到的「已发布」作品的 Query（SQLAlchemy 级联）。
    注意：只过滤 published + 已删除排除；草稿需要上层单独处理。
    """
    # 我关注了谁
    my_following = db.session.query(Follow.followed_id) \
        .filter(Follow.follower_id == user_id).subquery()
    # 谁关注了我
    my_followers = db.session.query(Follow.follower_id) \
        .filter(Follow.followed_id == user_id).subquery()
    # 我在白名单中的作品
    allow_list = db.session.query(WorkVisibilityRule.work_id) \
        .filter(WorkVisibilityRule.rule_type == 'allow',
                WorkVisibilityRule.user_id == user_id).subquery()
    # 我在黑名单中的作品
    deny_list = db.session.query(WorkVisibilityRule.work_id) \
        .filter(WorkVisibilityRule.rule_type == 'deny',
                WorkVisibilityRule.user_id == user_id).subquery()

    q = Work.query.filter(
        Work.status == 'published',
        db.or_(
            # 1) 作者本人，任何权限都可见
            Work.user_id == user_id,
            # 2) public
            Work.visibility_type == 'public',
            # 3) followers：我关注了作者
            db.and_(Work.visibility_type == 'followers',
                    Work.user_id.in_(my_following)),
            # 4) mutual：双向关注
            db.and_(Work.visibility_type == 'mutual',
                    Work.user_id.in_(my_following),
                    Work.user_id.in_(my_followers)),
            # 5) custom_allow：我在白名单
            db.and_(Work.visibility_type == 'custom_allow',
                    Work.id.in_(allow_list)),
            # 6) custom_deny：我不在黑名单
            db.and_(Work.visibility_type == 'custom_deny',
                    ~Work.id.in_(deny_list)),
        )
    )
    return q


def is_work_visible_to(work, user_id):
    """单条作品是否对 user_id 可见（用于详情等直接命中对象的场景）。
    草稿/软删除不在此判断，由上层先行处理。
    """
    if work.status != 'published':
        return False
    if work.user_id == user_id:
        return True
    vt = work.visibility_type
    if vt == 'public':
        return True
    if vt == 'followers':
        return Follow.query.filter_by(follower_id=user_id, followed_id=work.user_id).first() is not None
    if vt == 'mutual':
        f1 = Follow.query.filter_by(follower_id=user_id, followed_id=work.user_id).first() is not None
        f2 = Follow.query.filter_by(follower_id=work.user_id, followed_id=user_id).first() is not None
        return f1 and f2
    if vt == 'custom_allow':
        return WorkVisibilityRule.query.filter_by(work_id=work.id, rule_type='allow', user_id=user_id).first() is not None
    if vt == 'custom_deny':
        return WorkVisibilityRule.query.filter_by(work_id=work.id, rule_type='deny', user_id=user_id).first() is None
    return False  # 未知 visibility_type -> 默认不可见


# ============================================================
# 公共工具：get_work_or_404（已嵌入可见性校验）
# ============================================================
def get_work_or_404(work_id, include_deleted=False, viewer_id=None, enforce_visibility=True):
    query = Work.query.filter_by(id=work_id)
    if not include_deleted:
        query = query.filter(Work.status != 'deleted')
    work = query.first()
    if not work:
        return None, error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在', http_code=404)

    # 草稿仅作者可见（没传 viewer_id 不校验，用于作者侧内部操作）
    if work.status == 'draft' and viewer_id is not None and work.user_id != viewer_id:
        return None, error_response(ErrorCode.WORK_NOT_FOUND, '作品不存在', http_code=404)

    # 已发布作品做权限可见性校验
    if enforce_visibility and work.status == 'published' and viewer_id is not None:
        if not is_work_visible_to(work, viewer_id):
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


# ============================================================
# 1. 创建作品（支持 content_type / visibility_type / text_content / location / image_layout）
# ============================================================
@bp.route('/', methods=['POST'])
@login_required
def create_work():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    content_type = data.get('content_type', 'original')
    if content_type not in ALLOWED_CONTENT_TYPES:
        return error_response(ErrorCode.PARAM_ERROR, 'content_type 不合法', http_code=400)

    # --- 纯文字 ---
    if content_type == 'text_only':
        text_content = (data.get('text_content') or '').strip()
        if not text_content:
            return error_response(ErrorCode.PARAM_ERROR, 'text_content 不能为空（纯文字作品）', http_code=400)
        if len(text_content) > MAX_TEXT_CONTENT_LEN:
            return error_response(ErrorCode.PARAM_ERROR, 'text_content 过长', http_code=400)
        title = text_content[:MAX_TITLE_LEN] if len(text_content) > 0 else '纯文字作品'
        channel = 'writing'  # 纯文字默认 writing，前端可不传
    elif content_type == 'repost':
        title = (data.get('title') or '').strip()
        if not title:
            # 转发不传标题时，稍后在校验 source_work_id/project_id 后基于对象生成占位标题
            # 这里先留空，不报错
            title = ''
        if len(title) > MAX_TITLE_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)
        text_content = None
    else:  # original
        title = (data.get('title') or '').strip()
        if not title:
            return error_response(ErrorCode.PARAM_ERROR, '标题不能为空', http_code=400)
        if len(title) > MAX_TITLE_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)
        text_content = None

    description = data.get('description') or ''
    if len(description) > MAX_DESC_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '描述过长', http_code=400)

    channel = data.get('channel', 'writing')
    if channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    image_layout = data.get('image_layout', 'flip')
    if image_layout not in ALLOWED_IMAGE_LAYOUTS:
        return error_response(ErrorCode.PARAM_ERROR, 'image_layout 不合法', http_code=400)

    visibility_type = data.get('visibility_type', 'public')
    if visibility_type not in ALLOWED_VISIBILITY:
        return error_response(ErrorCode.VISIBILITY_TYPE_INVALID, 'visibility_type 不合法', http_code=400)

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

    location = (data.get('location') or None) and (data.get('location').strip() or None)

    # --- 转发类型 ---
    source_work_id = data.get('source_work_id')
    source_project_id = data.get('source_project_id')
    if content_type == 'repost':
        sw = bool(source_work_id)
        sp = bool(source_project_id)
        if not (sw ^ sp):  # XOR：必须二选一
            return error_response(ErrorCode.REPOST_XOR, '转发时 source_work_id 和 source_project_id 必须且只能填一个', http_code=400)
        src_title = ''
        if source_work_id:
            src_w = Work.query.filter_by(id=source_work_id, status='published').first()
            if not src_w:
                return error_response(ErrorCode.WORK_NOT_FOUND, '被转发的作品不存在', http_code=404)
            src_title = src_w.title
        if source_project_id:
            src_p = Project.query.filter_by(id=source_project_id).first()
            if not src_p:
                return error_response(ErrorCode.NOT_FOUND, '被转发的项目不存在', http_code=404)
            src_title = src_p.title if hasattr(src_p, 'title') else f'项目#{source_project_id}'
        # 没传标题就自动生成
        if not title:
            title = f'转发：{src_title}'
            if len(title) > MAX_TITLE_LEN:
                title = title[:MAX_TITLE_LEN]

    from datetime import datetime
    work = Work(
        user_id=request.user.id,
        title=title,
        description=description,
        text_content=text_content,
        channel=channel,
        content_type=content_type,
        image_layout=image_layout,
        visibility_type=visibility_type,
        location=location,
        cover_url=cover_url,
        is_collaborative=is_collaborative,
        status=status,
        published_at=datetime.utcnow() if status == 'published' else None,
    )
    work.set_files(files)
    work.set_collaborators(collaborators)
    work.set_skill_tags(valid_tags)

    db.session.add(work)
    db.session.flush()

    # 转发溯源
    if content_type == 'repost':
        if source_work_id:
            src_w = Work.query.get(source_work_id)
            source_uid = src_w.user_id
            src_w.repost_count = (src_w.repost_count or 0) + 1
        else:
            src_p = Project.query.get(source_project_id)
            source_uid = src_p.creator_id if hasattr(src_p, 'creator_id') else src_p.user_id
        repost = WorkRepost(
            work_id=work.id,
            source_work_id=source_work_id,
            source_project_id=source_project_id,
            source_user_id=source_uid,
        )
        db.session.add(repost)
        # 发起方作品 share_count +1（即这条转发帖发起了一次转发操作）
        # 注：被转发方 repost_count 已在上方加过

    # 自定义可见性规则
    allow_users = data.get('allow_users') or []
    deny_users = data.get('deny_users') or []
    if visibility_type == 'custom_allow':
        if not allow_users or len(allow_users) == 0:
            return error_response(ErrorCode.PARAM_ERROR, 'custom_allow 必须传 allow_users', http_code=400)
        if len(allow_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'allow_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        for uid in allow_users:
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=work.id, rule_type='allow', user_id=uid))
    if visibility_type == 'custom_deny':
        if deny_users and len(deny_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'deny_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        for uid in (deny_users or []):
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=work.id, rule_type='deny', user_id=uid))

    db.session.commit()
    logger.info(f'作品创建: work_id={work.id}, user_id={request.user.id}, content_type={content_type}, status={status}')

    return success_response(data=work.to_dict(), message='作品创建成功')


# 2. 编辑作品
@bp.route('/<int:work_id>', methods=['PUT'])
@login_required
def update_work(work_id):
    work, err = get_work_or_404(work_id, include_deleted=True, viewer_id=request.user.id, enforce_visibility=False)
    if err:
        return err

    if work.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作他人作品', http_code=403)

    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    if 'content_type' in data:
        if data['content_type'] not in ALLOWED_CONTENT_TYPES:
            return error_response(ErrorCode.PARAM_ERROR, 'content_type 不合法', http_code=400)
        work.content_type = data['content_type']

    if 'title' in data:
        title = (data['title'] or '').strip()
        if not title:
            return error_response(ErrorCode.PARAM_ERROR, '标题不能为空', http_code=400)
        if len(title) > MAX_TITLE_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)
        work.title = title

    if 'text_content' in data:
        tc = (data['text_content'] or '').strip() or None
        if tc and len(tc) > MAX_TEXT_CONTENT_LEN:
            return error_response(ErrorCode.PARAM_ERROR, 'text_content 过长', http_code=400)
        work.text_content = tc

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

    if 'image_layout' in data:
        if data['image_layout'] not in ALLOWED_IMAGE_LAYOUTS:
            return error_response(ErrorCode.PARAM_ERROR, 'image_layout 不合法', http_code=400)
        work.image_layout = data['image_layout']

    if 'visibility_type' in data:
        if data['visibility_type'] not in ALLOWED_VISIBILITY:
            return error_response(ErrorCode.VISIBILITY_TYPE_INVALID, 'visibility_type 不合法', http_code=400)
        work.visibility_type = data['visibility_type']
        # 切换类型时清空旧的 allow/deny 规则
        WorkVisibilityRule.query.filter_by(work_id=work.id).delete()

    if 'allow_users' in data and work.visibility_type == 'custom_allow':
        allow_users = data['allow_users'] or []
        if len(allow_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'allow_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        WorkVisibilityRule.query.filter_by(work_id=work.id, rule_type='allow').delete()
        for uid in allow_users:
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=work.id, rule_type='allow', user_id=uid))

    if 'deny_users' in data and work.visibility_type == 'custom_deny':
        deny_users = data['deny_users'] or []
        if len(deny_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'deny_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        WorkVisibilityRule.query.filter_by(work_id=work.id, rule_type='deny').delete()
        for uid in deny_users:
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=work.id, rule_type='deny', user_id=uid))

    if 'location' in data:
        loc = data.get('location')
        work.location = (loc.strip() or None) if isinstance(loc, str) else None

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


# 3. 发布作品（草稿 -> 已发布，同时写 published_at）
@bp.route('/<int:work_id>/publish', methods=['POST'])
@login_required
def publish_work(work_id):
    work, err = get_work_or_404(work_id, viewer_id=request.user.id, enforce_visibility=False)
    if err:
        return err

    if work.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作他人作品', http_code=403)

    if work.status == 'published':
        return success_response(data=work.to_dict(), message='作品已是发布状态')

    from datetime import datetime
    work.status = 'published'
    if work.published_at is None:
        work.published_at = datetime.utcnow()
    db.session.commit()
    logger.info(f'作品发布: work_id={work.id}, user_id={request.user.id}')

    return success_response(data=work.to_dict(), message='作品发布成功')


# 4. 删除作品（软删除）
@bp.route('/<int:work_id>', methods=['DELETE'])
@login_required
def delete_work(work_id):
    work, err = get_work_or_404(work_id, include_deleted=True, viewer_id=request.user.id, enforce_visibility=False)
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


# 5. 获取作品详情（已嵌入可见性校验）
@bp.route('/<int:work_id>', methods=['GET'])
@login_required
def get_work_detail(work_id):
    work, err = get_work_or_404(work_id, viewer_id=request.user.id, enforce_visibility=True)
    if err:
        return err

    author = User.query.get(work.user_id)
    # 浏览数+1（仅published，且非作者本人）
    if work.status == 'published' and work.user_id != request.user.id:
        work.view_count = (work.view_count or 0) + 1
        db.session.commit()

    resp = work.to_dict(with_author=True, author=author)
    # 如果是转发，附带上 source_work / source_project
    if work.content_type == 'repost':
        wr = WorkRepost.query.filter_by(work_id=work.id).first()
        if wr:
            if wr.source_work_id:
                src = Work.query.get(wr.source_work_id)
                src_author = User.query.get(src.user_id) if src else None
                resp['source'] = {
                    'type': 'work',
                    'data': src.to_dict(with_author=True, author=src_author) if src and src.status != 'deleted' else None
                }
            elif wr.source_project_id:
                src = Project.query.get(wr.source_project_id)
                resp['source'] = {
                    'type': 'project',
                    'data': src.to_dict() if src else None
                }
            if resp.get('source'):
                resp['source']['source_user_id'] = wr.source_user_id

    return success_response(data=resp)


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

    # 自己的作品：已发布按 published_at 倒序 + 草稿(published_at=NULL)沉到后面再按 created_at 倒序
    # MySQL 不支持 NULLS LAST，用 IF(published_at IS NULL,1,0) + published_at DESC + created_at DESC 实现
    from sqlalchemy import text as sql_text, desc as sql_desc
    query = query.order_by(
        sql_text("IF(published_at IS NULL, 1, 0)"),
        sql_desc(Work.published_at),
        sql_desc(Work.created_at),
    )
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
    """构造推流/搜索列表的作品项，附加作者信息、点赞状态、转发溯源、地点"""
    item = work.to_dict()
    if author is None:
        author = User.query.get(work.user_id)
    item['author'] = author.to_dict() if author else None
    if current_user_id is not None:
        from app.models import Like
        item['is_liked'] = Like.query.filter_by(user_id=current_user_id, work_id=work.id).first() is not None
    else:
        item['is_liked'] = False

    # 转发帖：附加 source 快照
    if work.content_type == 'repost':
        wr = WorkRepost.query.filter_by(work_id=work.id).first()
        if wr:
            if wr.source_work_id:
                src = Work.query.get(wr.source_work_id)
                if src and src.status != 'deleted' and current_user_id is not None:
                    if is_work_visible_to(src, current_user_id) or src.user_id == current_user_id:
                        src_author = User.query.get(src.user_id)
                        item['source'] = {'type': 'work', 'source_user_id': wr.source_user_id,
                                          'data': src.to_dict(with_author=True, author=src_author)}
                    else:
                        item['source'] = {'type': 'work', 'source_user_id': wr.source_user_id,
                                          'data': None, 'reason': 'invisible'}
                else:
                    item['source'] = {'type': 'work', 'source_user_id': wr.source_user_id,
                                      'data': None, 'reason': 'deleted' if src and src.status == 'deleted' else 'not_found'}
            elif wr.source_project_id:
                src = Project.query.get(wr.source_project_id)
                item['source'] = {'type': 'project', 'source_user_id': wr.source_user_id,
                                  'data': src.to_dict() if src else None}
    return item


# 8. 首页推荐推流（MVP：可见性 + published_at 排序 + 新热度公式，置顶暂不接入）
@bp.route('/feed', methods=['GET'])
@login_required
def get_feed():
    """首页推荐推流（MVP）
    排序:
      - latest: published_at 倒序（默认）
      - hot: 热度分 = like_count*2 + view_count + repost_count*1.5 倒序，相同再按 published_at
    筛选:
      - channel 可选
      - exclude_self 默认 true
      - content_type 可选（original/repost/text_only）
    注: work_top（置顶）MVP 暂不接入，留空后补。
    """
    page, page_size = get_pagination_params()
    sort = request.args.get('sort', 'latest')
    if sort not in ALLOWED_SORT:
        return error_response(ErrorCode.PARAM_ERROR, '排序参数不合法', http_code=400)

    channel = request.args.get('channel')
    if channel and channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    ct = request.args.get('content_type')
    if ct and ct not in ALLOWED_CONTENT_TYPES:
        return error_response(ErrorCode.PARAM_ERROR, 'content_type 不合法', http_code=400)

    exclude_self = request.args.get('exclude_self', 'true').lower() != 'false'

    query = visible_works_query(request.user.id)
    if exclude_self:
        query = query.filter(Work.user_id != request.user.id)
    if channel:
        query = query.filter(Work.channel == channel)
    if ct:
        query = query.filter(Work.content_type == ct)

    if sort == 'hot':
        hot_score = (Work.like_count * 2 + Work.view_count + Work.repost_count * 1.5)
        query = query.order_by(hot_score.desc(), Work.published_at.desc())
    else:
        query = query.order_by(Work.published_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)


# 8B. 关注Tab推流：仅展示我关注的人，纯按 published_at 排序
@bp.route('/feed/following', methods=['GET'])
@login_required
def get_following_feed():
    """广场「关注」Tab：只展示我关注账号的作品，纯按发布时间倒序（无热度）。"""
    page, page_size = get_pagination_params()

    # 我关注的作者集合
    following_sq = db.session.query(Follow.followed_id) \
        .filter(Follow.follower_id == request.user.id).subquery()

    query = visible_works_query(request.user.id)
    query = query.filter(Work.user_id.in_(following_sq))
    # 纯按发布时间倒序
    query = query.order_by(Work.published_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)


# 9. 搜索作品（套可见性 + published_at 排序）
@bp.route('/search', methods=['GET'])
@login_required
def search_works():
    """按标题/描述/纯文字关键词搜索可见作品, 可叠加 channel/content_type 筛选。"""
    keyword = (request.args.get('q') or '').strip()
    if not keyword:
        return error_response(ErrorCode.PARAM_ERROR, '搜索关键词不能为空', http_code=400)
    if len(keyword) > 100:
        return error_response(ErrorCode.PARAM_ERROR, '关键词过长', http_code=400)

    channel = request.args.get('channel')
    if channel and channel not in ALLOWED_CHANNELS:
        return error_response(ErrorCode.CHANNEL_INVALID, '渠道不合法', http_code=400)

    ct = request.args.get('content_type')
    if ct and ct not in ALLOWED_CONTENT_TYPES:
        return error_response(ErrorCode.PARAM_ERROR, 'content_type 不合法', http_code=400)

    page, page_size = get_pagination_params()
    like_pattern = f'%{keyword}%'

    query = visible_works_query(request.user.id).filter(db.or_(
        Work.title.like(like_pattern),
        Work.description.like(like_pattern),
        Work.text_content.like(like_pattern),
    ))
    if channel:
        query = query.filter(Work.channel == channel)
    if ct:
        query = query.filter(Work.content_type == ct)
    query = query.order_by(Work.published_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)


# 10. 按技能标签筛选作品（套可见性 + published_at 排序）
@bp.route('/by-skill', methods=['GET'])
@login_required
def get_works_by_skill():
    """按技能标签筛选可见作品。"""
    skill_id = request.args.get('skill_id', type=int)
    if not skill_id:
        return error_response(ErrorCode.PARAM_ERROR, 'skill_id 不能为空', http_code=400)

    sort = request.args.get('sort', 'latest')
    if sort not in ALLOWED_SORT:
        return error_response(ErrorCode.PARAM_ERROR, '排序参数不合法', http_code=400)

    page, page_size = get_pagination_params()
    from sqlalchemy import text
    query = visible_works_query(request.user.id).filter(
        text("JSON_CONTAINS(skill_tags, CAST(:sid AS JSON))").bindparams(sid=skill_id)
    )
    if sort == 'hot':
        hot_score = (Work.like_count * 2 + Work.view_count + Work.repost_count * 1.5)
        query = query.order_by(hot_score.desc(), Work.published_at.desc())
    else:
        query = query.order_by(Work.published_at.desc())

    result = format_pagination(query, page, page_size)
    author_ids = list({w.user_id for w in result['list']})
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    result['list'] = [build_work_list_item(w, author=authors.get(w.user_id), current_user_id=request.user.id) for w in result['list']]
    return success_response(data=result)




# 11. 快捷转发作品（等价于 content_type=repost POST /works/，前端转发按钮调用）
@bp.route('/<int:work_id>/repost', methods=['POST'])
@login_required
def repost_work(work_id):
    data = request.get_json() or {}
    description = data.get('description') or ''
    if len(description) > MAX_DESC_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '描述过长', http_code=400)

    visibility_type = data.get('visibility_type', 'public')
    if visibility_type not in ALLOWED_VISIBILITY:
        return error_response(ErrorCode.VISIBILITY_TYPE_INVALID, 'visibility_type 不合法', http_code=400)

    location = data.get('location')
    location = (location.strip() or None) if isinstance(location, str) else None

    allow_users = data.get('allow_users') or []
    deny_users = data.get('deny_users') or []

    # 原作品必须可见 + 未删除 + 已发布
    src, err = get_work_or_404(work_id, viewer_id=request.user.id, enforce_visibility=True)
    if err:
        return err
    if src.status != 'published':
        return error_response(ErrorCode.WORK_NOT_FOUND, '原作品未发布，不可转发', http_code=400)

    from datetime import datetime
    import json
    title = (description[:MAX_TITLE_LEN]) if description else f'转发 作品#{src.id}'
    new_work = Work(
        user_id=request.user.id,
        title=title,
        description=description,
        channel=src.channel,
        content_type='repost',
        image_layout=src.image_layout,
        visibility_type=visibility_type,
        location=location,
        cover_url=src.cover_url,
        is_collaborative=False,
        status='published',
        published_at=datetime.utcnow(),
    )
    new_work.files = src.files or '[]'
    new_work.collaborators = '[]'
    new_work.skill_tags = src.skill_tags or '[]'

    db.session.add(new_work)
    db.session.flush()

    repost = WorkRepost(
        work_id=new_work.id,
        source_work_id=src.id,
        source_project_id=None,
        source_user_id=src.user_id,
    )
    db.session.add(repost)
    src.repost_count = (src.repost_count or 0) + 1

    if visibility_type == 'custom_allow':
        if not allow_users:
            return error_response(ErrorCode.PARAM_ERROR, 'custom_allow 必须传 allow_users', http_code=400)
        if len(allow_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'allow_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        for uid in allow_users:
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=new_work.id, rule_type='allow', user_id=uid))
    if visibility_type == 'custom_deny':
        if len(deny_users) > MAX_CUSTOM_RULES:
            return error_response(ErrorCode.CUSTOM_RULES_LIMIT, f'deny_users 最多 {MAX_CUSTOM_RULES} 人', http_code=400)
        for uid in deny_users:
            if User.query.get(uid):
                db.session.add(WorkVisibilityRule(work_id=new_work.id, rule_type='deny', user_id=uid))

    db.session.commit()
    logger.info(f'快捷转发: src_work_id={work_id} -> new_work_id={new_work.id}, by={request.user.id}')

    author = User.query.get(new_work.user_id)
    resp = new_work.to_dict(with_author=True, author=author)
    src_author = User.query.get(src.user_id)
    resp['source'] = {'type': 'work', 'source_user_id': src.user_id,
                       'data': src.to_dict(with_author=True, author=src_author)}
    return success_response(data=resp, message='转发成功')
