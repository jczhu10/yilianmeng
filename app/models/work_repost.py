from app import db
from datetime import datetime


class WorkRepost(db.Model):
    """转发关系表：works表中content_type=repost的每一条记录对应一条溯源。"""
    __tablename__ = 'work_reposts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=False, unique=True,
                        comment='转发帖的作品ID（works表content_type=repost的那条）')
    source_work_id = db.Column(db.Integer, db.ForeignKey('works.id'), nullable=True,
                               comment='被转发的原始作品ID（转发项目时为NULL）')
    source_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True,
                                  comment='被转发的项目ID（转发作品时为NULL）')
    source_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                               comment='原始发布者/项目创建者ID（冗余）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'work_id': self.work_id,
            'source_work_id': self.source_work_id,
            'source_project_id': self.source_project_id,
            'source_user_id': self.source_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
