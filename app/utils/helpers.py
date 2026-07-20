import os
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import jwt
from app.models import User
from app import app

def generate_uuid():
    return str(uuid.uuid4().hex)

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def allowed_file(filename):
    return '.' in filename and get_file_extension(filename) in app.config['ALLOWED_EXTENSIONS']

def generate_filename(filename):
    ext = get_file_extension(filename)
    return f"{generate_uuid()}.{ext}"

def save_file(file, folder):
    filename = generate_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(filepath, exist_ok=True)
    file.save(os.path.join(filepath, filename))
    return f"/uploads/{folder}/{filename}"

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或Token过期', 'data': None}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'code': 401, 'message': '未登录或Token过期', 'data': None}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 401, 'message': '用户不存在', 'data': None}), 401
        
        request.user = user
        return f(*args, **kwargs)
    return decorated_function

def success_response(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data})

def error_response(code, message):
    return jsonify({'code': code, 'message': message, 'data': None}), code

def get_pagination_params():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)
    return page, page_size

def format_pagination(query, page, page_size):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size
    return {
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }
