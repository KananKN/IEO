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
    status_company: int
    zip_code: str
    shipping_address: str
    office_number: str
    fax_number: str
    bank: str
    account_number: str
    bank_branch: str
    type_bank: str
    foreign_banks: str
    swiftCode: str
    bank_address: str
    note: str
    account_name:str
    foreign_banks_name:str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    tax = db.Column(db.String(),unique=True, nullable=True)
    address = db.Column(db.String(), nullable=True)
    tel = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id", ondelete='CASCADE'))
    name_coondinator = db.Column(db.String(), nullable=True)
    files_organization = db.relationship(
        "FileOrganizationModel", backref="files_organization", cascade="all, delete", lazy=True )
    
    status_company = db.Column(db.Integer, comment='1:headquarters,2:branch')
    zip_code = db.Column(db.String(), nullable=False,server_default='00000')
    shipping_address = db.Column(db.String(), nullable=True)
    office_number = db.Column(db.String(), nullable=True)
    fax_number = db.Column(db.String(), nullable=True)
    bank = db.Column(db.String(), nullable=True)
    account_number = db.Column(db.String(), nullable=True)
    bank_branch = db.Column(db.String(), nullable=True)
    type_bank = db.Column(db.Integer, nullable=True, comment='1:savings,2:daily_current')
    foreign_banks = db.Column(db.String(), nullable=True)
    swiftCode = db.Column(db.String(), nullable=True)
    bank_address = db.Column(db.String(), nullable=True)
    note = db.Column(db.String(), nullable=True)
    account_name = db.Column(db.String(), nullable=True)
    foreign_banks_name = db.Column(db.String(), nullable=True)
    
    coordinator = db.relationship(
        "CoordinatorModel", backref="organization", cascade="all, delete", lazy=True )   
    
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
            "coordinators": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "tel": c.tel
                } for c in self.coordinator
            ]
            
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
    
 