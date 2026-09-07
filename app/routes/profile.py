import logging
from datetime import datetime
from flask import Blueprint, request
from app import db
from app.models import (
    Profile, SkillCategory, Skill, ProfileSkill,
    StyleTag, ProfileStyleTag,
    WorkExperience, WorkExperienceImage,
    EducationExperience,
    AbilityProof, AbilityProofFile
)
from app.utils.helpers import (
    login_required, success_response, error_response,
    save_file, allowed_file
)

bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    NOT_FOUND = 404
    IDENTITY_INVALID = 2001
    SKILL_NOT_FOUND = 2002
    SKILL_LIMIT_EXCEEDED = 2004
    STYLE_LIMIT_EXCEEDED = 2005
    STYLE_NOT_FOUND = 2006
    NO_PERMISSION = 2010
    SCHOOL_LEVEL_INVALID = 2011
    FILES_LIMIT_EXCEEDED = 2012


ALLOWED_IDENTITIES = {'学生', '艺术爱好者', '艺术相关工作者'}
ALLOWED_SCHOOL_LEVELS = {'小学', '中学', '大学'}
MAX_SKILLS = 5
MAX_STYLE_TAGS = 5
MAX_WORK_IMAGES = 5
MAX_ABILITY_FILES = 10
ALLOWED_FILE_TYPES = {'image', 'pdf', 'doc', 'video'}


def get_or_create_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id, identity='艺术爱好者')
        db.session.add(profile)
        db.session.commit()
    return profile


def guess_file_type(filename):
    ext = (filename.rsplit('.', 1)[-1] if '.' in filename else '').lower()
    if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        return 'image'
    if ext == 'pdf':
        return 'pdf'
    if ext in {'doc', 'docx'}:
        return 'doc'
    if ext in {'mp4', 'mov', 'avi', 'mkv'}:
        return 'video'
    return 'image'


# ==================== 档案基础（3个）====================

# 8. 获取我的完整档案
@bp.route('/me', methods=['GET'])
@login_required
def get_my_profile():
    profile = get_or_create_profile(request.user.id)
    return success_response(data=profile.to_dict(with_relations=True))


# 9. 更新档案基础信息
@bp.route('/me', methods=['PUT'])
@login_required
def update_my_profile():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)

    if 'identity' in data:
        identity = data['identity']
        if identity not in ALLOWED_IDENTITIES:
            return error_response(ErrorCode.IDENTITY_INVALID, '身份类型不合法，需为：学生/艺术爱好者/艺术相关工作者', http_code=400)
        profile.identity = identity

    db.session.commit()
    logger.info(f'档案更新: user_id={request.user.id}')
    return success_response(data=profile.to_dict(), message='档案更新成功')


# 10. 查看他人档案
@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        return error_response(ErrorCode.NOT_FOUND, '该用户尚未创建档案', http_code=404)
    return success_response(data=profile.to_dict(with_relations=True))


# ==================== 技能（4个）====================

# 11. 更新我的技能（覆盖式，上限5）
@bp.route('/skills', methods=['PUT'])
@login_required
def update_my_skills():
    data = request.get_json()
    if not data or 'skill_ids' not in data:
        return error_response(ErrorCode.PARAM_ERROR, 'skill_ids 参数不能为空', http_code=400)

    skill_ids = data['skill_ids']
    if not isinstance(skill_ids, list):
        return error_response(ErrorCode.PARAM_ERROR, 'skill_ids 必须为数组', http_code=400)

    skill_ids = list(dict.fromkeys(skill_ids))  # 去重
    if len(skill_ids) > MAX_SKILLS:
        return error_response(ErrorCode.SKILL_LIMIT_EXCEEDED, f'最多选择 {MAX_SKILLS} 个技能', http_code=400)

    valid_skills = Skill.query.filter(Skill.id.in_(skill_ids)).all() if skill_ids else []
    if len(valid_skills) != len(skill_ids):
        return error_response(ErrorCode.SKILL_NOT_FOUND, '存在无效的技能ID', http_code=404)

    profile = get_or_create_profile(request.user.id)
    ProfileSkill.query.filter_by(profile_id=profile.id).delete()
    for sid in skill_ids:
        db.session.add(ProfileSkill(profile_id=profile.id, skill_id=sid))

    db.session.commit()
    logger.info(f'技能更新: user_id={request.user.id}, skills={skill_ids}')
    return success_response(
        data={'skills': [s.to_dict() for s in valid_skills]},
        message='技能更新成功'
    )


# 12. 我的技能
@bp.route('/skills/mine', methods=['GET'])
@login_required
def get_my_skills():
    profile = get_or_create_profile(request.user.id)
    skills = [ps.skill.to_dict() for ps in profile.profile_skills if ps.skill]
    return success_response(data={'skills': skills})


