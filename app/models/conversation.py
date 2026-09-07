from app import db
from datetime import datetime


class Conversation(db.Model):
    """私聊会话表（含与官方账号的会话）。约束 user1_id < user2_id 保证两人唯一"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                         comment='用户1（约束 user1_id < user2_id）')
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                         comment='用户2')
    last_message_content = db.Column(db.String(500), comment='冗余：最后一条消息预览')
    last_message_at = db.Column(db.DateTime, comment='冗余：最后消息时间（排序用）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_conversation_users'),
        db.Index('ix_conv_user1_last', 'user1_id', 'last_message_at'),
        db.Index('ix_conv_user2_last', 'user2_id', 'last_message_at'),
    )

    def to_dict(self):
        return {
            'conversation_id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'last_message_content': self.last_message_content,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ConversationRead(db.Model):
    """私聊未读记录：每用户每会话一行"""
    __tablename__ = 'conversation_reads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'),
                                nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unread_count = db.Column(db.Integer, default=0, comment='未读条数')
    last_read_message_id = db.Column(db.Integer, comment='最后读到的消息ID')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('conversation_id', 'user_id', name='uq_conv_read_user'),
    )

    def to_dict(self):
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'unread_count': self.unread_count,
            'last_read_message_id': self.last_read_message_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
