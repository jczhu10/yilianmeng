from app import db
from datetime import datetime
import json

class Work(db.Model):
    __tablename__ = 'works'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    channel = db.Column(db.String(50), default='short_video')
    files = db.Column(db.Text, default='[]')
    cover_url = db.Column(db.String(255), default='')
    is_collaborative = db.Column(db.Boolean, default=False)
    collaborators = db.Column(db.Text, default='[]')
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'work_id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'channel': self.channel,
            'files': json.loads(self.files),
            'cover_url': self.cover_url,
            'is_collaborative': self.is_collaborative,
            'collaborators': json.loads(self.collaborators),
            'view_count': self.view_count,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat()
        }
    
    def set_files(self, files_list):
        self.files = json.dumps(files_list)
    
    def set_collaborators(self, collaborators_list):
        self.collaborators = json.dumps(collaborators_list)