# 13. 技能分类字典
@bp.route('/skills/categories', methods=['GET'])
def get_skill_categories():
    categories = SkillCategory.query.order_by(SkillCategory.sort_order).all()
    return success_response(
        data={'categories': [c.to_dict(with_skills=True) for c in categories]}
    )


# 14. 技能扁平列表
@bp.route('/skills', methods=['GET'])
def get_skills():
    category_id = request.args.get('category_id', type=int)
    query = Skill.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    skills = query.order_by(Skill.category_id, Skill.sort_order).all()
    return success_response(data={'skills': [s.to_dict() for s in skills]})


# ==================== 风格词汇（3个）====================

# 15. 风格词汇字典
@bp.route('/style-tags', methods=['GET'])
def get_style_tags():
    tags = StyleTag.query.filter_by(is_active=True).order_by(StyleTag.sort_order).all()
    return success_response(data={'style_tags': [t.to_dict() for t in tags]})


# 16. 更新我的风格词汇（覆盖式，上限5）
@bp.route('/style-tags', methods=['PUT'])
@login_required
def update_my_style_tags():
    data = request.get_json()
    if not data or 'style_tag_ids' not in data:
        return error_response(ErrorCode.PARAM_ERROR, 'style_tag_ids 参数不能为空', http_code=400)

    tag_ids = data['style_tag_ids']
    if not isinstance(tag_ids, list):
        return error_response(ErrorCode.PARAM_ERROR, 'style_tag_ids 必须为数组', http_code=400)

    tag_ids = list(dict.fromkeys(tag_ids))
    if len(tag_ids) > MAX_STYLE_TAGS:
        return error_response(ErrorCode.STYLE_LIMIT_EXCEEDED, f'最多选择 {MAX_STYLE_TAGS} 个风格词汇', http_code=400)

    valid_tags = StyleTag.query.filter(StyleTag.id.in_(tag_ids)).all() if tag_ids else []
    if len(valid_tags) != len(tag_ids):
        return error_response(ErrorCode.STYLE_NOT_FOUND, '存在无效的风格词汇ID', http_code=404)

    profile = get_or_create_profile(request.user.id)
    ProfileStyleTag.query.filter_by(profile_id=profile.id).delete()
    for tid in tag_ids:
        db.session.add(ProfileStyleTag(profile_id=profile.id, style_tag_id=tid))

    db.session.commit()
    logger.info(f'风格词汇更新: user_id={request.user.id}, tags={tag_ids}')
    return success_response(
        data={'style_tags': [t.to_dict() for t in valid_tags]},
        message='风格词汇更新成功'
    )


# 17. 我的风格词汇
@bp.route('/style-tags/mine', methods=['GET'])
@login_required
def get_my_style_tags():
    profile = get_or_create_profile(request.user.id)
    tags = [ps.style_tag.to_dict() for ps in profile.profile_style_tags if ps.style_tag]
    return success_response(data={'style_tags': tags})


# ==================== 工作经历（4个）====================

# 18. 我的工作经历列表
@bp.route('/work-experiences', methods=['GET'])
@login_required
def get_my_work_experiences():
    profile = get_or_create_profile(request.user.id)
    items = WorkExperience.query.filter_by(profile_id=profile.id).order_by(WorkExperience.sort_order, WorkExperience.created_at.desc()).all()
    return success_response(data={'work_experiences': [w.to_dict() for w in items]})


