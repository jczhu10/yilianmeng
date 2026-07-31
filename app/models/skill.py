from app import db
from datetime import datetime


class SkillCategory(db.Model):
    """技能分类表：如 文字创作 / 视觉创作 / 影像类 / 配音"""
    __tablename__ = 'skill_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, comment='分类名称')
    code = db.Column(db.String(20), unique=True, nullable=False, comment='分类编码')
    sort_order = db.Column(db.Integer, default=0, comment='排序，越小越靠前')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship(
        'Skill',
        backref='category',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def to_dict(self, with_skills=False):
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'sort_order': self.sort_order
        }
        if with_skills:
            data['skills'] = [s.to_dict() for s in sorted(self.skills, key=lambda x: x.sort_order)]
        return data


class Skill(db.Model):
    """技能项表：属于某个分类下的具体技能"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('skill_categories.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False, comment='技能名称')
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'sort_order': self.sort_order
        }


class ProfileSkill(db.Model):
    """用户档案-技能关联表：存储用户选择的技能（不存熟练度）"""
    __tablename__ = 'profile_skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skill = db.relationship('Skill', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('profile_id', 'skill_id', name='uq_profile_skill'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'skill': self.skill.to_dict() if self.skill else None,
            'created_at': self.created_at.isoformat()
        }
