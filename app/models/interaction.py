from app import db
from datetime import datetime


class Like(db.Model):
    """点赞记录表。
    user_id + work_id 联合唯一索引，防止同一用户对同一作品重复点赞。
    """
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'work_id', name='uq_user_work_like'),
    )

    def to_dict(self, user=None):
        data = {
            'like_id': self.id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if user is not None:
            data['user'] = user.to_dict()
        return data


class Comment(db.Model):
    """评论表。
    parent_id: 回复的根评论ID。NULL 表示一级评论；非 NULL 表示对该评论的回复。
    为防止无限嵌套，回复只能挂在一级评论下（parent_id 始终指向根评论，不指向其他回复）。
    is_deleted: 软删除标记，删除后内容显示为"[已删除]"，保留回复链不断裂。
    """
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, comment='回复的根评论ID，NULL为一级评论')
    content = db.Column(db.String(2000), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标记')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, user=None, reply_count=None):
        data = {
            'comment_id': self.id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'parent_id': self.parent_id,
            'content': '[已删除]' if self.is_deleted else self.content,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if user is not None:
            data['user'] = user.to_dict()
        if reply_count is not None:
            data['reply_count'] = reply_count
        return data
