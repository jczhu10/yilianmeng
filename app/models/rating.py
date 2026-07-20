from app import db
from datetime import datetime

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'rating_id': self.id,
            'project_id': self.project_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'score': self.score,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }
