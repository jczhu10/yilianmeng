import logging
from flask import Blueprint, request
from app import db
from app.models import Profile, SkillCategory, Skill, ProfileSkill
from app.utils.helpers import login_required, success_response, error_response

bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

# 业务错误码
class ErrorCode:
    PARAM_ERROR = 400
    NOT_FOUND = 404
    IDENTITY_TYPE_ERROR = 2001
    SKILL_NOT_FOUND = 2002
    SKILL_DUPLICATE = 2003
    SKILL_LIMIT_EXCEEDED = 2004

# 允许的身份类型
ALLOWED_IDENTITY_TYPES = {'amateur', 'professional'}
# 每个用户最多选择的技能数
MAX_SKILLS_PER_USER = 20


def get_or_create_profile(user_id):
    """获取或创建用户档案"""
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


# 1. 获取我的档案（含技能）
@bp.route('/me', methods=['GET'])
@login_required
def get_my_profile():
    profile = get_or_create_profile(request.user.id)
    return success_response(data=profile.to_dict(with_skills=True))


# 2. 更新我的档案基础信息
@bp.route('/me', methods=['PUT'])
@login_required
def update_my_profile():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)

    # 身份类型
    if 'identity_type' in data:
        identity_type = data['identity_type']
        if identity_type not in ALLOWED_IDENTITY_TYPES:
            return error_response(ErrorCode.IDENTITY_TYPE_ERROR, '身份类型不合法', http_code=400)
        profile.identity_type = identity_type

    # 风格标签
    if 'style_tags' in data:
        style_tags = data['style_tags']
        if not isinstance(style_tags, list):
            return error_response(ErrorCode.PARAM_ERROR, 'style_tags 必须为数组', http_code=400)
        if len(style_tags) > 10:
            return error_response(ErrorCode.PARAM_ERROR, '风格标签最多10个', http_code=400)
        profile.set_style_tags([str(t).strip() for t in style_tags if str(t).strip()])

    # 工作经历
    if 'work_history' in data:
        profile.work_history = str(data['work_history'] or '')[:2000]

    # 教育背景
    if 'education' in data:
        profile.education = str(data['education'] or '')[:2000]

    db.session.commit()
    logger.info(f'档案更新: user_id={request.user.id}')
    return success_response(data=profile.to_dict(with_skills=True), message='档案更新成功')


# 3. 更新我的技能（覆盖式：传入 skill_id 列表）
@bp.route('/skills', methods=['PUT'])
@login_required
def update_my_skills():
    data = request.get_json()
    if not data or 'skill_ids' not in data:
        return error_response(ErrorCode.PARAM_ERROR, 'skill_ids 参数不能为空', http_code=400)

    skill_ids = data['skill_ids']
    if not isinstance(skill_ids, list):
        return error_response(ErrorCode.PARAM_ERROR, 'skill_ids 必须为数组', http_code=400)

    # 去重
    skill_ids = list(dict.fromkeys(skill_ids))

    if len(skill_ids) > MAX_SKILLS_PER_USER:
        return error_response(
            ErrorCode.SKILL_LIMIT_EXCEEDED,
            f'最多选择 {MAX_SKILLS_PER_USER} 个技能',
            http_code=400
        )

    # 校验所有 skill_id 是否存在
    valid_skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
    if len(valid_skills) != len(skill_ids):
        return error_response(ErrorCode.SKILL_NOT_FOUND, '存在无效的技能ID', http_code=404)

    profile = get_or_create_profile(request.user.id)

    # 覆盖式更新：先删除旧关联，再新增
    ProfileSkill.query.filter_by(profile_id=profile.id).delete()
    for skill_id in skill_ids:
        db.session.add(ProfileSkill(profile_id=profile.id, skill_id=skill_id))

    db.session.commit()
    logger.info(f'技能更新: user_id={request.user.id}, skills={skill_ids}')

    return success_response(
        data={'skills': [s.to_dict() for s in valid_skills]},
        message='技能更新成功'
    )


# 4. 获取我的技能列表
@bp.route('/skills/mine', methods=['GET'])
@login_required
def get_my_skills():
    profile = get_or_create_profile(request.user.id)
    skills = [ps.skill.to_dict() for ps in profile.profile_skills if ps.skill]
    return success_response(data={'skills': skills})


# 5. 获取所有技能分类（含子技能，用于前端选择器）
@bp.route('/skills/categories', methods=['GET'])
def get_skill_categories():
    categories = SkillCategory.query.order_by(SkillCategory.sort_order).all()
    return success_response(
        data={'categories': [c.to_dict(with_skills=True) for c in categories]}
    )


# 6. 获取所有技能（扁平列表，可按 category_id 筛选）
@bp.route('/skills', methods=['GET'])
def get_skills():
    category_id = request.args.get('category_id', type=int)

    query = Skill.query
    if category_id:
        query = query.filter_by(category_id=category_id)

    skills = query.order_by(Skill.category_id, Skill.sort_order).all()
    return success_response(data={'skills': [s.to_dict() for s in skills]})


# 7. 查看他人档案（含技能）
@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        return error_response(ErrorCode.NOT_FOUND, '该用户尚未创建档案', http_code=404)
    return success_response(data=profile.to_dict(with_skills=True))
