# -*- coding: utf-8 -*-
"""协作项目模块路由"""
import logging
import json
from datetime import datetime
from flask import Blueprint, request
from app import db
from app.models import Project, ProjectApplication, User, Skill, Notification, ProjectViewHistory, Rating, RatingTag, Profile, ProfileSkill
from app.utils.helpers import (
    login_required, success_response, error_response,
    get_pagination_params, format_pagination
)

bp = Blueprint('projects', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    PROJECT_NOT_FOUND = 5001
    NO_PERMISSION = 5002
    INVALID_STATUS = 5003
    CANNOT_APPLY_OWN = 5004
    ALREADY_APPLIED = 5005
    APPLICATION_NOT_FOUND = 5006
    APPLICATION_PROCESSED = 5007
    NOT_A_MEMBER = 5008
    CANNOT_RATE_SELF = 5009
    ALREADY_RATED = 5010
    PROJECT_NOT_COMPLETED = 5011
    INVALID_RATING_SCORE = 5012
    INVALID_RATING_TAGS = 5013


# 状态枚举
PROJECT_STATUSES = {'recruiting', 'ongoing', 'completed', 'closed'}
PROJECT_MODES = {'free', 'paid'}
# 申请状态：pending/approved/rejected 为原有流转；left(主动退出)/removed(被踢) 为成员管理扩展值
APP_STATUSES = {'pending', 'approved', 'rejected', 'left', 'removed'}
# 可查询的申请状态（用于我的申请列表过滤）
APP_QUERY_STATUSES = {'pending', 'approved', 'rejected', 'left', 'removed'}
# 项目内互评分数范围
RATING_SCORE_MIN = 1
RATING_SCORE_MAX = 5
# 可编辑状态：仅 recruiting 状态项目可编辑
EDITABLE_STATUSES = {'recruiting'}

MAX_TITLE_LEN = 200
MAX_DESC_LEN = 2000
MAX_MESSAGE_LEN = 500
MAX_SKILL_TAGS = 10
MAX_TOPIC_LEN = 100
MAX_COVER_URL_LEN = 255
MAX_MEMBERS_MIN = 1
MAX_MEMBERS_MAX = 999
MIN_LEVEL = 1
MAX_LEVEL = 100


def validate_skills(skill_ids):
    """校验技能ID数组，返回 (valid_ids, error_response_or_None)"""
    if not isinstance(skill_ids, list):
        return None, error_response(ErrorCode.PARAM_ERROR, 'required_skills 必须为数组', http_code=400)
    if len(skill_ids) > MAX_SKILL_TAGS:
        return None, error_response(ErrorCode.PARAM_ERROR, '技能标签最多 10 个', http_code=400)
    skill_ids = list(dict.fromkeys(skill_ids))
    if not skill_ids:
        return [], None
    valid = Skill.query.filter(Skill.id.in_(skill_ids)).all()
    if len(valid) != len(skill_ids):
        return None, error_response(ErrorCode.PARAM_ERROR, '存在无效的技能ID', http_code=400)
    return skill_ids, None


def get_project_or_404(project_id, include_closed=False):
    query = Project.query.filter_by(id=project_id)
    project = query.first()
    if not project:
        return None, error_response(ErrorCode.PROJECT_NOT_FOUND, '项目不存在', http_code=404)
    return project, None


def build_project_item(project, current_user_id=None, with_applications=False, with_members=False):
    """构造项目对象，附加发起人/成员数/申请列表/成员头像/队长技能/队长参与项目数"""
    item = project.to_dict()
    # 发起人信息
    creator = User.query.get(project.user_id)
    if creator:
        creator_dict = creator.to_dict()
        # 队长技能列表
        profile = Profile.query.filter_by(user_id=creator.id).first()
        if profile:
            pss = ProfileSkill.query.filter_by(profile_id=profile.id).all()
            creator_dict['skills'] = [ps.skill.to_dict() for ps in pss if ps.skill]
        else:
            creator_dict['skills'] = []
        # 队长参与项目次数（作为 approved 成员的项目数）
        joined_count = ProjectApplication.query.filter_by(
            user_id=creator.id, status='approved'
        ).count()
        creator_dict['joined_project_count'] = joined_count
        item['creator'] = creator_dict
    else:
        item['creator'] = None
    item['is_creator'] = (current_user_id == project.user_id)
    # 成员数 = 已通过申请数 + 1(发起人)
    approved_apps = ProjectApplication.query.filter_by(
        project_id=project.id, status='approved'
    ).all()
    member_count = len(approved_apps)
    item['member_count'] = member_count + 1
    # 已招募队友头像（前 5 个，含发起人）
    member_ids = [project.user_id] + [a.user_id for a in approved_apps[:4]]
    member_users = {u.id: u for u in User.query.filter(User.id.in_(member_ids)).all()} if member_ids else {}
    item['member_avatars'] = [
        {'user_id': uid, 'avatar': member_users[uid].avatar, 'nickname': member_users[uid].nickname}
        for uid in member_ids if uid in member_users
    ]
    # 当前用户是否已申请
    if current_user_id is not None:
        app = ProjectApplication.query.filter_by(
            project_id=project.id, user_id=current_user_id
        ).first()
        item['my_application'] = app.to_dict() if app else None
    else:
        item['my_application'] = None
    # 申请列表（仅发起人可见）
    if with_applications and current_user_id == project.user_id:
        apps = ProjectApplication.query.filter_by(project_id=project.id).order_by(
            ProjectApplication.created_at.desc()
        ).all()
        applicant_ids = [a.user_id for a in apps]
        applicants = {u.id: u for u in User.query.filter(User.id.in_(applicant_ids)).all()} if applicant_ids else {}
        item['applications'] = [build_application_item(a, applicants.get(a.user_id)) for a in apps]
    else:
        item['applications'] = None
    # 成员列表
    if with_members:
        member_ids = [project.user_id] + [a.user_id for a in approved_apps]
        members = {u.id: u for u in User.query.filter(User.id.in_(member_ids)).all()} if member_ids else {}
        item['members'] = [members.get(uid).to_dict() for uid in member_ids if members.get(uid)]
    else:
        item['members'] = None
    return item


def build_application_item(application, applicant=None):
    item = application.to_dict()
    item['applicant'] = applicant.to_dict() if applicant else None
    return item


# 1. 发起协作项目
@bp.route('/', methods=['POST'])
@login_required
def create_project():
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

    required_skills = data.get('required_skills') or []
    valid_skills, err = validate_skills(required_skills)
    if err:
        return err

    mode = data.get('mode', 'free')
    if mode not in PROJECT_MODES:
        return error_response(ErrorCode.PARAM_ERROR, 'mode 不合法（free/paid）', http_code=400)

    budget = int(data.get('budget') or 0)
    if budget < 0:
        return error_response(ErrorCode.PARAM_ERROR, '预算不能为负', http_code=400)

    deadline = data.get('deadline')
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', ''))
        except (ValueError, TypeError):
            return error_response(ErrorCode.PARAM_ERROR, 'deadline 格式不合法（ISO 8601）', http_code=400)

    # 新增字段解析与校验
    topic = (data.get('topic') or '').strip()
    if len(topic) > MAX_TOPIC_LEN:
        return error_response(ErrorCode.PARAM_ERROR, 'topic 过长', http_code=400)

    cover_url = data.get('cover_url') or ''
    if len(cover_url) > MAX_COVER_URL_LEN:
        return error_response(ErrorCode.PARAM_ERROR, 'cover_url 过长', http_code=400)

    max_members = int(data.get('max_members', 10))
    if max_members < MAX_MEMBERS_MIN or max_members > MAX_MEMBERS_MAX:
        return error_response(ErrorCode.PARAM_ERROR, f'max_members 须在 {MAX_MEMBERS_MIN}-{MAX_MEMBERS_MAX} 之间', http_code=400)

    required_level = int(data.get('required_level', 1))
    if required_level < MIN_LEVEL or required_level > MAX_LEVEL:
        return error_response(ErrorCode.PARAM_ERROR, f'required_level 须在 {MIN_LEVEL}-{MAX_LEVEL} 之间', http_code=400)

    required_project_count = int(data.get('required_project_count', 0))
    if required_project_count < 0:
        return error_response(ErrorCode.PARAM_ERROR, 'required_project_count 不能为负', http_code=400)

    contact_visible = bool(data.get('contact_visible', True))

    project = Project(
        user_id=request.user.id,
        title=title,
        description=description,
        mode=mode,
        budget=budget,
        deadline=deadline_dt,
        max_members=max_members,
        cover_url=cover_url,
        topic=topic,
        required_level=required_level,
        required_project_count=required_project_count,
        contact_visible=contact_visible,
        status='recruiting'
    )
    db.session.add(project)
    db.session.flush()
    project.set_required_skills(valid_skills)
    db.session.commit()
    logger.info(f'项目创建: project_id={project.id}, user_id={request.user.id}')

    return success_response(data=build_project_item(project, current_user_id=request.user.id), message='项目创建成功')


# 2. 项目列表
@bp.route('/', methods=['GET'])
@login_required
def list_projects():
    page, page_size = get_pagination_params()
    status = request.args.get('status')
    mode = request.args.get('mode')
    skill_id = request.args.get('skill_id', type=int)

    query = Project.query
    if status:
        if status not in PROJECT_STATUSES:
            return error_response(ErrorCode.PARAM_ERROR, '状态参数不合法', http_code=400)
        query = query.filter(Project.status == status)
    else:
        # 默认不返回 closed
        query = query.filter(Project.status != 'closed')
    if mode:
        if mode not in PROJECT_MODES:
            return error_response(ErrorCode.PARAM_ERROR, 'mode 参数不合法', http_code=400)
        query = query.filter(Project.mode == mode)
    if skill_id:
        from sqlalchemy import text
        query = query.filter(
            text("JSON_CONTAINS(required_skills, CAST(:sid AS JSON))").bindparams(sid=skill_id)
        )

    query = query.order_by(Project.created_at.desc())
    result = format_pagination(query, page, page_size)
    result['list'] = [build_project_item(p, current_user_id=request.user.id) for p in result['list']]
    return success_response(data=result)


# 3. 项目详情
@bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project_detail(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    # 发起人可见申请列表，其他用户可见成员列表
    is_creator = (request.user.id == project.user_id)

    # 非发起人访问时写浏览记录
    if not is_creator:
        existing = ProjectViewHistory.query.filter_by(user_id=request.user.id, project_id=project.id).first()
        if existing:
            existing.view_count = (existing.view_count or 0) + 1
            existing.last_viewed_at = datetime.utcnow()
        else:
            db.session.add(ProjectViewHistory(user_id=request.user.id, project_id=project.id, author_id=project.user_id))
        db.session.commit()

    item = build_project_item(
        project,
        current_user_id=request.user.id,
        with_applications=is_creator,
        with_members=(not is_creator and project.status in ('ongoing', 'completed'))
    )
    return success_response(data=item)


# 4. 编辑项目（仅发起人，recruiting 状态可编辑）
@bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    if project.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作，仅发起人可编辑', http_code=403)
    if project.status not in EDITABLE_STATUSES:
        return error_response(ErrorCode.INVALID_STATUS, f'当前状态({project.status})不可编辑，仅 recruiting 状态可编辑', http_code=400)

    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    if 'title' in data:
        title = (data['title'] or '').strip()
        if not title:
            return error_response(ErrorCode.PARAM_ERROR, '标题不能为空', http_code=400)
        if len(title) > MAX_TITLE_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '标题过长', http_code=400)
        project.title = title
    if 'description' in data:
        description = data['description'] or ''
        if len(description) > MAX_DESC_LEN:
            return error_response(ErrorCode.PARAM_ERROR, '描述过长', http_code=400)
        project.description = description
    if 'required_skills' in data:
        valid_skills, err = validate_skills(data['required_skills'] or [])
        if err:
            return err
        project.set_required_skills(valid_skills)
    if 'mode' in data:
        mode = data['mode']
        if mode not in PROJECT_MODES:
            return error_response(ErrorCode.PARAM_ERROR, 'mode 不合法', http_code=400)
        project.mode = mode
    if 'budget' in data:
        budget = int(data['budget'] or 0)
        if budget < 0:
            return error_response(ErrorCode.PARAM_ERROR, '预算不能为负', http_code=400)
        project.budget = budget
    if 'deadline' in data:
        deadline = data['deadline']
        if deadline:
            try:
                project.deadline = datetime.fromisoformat(deadline.replace('Z', ''))
            except (ValueError, TypeError):
                return error_response(ErrorCode.PARAM_ERROR, 'deadline 格式不合法', http_code=400)
        else:
            project.deadline = None
    if 'topic' in data:
        topic = (data['topic'] or '').strip()
        if len(topic) > MAX_TOPIC_LEN:
            return error_response(ErrorCode.PARAM_ERROR, 'topic 过长', http_code=400)
        project.topic = topic
    if 'cover_url' in data:
        cover_url = data['cover_url'] or ''
        if len(cover_url) > MAX_COVER_URL_LEN:
            return error_response(ErrorCode.PARAM_ERROR, 'cover_url 过长', http_code=400)
        project.cover_url = cover_url
    if 'max_members' in data:
        max_members = int(data['max_members'])
        if max_members < MAX_MEMBERS_MIN or max_members > MAX_MEMBERS_MAX:
            return error_response(ErrorCode.PARAM_ERROR, f'max_members 须在 {MAX_MEMBERS_MIN}-{MAX_MEMBERS_MAX} 之间', http_code=400)
        project.max_members = max_members
    if 'required_level' in data:
        required_level = int(data['required_level'])
        if required_level < MIN_LEVEL or required_level > MAX_LEVEL:
            return error_response(ErrorCode.PARAM_ERROR, f'required_level 须在 {MIN_LEVEL}-{MAX_LEVEL} 之间', http_code=400)
        project.required_level = required_level
    if 'required_project_count' in data:
        required_project_count = int(data['required_project_count'])
        if required_project_count < 0:
            return error_response(ErrorCode.PARAM_ERROR, 'required_project_count 不能为负', http_code=400)
        project.required_project_count = required_project_count
    if 'contact_visible' in data:
        project.contact_visible = bool(data['contact_visible'])

    db.session.commit()
    logger.info(f'项目编辑: project_id={project.id}, user_id={request.user.id}')
    return success_response(data=build_project_item(project, current_user_id=request.user.id), message='项目更新成功')


# 5. 申请加入项目
@bp.route('/<int:project_id>/apply', methods=['POST'])
@login_required
def apply_project(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    # 不能申请自己发起的项目
    if project.user_id == request.user.id:
        return error_response(ErrorCode.CANNOT_APPLY_OWN, '不能申请自己发起的项目', http_code=400)
    # 仅 recruiting 状态可申请
    if project.status != 'recruiting':
        return error_response(ErrorCode.INVALID_STATUS, '该项目不在招募中，无法申请', http_code=400)
    # 不能重复申请
    existing = ProjectApplication.query.filter_by(
        project_id=project_id, user_id=request.user.id
    ).first()
    if existing:
        return error_response(ErrorCode.ALREADY_APPLIED, '已申请过该项目', http_code=400)

    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    if len(message) > MAX_MESSAGE_LEN:
        return error_response(ErrorCode.PARAM_ERROR, f'申请理由最多 {MAX_MESSAGE_LEN} 字', http_code=400)

    application = ProjectApplication(
        project_id=project_id,
        user_id=request.user.id,
        message=message,
        status='pending'
    )
    db.session.add(application)

    # 给项目发起人发待办通知
    db.session.add(Notification(
        user_id=project.user_id,
        type='todo',
        subtype='apply',
        title='新的项目申请',
        content=f'{request.user.nickname} 申请加入你的项目「{project.title}」',
        sender_id=request.user.id,
        related_type='project',
        related_id=project.id
    ))

    db.session.commit()
    logger.info(f'项目申请: application_id={application.id}, project_id={project_id}, user_id={request.user.id}')

    applicant = User.query.get(request.user.id)
    return success_response(data=build_application_item(application, applicant), message='申请已提交')


def _process_application(project_id, app_id, new_status, action_name):
    """审批申请的通用逻辑（approved/rejected）"""
    project, err = get_project_or_404(project_id)
    if err:
        return err
    if project.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, f'无权{action_name}，仅发起人可操作', http_code=403)
    if project.status != 'recruiting':
        return error_response(ErrorCode.INVALID_STATUS, '项目不在招募中，无法审批', http_code=400)

    application = ProjectApplication.query.filter_by(id=app_id, project_id=project_id).first()
    if not application:
        return error_response(ErrorCode.APPLICATION_NOT_FOUND, '申请不存在', http_code=404)
    if application.status != 'pending':
        return error_response(ErrorCode.APPLICATION_PROCESSED, f'申请已处理（{application.status}）', http_code=400)

    application.status = new_status
    application.processed_at = datetime.utcnow()

    # 通过申请后，项目自动转为 ongoing
    if new_status == 'approved':
        project.status = 'ongoing'

    db.session.commit()
    logger.info(f'申请{action_name}: app_id={app_id}, status={new_status}, operator={request.user.id}')

    applicant = User.query.get(application.user_id)
    return success_response(data=build_application_item(application, applicant), message=f'已{action_name}该申请')


# 6. 通过申请
@bp.route('/<int:project_id>/applications/<int:app_id>/approve', methods=['POST'])
@login_required
def approve_application(project_id, app_id):
    return _process_application(project_id, app_id, 'approved', '通过')


# 7. 拒绝申请
@bp.route('/<int:project_id>/applications/<int:app_id>/reject', methods=['POST'])
@login_required
def reject_application(project_id, app_id):
    return _process_application(project_id, app_id, 'rejected', '拒绝')


# 8. 关闭项目（仅发起人）
@bp.route('/<int:project_id>/close', methods=['POST'])
@login_required
def close_project(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    if project.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作，仅发起人可关闭', http_code=403)
    if project.status == 'closed':
        return success_response(message='项目已关闭')

    project.status = 'closed'
    db.session.commit()
    logger.info(f'项目关闭: project_id={project.id}, user_id={request.user.id}')
    return success_response(message='项目已关闭')


# 指定用户的项目列表
@bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_projects(user_id):
    page, page_size = get_pagination_params()
    query = Project.query.filter(Project.user_id == user_id, Project.status != 'deleted') \
        .order_by(Project.created_at.desc())
    result = format_pagination(query, page, page_size)
    result['list'] = [build_project_item(p, current_user_id=request.user.id) for p in result['list']]
    return success_response(data=result)


# 9. 我的项目（发起的 + 已通过申请参与的）
@bp.route('/mine', methods=['GET'])
@login_required
def my_projects():
    page, page_size = get_pagination_params()
    role = request.args.get('role', 'all')  # all/created/joined

    if role == 'created':
        query = Project.query.filter(Project.user_id == request.user.id)
    elif role == 'joined':
        # 已通过申请的项目ID
        joined_ids = db.session.query(ProjectApplication.project_id).filter(
            ProjectApplication.user_id == request.user.id,
            ProjectApplication.status == 'approved'
        ).subquery()
        query = Project.query.filter(Project.id.in_(joined_ids))
    else:
        # 全部：发起的 + 已通过的
        joined_ids = db.session.query(ProjectApplication.project_id).filter(
            ProjectApplication.user_id == request.user.id,
            ProjectApplication.status == 'approved'
        ).subquery()
        query = Project.query.filter(
            db.or_(Project.user_id == request.user.id, Project.id.in_(joined_ids))
        )

    query = query.order_by(Project.created_at.desc())
    result = format_pagination(query, page, page_size)
    result['list'] = [build_project_item(p, current_user_id=request.user.id) for p in result['list']]
    return success_response(data=result)


# ============================================================
# 项目模块新增接口（成员管理 / 互评）
# ============================================================

def _is_project_member(project, user_id):
    """判断 user_id 是否为项目成员（发起人 or approved 申请）"""
    if project.user_id == user_id:
        return True
    return ProjectApplication.query.filter_by(
        project_id=project.id, user_id=user_id, status='approved'
    ).first() is not None


def _build_my_application_item(application, project=None):
    """我的申请列表项：附带项目摘要 + 动态过期标记"""
    item = application.to_dict(with_expired=True)
    if project is None:
        project = Project.query.get(application.project_id)
    item['project'] = project.to_dict() if project else None
    return item


# 10. 我的申请列表
@bp.route('/my-applications', methods=['GET'])
@login_required
def my_applications():
    page, page_size = get_pagination_params()
    status = request.args.get('status')
    if status and status not in APP_QUERY_STATUSES:
        return error_response(ErrorCode.PARAM_ERROR, 'status 参数不合法', http_code=400)

    query = ProjectApplication.query.filter_by(user_id=request.user.id)
    if status:
        query = query.filter(ProjectApplication.status == status)
    query = query.order_by(ProjectApplication.created_at.desc())
    result = format_pagination(query, page, page_size)
    # 批量预取项目，避免 N+1
    pids = [a.project_id for a in result['list']]
    projects_map = {p.id: p for p in Project.query.filter(Project.id.in_(pids)).all()} if pids else {}
    result['list'] = [_build_my_application_item(a, projects_map.get(a.project_id)) for a in result['list']]
    return success_response(data=result)


# 11. 退出项目（成员主动退出）
@bp.route('/<int:project_id>/leave', methods=['POST'])
@login_required
def leave_project(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    # 发起人不能退出自己发起的项目
    if project.user_id == request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '发起人不能退出自己的项目', http_code=400)
    # 项目须处于 ongoing 或 completed 状态
    if project.status not in ('ongoing', 'completed'):
        return error_response(ErrorCode.INVALID_STATUS, '当前项目状态不允许退出', http_code=400)

    application = ProjectApplication.query.filter_by(
        project_id=project_id, user_id=request.user.id, status='approved'
    ).first()
    if not application:
        return error_response(ErrorCode.NOT_A_MEMBER, '你不是该项目的成员', http_code=400)

    application.status = 'left'
    application.processed_at = datetime.utcnow()

    # 给发起人发通知
    db.session.add(Notification(
        user_id=project.user_id,
        type='system',
        subtype='leave',
        title='成员退出项目',
        content=f'{request.user.nickname} 退出了你的项目「{project.title}」',
        sender_id=request.user.id,
        related_type='project',
        related_id=project.id
    ))

    db.session.commit()
    logger.info(f'成员退出项目: project_id={project_id}, user_id={request.user.id}')
    return success_response(message='已退出项目')


# 12. 踢人（发起人移除成员）
@bp.route('/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    if project.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作，仅发起人可踢人', http_code=403)
    if project.user_id == user_id:
        return error_response(ErrorCode.NO_PERMISSION, '不能踢出自己', http_code=400)
    if project.status not in ('ongoing', 'completed'):
        return error_response(ErrorCode.INVALID_STATUS, '当前项目状态不允许踢人', http_code=400)

    application = ProjectApplication.query.filter_by(
        project_id=project_id, user_id=user_id, status='approved'
    ).first()
    if not application:
        return error_response(ErrorCode.NOT_A_MEMBER, '该用户不是项目成员', http_code=400)

    application.status = 'removed'
    application.processed_at = datetime.utcnow()

    # 给被踢者发通知
    db.session.add(Notification(
        user_id=user_id,
        type='system',
        subtype='removed',
        title='你被移出项目',
        content=f'你被移出项目「{project.title}」',
        sender_id=request.user.id,
        related_type='project',
        related_id=project.id
    ))

    db.session.commit()
    logger.info(f'踢人: project_id={project_id}, target_user_id={user_id}, operator={request.user.id}')
    return success_response(message='已移出该成员')


# 13. 结束项目（ongoing -> completed）
@bp.route('/<int:project_id>/finish', methods=['POST'])
@login_required
def finish_project(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    if project.user_id != request.user.id:
        return error_response(ErrorCode.NO_PERMISSION, '无权操作，仅发起人可结束项目', http_code=403)
    if project.status == 'completed':
        return success_response(message='项目已结束')
    if project.status != 'ongoing':
        return error_response(ErrorCode.INVALID_STATUS, f'当前状态({project.status})不可结束，仅 ongoing 可结束', http_code=400)

    project.status = 'completed'
    db.session.commit()
    logger.info(f'项目结束: project_id={project.id}, user_id={request.user.id}')
    return success_response(message='项目已结束')


# 14. 提交互评
@bp.route('/<int:project_id>/ratings', methods=['POST'])
@login_required
def create_rating(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    # 项目须已完成
    if project.status != 'completed':
        return error_response(ErrorCode.PROJECT_NOT_COMPLETED, '项目未完成，无法互评', http_code=400)
    # 当前用户须为项目成员
    if not _is_project_member(project, request.user.id):
        return error_response(ErrorCode.NOT_A_MEMBER, '你不是该项目成员，无法评价', http_code=403)

    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    to_user_id = data.get('to_user_id')
    if not isinstance(to_user_id, int):
        return error_response(ErrorCode.PARAM_ERROR, 'to_user_id 必须为整数', http_code=400)
    if to_user_id == request.user.id:
        return error_response(ErrorCode.CANNOT_RATE_SELF, '不能评价自己', http_code=400)
    # 被评价者须为项目成员
    if not _is_project_member(project, to_user_id):
        return error_response(ErrorCode.NOT_A_MEMBER, '被评价者不是该项目成员', http_code=400)

    score = data.get('score')
    if not isinstance(score, int) or score < RATING_SCORE_MIN or score > RATING_SCORE_MAX:
        return error_response(ErrorCode.INVALID_RATING_SCORE, f'score 须在 {RATING_SCORE_MIN}-{RATING_SCORE_MAX} 之间', http_code=400)

    comment = data.get('comment') or ''
    if len(comment) > MAX_DESC_LEN:
        return error_response(ErrorCode.PARAM_ERROR, '评价内容过长', http_code=400)

    # 标签校验
    tag_ids = data.get('tags') or []
    if not isinstance(tag_ids, list):
        return error_response(ErrorCode.PARAM_ERROR, 'tags 必须为数组', http_code=400)
    if tag_ids:
        valid_tags = RatingTag.query.filter(RatingTag.id.in_(tag_ids), RatingTag.is_active == True).all()
        if len(valid_tags) != len(set(tag_ids)):
            return error_response(ErrorCode.INVALID_RATING_TAGS, '存在无效或未启用的评价标签', http_code=400)
        tag_ids = list(dict.fromkeys(tag_ids))

    is_anonymous = bool(data.get('is_anonymous', False))

    # 唯一性校验：(project_id, from_user_id, to_user_id) 不可重复
    existing = Rating.query.filter_by(
        project_id=project_id, from_user_id=request.user.id, to_user_id=to_user_id
    ).first()
    if existing:
        return error_response(ErrorCode.ALREADY_RATED, '已评价过该成员', http_code=400)

    rating = Rating(
        project_id=project_id,
        from_user_id=request.user.id,
        to_user_id=to_user_id,
        score=score,
        comment=comment,
        tags=json.dumps(tag_ids),
        is_anonymous=is_anonymous
    )
    db.session.add(rating)
    db.session.commit()
    logger.info(f'互评提交: rating_id={rating.id}, project_id={project_id}, from={request.user.id}, to={to_user_id}')
    return success_response(data=rating.to_dict(), message='评价提交成功')


# 15. 查看互评列表
@bp.route('/<int:project_id>/ratings', methods=['GET'])
@login_required
def list_ratings(project_id):
    project, err = get_project_or_404(project_id)
    if err:
        return err
    # 仅项目成员可查看互评
    if not _is_project_member(project, request.user.id):
        return error_response(ErrorCode.NOT_A_MEMBER, '你不是该项目成员，无法查看互评', http_code=403)

    page, page_size = get_pagination_params()
    query = Rating.query.filter_by(project_id=project_id).order_by(Rating.created_at.desc())
    result = format_pagination(query, page, page_size)
    # 批量预取用户信息（用于非匿名评价展示发起人）
    from_user_ids = [r.from_user_id for r in result['list'] if not r.is_anonymous]
    users_map = {u.id: u for u in User.query.filter(User.id.in_(from_user_ids)).all()} if from_user_ids else {}
    items = []
    for r in result['list']:
        d = r.to_dict()
        if r.is_anonymous:
            d['from_user_id'] = None
            d['from_user'] = None
        else:
            u = users_map.get(r.from_user_id)
            d['from_user'] = u.to_dict() if u else None
        items.append(d)
    result['list'] = items
    return success_response(data=result)
