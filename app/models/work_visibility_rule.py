from app import db
from datetime import datetime


class WorkVisibilityRule(db.Model):
    """作品可见白名单/黑名单（visibility_type=custom_allow/custom_deny 时使用）。"""
    __tablename__ = 'work_visibility_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False, comment='作品ID')
    rule_type = db.Column(db.String(10), nullable=False, comment='allow白名单 / deny黑名单')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='被允许/被禁止的用户')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('work_id', 'rule_type', 'user_id', name='uq_work_rule_user'),
        db.Index('ix_work_rule', 'work_id', 'rule_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'work_id': self.work_id,
            'rule_type': self.rule_type,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
