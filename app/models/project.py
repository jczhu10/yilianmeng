from app import db
from datetime import datetime
import json

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    mode = db.Column(db.String(20), default='free')
    budget = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime)
    max_members = db.Column(db.Integer, default=10, comment='招募总人数上限')
    cover_url = db.Column(db.String(255), default='', comment='项目封面')
    topic = db.Column(db.String(100), default='', comment='项目主题')
    required_level = db.Column(db.Integer, default=1, comment='要求账号最低等级')
    required_project_count = db.Column(db.Integer, default=0, comment='要求参与项目次数下限')
    contact_visible = db.Column(db.Boolean, default=True, comment='队长是否公开联系方式')
    status = db.Column(db.String(20), default='recruiting')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_required_skills(self, skill_ids):
        """设置项目所需技能（覆盖式）：先删旧记录再新增"""
        ProjectRequiredSkill.query.filter_by(project_id=self.id).delete()
        for sid in skill_ids:
            db.session.add(ProjectRequiredSkill(project_id=self.id, skill_id=sid))

    def to_dict(self):
        result = {
            'project_id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'mode': self.mode,
            'budget': self.budget,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'max_members': self.max_members,
            'cover_url': self.cover_url,
            'topic': self.topic,
            'required_level': self.required_level,
            'required_project_count': self.required_project_count,
            'contact_visible': self.contact_visible,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'required_skills': [s.to_dict() for s in ProjectRequiredSkill.query.filter_by(project_id=self.id).all()]
        }
        return result

class ProjectApplication(db.Model):
    __tablename__ = 'project_applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, comment='审批时间')
    
    def to_dict(self, with_expired=False):
        d = {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
        if with_expired:
            # 动态判断过期：pending + 项目截止时间已过
            project = Project.query.get(self.project_id)
            from datetime import datetime
            d['is_expired'] = (self.status == 'pending' and project
                               and project.deadline and project.deadline < datetime.utcnow())
            if d['is_expired']:
                d['status'] = 'expired'
        return d

class ProjectRequiredSkill(db.Model):
    """项目所需技能表：替代 projects.required_skills JSON 字段，
    每个技能独立一行，附带所需人数与已招人数。"""
    __tablename__ = 'project_required_skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    required_count = db.Column(db.Integer, nullable=False, default=1, comment='所需人数')
    filled_count = db.Column(db.Integer, default=0, comment='已招到人数（冗余）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skill = db.relationship('Skill', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'skill_id', name='uq_project_skill'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'skill': self.skill.to_dict() if self.skill else None,
            'required_count': self.required_count,
            'filled_count': self.filled_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
