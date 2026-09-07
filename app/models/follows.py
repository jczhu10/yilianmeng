from app import db
from datetime import datetime


class Follow(db.Model):
    """关注关系表：follower 关注 followed"""
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='关注者')
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='被关注者')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following_rel')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='follower_rel')

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='uq_follower_followed'),
        db.Index('ix_follower_id', 'follower_id'),
        db.Index('ix_followed_id', 'followed_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'followed_id': self.followed_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
