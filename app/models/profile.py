from app import db
from datetime import datetime
import json


class Profile(db.Model):
    """创作者档案：身份类型、风格标签、工作经历、教育背景等。
    技能已迁移到关联表 ProfileSkill，不再使用 JSON 字段存储。"""
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    identity_type = db.Column(db.String(20), default='amateur', comment='身份类型：amateur业余 / professional专业')
    style_tags = db.Column(db.Text, default='[]', comment='风格标签，JSON数组')
    work_history = db.Column(db.Text, default='', comment='工作经历')
    education = db.Column(db.Text, default='', comment='教育背景')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联用户选择的技能
    profile_skills = db.relationship(
        'ProfileSkill',
        backref='profile',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def to_dict(self, with_skills=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'identity_type': self.identity_type,
            'style_tags': json.loads(self.style_tags) if self.style_tags else [],
            'work_history': self.work_history,
            'education': self.education,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if with_skills:
            data['skills'] = [ps.skill.to_dict() for ps in self.profile_skills if ps.skill]
        return data

    def set_style_tags(self, tags_list):
        self.style_tags = json.dumps(tags_list)
