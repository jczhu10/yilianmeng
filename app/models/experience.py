from app import db
from datetime import datetime


class WorkExperience(db.Model):
    """工作经历表（多对一 profile）"""
    __tablename__ = "work_experiences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    company_name = db.Column(db.String(100), nullable=False, comment="公司名称")
    position = db.Column(db.String(80), nullable=False, comment="职位名称")
    start_date = db.Column(db.Date, nullable=False, comment="入职时间")
    end_date = db.Column(db.Date, nullable=True, comment="离职时间，空=至今")
    is_current = db.Column(db.Boolean, default=False, comment="是否当前在职")
    description = db.Column(db.Text, default="", comment="工作描述")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship(
        "WorkExperienceImage", backref="work_experience", lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self, with_images=True):
        data = {
            "id": self.id,
            "profile_id": self.profile_id,
            "company_name": self.company_name,
            "position": self.position,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_current": self.is_current,
            "description": self.description,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if with_images:
            data["images"] = [img.to_dict() for img in self.images]
        return data


class WorkExperienceImage(db.Model):
    """工作经历图片证明（上限5张/经历）"""
    __tablename__ = "work_experience_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_experience_id = db.Column(db.Integer, db.ForeignKey("work_experiences.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False, comment="图片地址")
    caption = db.Column(db.String(200), default="", comment="图片说明")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "work_experience_id": self.work_experience_id,
            "image_url": self.image_url,
            "caption": self.caption,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class EducationExperience(db.Model):
    """教育经历表（多对一 profile，上限10条/人）"""
    __tablename__ = "education_experiences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    school_level = db.Column(db.String(20), nullable=False, comment="学段：小学 / 中学 / 大学")
    school_name = db.Column(db.String(100), nullable=False, comment="学校名称")
    start_year = db.Column(db.Integer, nullable=False, comment="入学年份，如2020")
    end_year = db.Column(db.Integer, nullable=True, comment="毕业年份，空=在读")
    degree = db.Column(db.String(20), nullable=True, comment="学历层级：本科/硕士/博士（仅大学）")
    major = db.Column(db.String(80), nullable=True, comment="专业名称（仅大学）")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "school_level": self.school_level,
            "school_name": self.school_name,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "degree": self.degree,
            "major": self.major,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
