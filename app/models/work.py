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
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True, comment='关联的协作项目ID')
    collaborators = db.Column(db.Text, default='[]', comment='协作者用户ID数组')
    skill_tags = db.Column(db.Text, default='[]', comment='技能标签ID数组，用于后续推流')

    # ===== 广场扩展字段 =====
    content_type = db.Column(db.String(20), default='original', comment='original原创 / repost转发 / text_only纯文字')
    image_layout = db.Column(db.String(20), default='flip', comment='flip翻页(小红书抖音) / grid并排(朋友圈) 仅channel=visual有效')
    text_content = db.Column(db.Text, nullable=True, comment='纯文字内容（content_type=text_only时专用）')
    visibility_type = db.Column(db.String(20), default='public', comment='可见性:private/followers/mutual/public/custom_allow/custom_deny')
    location = db.Column(db.String(200), nullable=True, comment='发布地点（选填）')
    share_count = db.Column(db.Integer, default=0, comment='本作品发起转发的次数')
    repost_count = db.Column(db.Integer, default=0, comment='本作品被别人转发的次数')
    published_at = db.Column(db.DateTime, nullable=True, comment='实际发布时间（排序依据，不是created_at）')

    status = db.Column(db.String(20), default='draft', comment='状态：draft/published/deleted')
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0, comment='评论数（冗余）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_user_status_published', 'user_id', 'status', 'published_at'),
        db.Index('idx_status_published', 'status', 'published_at'),
        db.Index('idx_status_channel', 'status', 'channel', 'published_at'),
    )

    def to_dict(self, with_author=False, author=None):
        data = {
            'work_id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'text_content': self.text_content,
            'channel': self.channel,
            'content_type': self.content_type,
            'image_layout': self.image_layout,
            'visibility_type': self.visibility_type,
            'location': self.location,
            'files': json.loads(self.files) if self.files else [],
            'cover_url': self.cover_url,
            'is_collaborative': self.is_collaborative,
            'project_id': self.project_id,
            'collaborators': json.loads(self.collaborators) if self.collaborators else [],
            'skill_tags': json.loads(self.skill_tags) if self.skill_tags else [],
            'status': self.status,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'repost_count': self.repost_count,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
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
