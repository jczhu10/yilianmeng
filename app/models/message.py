from app import db
from datetime import datetime


class Message(db.Model):
    """消息表：私聊 + 群聊合并。私聊用 conversation_id，群聊用 group_id"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_type = db.Column(db.String(10), nullable=False,
                                   comment='private=私聊 / group=群聊')
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'),
                                comment='私聊会话ID，群聊为NULL')
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                         comment='群聊ID，私聊为NULL')
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                          comment='发送者')
    msg_type = db.Column(db.String(20), nullable=False,
                         comment='text/image/voice/file/invite_project/invite_review/call')
    content = db.Column(db.Text, nullable=False, comment='消息内容（文字/URL/JSON）')
    file_name = db.Column(db.String(200), comment='文件名（file 类型）')
    file_size = db.Column(db.BigInteger, comment='文件大小字节')
    voice_duration = db.Column(db.Integer, comment='语音时长秒')
    related_type = db.Column(db.String(20), comment='关联类型：project 等')
    related_id = db.Column(db.Integer, comment='关联ID（项目邀请用 project_id）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('ix_msg_conv_time', 'conversation_id', 'created_at'),
        db.Index('ix_msg_group_time', 'group_id', 'created_at'),
        db.Index('ix_msg_sender_time', 'sender_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'message_id': self.id,
            'conversation_type': self.conversation_type,
            'conversation_id': self.conversation_id,
            'group_id': self.group_id,
            'sender_id': self.sender_id,
            'msg_type': self.msg_type,
            'content': self.content,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'voice_duration': self.voice_duration,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
