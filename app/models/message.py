from app import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), default=0)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), default='private')
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'message_id': self.id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'type': self.type,
            'content': self.content,
            'is_read': self.is_read,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat()
        }
