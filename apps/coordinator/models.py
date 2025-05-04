from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey


@dataclass
class CoordinatorModel(db.Model):
    __tablename__ = "coordinator"
    
    id: int
    name: str
    email: str
    tel: str
    
    
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    tel = db.Column(db.String(), nullable=False)

    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete='CASCADE'))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id", ondelete='CASCADE'))
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id", ondelete='CASCADE'))
    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())    
    flag_delete = db.Column(db.Boolean, default=False) 
    
   

   
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "tel": self.tel,
            "coordinators": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "tel": c.tel
                } for c in self.coordinator
            ]
        }
 