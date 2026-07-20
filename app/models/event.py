from app import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    cover_url = db.Column(db.String(255), default='')
    deadline = db.Column(db.DateTime)
    reward = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='ongoing')
    participant_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'event_id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_url': self.cover_url,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'reward': self.reward,
            'status': self.status,
            'participant_count': self.participant_count,
            'created_at': self.created_at.isoformat()
        }

class EventParticipant(db.Model):
    __tablename__ = 'event_participants'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    rank = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'rank': self.rank,
            'score': self.score,
            'created_at': self.created_at.isoformat()
        }
