from app import db
from datetime import datetime


class Notification(db.Model):
    """通知表：互动消息（点赞/评论/关注）+ 待办事项。官方消息走 conversations 不入此表"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        comment='接收者')
    type = db.Column(db.String(20), nullable=False,
                     comment='interaction 互动 / todo 待办')
    subtype = db.Column(db.String(30), nullable=False,
                        comment='interaction->like/comment/follow; todo->apply/pending_review/pending_invite')
    title = db.Column(db.String(100), comment='通知标题')
    content = db.Column(db.String(500), nullable=False, comment='通知内容')
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                          comment='操作账号，系统待办=NULL')
    related_type = db.Column(db.String(20), comment='被操作对象类型：work/project/user')
    related_id = db.Column(db.Integer, nullable=False, comment='被操作对象ID')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('ix_noti_user_type_read', 'user_id', 'type', 'is_read'),
        db.Index('ix_noti_user_created', 'user_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'notification_id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'subtype': self.subtype,
            'title': self.title,
            'content': self.content,
            'sender_id': self.sender_id,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
