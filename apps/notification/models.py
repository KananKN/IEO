from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from decimal import Decimal


class LineConfigModel(db.Model):
    __tablename__ = "line_config"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    channel_access_token = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=True)   # ส่งหาคน
    group_id = db.Column(db.String, nullable=True)  # ส่งหากลุ่ม
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "channel_access_token": self.channel_access_token,
            "user_id": self.user_id,
            "name": self.name,  
            }