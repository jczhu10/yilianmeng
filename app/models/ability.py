from app import db
from datetime import datetime


class AbilityProof(db.Model):
    """其他能力证明表（多对一 profile）"""
    __tablename__ = "ability_proofs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False, comment="标题")
    description = db.Column(db.Text, default="", comment="详细介绍")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = db.relationship(
        "AbilityProofFile", backref="ability_proof", lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self, with_files=True):
        data = {
            "id": self.id,
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if with_files:
            data["files"] = [f.to_dict() for f in self.files]
        return data


class AbilityProofFile(db.Model):
    """能力证明文件（上限10个/证明）"""
    __tablename__ = "ability_proof_files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ability_proof_id = db.Column(db.Integer, db.ForeignKey("ability_proofs.id"), nullable=False)
    file_url = db.Column(db.String(255), nullable=False, comment="文件地址")
    file_name = db.Column(db.String(200), default="", comment="文件名")
    file_type = db.Column(db.String(20), default="image", comment="image/pdf/doc/video等")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ability_proof_id": self.ability_proof_id,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
