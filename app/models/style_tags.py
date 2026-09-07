from app import db
from datetime import datetime


class StyleTag(db.Model):
    """风格词汇字典表：预置20条，支持后台管理扩展"""
    __tablename__ = "style_tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False, comment="风格词汇名称")
    description = db.Column(db.String(200), default="", comment="词汇描述")
    sort_order = db.Column(db.Integer, default=0, comment="排序，越小越前")
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ProfileStyleTag(db.Model):
    """档案-风格词汇关联表（多对多，上限5个）"""
    __tablename__ = "profile_style_tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    style_tag_id = db.Column(db.Integer, db.ForeignKey("style_tags.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    style_tag = db.relationship("StyleTag", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("profile_id", "style_tag_id", name="uq_profile_style_tag"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "style_tag": self.style_tag.to_dict() if self.style_tag else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
