from app import db
from datetime import datetime
import json

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    identity_type = db.Column(db.String(20), default='amateur')
    skills = db.Column(db.Text, default='[]')
    style_tags = db.Column(db.Text, default='[]')
    work_history = db.Column(db.Text, default='')
    education = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'identity_type': self.identity_type,
            'skills': json.loads(self.skills),
            'style_tags': json.loads(self.style_tags),
            'work_history': self.work_history,
            'education': self.education,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def set_skills(self, skills_list):
        self.skills = json.dumps(skills_list)
    
    def set_style_tags(self, tags_list):
        self.style_tags = json.dumps(tags_list)
