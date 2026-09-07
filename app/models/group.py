from app import db
from datetime import datetime


class Group(db.Model):
    """群聊表"""
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='群名称')
    avatar = db.Column(db.String(255), comment='群头像')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                         comment='群主')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'),
                           comment='关联项目（协作群自动创建），自由群=NULL')
    member_count = db.Column(db.Integer, default=1, comment='冗余：成员数')
    last_message_content = db.Column(db.String(500), comment='冗余：最后消息预览')
    last_message_at = db.Column(db.DateTime, comment='冗余：最后消息时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'group_id': self.id,
            'name': self.name,
            'avatar': self.avatar,
            'owner_id': self.owner_id,
            'project_id': self.project_id,
            'member_count': self.member_count,
            'last_message_content': self.last_message_content,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class GroupMember(db.Model):
    """群成员表"""
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(10), default='member',
                     comment='owner/admin/member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    nickname = db.Column(db.String(50), comment='群内昵称（可选）')

    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )

    def to_dict(self):
        return {
            'group_id': self.group_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'nickname': self.nickname
        }


class GroupRead(db.Model):
    """群聊未读记录：每用户每群一行"""
    __tablename__ = 'group_reads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unread_count = db.Column(db.Integer, default=0, comment='未读条数')
    last_read_message_id = db.Column(db.Integer, comment='最后读到的消息ID')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_read_user'),
    )

    def to_dict(self):
        return {
            'group_id': self.group_id,
            'user_id': self.user_id,
            'unread_count': self.unread_count,
            'last_read_message_id': self.last_read_message_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
