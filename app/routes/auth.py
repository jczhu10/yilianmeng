import re
import random
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request
from app import db
from app.models import User, Profile
from app.utils.helpers import create_token, login_required, success_response, error_response

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


class ErrorCode:
    PARAM_ERROR = 400
    UNAUTHORIZED = 401
    RATE_LIMITED = 429
    PHONE_FORMAT_ERROR = 1001
    CODE_ERROR = 1002
    CODE_EXPIRED = 1003
    CODE_SENT_FIRST = 1004
    PHONE_REGISTERED = 1005
    LOGIN_FAILED = 1006
    PASSWORD_FORMAT_ERROR = 1007
    SCENE_INVALID = 1008


# 验证码存储 {phone: {'code': code, 'expire': dt, 'sent': dt, 'scene': scene}}
verification_codes = {}

ALLOWED_SCENES = {'register', 'reset'}
PHONE_RE = re.compile(r'^1[3-9]\d{9}$')
# 密码：8-20位，含字母+数字
PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$')


def is_valid_phone(phone):
    return bool(PHONE_RE.match(phone))


def is_valid_password(password):
    return bool(PASSWORD_RE.match(password))


def generate_code():
    return ''.join(random.choices('0123456789', k=6))


# 1. 发送验证码
@bp.route('/send-code', methods=['POST'])
def send_code():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    phone = data.get('phone', '').strip()
    scene = data.get('scene', '').strip()

    if not phone:
        return error_response(ErrorCode.PARAM_ERROR, '手机号不能为空')
    if not is_valid_phone(phone):
        return error_response(ErrorCode.PHONE_FORMAT_ERROR, '手机号格式不正确', http_code=400)
    if scene not in ALLOWED_SCENES:
        return error_response(ErrorCode.SCENE_INVALID, '场景参数不合法，需为 register/reset', http_code=400)

    # 场景业务校验
    if scene == 'register':
        # 注册场景：手机号不能已注册
        if User.query.filter_by(phone=phone).first():
            return error_response(ErrorCode.PHONE_REGISTERED, '该手机号已注册', http_code=400)
    elif scene == 'reset':
        # 重置场景：手机号必须已注册
        if not User.query.filter_by(phone=phone).first():
            return error_response(ErrorCode.LOGIN_FAILED, '该手机号未注册', http_code=400)

    # 60秒限流
    if phone in verification_codes:
        sent = verification_codes[phone]['sent']
        if (datetime.now() - sent).total_seconds() < 60:
            return error_response(ErrorCode.RATE_LIMITED, '验证码发送过于频繁，请60秒后重试', http_code=429)

    code = generate_code()
    verification_codes[phone] = {
        'code': code,
        'expire': datetime.now() + timedelta(minutes=5),
        'sent': datetime.now(),
        'scene': scene
    }
    logger.info(f'验证码已发送: phone={phone}, scene={scene}')

    return success_response(
        data={'dev_code': code},
        message='验证码已发送'
    )


# 2. 注册
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '').strip()

    if not phone or not code or not password:
        return error_response(ErrorCode.PARAM_ERROR, '手机号、验证码、密码不能为空')

    if not is_valid_phone(phone):
        return error_response(ErrorCode.PHONE_FORMAT_ERROR, '手机号格式不正确', http_code=400)
    if not is_valid_password(password):
        return error_response(ErrorCode.PASSWORD_FORMAT_ERROR, '密码格式不正确，需8-20位含字母和数字', http_code=400)

    # 校验验证码
    err = _verify_code(phone, code, 'register')
    if err:
        return err

    # 手机号不能已注册
    if User.query.filter_by(phone=phone).first():
        return error_response(ErrorCode.PHONE_REGISTERED, '该手机号已注册', http_code=400)

    # 创建用户
    nickname = nickname or f'用户{phone[-4:]}'
    user = User(phone=phone, nickname=nickname, is_new_user=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # 拿 user.id

    # 自动建空档案
    profile = Profile(user_id=user.id, identity='艺术爱好者')
    db.session.add(profile)
    db.session.commit()

    logger.info(f'新用户注册: phone={phone}, user_id={user.id}')
    token = create_token(user.id)

    return success_response(
        data={'token': token, 'user': user.to_dict(), 'is_new_user': True},
        message='注册成功'
    )


# 3. 登录（密码模式）
@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    if not phone or not password:
        return error_response(ErrorCode.PARAM_ERROR, '手机号和密码不能为空')

    if not is_valid_phone(phone):
        return error_response(ErrorCode.PHONE_FORMAT_ERROR, '手机号格式不正确', http_code=400)

    user = User.query.filter_by(phone=phone).first()
    # 统一提示，防撞库
    if not user or not user.check_password(password):
        return error_response(ErrorCode.LOGIN_FAILED, '手机号或密码错误', http_code=400)

    logger.info(f'用户登录: user_id={user.id}')
    token = create_token(user.id)

    # 老用户清除新用户标记
    if user.is_new_user:
        user.is_new_user = False
        db.session.commit()

    return success_response(
        data={'token': token, 'user': user.to_dict(), 'is_new_user': False},
        message='登录成功'
    )


# 4. 重置密码
@bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    if not data:
        return error_response(ErrorCode.PARAM_ERROR, '请求参数不能为空', http_code=400)

    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not phone or not code or not new_password:
        return error_response(ErrorCode.PARAM_ERROR, '手机号、验证码、新密码不能为空')

    if not is_valid_phone(phone):
        return error_response(ErrorCode.PHONE_FORMAT_ERROR, '手机号格式不正确', http_code=400)
    if not is_valid_password(new_password):
        return error_response(ErrorCode.PASSWORD_FORMAT_ERROR, '密码格式不正确，需8-20位含字母和数字', http_code=400)

    err = _verify_code(phone, code, 'reset')
    if err:
        return err

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error_response(ErrorCode.LOGIN_FAILED, '该手机号未注册', http_code=400)

    user.set_password(new_password)
    db.session.commit()
    logger.info(f'密码重置: user_id={user.id}')

    return success_response(message='密码重置成功')


# 5. 刷新 token
@bp.route('/refresh', methods=['POST'])
@login_required
def refresh_token():
    new_token = create_token(request.user.id)
    logger.info(f'Token刷新: user_id={request.user.id}')
    return success_response(data={'token': new_token}, message='Token刷新成功')


# 6. 获取当前用户信息
@bp.route('/me', methods=['GET'])
@login_required
def get_me():
    return success_response(data=request.user.to_dict())


# 7. 退出登录
@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logger.info(f'用户登出: user_id={request.user.id}')
    return success_response(message='已退出登录')


# ========== 内部工具 ==========
def _verify_code(phone, code, scene):
    """校验验证码，返回 error_response 或 None"""
    if phone not in verification_codes:
        return error_response(ErrorCode.CODE_SENT_FIRST, '请先发送验证码', http_code=400)

    record = verification_codes[phone]
    if datetime.now() > record['expire']:
        del verification_codes[phone]
        return error_response(ErrorCode.CODE_EXPIRED, '验证码已过期，请重新获取', http_code=400)

    if record['scene'] != scene:
        return error_response(ErrorCode.CODE_ERROR, '验证码场景不匹配', http_code=400)

    if code != record['code']:
        logger.warning(f'验证码错误: phone={phone}')
        return error_response(ErrorCode.CODE_ERROR, '验证码错误', http_code=400)

    # 验证通过，清除
    del verification_codes[phone]
    return None
