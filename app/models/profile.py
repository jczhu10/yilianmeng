from app import db
from datetime import datetime


class Profile(db.Model):
    """创作者档案：仅存基础信息。
    - identity：身份（学生 / 艺术爱好者 / 艺术相关工作者）
    - 风格词汇 -> style_tags 字典 + profile_style_tags 关联表
    - 技能 -> skills 字典 + profile_skills 关联表
    - 工作经历 -> work_experiences 表
    - 教育经历 -> education_experiences 表
    - 能力证明 -> ability_proofs 表
    """
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    identity = db.Column(db.String(30), nullable=False, default="艺术爱好者",
                         comment="身份：学生 / 艺术爱好者 / 艺术相关工作者")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    profile_skills = db.relationship(
        "ProfileSkill", backref="profile", lazy=True, cascade="all, delete-orphan"
    )
    profile_style_tags = db.relationship(
        "ProfileStyleTag", backref="profile", lazy=True, cascade="all, delete-orphan"
    )
    work_experiences = db.relationship(
        "WorkExperience", backref="profile", lazy=True, cascade="all, delete-orphan"
    )
    education_experiences = db.relationship(
        "EducationExperience", backref="profile", lazy=True, cascade="all, delete-orphan"
    )
    ability_proofs = db.relationship(
        "AbilityProof", backref="profile", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, with_relations=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "identity": self.identity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if with_relations:
            data["style_tags"] = [ps.style_tag.to_dict() for ps in self.profile_style_tags if ps.style_tag]
            data["skills"] = [ps.skill.to_dict() for ps in self.profile_skills if ps.skill]
            data["work_experiences"] = [w.to_dict() for w in self.work_experiences]
            data["education_experiences"] = [e.to_dict() for e in self.education_experiences]
            data["ability_proofs"] = [a.to_dict() for a in self.ability_proofs]
        return data
