from app import db
from datetime import datetime


class ProjectViewHistory(db.Model):
    """项目浏览记录：用于"我浏览过的项目"列表。
    (user_id, project_id) 联合唯一；重复访问只更新 last_viewed_at + view_count。"""
    __tablename__ = 'project_view_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='浏览者')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, comment='被浏览项目')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                          comment='项目创建者（冗余）')
    view_count = db.Column(db.Integer, default=1, comment='该用户对该项目累计浏览次数')
    last_viewed_at = db.Column(db.DateTime, default=datetime.utcnow,
                               comment='最近一次浏览时间（排序主键）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'project_id', name='uq_user_project_view'),
        db.Index('ix_user_last_view_project', 'user_id', 'last_viewed_at'),
        db.Index('ix_author_last_view_project', 'author_id', 'last_viewed_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'author_id': self.author_id,
            'view_count': self.view_count,
            'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
