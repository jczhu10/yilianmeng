from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    nickname = db.Column(db.String(50), default='用户')
    avatar = db.Column(db.String(255), default='')
    bio = db.Column(db.String(500), default='')
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    is_new_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'user_id': self.id,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone[:3] + '****' + self.phone[-4:] if len(self.phone) >= 7 else self.phone,
            'level': self.level,
            'bio': self.bio,
            'is_new_user': self.is_new_user,
            'created_at': self.created_at.isoformat()
        }
