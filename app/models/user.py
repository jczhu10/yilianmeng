from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True, comment='密码哈希（werkzeug）')
    nickname = db.Column(db.String(50), default='用户')
    avatar = db.Column(db.String(255), default='')
    bio = db.Column(db.String(500), default='')
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    is_new_user = db.Column(db.Boolean, default=True)
    is_official = db.Column(db.Boolean, default=False, comment='0=普通用户，1=官方账号')

    # ===== 个人主页冗余计数（跟随增删事件异步/同步刷新，详情接口免 COUNT 查询）=====
    following_count = db.Column(db.Integer, default=0, comment='我关注的人数')
    follower_count  = db.Column(db.Integer, default=0, comment='关注我的人数（粉丝数）')
    work_count      = db.Column(db.Integer, default=0, comment='我发布的已删除除外的作品数')
    project_count   = db.Column(db.Integer, default=0, comment='我创建的项目数')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """设置密码（哈希存储）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """校验密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'user_id': self.id,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone[:3] + '****' + self.phone[-4:] if len(self.phone) >= 7 else self.phone,
            'level': self.level,
            'exp': self.exp,
            'bio': self.bio,
            'is_new_user': self.is_new_user,
            'is_official': self.is_official,
            'following_count': self.following_count or 0,
            'follower_count':  self.follower_count  or 0,
            'work_count':      self.work_count      or 0,
            'project_count':   self.project_count   or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
