from app import db
from datetime import datetime


class WorkViewHistory(db.Model):
    """作品浏览记录：用于"我浏览过的作品"列表 + 用户浏览总数。
    (user_id, work_id) 联合唯一，重复访问仅更新 last_viewed_at 并累加 view_count。"""
    __tablename__ = 'work_view_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='浏览者')
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False, comment='被浏览作品')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                          comment='作品作者（冗余，用于"TA被看过的作品"反查与索引）')
    view_count = db.Column(db.Integer, default=1, comment='该用户对该作品累计浏览次数')
    last_viewed_at = db.Column(db.DateTime, default=datetime.utcnow,
                               comment='最近一次浏览时间（排序主键）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'work_id', name='uq_user_work_view'),
        db.Index('ix_user_last_view_work', 'user_id', 'last_viewed_at'),
        db.Index('ix_author_last_view_work', 'author_id', 'last_viewed_at'),
    )

    def to_dict(self, with_work=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'work_id': self.work_id,
            'author_id': self.author_id,
            'view_count': self.view_count,
            'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return data
