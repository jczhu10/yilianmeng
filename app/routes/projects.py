# -*- coding: utf-8 -*-
"""协作项目模块路由"""
import logging
from datetime import datetime
from flask import Blueprint, request
from app import db
from app.models import Project, ProjectApplication, User, Skill
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


# 状态枚举
PROJECT_STATUSES = {'recruiting', 'ongoing', 'completed', 'closed'}
PROJECT_MODES = {'free', 'paid'}
APP_STATUSES = {'pending', 'approved', 'rejected'}
# 可编辑状态：仅 recruiting 状态项目可编辑
EDITABLE_STATUSES = {'recruiting'}

MAX_TITLE_LEN = 200
MAX_DESC_LEN = 2000
MAX_MESSAGE_LEN = 500
MAX_SKILL_TAGS = 10


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
    """构造项目对象，附加发起人/成员数/申请列表"""
    item = project.to_dict()
    # 发起人信息
    creator = User.query.get(project.user_id)
    item['creator'] = creator.to_dict() if creator else None
    item['is_creator'] = (current_user_id == project.user_id)
    # 成员数 = 已通过申请数 + 1(发起人)
    member_count = ProjectApplication.query.filter_by(
        project_id=project.id, status='approved'
    ).count()
    item['member_count'] = member_count + 1
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
        approved_apps = ProjectApplication.query.filter_by(
            project_id=project.id, status='approved'
        ).all()
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

    project = Project(
        user_id=request.user.id,
        title=title,
        description=description,
        mode=mode,
        budget=budget,
        deadline=deadline_dt,
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
