from app import db
from datetime import datetime

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False, comment='分数 1-5')
    comment = db.Column(db.Text, default='', comment='文字评价')
    tags = db.Column(db.Text, default='[]', comment='评价标签ID数组（JSON，见 rating_tags 字典）')
    is_anonymous = db.Column(db.Boolean, default=False, comment='是否匿名评价')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'from_user_id', 'to_user_id', name='uq_project_from_to'),
    )

    def to_dict(self):
        import json
        return {
            'rating_id': self.id,
            'project_id': self.project_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'score': self.score,
            'comment': self.comment,
            'tags': json.loads(self.tags) if self.tags else [],
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat()
        }


class RatingTag(db.Model):
    """评价标签字典表：预置一组评价标签（类似 style_tags 字典），用户评分时可多选。"""
    __tablename__ = 'rating_tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False, comment='标签名')
    category = db.Column(db.String(20), default='positive', comment='positive 正向 / negative 负向 / neutral 中性')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
