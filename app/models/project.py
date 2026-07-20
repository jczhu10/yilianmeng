from app import db
from datetime import datetime
import json

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    required_skills = db.Column(db.Text, default='[]')
    mode = db.Column(db.String(20), default='free')
    budget = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='recruiting')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'project_id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'required_skills': json.loads(self.required_skills),
            'mode': self.mode,
            'budget': self.budget,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def set_required_skills(self, skills_list):
        self.required_skills = json.dumps(skills_list)

class ProjectApplication(db.Model):
    __tablename__ = 'project_applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
