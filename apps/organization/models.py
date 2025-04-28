from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey


@dataclass
class OrganizationModel(db.Model):
    __tablename__ = "organization"
    
    id: int
    name:str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    tax = db.Column(db.String(),unique=True, nullable=True)
    address = db.Column(db.String(), nullable=True)
    tel = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id", ondelete='CASCADE'))
    name_coondinator = db.Column(db.String(), nullable=False)
    files_organization = db.relationship(
        "FileOrganizationModel", backref="files_organization", cascade="all, delete", lazy=True )
    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tax": self.tax,
            "address": self.address,
            "tel": self.tel,
            "email": self.email,
            "supplierType_id": self.supplierType_id,
            "country_id": self.country_id,
            "name_coondinator": self.name_coondinator,
            
        }
@dataclass
class FileOrganizationModel(db.Model):
    __tablename__ = 'files_organization'
    id :int
    organization_id :int

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), default=False)  # ชื่อไฟล์
    filepath = db.Column(db.String(512), default=False)  # พาธของไฟล์
    file_type  = db.Column(db.Integer, comment='1:organization')
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id", ondelete='CASCADE'))
    flag_delete = db.Column(db.Boolean, default=False)    

@dataclass        
class ProductOrganizationAssociation(db.Model):
    __tablename__ = 'product_organization_association'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product_for_sales.id', ondelete='CASCADE'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id' , ondelete='CASCADE'))

    # ข้อมูลเพิ่มเติมที่อยากเก็บ (optional)
    status = db.Column(db.String(20), default='active')  # active, pending
    assigned_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.Text)

    product = db.relationship('ProductForSalesModel', backref='organization_links')
    employee = db.relationship('OrganizationModel', backref='product_links')    
 