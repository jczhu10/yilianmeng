import re
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils.helpers import create_token, verify_token, login_required, success_response, error_response

bp = Blueprint('auth', __name__)

# 开发阶段：内存存储验证码 {phone: (code, expire_time, send_time)}
verification_codes = {}

# 手机号格式校验
def is_valid_phone(phone):
    return bool(re.match(r'^1[3-9]\d{9}$', phone))

# 生成6位随机验证码
def generate_code():
    return ''.join(random.choices('0123456789', k=6))

# 发送验证码
@bp.route('/send-code', methods=['POST'])
def send_code():
    data = request.get_json()
    if not data:
        return error_response(400, '请求参数不能为空')
    
    phone = data.get('phone', '').strip()
    if not phone:
        return error_response(400, '手机号不能为空')
    
    if not is_valid_phone(phone):
        return error_response(400, '手机号格式不正确')
    
    # 60秒内不能重复发送
    if phone in verification_codes:
        _, _, send_time = verification_codes[phone]
        if (datetime.now() - send_time).total_seconds() < 60:
            return error_response(429, '验证码发送过于频繁，请60秒后重试')
    
    # 生成验证码
    code = generate_code()
    expire_time = datetime.now() + timedelta(minutes=5)
    send_time = datetime.now()
    verification_codes[phone] = (code, expire_time, send_time)
    
    # 开发模式：直接返回验证码（生产环境应调用短信服务）
    return success_response(
        data={'dev_code': code},
        message='验证码已发送'
    )

# 登录/注册
@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error_response(400, '请求参数不能为空')
    
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    if not phone or not code:
        return error_response(400, '手机号和验证码不能为空')
    
    if not is_valid_phone(phone):
        return error_response(400, '手机号格式不正确')
    
    # 校验验证码
    if phone not in verification_codes:
        return error_response(400, '请先发送验证码')
    
    stored_code, expire_time, _ = verification_codes[phone]
    if datetime.now() > expire_time:
        del verification_codes[phone]
        return error_response(400, '验证码已过期，请重新获取')
    
    if code != stored_code:
        return error_response(400, '验证码错误')
    
    # 验证成功，清除验证码
    del verification_codes[phone]
    
    # 查询用户是否存在
    user = User.query.filter_by(phone=phone).first()
    is_new_user = False
    
    if not user:
        # 新用户自动注册
        user = User(phone=phone, nickname=f'用户{phone[-4:]}')
        db.session.add(user)
        db.session.commit()
        is_new_user = True
    
    # 生成Token
    token = create_token(user.id)
    
    return success_response(
        data={
            'token': token,
            'user_id': user.id,
            'is_new_user': is_new_user
        },
        message='登录成功'
    )

# 刷新Token
@bp.route('/refresh', methods=['POST'])
@login_required
def refresh_token():
    # 获取旧Token
    auth_header = request.headers.get('Authorization')
    old_token = auth_header.split(' ')[1]
    
    # 验证旧Token
    user_id = verify_token(old_token)
    if not user_id:
        return error_response(401, 'Token无效或已过期')
    
    # 生成新Token
    new_token = create_token(user_id)
    
    return success_response(
        data={'token': new_token},
        message='Token刷新成功'
    )

# 获取当前用户信息
@bp.route('/me', methods=['GET'])
@login_required
def get_me():
    user = request.user
    return success_response(data=user.to_dict())

# 登出
@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # JWT是无状态的，登出由前端清除Token即可
    # 后端可选择记录登出日志（此处省略）
    return success_response(message='已退出登录')
