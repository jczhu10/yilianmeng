# -*- coding: utf-8 -*-
"""消息文件上传路由"""
import os
from flask import Blueprint, request
from app import app
from app.utils.helpers import login_required, success_response, error_response, save_file

bp = Blueprint('messages_upload', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov',
                      'mp3', 'wav', 'm4a', 'pdf', 'doc', 'docx', 'zip', 'rar'}


def _get_file_type(filename):
    """根据扩展名判断文件类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        return 'image'
    if ext in {'mp3', 'wav', 'm4a'}:
        return 'voice'
    if ext in {'mp4', 'mov'}:
        return 'video'
    return 'file'


# ========== 接口22：上传消息附件 ==========
@bp.route('/upload', methods=['POST'])
@login_required
def upload_message_file():
    """上传消息附件（图片/语音/文件），返回 URL"""
    if 'file' not in request.files:
        return error_response(400, '未找到文件')
    file = request.files['file']
    if not file.filename:
        return error_response(400, '文件名为空')

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return error_response(400, f'不支持的文件类型：{ext}')

    # 限制 20MB
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 20 * 1024 * 1024:
        return error_response(400, '文件大小超过 20MB')

    file_url = save_file(file, 'messages')
    return success_response(data={
        'file_url': file_url,
        'file_name': file.filename,
        'file_size': size,
        'file_type': _get_file_type(file.filename)
    }, message='上传成功')