# 19. 新增工作经历
@bp.route('/work-experiences', methods=['POST'])
@login_required
def create_work_experience():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    company_name = data.get('company_name', '').strip()
    position = data.get('position', '').strip()
    start_date_str = data.get('start_date')

    if not company_name or not position or not start_date_str:
        return error_response(ErrorCode.PARAM_ERROR, 'company_name/position/start_date 不能为空', http_code=400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return error_response(ErrorCode.PARAM_ERROR, 'start_date 格式应为 YYYY-MM-DD', http_code=400)

    end_date = None
    if data.get('end_date'):
        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return error_response(ErrorCode.PARAM_ERROR, 'end_date 格式应为 YYYY-MM-DD', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = WorkExperience(
        profile_id=profile.id,
        company_name=company_name,
        position=position,
        start_date=start_date,
        end_date=end_date,
        is_current=data.get('is_current', False),
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(item)
    db.session.flush()

    # 图片
    images = data.get('images', [])
    if images:
        if len(images) > MAX_WORK_IMAGES:
            return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, f'图片最多 {MAX_WORK_IMAGES} 张', http_code=400)
        for img in images:
            db.session.add(WorkExperienceImage(
                work_experience_id=item.id,
                image_url=img.get('image_url', ''),
                caption=img.get('caption', ''),
                sort_order=img.get('sort_order', 0)
            ))

    db.session.commit()
    logger.info(f'工作经历新增: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='新增成功')


# 20. 编辑工作经历（部分更新）
@bp.route('/work-experiences/<int:exp_id>', methods=['PUT'])
@login_required
def update_work_experience(exp_id):
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = WorkExperience.query.filter_by(id=exp_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '工作经历不存在或无权操作', http_code=404)

    if 'company_name' in data:
        item.company_name = data['company_name']
    if 'position' in data:
        item.position = data['position']
    if 'start_date' in data:
        try:
            item.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return error_response(ErrorCode.PARAM_ERROR, 'start_date 格式应为 YYYY-MM-DD', http_code=400)
    if 'end_date' in data:
        item.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
    if 'is_current' in data:
        item.is_current = data['is_current']
    if 'description' in data:
        item.description = data['description']
    if 'sort_order' in data:
        item.sort_order = data['sort_order']

    # images 传则整体覆盖
    if 'images' in data:
        images = data['images']
        if len(images) > MAX_WORK_IMAGES:
            return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, f'图片最多 {MAX_WORK_IMAGES} 张', http_code=400)
        WorkExperienceImage.query.filter_by(work_experience_id=item.id).delete()
        for img in images:
            db.session.add(WorkExperienceImage(
                work_experience_id=item.id,
                image_url=img.get('image_url', ''),
                caption=img.get('caption', ''),
                sort_order=img.get('sort_order', 0)
            ))

    db.session.commit()
    logger.info(f'工作经历编辑: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='更新成功')


# 21. 删除工作经历
@bp.route('/work-experiences/<int:exp_id>', methods=['DELETE'])
@login_required
def delete_work_experience(exp_id):
    profile = get_or_create_profile(request.user.id)
    item = WorkExperience.query.filter_by(id=exp_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '工作经历不存在或无权操作', http_code=404)

    db.session.delete(item)  # cascade 删图片
    db.session.commit()
    logger.info(f'工作经历删除: user_id={request.user.id}, id={exp_id}')
    return success_response(message='删除成功')


# ==================== 教育经历（4个）====================

# 22. 我的教育经历列表
@bp.route('/education-experiences', methods=['GET'])
@login_required
def get_my_education_experiences():
    profile = get_or_create_profile(request.user.id)
    items = EducationExperience.query.filter_by(profile_id=profile.id).order_by(EducationExperience.sort_order, EducationExperience.created_at.desc()).all()
    return success_response(data={'education_experiences': [e.to_dict() for e in items]})


# 23. 新增教育经历
@bp.route('/education-experiences', methods=['POST'])
@login_required
def create_education_experience():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    school_level = data.get('school_level', '').strip()
    school_name = data.get('school_name', '').strip()
    start_year = data.get('start_year')

    if not school_level or not school_name or start_year is None:
        return error_response(ErrorCode.PARAM_ERROR, 'school_level/school_name/start_year 不能为空', http_code=400)
    if school_level not in ALLOWED_SCHOOL_LEVELS:
        return error_response(ErrorCode.SCHOOL_LEVEL_INVALID, '学段不合法，需为：小学/中学/大学', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = EducationExperience(
        profile_id=profile.id,
        school_level=school_level,
        school_name=school_name,
        start_year=int(start_year),
        end_year=int(data['end_year']) if data.get('end_year') else None,
        degree=data.get('degree'),
        major=data.get('major'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(item)
    db.session.commit()
    logger.info(f'教育经历新增: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='新增成功')


# 24. 编辑教育经历（部分更新）
@bp.route('/education-experiences/<int:edu_id>', methods=['PUT'])
@login_required
def update_education_experience(edu_id):
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = EducationExperience.query.filter_by(id=edu_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '教育经历不存在或无权操作', http_code=404)

    if 'school_level' in data:
        if data['school_level'] not in ALLOWED_SCHOOL_LEVELS:
            return error_response(ErrorCode.SCHOOL_LEVEL_INVALID, '学段不合法', http_code=400)
        item.school_level = data['school_level']
    if 'school_name' in data:
        item.school_name = data['school_name']
    if 'start_year' in data:
        item.start_year = int(data['start_year'])
    if 'end_year' in data:
        item.end_year = int(data['end_year']) if data['end_year'] else None
    if 'degree' in data:
        item.degree = data['degree']
    if 'major' in data:
        item.major = data['major']
    if 'sort_order' in data:
        item.sort_order = data['sort_order']

    db.session.commit()
    logger.info(f'教育经历编辑: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='更新成功')


# 25. 删除教育经历
@bp.route('/education-experiences/<int:edu_id>', methods=['DELETE'])
@login_required
def delete_education_experience(edu_id):
    profile = get_or_create_profile(request.user.id)
    item = EducationExperience.query.filter_by(id=edu_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '教育经历不存在或无权操作', http_code=404)

    db.session.delete(item)
    db.session.commit()
    logger.info(f'教育经历删除: user_id={request.user.id}, id={edu_id}')
    return success_response(message='删除成功')


# ==================== 能力证明（4个）====================

# 26. 我的能力证明列表
@bp.route('/ability-proofs', methods=['GET'])
@login_required
def get_my_ability_proofs():
    profile = get_or_create_profile(request.user.id)
    items = AbilityProof.query.filter_by(profile_id=profile.id).order_by(AbilityProof.sort_order, AbilityProof.created_at.desc()).all()
    return success_response(data={'ability_proofs': [a.to_dict() for a in items]})


# 27. 新增能力证明
@bp.route('/ability-proofs', methods=['POST'])
@login_required
def create_ability_proof():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    title = data.get('title', '').strip()
    if not title:
        return error_response(ErrorCode.PARAM_ERROR, 'title 不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = AbilityProof(
        profile_id=profile.id,
        title=title,
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(item)
    db.session.flush()

    files = data.get('files', [])
    if files:
        if len(files) > MAX_ABILITY_FILES:
            return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, f'文件最多 {MAX_ABILITY_FILES} 个', http_code=400)
        for f in files:
            file_type = f.get('file_type') or guess_file_type(f.get('file_name', '') or f.get('file_url', ''))
            db.session.add(AbilityProofFile(
                ability_proof_id=item.id,
                file_url=f.get('file_url', ''),
                file_name=f.get('file_name', ''),
                file_type=file_type,
                sort_order=f.get('sort_order', 0)
            ))

    db.session.commit()
    logger.info(f'能力证明新增: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='新增成功')


# 28. 编辑能力证明（部分更新）
@bp.route('/ability-proofs/<int:proof_id>', methods=['PUT'])
@login_required
def update_ability_proof(proof_id):
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    profile = get_or_create_profile(request.user.id)
    item = AbilityProof.query.filter_by(id=proof_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '能力证明不存在或无权操作', http_code=404)

    if 'title' in data:
        item.title = data['title']
    if 'description' in data:
        item.description = data['description']
    if 'sort_order' in data:
        item.sort_order = data['sort_order']

    # files 传则整体覆盖
    if 'files' in data:
        files = data['files']
        if len(files) > MAX_ABILITY_FILES:
            return error_response(ErrorCode.FILES_LIMIT_EXCEEDED, f'文件最多 {MAX_ABILITY_FILES} 个', http_code=400)
        AbilityProofFile.query.filter_by(ability_proof_id=item.id).delete()
        for f in files:
            file_type = f.get('file_type') or guess_file_type(f.get('file_name', '') or f.get('file_url', ''))
            db.session.add(AbilityProofFile(
                ability_proof_id=item.id,
                file_url=f.get('file_url', ''),
                file_name=f.get('file_name', ''),
                file_type=file_type,
                sort_order=f.get('sort_order', 0)
            ))

    db.session.commit()
    logger.info(f'能力证明编辑: user_id={request.user.id}, id={item.id}')
    return success_response(data=item.to_dict(), message='更新成功')


# 29. 删除能力证明
@bp.route('/ability-proofs/<int:proof_id>', methods=['DELETE'])
@login_required
def delete_ability_proof(proof_id):
    profile = get_or_create_profile(request.user.id)
    item = AbilityProof.query.filter_by(id=proof_id, profile_id=profile.id).first()
    if not item:
        return error_response(ErrorCode.NO_PERMISSION, '能力证明不存在或无权操作', http_code=404)

    db.session.delete(item)  # cascade 删文件
    db.session.commit()
    logger.info(f'能力证明删除: user_id={request.user.id}, id={proof_id}')
    return success_response(message='删除成功')


# ==================== 文件上传（1个）====================

# 30. 档案文件上传
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
        url = save_file(file, folder='profile')
        file_type = guess_file_type(file.filename)
        logger.info(f'档案文件上传: user_id={request.user.id}, url={url}')
        return success_response(
            data={'url': url, 'file_name': file.filename, 'file_type': file_type},
            message='上传成功'
        )
    except Exception as e:
        logger.error(f'档案文件上传失败: {e}')
        return error_response(ErrorCode.PARAM_ERROR, '文件上传失败', http_code=500)
