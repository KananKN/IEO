from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey


@dataclass
class FeesModel(db.Model):
    __tablename__ = "fees"
    
    id: int
    name:str
    description:str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            
        }
        
@dataclass
class SupplierTypeModel(db.Model):
    __tablename__ = "supplier_type"
    
    id: int
    name:str
    description:str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    supplier_type = db.relationship(
        "SupplierModel", backref="supplier_type", )
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            
        }        
    
@dataclass
class SupplierModel(db.Model):
    __tablename__ = "supplier"
    
    id: int
    supplierType_id: int
    name:str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    tax = db.Column(db.String(),unique=True, nullable=True)
    address = db.Column(db.String(), nullable=True)
    tel = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(), nullable=True)
    supplierType_id = db.Column(db.Integer, db.ForeignKey("supplier_type.id", ondelete='SET NULL'))
    country_id = db.Column(db.Integer, db.ForeignKey("country.id", ondelete='CASCADE'))
    name_coondinator = db.Column(db.String(), nullable=False)
    files_supplier = db.relationship(
        "FileSupplierModel", backref="files_supplier", cascade="all, delete", lazy=True )
    
   
    
 
    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tax": self.tax,
            "address": self.address,
            "tel": self.tel,
            "email": self.email,
            "supplierType_id": self.supplierType_id,
            "country_id": self.country_id,
            "name_coondinator": self.name_coondinator,
            
        }        

@dataclass
class FileSupplierModel(db.Model):
    __tablename__ = 'files_supplier'
    id :int
    supplier_id :int

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), default=False)  # ชื่อไฟล์
    filepath = db.Column(db.String(512), default=False)  # พาธของไฟล์
    file_type  = db.Column(db.Integer, comment='1:supplier')
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete='CASCADE'))
    flag_delete = db.Column(db.Boolean, default=False)   
    
    
class ProductSupplierAssociation(db.Model):
    __tablename__ = 'product_supplier_association'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product_for_sales.id',ondelete='CASCADE'  ))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id' ,ondelete='CASCADE'))

    # ข้อมูลเพิ่มเติมที่อยากเก็บ (optional)
    status = db.Column(db.String(20), default='active')  # active, pending
    assigned_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.Text)

    product = db.relationship('ProductForSalesModel', backref='supplier_links')
    supplier = db.relationship('SupplierModel', backref='product_links', passive_deletes=True)    