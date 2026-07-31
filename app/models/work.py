from app import db
from datetime import datetime
import json


class Work(db.Model):
    """作品表。
    files / collaborators / skill_tags 暂用 JSON 数组存储（MVP 阶段够用），
    后续按协作者/技能查询需求再拆关联表。
    status: draft(草稿) / published(已发布) / deleted(已删除，软删除)
    channel: writing / visual / video / voice （与 skill_categories.code 对齐）
    """
    __tablename__ = 'works'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    channel = db.Column(db.String(50), default='short_video', comment='渠道：writing/visual/video/voice')
    files = db.Column(db.Text, default='[]', comment='文件URL数组')
    cover_url = db.Column(db.String(255), default='', comment='封面URL')
    is_collaborative = db.Column(db.Boolean, default=False, comment='是否协作作品')
    collaborators = db.Column(db.Text, default='[]', comment='协作者用户ID数组')
    skill_tags = db.Column(db.Text, default='[]', comment='技能标签ID数组，用于后续推流')
    status = db.Column(db.String(20), default='draft', comment='状态：draft/published/deleted')
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, with_author=False, author=None):
        data = {
            'work_id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'channel': self.channel,
            'files': json.loads(self.files) if self.files else [],
            'cover_url': self.cover_url,
            'is_collaborative': self.is_collaborative,
            'collaborators': json.loads(self.collaborators) if self.collaborators else [],
            'skill_tags': json.loads(self.skill_tags) if self.skill_tags else [],
            'status': self.status,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if with_author and author is not None:
            data['author'] = author.to_dict()
        return data

    def set_files(self, files_list):
        self.files = json.dumps(files_list)

    def set_collaborators(self, collaborators_list):
        self.collaborators = json.dumps(collaborators_list)

    def set_skill_tags(self, tags_list):
        self.skill_tags = json.dumps(tags_list)
