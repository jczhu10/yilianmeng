from app import db
from datetime import datetime, timedelta


class WorkTop(db.Model):
    """广场置顶池（MVP 用不到，先建表留空）。"""
    __tablename__ = 'work_top'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False, unique=True, comment='置顶的作品')
    weight = db.Column(db.Integer, default=0, comment='排序权重，值越小越靠前（1最高）')
    started_at = db.Column(db.DateTime, default=datetime.utcnow, comment='生效开始时间')
    ended_at = db.Column(db.DateTime,
                         default=lambda: datetime.utcnow() + timedelta(days=7),
                         comment='失效时间（到期自动不展示）')
    reason = db.Column(db.String(200), nullable=True, comment='置顶原因/标签：推荐/广告/活动/官方公告')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'work_id': self.work_id,
            'weight': self.weight,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'reason': self.reason,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
